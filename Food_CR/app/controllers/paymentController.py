import os

from flask import request, jsonify, render_template, current_app, redirect, url_for, flash
from flask_login import current_user, login_required

from app.extensions import db
from app.dao.cartDao import CartDao
from app.dao.orderDao import OrderDao
from app.dao.restaurantsDao import RestaurantsDao
from app.models.model import Order, Status, UserRole
from app.service.momoService import create_momo_payment, verify_momo_signature
from app.service.vnpayService import build_vnpay_url, verify_vnpay_signature, get_order_id_from_txn_ref
from app.service.notificationByEmail import send_order_payment_success_email


def _ipn_response(message, status_code=200):
    return jsonify({"message": message}), status_code


def _get_client_ip():
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "127.0.0.1"


class PaymentController:

    @staticmethod
    @login_required
    def checkout(restaurant_id):
        if current_user.role == UserRole.ADMIN:
            return redirect('/admin/')
        elif current_user.role == UserRole.RESTAURANT:
            return redirect(url_for('me_bp.me_page'))

        restaurant = RestaurantsDao.get_restaurant_by_id(restaurant_id)
        cart = CartDao.get_cart_by_user_and_restaurant(current_user.id, restaurant_id)
        if not restaurant or not cart or not cart.items:
            return redirect(url_for("restaurant_bp.index", restaurant_id=restaurant_id))

        cart_total = sum(item.price * item.quantity for item in cart.items)

        return render_template(
            "payment.html",
            restaurant=restaurant,
            cart=cart,
            cart_total=cart_total,
            customer=current_user,
        )

    @staticmethod
    @login_required
    def create_payment(restaurant_id):
        data = request.get_json(silent=True) or {}
        payment_method = data.get("payment")

        cart = CartDao.get_cart_by_user_and_restaurant(
            current_user.id,
            restaurant_id
        )

        if not cart:
            return jsonify({
                "success": False,
                "message": "Cart không tồn tại"
            }), 404

        if payment_method not in ("momo", "vnpay"):
            return jsonify({
                "success": False,
                "message": "Phương thức thanh toán không hợp lệ"
            }), 400

        try:
            order = OrderDao.create_order_from_cart(cart, data)

            if payment_method == "momo":
                redirect_url = os.getenv("MOMO_REDIRECT_URL", "http://127.0.0.1:5000/payment/return")
                ipn_url = os.getenv("MOMO_IPN_URL", "http://127.0.0.1:5000/api/payment/ipn")

                momo_res, momo_order_id, request_id = create_momo_payment(
                    amount=int(order.total_amount),
                    order_info=f"Thanh toan don hang #{order.id}",
                    redirect_url=redirect_url,
                    ipn_url=ipn_url,
                )

                if momo_res.get("resultCode") != 0:
                    db.session.rollback()
                    return jsonify({
                        "success": False,
                        "message": momo_res.get("message", "Không thể tạo thanh toán MoMo")
                    }), 400

                order.momo_order_id = momo_order_id
                order.momo_request_id = request_id
                db.session.commit()

                return jsonify({
                    "success": True,
                    "payment_url": momo_res["payUrl"],
                    "order_id": order.id,
                }), 200

            # payment_method == "vnpay"
            payment_url, txn_ref = build_vnpay_url(
                order_id=order.id,
                amount=order.total_amount,
                order_info=f"Thanh toan don hang #{order.id}",
                ip_addr=_get_client_ip(),
            )
            db.session.commit()

            return jsonify({
                "success": True,
                "payment_url": payment_url,
                "order_id": order.id,
            }), 200

        except ValueError as e:
            db.session.rollback()
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400

        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(e)
            return jsonify({
                "success": False,
                "message": "Không thể tạo thanh toán"
            }), 500

    @staticmethod
    @login_required
    def pay_existing_order(order_id):
        """Tạo payment_url cho một đơn ĐÃ TỒN TẠI (không tạo đơn mới).

        Dùng bởi paymentCountdown.html: đơn đã được tạo trước đó (qua
        /api/orders_customer/create), người dùng chọn MoMo/VNPay ngay tại
        trang chờ thanh toán rồi mới gọi API này để lấy link cổng thanh toán.
        """
        order = Order.query.get(order_id)
        if not order or order.user_id != current_user.id:
            return jsonify({
                "success": False,
                "message": "Không tìm thấy đơn hàng hoặc bạn không có quyền truy cập"
            }), 404

        if order.status != Status.PENDING_PAYMENT:
            return jsonify({
                "success": False,
                "message": "Đơn hàng này không ở trạng thái chờ thanh toán"
            }), 400

        data = request.get_json(silent=True) or {}
        payment_method = data.get("payment")

        if payment_method not in ("momo", "vnpay"):
            return jsonify({
                "success": False,
                "message": "Phương thức thanh toán không hợp lệ"
            }), 400

        try:
            if payment_method == "momo":
                redirect_url = os.getenv("MOMO_REDIRECT_URL", "http://127.0.0.1:5000/payment/return")
                ipn_url = os.getenv("MOMO_IPN_URL", "http://127.0.0.1:5000/api/payment/ipn")

                momo_res, momo_order_id, request_id = create_momo_payment(
                    amount=int(order.total_amount),
                    order_info=f"Thanh toan don hang #{order.id}",
                    redirect_url=redirect_url,
                    ipn_url=ipn_url,
                )

                if momo_res.get("resultCode") != 0:
                    return jsonify({
                        "success": False,
                        "message": momo_res.get("message", "Không thể tạo thanh toán MoMo")
                    }), 400

                order.momo_order_id = momo_order_id
                order.momo_request_id = request_id
                db.session.commit()

                return jsonify({
                    "success": True,
                    "payment_url": momo_res["payUrl"],
                    "order_id": order.id,
                }), 200

            # payment_method == "vnpay"
            payment_url, txn_ref = build_vnpay_url(
                order_id=order.id,
                amount=order.total_amount,
                order_info=f"Thanh toan don hang #{order.id}",
                ip_addr=_get_client_ip(),
            )

            return jsonify({
                "success": True,
                "payment_url": payment_url,
                "order_id": order.id,
            }), 200

        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(e)
            return jsonify({
                "success": False,
                "message": "Không thể tạo thanh toán"
            }), 500

    @staticmethod
    def payment_return():
        params = request.args.to_dict()

        result_code = params.get("resultCode")
        momo_order_id = params.get("orderId")

        is_valid_signature = verify_momo_signature(params)
        order = OrderDao.get_order_by_momo_order_id(momo_order_id)

        if is_valid_signature and result_code == "0" and order:
            order, updated = OrderDao.mark_order_paid_momo(order.id, momo_order_id)

            if updated and order.customer_email:
                try:
                    send_order_payment_success_email(
                        recipient=order.customer_email,
                        order_id=order.id,
                        total_amount=order.total_amount,
                        restaurant_name=order.restaurant.name if order.restaurant else "Nhà hàng"
                    )
                except Exception as email_error:
                    current_app.logger.exception(email_error)

            flash("Thanh toán thành công!", "success")
        else:
            if order:
                OrderDao.mark_order_payment_failed(order.id)
            flash("Thanh toán chưa thành công, vui lòng thử lại.", "danger")

        if order:
            return redirect(url_for("orderCustomer_bp.order_detail_page", order_id=order.id))
        return redirect(url_for("orderCustomer_bp.index"))

    @staticmethod
    def payment_ipn():
        # MoMo gọi IPN bằng POST kèm JSON body (khác GET query string của VNPay)
        params = request.get_json(silent=True) or {}

        try:
            if not verify_momo_signature(params):
                return _ipn_response("Invalid signature", 400)

            momo_order_id = params.get("orderId")
            result_code = params.get("resultCode")

            order = OrderDao.get_order_by_momo_order_id(momo_order_id)
            if not order:
                return _ipn_response("Order not found", 404)

            expected_amount = int(order.total_amount)
            if int(params.get("amount", 0)) != expected_amount:
                return _ipn_response("Invalid amount", 400)

            if result_code == "0":
                order, updated = OrderDao.mark_order_paid_momo(order.id, momo_order_id)

                if updated and order.customer_email:
                    try:
                        send_order_payment_success_email(
                            recipient=order.customer_email,
                            order_id=order.id,
                            total_amount=order.total_amount,
                            restaurant_name=order.restaurant.name if order.restaurant else "Nhà hàng"
                        )
                    except Exception as email_error:
                        current_app.logger.exception(email_error)
            else:
                OrderDao.mark_order_payment_failed(order.id)

            return _ipn_response("Confirm Success", 200)

        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(e)
            return _ipn_response("Unknown error", 500)

    @staticmethod
    def vnpay_return():
        params = request.args.to_dict()

        is_valid_signature = verify_vnpay_signature(params)
        response_code = params.get("vnp_ResponseCode")
        order_id = get_order_id_from_txn_ref(params.get("vnp_TxnRef"))

        if is_valid_signature and response_code == "00" and order_id:
            order, updated = OrderDao.mark_order_paid_vnpay(order_id)

            if order and updated and order.customer_email:
                try:
                    send_order_payment_success_email(
                        recipient=order.customer_email,
                        order_id=order.id,
                        total_amount=order.total_amount,
                        restaurant_name=order.restaurant.name if order.restaurant else "Nhà hàng"
                    )
                except Exception as email_error:
                    current_app.logger.exception(email_error)

            if order:
                flash("Thanh toán thành công!", "success")
            else:
                flash("Không tìm thấy đơn hàng tương ứng.", "danger")
        else:
            if order_id:
                OrderDao.mark_order_payment_failed(order_id)
            flash("Thanh toán chưa thành công, vui lòng thử lại.", "danger")

        if order_id:
            return redirect(url_for("orderCustomer_bp.order_detail_page", order_id=order_id))
        return redirect(url_for("orderCustomer_bp.index"))

    @staticmethod
    def vnpay_ipn():
        # VNPay gọi IPN bằng GET kèm query string, response format khác MoMo:
        # {"RspCode": ..., "Message": ...} thay vì {"message": ...}.
        params = request.args.to_dict()

        def _vnpay_response(rsp_code, message):
            return jsonify({"RspCode": rsp_code, "Message": message}), 200

        try:
            if not verify_vnpay_signature(params):
                return _vnpay_response("97", "Invalid signature")

            order_id = get_order_id_from_txn_ref(params.get("vnp_TxnRef"))
            if not order_id:
                return _vnpay_response("01", "Order not found")

            order = Order.query.get(order_id)
            if not order:
                return _vnpay_response("01", "Order not found")

            vnp_amount = params.get("vnp_Amount")
            try:
                paid_amount = int(vnp_amount) // 100 if vnp_amount is not None else None
            except ValueError:
                paid_amount = None

            if paid_amount is None or paid_amount != int(order.total_amount):
                return _vnpay_response("04", "Invalid amount")

            if order.status != Status.PENDING_PAYMENT:
                return _vnpay_response("02", "Order already confirmed")

            response_code = params.get("vnp_ResponseCode")
            if response_code == "00":
                order, updated = OrderDao.mark_order_paid_vnpay(order.id)

                if updated and order.customer_email:
                    try:
                        send_order_payment_success_email(
                            recipient=order.customer_email,
                            order_id=order.id,
                            total_amount=order.total_amount,
                            restaurant_name=order.restaurant.name if order.restaurant else "Nhà hàng"
                        )
                    except Exception as email_error:
                        current_app.logger.exception(email_error)
            else:
                OrderDao.mark_order_payment_failed(order.id)

            return _vnpay_response("00", "Confirm Success")

        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(e)
            return _vnpay_response("99", "Unknown error")
