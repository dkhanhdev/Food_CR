from app.extensions import db
from app.models.model import SystemConfig, RestaurantConfig, DEFAULT_MAX_CART_ITEMS


class SystemConfigDao:

    @staticmethod
    def _get_restaurant_config(restaurant_id):
        """RestaurantConfig của nhà hàng; None nếu không có (lúc đó sẽ dùng giá trị admin)."""
        if not restaurant_id:
            return None
        return RestaurantConfig.query.filter_by(restaurant_id=restaurant_id).first()

    @staticmethod
    def get_max_cart_items(restaurant_id):
        """Limit hiệu lực: có RestaurantConfig thì theo nó, không có thì theo admin."""
        admin_max = SystemConfig.query.first()
        admin_max = admin_max.max_cart_items if admin_max else DEFAULT_MAX_CART_ITEMS
        cfg = SystemConfigDao._get_restaurant_config(restaurant_id)
        if cfg:
            # Nếu admin hạ cap xuống thấp hơn giá trị nhà hàng đang đặt -> tự co theo cap.
            return min(cfg.max_cart_items, admin_max)
        return admin_max

    @staticmethod
    def set_restaurant_max_cart_items(restaurant_id, value):
        """Set/override limit riêng của nhà hàng. Trả về value; None nếu vượt cap admin."""
        admin_max = SystemConfigDao.get_max_cart_items(None)
        if value is None or value < 1 or value > admin_max:
            return None
        cfg = SystemConfigDao._get_restaurant_config(restaurant_id)
        if cfg:
            cfg.max_cart_items = value
        else:
            cfg = RestaurantConfig(restaurant_id=restaurant_id, max_cart_items=value)
            db.session.add(cfg)
        db.session.commit()
        return value