from sqlalchemy import or_
from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models.model import Order, OrderItem, Status, Restaurant, Cart, CartItems
from app.dao.vouchersDao import VouchersDao

from app.service.notificationByFCM import send_push_notification
from flask_login import current_user

class OrdersDao:

    PIPELINE_STATUSES = [
        Status.PAID,
        Status.PREPARING,
        Status.COMPLETED,
    ]

    from sqlalchemy.orm import joinedload

    @staticmethod
    def get_orders_customer(status=None, keyword=None):
        query = Order.query.options(
            db.joinedload(Order.restaurant).joinedload(Restaurant.user),
            db.joinedload(Order.items).joinedload(OrderItem.dish)
        ).filter(Order.user_id == current_user.id)

        if status is not None:
            try:
                status_enum = status if isinstance(status, Status) else Status[status.upper()]
                query = query.filter(Order.status == status_enum)
            except (KeyError, AttributeError):
                pass

        if keyword:
            like = f"%{keyword.strip()}%"
            query = query.filter(
                or_(
                    Order.id.ilike(like),
                    Order.note.ilike(like),
                )
            )

        query = query.order_by(Order.created_at.desc())

        data = []

        for r in query:
            data.append({
                "id": r.id,
                "status": r.status.value if r.status else None,
                "note": r.note,
                "rejection_reason": r.rejection_reason,
                "shipping_fee": float(r.shipping_fee) if r.shipping_fee is not None else None,
                "total_amount": float(r.total_amount) if r.total_amount is not None else None,
                "restaurant": {
                    "id": r.restaurant.id,
                    "name": r.restaurant.name,
                    "cover_image": r.restaurant.cover_image,
                } if r.restaurant else None,

                "items": [
                    {
                        "id": item.id,
                        "dish_id": item.dish_id,
                        "dish_name": item.dish.name if item.dish else None,
                        "dish_image": item.dish.image if item.dish else None,
                        "quantity": item.quantity,
                    }
                    for item in r.items
                ],
            })

        return data

    @staticmethod
    def get_orders(restaurant_id, status=None, keyword=None,
                            start_date=None, end_date=None,
                            page=1, per_page=10):
        query = Order.query.options(
            db.joinedload(Order.items).joinedload(OrderItem.dish),
            db.joinedload(Order.voucher)
        ).filter(Order.restaurant_id == restaurant_id)

        if status is not None:
            try:
                status_enum = status if isinstance(status, Status) else Status[status.upper()]
                query = query.filter(Order.status == status_enum)
            except (KeyError, AttributeError):
                pass
        else:
            query = query.filter(Order.status.in_(OrdersDao.PIPELINE_STATUSES))

        if keyword:
            like = f"%{keyword.strip()}%"
            query = query.filter(
                or_(
                    Order.name.ilike(like),
                    Order.customer_name.ilike(like),
                    Order.customer_phone.ilike(like),
                )
            )

        if start_date is not None:
            query = query.filter(Order.created_at >= start_date)
        if end_date is not None:
            query = query.filter(Order.created_at <= end_date)

        return query.order_by(Order.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def get_order_by_id_and_restaurant(order_id, restaurant_id):
        return Order.query.options(
            db.joinedload(Order.items).joinedload(OrderItem.dish),
            db.joinedload(Order.voucher)
        ).filter_by(id=order_id, restaurant_id=restaurant_id).first()

    @staticmethod
    def get_order_by_id_and_customer(order_id, isRestaurant = False):
        if isRestaurant==False :
            order = Order.query.options(
                db.joinedload(Order.items).joinedload(OrderItem.dish),
                db.joinedload(Order.voucher),
                db.joinedload(Order.restaurant)
            ).filter_by(id=order_id, user_id=current_user.id).first()
        else:
            order = Order.query.options(
                db.joinedload(Order.items).joinedload(OrderItem.dish),
                db.joinedload(Order.voucher),
                db.joinedload(Order.restaurant)
            ).filter_by(id=order_id, restaurant_id=current_user.id).first()
        

        if not order:
            return None

        return {
            "id": order.id,
            "status": order.status.value if order.status else None,
            "note": order.note,
            "rejection_reason": order.rejection_reason,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "customer_email": order.customer_email,
            "delivery_address": order.delivery_address,
            "shipping_fee": float(order.shipping_fee) if order.shipping_fee is not None else None,
            "discount_amount": float(order.discount_amount) if order.discount_amount is not None else None,
            "total_amount": float(order.total_amount) if order.total_amount is not None else None,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "payment_deadline": order.payment_deadline.isoformat() if order.payment_deadline else None,

            "restaurant": {
                "id": order.restaurant.id,
                "name": order.restaurant.name,
                "cover_image": order.restaurant.cover_image,
                "cuisine_type": order.restaurant.cuisine_type.value if order.restaurant.cuisine_type else None,
            } if order.restaurant else None,

            "voucher": {
                "id": order.voucher.id,
                "code": order.voucher.code,
                "name": order.voucher.name,
                "discount_type": order.voucher.discount_type.value if order.voucher.discount_type else None,
                "discount_value": float(order.voucher.discount_value) if order.voucher.discount_value is not None else None,
            } if order.voucher else None,

            "items": [
                {
                    "id": item.id,
                    "dish_id": item.dish_id,
                    "dish_name": item.dish.name if item.dish else None,
                    "dish_image": item.dish.image if item.dish else None,
                    "unit_price": float(item.unit_price) if item.unit_price is not None else None,
                    "quantity": item.quantity,
                    "subtotal": float(item.unit_price) * item.quantity if item.unit_price is not None else None,
                }
                for item in order.items
            ],
        }

    @staticmethod
    def approve_order(order_id, restaurant_id):
        order = OrdersDao.get_order_by_id_and_restaurant(order_id, restaurant_id)
        if not order:
            return None

        if order.status == Status.PAID:
            order.status = Status.PREPARING
            notify = True
        elif order.status == Status.PREPARING:
            order.status = Status.COMPLETED
            notify = False
        else:
            return None

        db.session.commit()
        if notify:
            send_push_notification(
                order.user_id,
                "Đơn hàng đã được duyệt",
                f"Đơn hàng {order.name} đã được nhà hàng xác nhận."
            )
        return order

    @staticmethod
    def reject_order(order_id, restaurant_id, reason=None):
        order = OrdersDao.get_order_by_id_and_restaurant(order_id, restaurant_id)
        if not order or order.status not in (Status.PAID, Status.PREPARING):
            return None

        reason = (reason or "").strip()
        if not reason:
            raise ValueError("rejection_reason là bắt buộc")

        order.status = Status.CANCELLED
        order.rejection_reason = reason
        db.session.commit()
        send_push_notification(
            order.user_id,
            "Đơn hàng bị từ chối",
            f"Đơn hàng {order.name} bị từ chối: {reason}"
        )
        return order

    @staticmethod
    def create_order_from_cart(user_id, restaurant_id, note=None, shipping_fee=20000,
                               customer_name="", customer_phone="",
                               customer_email="", delivery_address="",
                               voucher_code=None):
        cart = Cart.query.filter_by(user_id=user_id, restaurant_id=restaurant_id).first()
        if not cart or not cart.items:
            return None, "Giỏ hàng trống"

        subtotal = sum(float(item.price) * item.quantity for item in cart.items)

        voucher = None
        discount_amount = 0
        if voucher_code:
            voucher = VouchersDao.get_order_voucher_by_code(voucher_code.strip().upper(), restaurant_id)
            if not voucher or not voucher.is_valid_now():
                return None, "Mã giảm giá không hợp lệ hoặc đã hết hạn"
            if subtotal < (voucher.minimum_order or 0):
                return None, f"Đơn hàng tối thiểu {voucher.minimum_order:,.0f}đ để dùng mã này"
            discount_amount = subtotal - voucher.apply_discount(subtotal)

        total_amount = subtotal - discount_amount + shipping_fee
        now = datetime.now(timezone.utc)
        payment_deadline = now + timedelta(minutes=15)

        order_count = Order.query.count()
        order = Order(
            name=f"DH-{order_count + 1:05d}",
            user_id=user_id,
            restaurant_id=restaurant_id,
            voucher_id=voucher.id if voucher else None,
            status=Status.PENDING_PAYMENT,
            note=note,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            delivery_address=delivery_address,
            shipping_fee=shipping_fee,
            discount_amount=discount_amount,
            total_amount=total_amount,
            payment_deadline=payment_deadline,
        )
        db.session.add(order)
        db.session.flush()

        for item in cart.items:
            order_item = OrderItem(
                order_id=order.id,
                dish_id=item.dish_id,
                unit_price=item.price,
                quantity=item.quantity,
                name=item.dish.name,
            )
            db.session.add(order_item)

        CartItems.query.filter_by(cart_id=cart.id).delete()
        db.session.commit()

        return {
            "order_id": order.id,
            "total_amount": total_amount,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "payment_deadline": payment_deadline.isoformat(),
        }, None

    @staticmethod
    def expire_order(order_id):
        order = Order.query.get(order_id)
        if not order or order.status != Status.PENDING_PAYMENT:
            return None, "Đơn hàng không thể huỷ"
        order.status = Status.PAYMENT_FAILED
        db.session.commit()
        return order, None