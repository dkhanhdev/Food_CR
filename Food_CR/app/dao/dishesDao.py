from app.extensions import db
from app.models.model import Dish, DishCategory, CartItems, VoucherDish, AssociationRule
from sqlalchemy import or_, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError



class DishesDao:
    @staticmethod
    def get_active_by_ids_and_restaurant(dish_ids, restaurant_id):
        if not dish_ids:
            return []
        return Dish.query.filter(
            Dish.id.in_(dish_ids),
            Dish.restaurant_id == restaurant_id,
            Dish.active == True
        ).order_by(Dish.created_at.desc()).all()

    @staticmethod
    def get_list_dishes_by_restaurant(restaurant_id, page=1, per_page=12, category=None, keyword=None):
        query = Dish.query.with_entities(
            Dish.id,
            Dish.name,
            Dish.category,
            Dish.description,
            Dish.price,
            Dish.image,
            Dish.active
        ).order_by(Dish.created_at.desc()).filter_by(restaurant_id=restaurant_id)

        if category and category != 'all':
            category_enum = next((c for c in DishCategory if c.value == category), None)
            if category_enum:
                query = query.filter(Dish.category == category_enum)

        if keyword:
            query = query.filter(
                or_(
                    Dish.name.ilike(f'%{keyword}%'),
                    Dish.description.ilike(f'%{keyword}%')
                )
            )

        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        return pagination

    @staticmethod
    def get_dishes_stats(restaurant_id):
        rows = db.session.query(
            Dish.active, func.count(Dish.id)
        ).filter_by(restaurant_id=restaurant_id).group_by(Dish.active).all()

        active = next((count for is_active, count in rows if is_active), 0)
        total = sum(count for _, count in rows)

        return {
            "total": total,
            "active": active,
            "inactive": total - active
        }

    @staticmethod
    def create_dishes(name, price, category, restaurant_id, description=None, image=None):
        try:
            if isinstance(category, str):
                if category in DishCategory.__members__:
                    category = DishCategory[category]
                elif category in DishCategory._value2member_map_:
                    category = DishCategory(category)
                else:
                    raise ValueError(f"Category không hợp lệ: {category}")

            new_dish = Dish(
                name=name,
                description=description,
                image=image,
                price=price,
                category=category,
                restaurant_id=restaurant_id
            )

            db.session.add(new_dish)
            db.session.commit()
            return new_dish

        except ValueError as ve:
            print(f"Lỗi giá trị: {ve}")
            db.session.rollback()
            return None
        except SQLAlchemyError as e:
            print(f"Lỗi khi tạo món ăn: {e}")
            db.session.rollback()
            return None

    @staticmethod
    def change_dishe_status(id, restaurant_id):
        try:
            dish = Dish.query.filter_by(id=id, restaurant_id=restaurant_id).first()

            if not dish:
                return None

            dish.active = not dish.active
            db.session.commit()
            return dish

        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    @staticmethod
    def delete_dishes(id, restaurant_id):
        try:
            dish = Dish.query.filter_by(id=id, restaurant_id=restaurant_id).first()

            if not dish:
                return None

            CartItems.query.filter_by(dish_id=dish.id).delete()

            db.session.delete(dish)
            db.session.commit()
            return dish

        except IntegrityError as e:
            db.session.rollback()
            raise ValueError("Món ăn đang được sử dụng trong đơn hàng, không thể xóa")
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    @staticmethod
    def get_top_recommended_dishes(limit=10):
        rule_dishes = (
            Dish.query
            .join(AssociationRule, AssociationRule.consequent_dish_id == Dish.id)
            .filter(Dish.active == True)
            .order_by(AssociationRule.lift.desc())
            .all()
        )
        seen_ids = set()
        dishes = []
        for d in rule_dishes:
            if d.id not in seen_ids:
                seen_ids.add(d.id)
                dishes.append(d)
            if len(dishes) >= limit:
                break

        if len(dishes) < limit:
            fallback = (
                Dish.query
                .filter(Dish.active == True, ~Dish.id.in_(seen_ids) if seen_ids else True)
                .order_by(Dish.id.desc())
                .limit(limit - len(dishes))
                .all()
            )
            dishes.extend(fallback)

        return dishes





