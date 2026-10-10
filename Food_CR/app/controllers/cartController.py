from flask import jsonify, request,flash
from flask_login import current_user
from app.dao.cartDao import CartDao
from app.dao.restaurantsDao import RestaurantsDao
from app.dao.vouchersDao import VouchersDao


class CartController:

    @staticmethod
    def get_cart(restaurant_id):
        restaurant = RestaurantsDao.get_restaurant_by_id(restaurant_id)
        if not restaurant:
            return jsonify({"success": False, "message": "Restaurant not found"}), 404

        cart = CartDao.get_cart_by_user_and_restaurant(current_user.id, restaurant_id)
        if not cart:
            return jsonify({"id": None, "restaurant_id": restaurant_id, "note": None, "items": [], "total": 0}), 200

        items = []
        total = 0
        for item in cart.items:
            subtotal = item.price * item.quantity
            total += subtotal
            items.append({
                "id": item.id,
                "dish_id": item.dish_id,
                "dish_name": item.dish.name,
                "image": item.dish.image,
                "quantity": item.quantity,
                "price": item.price,
                "subtotal": subtotal,
            })

        return jsonify({
            "id": cart.id,
            "restaurant_id": cart.restaurant_id,
            "note": cart.note,
            "items": items,
            "total": total,
        }), 200

    @staticmethod
    def add_item(restaurant_id):
        restaurant = RestaurantsDao.get_restaurant_by_id(restaurant_id)
        if not restaurant:
            return jsonify({"success": False, "message": "Restaurant not found"}), 404
        data = request.get_json() or {}
        dish_id = data.get("dish_id")
        quantity = data.get("quantity", 1)

        if not dish_id:
            return jsonify({"success": False, "message": "dish_id is required"}), 400

        try:
            item = CartDao.add_item(current_user.id, restaurant_id, dish_id, quantity=quantity)
        except ValueError as e:
            return jsonify({"success": False, "message": str(e)}), 400

        if not item:
            return jsonify({"success": False, "message": "Dish not found"}), 404

        return jsonify({
            "success": True,
            "id": item.id,
            "cart_id": item.cart_id,
            "dish_id": item.dish_id,
            "quantity": item.quantity,
            "price": item.price,
        }), 200

    @staticmethod
    def update_item(restaurant_id, cart_item_id):
        item = CartDao.get_item_by_id(cart_item_id)
        if not item or item.cart.user_id != current_user.id or item.cart.restaurant_id != restaurant_id:
            return jsonify({"success": False, "message": "Cart item not found"}), 404

        data = request.get_json() or {}
        quantity = data.get("quantity")
        if quantity is None:
            return jsonify({"success": False, "message": "quantity is required"}), 400

        try:
            item = CartDao.update_item_quantity(cart_item_id, quantity)
        except ValueError as e:
            return jsonify({"success": False, "message": str(e)}), 400

        if not item:
            return jsonify({"success": True, "removed": True}), 200

        return jsonify({
            "success": True,
            "id": item.id,
            "quantity": item.quantity,
        }), 200

    @staticmethod
    def remove_item(restaurant_id, cart_item_id):
        item = CartDao.get_item_by_id(cart_item_id)
        if not item or item.cart.user_id != current_user.id or item.cart.restaurant_id != restaurant_id:
            return jsonify({"success": False, "message": "Cart item not found"}), 404
        CartDao.remove_item(cart_item_id)
        return jsonify({"success": True}), 200

    @staticmethod
    def validate_voucher(restaurant_id):
        cart = CartDao.get_cart_by_user_and_restaurant(current_user.id, restaurant_id)
        if not cart or not cart.items:
            return jsonify({"valid": False, "message": "Giỏ hàng đang trống"}), 400

        data = request.get_json() or {}
        code = str(data.get("code") or "").strip().upper()
        if not code:
            return jsonify({"valid": False, "message": "Vui lòng nhập mã giảm giá"}), 400

        voucher = VouchersDao.get_order_voucher_by_code(code, restaurant_id)
        if not voucher or not voucher.is_valid_now():
            return jsonify({"valid": False, "message": "Mã giảm giá không hợp lệ hoặc đã hết hạn"}), 404

        subtotal = sum(item.price * item.quantity for item in cart.items)
        if subtotal < (voucher.minimum_order or 0):
            return jsonify({
                "valid": False,
                "message": f"Đơn hàng tối thiểu {voucher.minimum_order:,.0f}đ để dùng mã này"
            }), 400

        discount_amount = subtotal - voucher.apply_discount(subtotal)

        return jsonify({
            "valid": True,
            "discount_amount": discount_amount,
            "final_subtotal": subtotal - discount_amount,
            "voucher": {
                "id": voucher.id,
                "code": voucher.code,
                "name": voucher.name,
            }
        }), 200

    @staticmethod
    def clear_cart(restaurant_id):
        cart = CartDao.get_cart_by_user_and_restaurant(current_user.id, restaurant_id)
        if not cart:
            return jsonify({"success": False, "message": "Cart not found"}), 404
        CartDao.clear_cart(cart.id)
        return jsonify({"success": True}), 200
