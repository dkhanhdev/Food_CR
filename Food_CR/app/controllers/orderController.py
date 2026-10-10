from datetime import datetime

from flask import request, jsonify, render_template, current_app
from flask_login import current_user

from app.dao.ordersDao import OrdersDao
from app.models.model import Status


class OrderController:
    PIPELINE_STATUSES = OrdersDao.PIPELINE_STATUSES

    @staticmethod
    def _parse_date(value):
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            try:
                dt = datetime.strptime(value, "%d-%m-%Y")
            except ValueError:
                return None
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt

    @staticmethod
    def _serialize_order(order):
        items = []
        subtotal = 0
        for item in order.items:
            subtotal += float(item.unit_price) * item.quantity
            items.append({
                "id": item.id,
                "name": item.dish.name,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
            })
        return {
            "id": order.id,
            "code": order.name,
            "status": order.status.name,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "customer_email": order.customer_email,
            "delivery_address": order.delivery_address,
            "note": order.note,
            "rejection_reason": order.rejection_reason,
            "shipping_fee": float(order.shipping_fee),
            "total_amount": float(order.total_amount),
            "subtotal": round(subtotal, 0),
            "items_count": sum(i.quantity for i in order.items),
            "items": items,
            "voucher": {
                "id": order.voucher.id,
                "code": order.voucher.code,
                "name": order.voucher.name,
            } if order.voucher else None,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "created_at_display": order.created_at.strftime("%H:%M - %d/%m/%Y") if order.created_at else None,
        }

    @staticmethod
    def _get_restaurant_id():
        restaurant = current_user.restaurant
        if not restaurant:
            return None
        return restaurant.id

    @staticmethod
    def _today():
        return datetime.utcnow().date().isoformat()

    @staticmethod
    def board():
        restaurant_id = OrderController._get_restaurant_id()
        if not restaurant_id:
            return jsonify({"success": False, "message": "Nhà hàng không tồn tại"}), 403

        keyword = (request.args.get("keyword") or "").strip()
        today = OrderController._today()
        start_date = OrderController._parse_date(request.args.get("start_date") or today)
        end_date = OrderController._parse_date(request.args.get("end_date") or today)
        if end_date is not None:
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=0)
        per_page = current_app.config.get("PAGE_SIZE", 4)

        columns = {}
        for status in OrderController.PIPELINE_STATUSES:
            page = OrdersDao.get_orders(
                restaurant_id=restaurant_id,
                status=status.name,
                keyword=keyword,
                start_date=start_date,
                end_date=end_date,
                page=1,
                per_page=per_page,
            )
            columns[status.name] = {
                "orders": [OrderController._serialize_order(o) for o in page.items],
                "total": page.total,
                "has_more": page.has_next,
            }

        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        return render_template(
            "restaurantOrders.html",
            columns=columns,
            keyword=keyword,
            start_date=request.args.get("start_date") or today_str,
            end_date=request.args.get("end_date") or today_str,
            pipeline_statuses=OrderController.PIPELINE_STATUSES,
            page_size=per_page,
        )

    @staticmethod
    def board_more():
        restaurant_id = OrderController._get_restaurant_id()
        if not restaurant_id:
            return jsonify({"success": False, "message": "Nhà hàng không tồn tại"}), 403

        status_name = request.args.get("status", "")
        try:
            status = Status[status_name.upper()]
        except KeyError:
            return jsonify({"success": False, "message": "Trạng thái không hợp lệ"}), 400
        if status not in OrderController.PIPELINE_STATUSES:
            return jsonify({"success": False, "message": "Trạng thái không hợp lệ"}), 400

        keyword = (request.args.get("keyword") or "").strip()
        today = OrderController._today()
        start_date = OrderController._parse_date(request.args.get("start_date") or today)
        end_date = OrderController._parse_date(request.args.get("end_date") or today)
        if end_date is not None:
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=0)
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", current_app.config.get("PAGE_SIZE", 4), type=int)

        result = OrdersDao.get_orders(
            restaurant_id=restaurant_id,
            status=status.name,
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            page=page,
            per_page=per_page,
        )

        return jsonify({
            "success": True,
            "items": [OrderController._serialize_order(o) for o in result.items],
            "total": result.total,
            "page": result.page,
            "has_more": result.has_next,
        }), 200

    @staticmethod
    def order_detail(order_id):
        restaurant_id = OrderController._get_restaurant_id()
        if not restaurant_id:
            return jsonify({"success": False, "message": "Nhà hàng không tồn tại"}), 403

        order = OrdersDao.get_order_by_id_and_restaurant(order_id, restaurant_id)
        if not order:
            return jsonify({"success": False, "message": "Đơn hàng không tồn tại"}), 404

        return jsonify({
            "success": True,
            "order": OrderController._serialize_order(order),
        }), 200

    @staticmethod
    def approve(order_id):
        restaurant_id = OrderController._get_restaurant_id()
        if not restaurant_id:
            return jsonify({"success": False, "status": "error", "message": "Nhà hàng không tồn tại"}), 403

        order = OrdersDao.approve_order(order_id, restaurant_id)
        if not order:
            return jsonify({
                "success": False,
                "status": "error",
                "message": "Đơn hàng không tồn tại hoặc không thể duyệt"
            }), 404

        return jsonify({
            "success": True,
            "status": "ok",
            "message": "Đã duyệt đơn hàng",
            "order": OrderController._serialize_order(order),
        }), 200

    @staticmethod
    def reject(order_id):
        restaurant_id = OrderController._get_restaurant_id()
        if not restaurant_id:
            return jsonify({"success": False, "status": "error", "message": "Nhà hàng không tồn tại"}), 403

        data = request.get_json(silent=True) or {}
        reason = data.get("reason")
        if not reason or not str(reason).strip():
            return jsonify({
                "success": False,
                "status": "error",
                "message": "Lý do từ chối là bắt buộc"
            }), 400

        try:
            order = OrdersDao.reject_order(order_id, restaurant_id, reason)
        except ValueError as e:
            return jsonify({"success": False, "status": "error", "message": str(e)}), 400

        if not order:
            return jsonify({
                "success": False,
                "status": "error",
                "message": "Đơn hàng không tồn tại hoặc không thể từ chối"
            }), 404

        return jsonify({
            "success": True,
            "status": "ok",
            "message": "Đã từ chối đơn hàng",
            "order": OrderController._serialize_order(order),
        }), 200