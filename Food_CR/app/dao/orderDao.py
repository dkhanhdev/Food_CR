from decimal import Decimal

from app.extensions import db
from app.models.model import Order, OrderItem, Status


class OrderDao:
    """Data access for creating and updating customer payment orders."""

    @staticmethod
    def _consume_voucher_usage(order):
        voucher = order.voucher
        if voucher and voucher.used_count < voucher.usage_limit:
            voucher.used_count += 1

    @staticmethod
    def create_order_from_cart(cart, data):
        customer_name = str(data.get("customer_name") or "").strip()
        customer_phone = str(data.get("customer_phone") or "").strip()
        customer_email = str(data.get("customer_email") or "").strip() or None
        delivery_address = str(data.get("delivery_address") or "").strip()
        note = str(data.get("note") or "").strip() or None

        if not customer_name:
            raise ValueError("Vui lòng nhập họ và tên")
        if not customer_phone:
            raise ValueError("Vui lòng nhập số điện thoại")
        if not delivery_address:
            raise ValueError("Vui lòng nhập địa chỉ giao hàng")
        if len(customer_name) > 150:
            raise ValueError("Họ và tên quá dài")
        if len(customer_phone) > 50:
            raise ValueError("Số điện thoại quá dài")
        if customer_email and len(customer_email) > 150:
            raise ValueError("Email quá dài")
        if len(delivery_address) > 300:
            raise ValueError("Địa chỉ giao hàng quá dài")
        if note and len(note) > 300:
            raise ValueError("Ghi chú quá dài")
        if not cart.items:
            raise ValueError("Giỏ hàng đang trống")

        subtotal = Decimal("0")
        order_items = []
        for cart_item in cart.items:
            if not cart_item.dish or not cart_item.dish.active:
                raise ValueError("Một món ăn trong giỏ hàng không còn phục vụ")
            if cart_item.quantity <= 0:
                raise ValueError("Số lượng món ăn không hợp lệ")

            unit_price = Decimal(str(cart_item.price))
            subtotal += unit_price * cart_item.quantity
            order_items.append(OrderItem(
                name=cart_item.dish.name,
                dish_id=cart_item.dish_id,
                unit_price=unit_price,
                quantity=cart_item.quantity,
            ))

        order = Order(
            name="pending-order",
            user_id=cart.user_id,
            restaurant_id=cart.restaurant_id,
            status=Status.PENDING_PAYMENT,
            note=note,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            delivery_address=delivery_address,
            shipping_fee=Decimal("0"),
            total_amount=subtotal,
            items=order_items,
        )
        db.session.add(order)
        db.session.flush()
        order.name = f"DH-{order.id:05d}"

        for cart_item in list(cart.items):
            db.session.delete(cart_item)

        return order

    @staticmethod
    def update_order_status(order_id, status):
        order = Order.query.get(order_id)
        if not order:
            return None
        order.status = status
        db.session.commit()
        return order

    # ---- MoMo payment helpers (thay cho paymentsDao.PaymentDao trước đây) ----

    @staticmethod
    def get_order_by_momo_order_id(momo_order_id):
        if not momo_order_id:
            return None
        return Order.query.filter_by(momo_order_id=momo_order_id).first()

    @staticmethod
    def mark_order_paid_momo(order_id, momo_order_id):
        """Đánh dấu order đã thanh toán qua MoMo.

        Có guard theo status hiện tại để đảm bảo idempotent: cả payment_return
        (redirect trình duyệt) và payment_ipn (server-to-server) đều có thể
        cùng gọi hàm này cho một order, nhưng chỉ lần gọi đầu tiên mới thực sự
        cập nhật trạng thái / trigger side-effect (gửi email).
        """
        order = Order.query.get(order_id)
        if not order:
            return None, False

        if order.status != Status.PENDING_PAYMENT:
            return order, False

        order.paid_by = "CUSTOMER_MOMO"
        order.momo_order_id = momo_order_id
        order.status = Status.PAID
        OrderDao._consume_voucher_usage(order)
        db.session.commit()
        return order, True

    @staticmethod
    def mark_order_paid_vnpay(order_id):
        """Đánh dấu order đã thanh toán qua VNPay.

        Cùng cấu trúc/guard idempotent như mark_order_paid_momo, nhưng không
        có cột riêng nào để lưu (VNPay không cần lưu thêm gì lên Order, vì
        order_id đã được nhúng thẳng vào vnp_TxnRef, không cần tra cứu qua
        cột phụ như momo_order_id).
        """
        order = Order.query.get(order_id)
        if not order:
            return None, False

        if order.status != Status.PENDING_PAYMENT:
            return order, False

        order.paid_by = "CUSTOMER_VNPAY"
        order.status = Status.PAID
        OrderDao._consume_voucher_usage(order)
        db.session.commit()
        return order, True

    @staticmethod
    def mark_order_payment_failed(order_id):
        order = Order.query.get(order_id)
        if not order:
            return None, False

        if order.status != Status.PENDING_PAYMENT:
            return order, False

        order.status = Status.PAYMENT_FAILED
        db.session.commit()
        return order, True
