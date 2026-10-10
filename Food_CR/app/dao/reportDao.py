from sqlalchemy import func, cast, Date, case
from datetime import datetime, timedelta

from app.extensions import db
from app.models.model import Order, OrderItem, Dish, Status


class ReportDao:

    @staticmethod
    def get_revenue_summary(restaurant_id, start_date, end_date):
        query = db.session.query(
            func.coalesce(func.sum(Order.total_amount), 0).label("total_revenue"),
            func.count(Order.id).label("total_orders"),
            func.coalesce(func.sum(
                case((Order.status == Status.COMPLETED, Order.total_amount), else_=0)
            ), 0).label("completed_revenue"),
            func.count(
                case((Order.status == Status.COMPLETED, 1))
            ).label("completed_orders"),
            func.count(
                case((Order.status == Status.CANCELLED, 1))
            ).label("cancelled_orders"),
        ).filter(
            Order.restaurant_id == restaurant_id,
            Order.created_at >= start_date,
            Order.created_at <= end_date,
        ).first()

        return {
            "total_revenue": float(query.total_revenue),
            "total_orders": query.total_orders,
            "completed_revenue": float(query.completed_revenue),
            "completed_orders": query.completed_orders,
            "cancelled_orders": query.cancelled_orders,
            "avg_order_value": (
                round(float(query.completed_revenue) / query.completed_orders, 0)
                if query.completed_orders > 0 else 0
            ),
        }

    @staticmethod
    def get_revenue_by_date(restaurant_id, start_date, end_date):
        rows = db.session.query(
            cast(Order.created_at, Date).label("date"),
            func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
            func.count(Order.id).label("order_count"),
        ).filter(
            Order.restaurant_id == restaurant_id,
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status.in_([Status.PAID, Status.PREPARING, Status.COMPLETED]),
        ).group_by(
            cast(Order.created_at, Date)
        ).order_by(
            cast(Order.created_at, Date)
        ).all()

        return [
            {
                "date": r.date.isoformat() if r.date else None,
                "revenue": float(r.revenue),
                "order_count": r.order_count,
            }
            for r in rows
        ]

    @staticmethod
    def get_top_dishes(restaurant_id, start_date, end_date, limit=10):
        rows = db.session.query(
            Dish.id,
            Dish.name,
            Dish.price,
            Dish.image,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("total_quantity"),
            func.coalesce(func.sum(OrderItem.unit_price * OrderItem.quantity), 0).label("total_revenue"),
        ).join(
            OrderItem, OrderItem.dish_id == Dish.id
        ).join(
            Order, Order.id == OrderItem.order_id
        ).filter(
            Order.restaurant_id == restaurant_id,
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status.in_([Status.PAID, Status.PREPARING, Status.COMPLETED]),
        ).group_by(
            Dish.id
        ).order_by(
            func.sum(OrderItem.quantity).desc()
        ).limit(limit).all()

        return [
            {
                "id": r.id,
                "name": r.name,
                "price": float(r.price),
                "image": r.image,
                "total_quantity": r.total_quantity,
                "total_revenue": float(r.total_revenue),
            }
            for r in rows
        ]

    @staticmethod
    def get_revenue_by_category(restaurant_id, start_date, end_date):
        from app.models.model import DishCategory

        rows = db.session.query(
            Dish.category,
            func.coalesce(func.sum(OrderItem.unit_price * OrderItem.quantity), 0).label("revenue"),
            func.coalesce(func.sum(OrderItem.quantity), 0).label("quantity"),
        ).join(
            OrderItem, OrderItem.dish_id == Dish.id
        ).join(
            Order, Order.id == OrderItem.order_id
        ).filter(
            Order.restaurant_id == restaurant_id,
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status.in_([Status.PAID, Status.PREPARING, Status.COMPLETED]),
        ).group_by(
            Dish.category
        ).all()

        revenue_map = {
            (r.category.value if r.category else "Khác"): {
                "revenue": float(r.revenue),
                "quantity": r.quantity,
            }
            for r in rows
        }

        result = []
        for cat in DishCategory:
            data = revenue_map.get(cat.value, {"revenue": 0, "quantity": 0})
            result.append({
                "category": cat.value,
                "revenue": data["revenue"],
                "quantity": data["quantity"],
            })

        return sorted(result, key=lambda x: x["revenue"], reverse=True)

    @staticmethod
    def get_order_status_distribution(restaurant_id, start_date, end_date):
        rows = db.session.query(
            Order.status,
            func.count(Order.id).label("count"),
        ).filter(
            Order.restaurant_id == restaurant_id,
            Order.created_at >= start_date,
            Order.created_at <= end_date,
        ).group_by(
            Order.status
        ).all()

        return [
            {
                "status": r.status.value if r.status else "Unknown",
                "count": r.count,
            }
            for r in rows
        ]
