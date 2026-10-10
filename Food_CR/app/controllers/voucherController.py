from datetime import datetime, timezone
from flask import request, jsonify, abort
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.extensions import db
from app.models.model import Voucher, DiscountType, UserRole
from app.dao.dishesDao import DishesDao
from app.dao.vouchersDao import VouchersDao


class VoucherController:
    @staticmethod
    def _require_restaurant():
        if current_user.role != UserRole.RESTAURANT:
            abort(403)

        restaurant = current_user.restaurant
        if not restaurant:
            abort(403)

        return restaurant.id

    @staticmethod
    def _serialize_voucher(voucher):
        dishes = [
            {
                "id": link.dish.id,
                "name": link.dish.name,
                "price": link.dish.price,
                "active": link.dish.active,
            }
            for link in voucher.dish_links
            if link.dish
        ]

        return {
            "id": voucher.id,
            "name": voucher.name,
            "code": voucher.code,
            "description": voucher.description,
            "discount_type": voucher.discount_type.name if voucher.discount_type else None,
            "discount_value": voucher.discount_value,
            "minimum_order": voucher.minimum_order,
            "max_discount": voucher.max_discount,
            "start_date": voucher.start_date.isoformat() + "Z" if voucher.start_date else None,
            "end_date": voucher.end_date.isoformat() + "Z" if voucher.end_date else None,
            "usage_limit": voucher.usage_limit,
            "used_count": voucher.used_count,
            "restaurant_id": voucher.restaurant_id,
            "dish_ids": [dish["id"] for dish in dishes],
            "dishes": dishes,
            "scope": "DISH" if dishes else "ORDER",
            "active": voucher.active,
            "is_valid": voucher.is_valid_now(),
            "created_at": voucher.created_at.isoformat() if voucher.created_at else None,
            "created_updated_at": voucher.created_updated_at.isoformat() if voucher.created_updated_at else None,
        }

    @staticmethod
    def _validate_dish_ids(dish_ids, restaurant_id, exclude_voucher_id=None):
        if not isinstance(dish_ids, list):
            return None, {"dish_ids": "dish_ids phải là một danh sách"}

        if not dish_ids:
            return [], None

        if any(isinstance(dish_id, bool) or not isinstance(dish_id, int) for dish_id in dish_ids):
            return None, {"dish_ids": "Mỗi dish_id phải là số nguyên"}

        if len(dish_ids) != len(set(dish_ids)):
            return None, {"dish_ids": "Danh sách món không được trùng"}

        dishes = DishesDao.get_active_by_ids_and_restaurant(dish_ids, restaurant_id)
        found_ids = {dish.id for dish in dishes}
        invalid_ids = [dish_id for dish_id in dish_ids if dish_id not in found_ids]
        if invalid_ids:
            return None, {
                "dish_ids": "Món không tồn tại, không hoạt động hoặc không thuộc nhà hàng này",
                "invalid_ids": invalid_ids,
            }

        dishes_by_id = {dish.id: dish for dish in dishes}

        conflicts = VouchersDao.get_dish_conflicts(dish_ids, restaurant_id, exclude_voucher_id)
        if conflicts:
            return None, {
                "dish_ids": [
                    {
                        "dish_id": dish_id,
                        "dish_name": dishes_by_id[dish_id].name,
                        "voucher_code": voucher.code,
                    }
                    for dish_id, voucher in conflicts.items()
                ],
            }

        return [dishes_by_id[dish_id] for dish_id in dish_ids], None

    @staticmethod
    def _parse_datetime(value, field_name):
        if not value:
            raise ValueError(f"{field_name} là bắt buộc")

        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"{field_name} không đúng định dạng datetime")

        # Chuẩn hoá về naive-UTC để nhất quán với datetime.utcnow() dùng trong is_valid_now().
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

    @staticmethod
    def _validate_payload(data, is_update=False):
        if not data:
            return None, {"message": "Invalid JSON"}

        cleaned = {}
        errors = {}

        allowed_fields = {
            "name", "code", "discount_type", "discount_value",
            "max_discount", "start_date", "end_date", "usage_limit",
            "dish_ids"
        }

        for key in data:
            if key not in allowed_fields:
                continue
            cleaned[key] = data.get(key)

        required_fields = ["name", "code", "discount_value", "start_date", "end_date", "usage_limit"]
        if not is_update:
            for field in required_fields:
                if cleaned.get(field) in [None, ""]:
                    errors[field] = f"{field} là bắt buộc"
            if "dish_ids" not in cleaned:
                cleaned["dish_ids"] = []

        if "dish_ids" in cleaned and not isinstance(cleaned["dish_ids"], list):
            errors["dish_ids"] = "dish_ids phải là một danh sách"

        if "discount_type" in cleaned:
            if cleaned["discount_type"] in [None, ""]:
                cleaned["discount_type"] = DiscountType.PERCENTAGE
            else:
                try:
                    cleaned["discount_type"] = DiscountType[str(cleaned["discount_type"]).upper()]
                except KeyError:
                    errors["discount_type"] = "discount_type phải là PERCENTAGE hoặc FIXED_AMOUNT"

        if "name" in cleaned and cleaned["name"] is not None:
            cleaned["name"] = str(cleaned["name"]).strip()
            if not cleaned["name"]:
                errors["name"] = "Tên voucher không được để trống"

        if "code" in cleaned and cleaned["code"] is not None:
            cleaned["code"] = str(cleaned["code"]).strip().upper()
            if not cleaned["code"]:
                errors["code"] = "Mã voucher không được để trống"

        number_fields = ["discount_value", "max_discount", "usage_limit"]
        for field in number_fields:
            if field in cleaned and cleaned[field] not in [None, ""]:
                try:
                    if field == "usage_limit":
                        cleaned[field] = int(cleaned[field])
                    else:
                        cleaned[field] = float(cleaned[field])
                except (TypeError, ValueError):
                    errors[field] = f"{field} phải là số hợp lệ"

        if "discount_value" in cleaned and isinstance(cleaned.get("discount_value"), (int, float)):
            if cleaned["discount_value"] <= 0:
                errors["discount_value"] = "discount_value phải lớn hơn 0"

        if "usage_limit" in cleaned and isinstance(cleaned.get("usage_limit"), int):
            if cleaned["usage_limit"] < 1:
                errors["usage_limit"] = "usage_limit phải >= 1"

        if "start_date" in cleaned and cleaned["start_date"] not in [None, ""]:
            try:
                cleaned["start_date"] = VoucherController._parse_datetime(cleaned["start_date"], "start_date")
            except ValueError as e:
                errors["start_date"] = str(e)

        if "end_date" in cleaned and cleaned["end_date"] not in [None, ""]:
            try:
                cleaned["end_date"] = VoucherController._parse_datetime(cleaned["end_date"], "end_date")
            except ValueError as e:
                errors["end_date"] = str(e)

        if (
            "start_date" in cleaned and "end_date" in cleaned
            and isinstance(cleaned.get("start_date"), datetime)
            and isinstance(cleaned.get("end_date"), datetime)
        ):
            if cleaned["start_date"] >= cleaned["end_date"]:
                errors["end_date"] = "end_date phải lớn hơn start_date"

        discount_value = cleaned.get("discount_value")
        discount_type = cleaned.get("discount_type", DiscountType.PERCENTAGE if not is_update else None)
        if discount_type == DiscountType.PERCENTAGE and isinstance(discount_value, (int, float)) and discount_value > 100:
            errors["discount_value"] = "Phần trăm giảm không được vượt quá 100"

        if errors:
            return None, {"message": "Dữ liệu không hợp lệ", "errors": errors}

        return cleaned, None

    @staticmethod
    @login_required
    def list_vouchers():
        restaurant_id = VoucherController._require_restaurant()
        vouchers = VouchersDao.get_all_by_restaurant(restaurant_id)

        return jsonify({
            "items": [VoucherController._serialize_voucher(v) for v in vouchers]
        }), 200

    @staticmethod
    @login_required
    def list_dishes():
        restaurant_id = VoucherController._require_restaurant()
        dishes = DishesDao.get_list_dishes_by_restaurant(restaurant_id)

        return jsonify({
            "items": [
                {
                    "id": dish.id,
                    "name": dish.name,
                    "description": dish.description,
                    "price": dish.price,
                    "category": dish.category.value if dish.category else None,
                    "image": dish.image,
                }
                for dish in dishes
            ]
        }), 200

    @staticmethod
    @login_required
    def create_voucher():
        restaurant_id = VoucherController._require_restaurant()

        data = request.get_json()
        payload, error = VoucherController._validate_payload(data, is_update=False)
        if error:
            return jsonify(error), 400

        dishes, dish_error = VoucherController._validate_dish_ids(
            payload["dish_ids"],
            restaurant_id
        )
        if dish_error:
            return jsonify({
                "message": "Danh sách món không hợp lệ",
                "errors": dish_error,
            }), 400

        try:
            existing = VouchersDao.get_by_code_any_status(payload["code"])
            if existing and existing.active:
                return jsonify({
                    "message": "Mã voucher đã tồn tại"
                }), 409

            if existing and not existing.active:
                # Mã này thuộc một voucher đã bị xoá (soft-delete) - tái sử dụng lại hàng đó
                # thay vì insert mới, vì cột code là unique ở cấp DB.
                existing.name = payload["name"]
                existing.discount_type = payload.get("discount_type", DiscountType.PERCENTAGE)
                existing.discount_value = payload["discount_value"]
                existing.minimum_order = 0
                existing.max_discount = payload.get("max_discount")
                existing.start_date = payload["start_date"]
                existing.end_date = payload["end_date"]
                existing.usage_limit = payload["usage_limit"]
                existing.used_count = 0
                existing.restaurant_id = restaurant_id
                existing.active = True
                VouchersDao.replace_dishes(existing, dishes)
                voucher = VouchersDao.save(existing)
            else:
                voucher = Voucher(
                    name=payload["name"],
                    code=payload["code"],
                    discount_type=payload.get("discount_type", DiscountType.PERCENTAGE),
                    discount_value=payload["discount_value"],
                    minimum_order=0,
                    max_discount=payload.get("max_discount"),
                    start_date=payload["start_date"],
                    end_date=payload["end_date"],
                    usage_limit=payload["usage_limit"],
                    restaurant_id=restaurant_id
                )
                voucher = VouchersDao.create_voucher(voucher, dishes)

            return jsonify({
                "message": "Tạo voucher thành công",
                "voucher": VoucherController._serialize_voucher(voucher)
            }), 201

        except IntegrityError:
            db.session.rollback()
            return jsonify({
                "message": "Mã voucher đã tồn tại"
            }), 409
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({
                "message": "Không thể tạo voucher"
            }), 500

    @staticmethod
    @login_required
    def update_voucher(voucher_id):
        restaurant_id = VoucherController._require_restaurant()

        voucher = VouchersDao.get_by_id_and_restaurant(voucher_id, restaurant_id)
        if not voucher:
            return jsonify({"message": "Voucher không tồn tại"}), 404

        data = request.get_json()
        payload, error = VoucherController._validate_payload(data, is_update=True)
        if error:
            return jsonify(error), 400

        dishes = None
        if "dish_ids" in payload:
            dishes, dish_error = VoucherController._validate_dish_ids(
                payload["dish_ids"],
                restaurant_id,
                exclude_voucher_id=voucher.id
            )
            if dish_error:
                return jsonify({
                    "message": "Danh sách món không hợp lệ",
                    "errors": dish_error,
                }), 400

        try:
            for key, value in payload.items():
                if key != "dish_ids":
                    setattr(voucher, key, value)

            if dishes is not None:
                VouchersDao.replace_dishes(voucher, dishes)

            voucher = VouchersDao.save(voucher)

            return jsonify({
                "message": "Cập nhật voucher thành công",
                "voucher": VoucherController._serialize_voucher(voucher)
            }), 200

        except IntegrityError:
            db.session.rollback()
            return jsonify({
                "message": "Mã voucher đã tồn tại"
            }), 409
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({
                "message": "Không thể cập nhật voucher"
            }), 500

    @staticmethod
    @login_required
    def delete_voucher(voucher_id):
        restaurant_id = VoucherController._require_restaurant()

        voucher = VouchersDao.get_by_id_and_restaurant(voucher_id, restaurant_id)
        if not voucher:
            return jsonify({"message": "Voucher không tồn tại"}), 404

        VouchersDao.soft_delete(voucher)

        return jsonify({
            "message": "Xóa voucher thành công"
        }), 200