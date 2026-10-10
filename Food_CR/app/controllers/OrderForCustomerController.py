from flask import render_template, jsonify, request, redirect, url_for
from flask_login import current_user, login_required
from app.dao.ordersDao import OrdersDao
from app.models.model import UserRole

class OrderForCustomerController:

    @staticmethod
    def loadOrders():
        try:
            status = request.args.get("status", None)
            keyword = request.args.get("keyword", None)
            data = OrdersDao.get_orders_customer(status=status, keyword=keyword)
            return jsonify({
                "success": True,
                "data": data
            }), 200
        except Exception as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500
        
    @staticmethod
    def get_order_detail_customer(order_id):
        data = OrdersDao.get_order_by_id_and_customer(order_id)
        if not data:
            return jsonify({
                "success": False,
                "message": "Không tìm thấy đơn hàng"
            }), 404

        return jsonify({
            "success": True,
            "data": data
        }), 200
        
    @staticmethod
    def index():
        if current_user.role == UserRole.ADMIN:
            return redirect('/admin/')
        elif current_user.role == UserRole.RESTAURANT:
            return redirect(url_for('me_bp.me_page'))
        return render_template("OrderForCustomer.html")

    @staticmethod
    def order_detail_page(order_id):
        if current_user.role == UserRole.ADMIN:
            return redirect('/admin/')
        elif current_user.role == UserRole.RESTAURANT:
            return redirect(url_for('me_bp.me_page'))
        return render_template("OrderForCustomerDetail.html", order_id=order_id)

    @staticmethod
    @login_required
    def create_order():
        data = request.get_json() or {}
        restaurant_id = data.get("restaurant_id")
        note = data.get("note", "")
        shipping_fee = data.get("shipping_fee", 20000)
        customer_name = (data.get("customer_name") or "").strip()
        customer_phone = (data.get("customer_phone") or "").strip()
        customer_email = (data.get("customer_email") or "").strip()
        delivery_address = (data.get("delivery_address") or "").strip()
        voucher_code = (data.get("voucher_code") or "").strip() or None

        if not restaurant_id:
            return jsonify({"success": False, "message": "restaurant_id là bắt buộc"}), 400
        if not customer_name or not customer_phone or not delivery_address:
            return jsonify({"success": False, "message": "Vui lòng điền đầy đủ họ tên, số điện thoại và địa chỉ giao hàng"}), 400

        result, error = OrdersDao.create_order_from_cart(
            user_id=current_user.id,
            restaurant_id=int(restaurant_id),
            note=note,
            shipping_fee=int(shipping_fee),
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            delivery_address=delivery_address,
            voucher_code=voucher_code,
        )

        if error:
            return jsonify({"success": False, "message": error}), 400

        return jsonify({
            "success": True,
            "message": "Đặt hàng thành công",
            "order_id": result["order_id"],
            "total_amount": result["total_amount"],
            "created_at": result["created_at"],
            "payment_deadline": result["payment_deadline"],
        }), 201

    @staticmethod
    @login_required
    def expire_order(order_id):
        result, error = OrdersDao.expire_order(order_id)
        if error:
            return jsonify({"success": False, "message": error}), 400
        return jsonify({"success": True, "message": "Đơn hàng đã hết hạn"}), 200
