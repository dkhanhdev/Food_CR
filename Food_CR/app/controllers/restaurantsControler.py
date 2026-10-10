from app.dao.restaurantsDao import RestaurantsDao
from flask import jsonify, render_template, request, current_app, redirect, url_for
from flask_login import current_user
from app.models.model import UserRole, DiscountType
from app.dao.dishesDao import DishesDao
from app.dao.vouchersDao import VouchersDao
from app.models.model import VoucherDish, Voucher
from app.service.notificationByFCM import send_push_notification


class RestaurantsController:
    @staticmethod
    def get_all_restaurants():
        restaurants = RestaurantsDao.get_all_restaurants()

        data = []

        for r in restaurants:
            data.append({
                "id": r.id,
                "name": r.name,
                "address": r.address,
                "cover_image": r.cover_image,
                "cuisine_type": r.cuisine_type.value if r.cuisine_type else None,
                "opening_time":
                    r.opening_time.strftime("%H:%M")
                    if r.opening_time else None,
                "closing_time":
                    r.closing_time.strftime("%H:%M")
                    if r.closing_time else None
            })

        return jsonify({
            "data": data
        }), 200

    @staticmethod
    def get_restaurant_by_id(restaurant_id):
        restaurant = RestaurantsDao.get_restaurant_by_id(restaurant_id)
        if restaurant:
            user = restaurant.user
            return jsonify({
                "id": restaurant.id,
                "name": restaurant.name,
                "address": user.address if user else None,
                "avatar": user.avatar if user else None,
                "cover_image": restaurant.cover_image,
                "description": restaurant.description,
                "cuisine_type": restaurant.cuisine_type.value if restaurant.cuisine_type else None,
                "opening_time":
                    restaurant.opening_time.strftime("%H:%M")
                    if restaurant.opening_time else None,
                "closing_time":
                    restaurant.closing_time.strftime("%H:%M")
                    if restaurant.closing_time else None,
                "phonenumber": user.phonenumber if user else None,
                "email": user.email if user else None,
                "status": restaurant.status,
                "active": restaurant.active,
                "created_at": restaurant.created_at.isoformat() if restaurant.created_at else None,
                "created_updated_at": restaurant.created_updated_at.isoformat() if restaurant.created_updated_at else None
            }), 200
        else:
            return jsonify({'message': 'Restaurant not found'}), 404


    @staticmethod
    def get_list_dishes(restaurant_id):
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        category = request.args.get("category", None, type=str)
        keyword = request.args.get("q", None, type=str)

        pagination = DishesDao.get_list_dishes_by_restaurant(restaurant_id, page, per_page, category, keyword)

        dish_ids = [d.id for d in pagination.items]
        voucher_by_dish = {}
        if dish_ids:
            links = VoucherDish.query.join(Voucher).filter(
                VoucherDish.dish_id.in_(dish_ids),
                Voucher.active == True
            ).all()
            for link in links:
                if link.voucher.is_valid_now():
                    voucher_by_dish[link.dish_id] = link.voucher

        data = []
        for d in pagination.items:
            original_price = float(d.price) if d.price is not None else None
            voucher = voucher_by_dish.get(d.id)
            final_price = float(voucher.apply_discount(original_price)) if voucher and original_price is not None else original_price

            data.append({
                "id": d.id,
                "name": d.name,
                "category": d.category.value if d.category else None,
                "description": d.description,
                "price": original_price,
                "original_price": original_price,
                "final_price": final_price,
                "voucher_code": voucher.code if voucher else None,
                "voucher_label": (
                    f"-{voucher.discount_value:g}%" if voucher.discount_type == DiscountType.PERCENTAGE
                    else f"-{voucher.discount_value:,.0f}đ"
                ) if voucher else None,
                "image": d.image,
                "active": d.active
            })

        return jsonify({
            "data": data,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }), 200

    @staticmethod
    def get_active_vouchers(restaurant_id):
        vouchers = VouchersDao.get_public_order_vouchers(restaurant_id)

        data = []
        for v in vouchers:
            if v.discount_type == DiscountType.PERCENTAGE:
                label = f"Giảm {v.discount_value:g}%"
                if v.max_discount:
                    label += f" (tối đa {v.max_discount:,.0f}đ)"
            else:
                label = f"Giảm {v.discount_value:,.0f}đ"

            data.append({
                "code": v.code,
                "name": v.name,
                "description": v.description,
                "label": label,
                "minimum_order": v.minimum_order,
                "end_date": v.end_date.isoformat() + "Z" if v.end_date else None,
            })

        return jsonify({"items": data}), 200

    @staticmethod
    def open_restaurant(restaurant_id):
        if current_user.role != UserRole.ADMIN and current_user.id != restaurant_id:
            return jsonify({"success": False, "message": "Bạn không có quyền truy cập trang này."}), 403

        restaurant = RestaurantsDao.open_restaurant(restaurant_id)
        if not restaurant:
            return jsonify({"success": False, "message": "Restaurant not found"}), 404

        return jsonify({
            "success": True,
            "message": "Restaurant opened successfully",
            "id": restaurant.id,
            "is_open": restaurant.status
        }), 200

    @staticmethod
    def close_restaurant(restaurant_id):
        if current_user.role != UserRole.ADMIN and current_user.id != restaurant_id:
            return jsonify({"success": False, "message": "Bạn không có quyền truy cập trang này."}), 403

        restaurant = RestaurantsDao.close_restaurant(restaurant_id)
        if not restaurant:
            return jsonify({"success": False, "message": "Restaurant not found"}), 404

        return jsonify({
            "success": True,
            "message": "Restaurant closed successfully",
            "id": restaurant.id,
            "is_open": restaurant.status
        }), 200

    @staticmethod
    def get_recommended_dishes(restaurant_id):
        dish_id = request.args.get("dish_id", type=int)
        recommendations = RestaurantsDao.get_recommended_dishes(restaurant_id, dish_id)

        return jsonify({
            "data": recommendations
        }), 200

    @staticmethod
    def index(restaurant_id):
        if current_user.is_authenticated:
            if current_user.role == UserRole.ADMIN:
                return redirect('/admin/')
            elif current_user.role == UserRole.RESTAURANT:
                return redirect(url_for('me_bp.me_page'))
        return render_template(
            "restaurantDetail.html",
            title="Chi tiết nhà hàng"
        )
