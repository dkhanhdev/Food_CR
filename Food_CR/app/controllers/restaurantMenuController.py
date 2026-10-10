from flask import render_template, request, jsonify
from app.dao.dishesDao import DishesDao
from app.models.model import UserRole
from flask_login import current_user
import cloudinary.uploader


class RestaurantMenuController:

    @staticmethod
    def create_dishes():
        if current_user.role != UserRole.RESTAURANT:
            return jsonify({"message": "Không có quyền thực hiện thao tác này"}), 403

        name = request.form.get("name")
        price = request.form.get("price")
        category = request.form.get("category")
        description = request.form.get("description")
        avatar_file = request.files.get("image")

        required_fields = {"name": name, "price": price, "category": category, "description": description}
        missing_fields = [key for key, value in required_fields.items() if value in [None, ""]]

        if missing_fields:
            return jsonify({
                "message": "Thiếu thông tin bắt buộc",
                "missing_fields": missing_fields
            }), 400

        image_url = None
        if avatar_file and avatar_file.filename:
            try:
                res = cloudinary.uploader.upload(
                    avatar_file,
                    transformation=[
                        {"width": 1000, "height": 1000, "crop": "limit"},
                        {"quality": "auto:good"},
                        {"fetch_format": "auto"}
                    ]
                )
                image_url = res["secure_url"]
            except Exception as e:
                return jsonify({"message": "Upload ảnh thất bại", "error": str(e)}), 400

        try:
            new_dish = DishesDao.create_dishes(
                name=name,
                price=float(price),
                category=category,
                restaurant_id=current_user.id,
                description=description,
                image=image_url
            )

            if not new_dish:
                return jsonify({"message": "Tạo món ăn thất bại"}), 400

            return jsonify({"message": "successful"}), 200

        except ValueError as ve:
            return jsonify({"message": str(ve)}), 400
        except Exception as e:
            return jsonify({"message": "Lỗi hệ thống", "error": str(e)}), 500

    @staticmethod
    def delete_dishes(dishes_id):
        if current_user.role != UserRole.RESTAURANT:
            return jsonify({"message": "Không có quyền thực hiện thao tác này"}), 403

        try:
            dish = DishesDao.delete_dishes(dishes_id, current_user.id)
        except ValueError as ve:
            return jsonify({"message": str(ve)}), 400
        except Exception as e:
            print(f"Lỗi: {e}")  # hiện ngay trên terminal chạy Flask
            return jsonify({"message": "Lỗi hệ thống", "error": str(e)}), 500

        if not dish:
            return jsonify({"message": "Món ăn không tồn tại"}), 404

        return jsonify({"message": "Xóa món ăn thành công"}), 200

    @staticmethod
    def change_dishes_status():
        if current_user.role != UserRole.RESTAURANT:
            return jsonify({"message": "Không có quyền thực hiện thao tác này"}), 403

        id_dishes = request.get_json().get("id_dishes")

        dish = DishesDao.change_dishe_status(id_dishes, current_user.id) if id_dishes else None

        if not dish:
            return jsonify({"message": "Thiếu id_dishes hoặc không tìm thấy món ăn"}), 400

        return jsonify({
            "message": "Cập nhật trạng thái thành công",
            "dish_id": dish.id,
            "active": dish.active
        }), 200
        

    @staticmethod
    def get_dishes_stats():
        if current_user.role != UserRole.RESTAURANT:
            return jsonify({"message": "Không có quyền thực hiện thao tác này"}), 403

        return jsonify(DishesDao.get_dishes_stats(current_user.id)), 200

    @staticmethod
    def get_top_recommended_dishes():
        limit = request.args.get("limit", 10, type=int)
        dishes = DishesDao.get_top_recommended_dishes(limit=limit)

        data = []
        for d in dishes:
            data.append({
                "id": d.id,
                "name": d.name,
                "price": d.price,
                "image": d.image,
                "restaurant_id": d.restaurant_id
            })

        return jsonify({
            "data": data
        }), 200


    @staticmethod
    def index():

        return render_template(
            "retaurantMenuPage.html",
            title="Quản lý thực đơn"
        )