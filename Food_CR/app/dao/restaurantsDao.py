from app.models.model import Restaurant, User, Dish, RestaurantApprovalStatus, AssociationRule
from app.extensions import db
from sqlalchemy import func
from app.service.notificationByEmail import send_restaurant_approved_email,send_restaurant_rejected_email
from app.service.notificationByFCM import send_push_notification


class RestaurantsDao:

    @staticmethod
    def get_restaurants_by_status(status, page=1, per_page=10):
        query = Restaurant.query.options(
            db.joinedload(Restaurant.user)
        )
        if status and status.lower() != "all":
            try:
                status_enum = RestaurantApprovalStatus[status.upper()]
                query = query.filter(Restaurant.approval_status == status_enum)
            except KeyError:
                pass
        query = query.order_by(Restaurant.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

        return query
    
    @staticmethod
    def approve_restaurant(restaurant_id):
        r = Restaurant.query.get(restaurant_id)
        if not r:
            return None
        r.approval_status = RestaurantApprovalStatus.APPROVED
        r.rejection_reason = None
        if r.user:
            r.user.active = True
            r.active = True
        db.session.commit()
        try:
            send_push_notification(r.user.id, "Nhà hàng của bạn đã được phê duyệt!",
                                                           f"Nhà hàng {r.name} vừa được admin phê duyệt.")
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Gửi push notification thất bại: {e}")
        send_restaurant_approved_email(
            recipient=r.user.email,
            restaurant_name=r.user.name
        )
        return r

    @staticmethod
    def reject_restaurant(restaurant_id, reason=None):
        r = Restaurant.query.get(restaurant_id)
        if not r:
            return None
        reason = reason.strip()
        r.approval_status = RestaurantApprovalStatus.REJECTED
        r.rejection_reason = reason
        if r.user:
            r.user.active = False
        db.session.commit()
        try:
            send_push_notification(
                r.user.id,
                "Nhà hàng bị từ chối",
                f"Nhà hàng {r.name} bị admin từ chối: {reason}"
            )
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Gửi push notification thất bại: {e}")
        send_restaurant_rejected_email(
            recipient=r.user.email,
            restaurant_name=r.user.name,
            reason=reason
        )
        return r
    
    @staticmethod
    def get_all_restaurants():
        return db.session.query(
            Restaurant.id,
            func.coalesce(Restaurant.cover_image, User.avatar).label("cover_image"),
            Restaurant.name,
            Restaurant.cuisine_type,
            User.address,
            Restaurant.opening_time,
            Restaurant.closing_time
        ).join(User, Restaurant.id == User.id
        ).filter(Restaurant.active == True).all()

    @staticmethod
    def get_restaurant_by_id(restaurant_id):
        return Restaurant.query.options(
            db.joinedload(Restaurant.user)
        ).filter_by(id=restaurant_id, active=True).first()

    @staticmethod
    def search_restaurants(keyword, page=1, per_page=9):
        query = Restaurant.query.options(db.joinedload(Restaurant.user)).filter(Restaurant.active == True)
        if keyword:
            query = query.filter(Restaurant.name.ilike(f"%{keyword}%"))
        return query.order_by(Restaurant.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def search_dishes(keyword, page=1, per_page=9):
        if not keyword:
            return Dish.query.filter(False).paginate(page=page, per_page=per_page, error_out=False)
        return Dish.query.options(
            db.joinedload(Dish.restaurant).joinedload(Restaurant.user)
        ).filter(
            Dish.active == True,
            Dish.name.ilike(f"%{keyword}%")
        ).paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def open_restaurant(restaurant_id):
        r = Restaurant.query.get(restaurant_id)
        if not r:
            return None
        r.status = True
        db.session.commit()
        return r

    @staticmethod
    def close_restaurant(restaurant_id):
        r = Restaurant.query.get(restaurant_id)
        if not r:
            return None
        r.status = False
        db.session.commit()
        return r

    @staticmethod
    def get_recommended_dishes(restaurant_id, dish_id):
        rules = AssociationRule.query.filter_by(
            restaurant_id=restaurant_id,
            antecedent_dish_id=dish_id
        ).order_by(AssociationRule.lift.desc()).all()

        recommended_dishes = []
        seen_ids = set()
        if dish_id:
            seen_ids.add(dish_id)

        for rule in rules:
            dish = rule.consequent_dish
            if dish and dish.active and dish.id not in seen_ids:
                seen_ids.add(dish.id)
                recommended_dishes.append({
                    "id": dish.id,
                    "name": dish.name,
                    "price": dish.price,
                    "image": dish.image
                })

        # Fallback lấy các món khác của cùng nhà hàng nếu chưa đủ luật kết hợp
        if len(recommended_dishes) < 4:
            fallback = Dish.query.filter(
                Dish.restaurant_id == restaurant_id,
                Dish.active == True,
                ~Dish.id.in_(seen_ids) if seen_ids else True
            ).limit(4 - len(recommended_dishes)).all()

            for dish in fallback:
                recommended_dishes.append({
                    "id": dish.id,
                    "name": dish.name,
                    "price": dish.price,
                    "image": dish.image
                })

        return recommended_dishes


