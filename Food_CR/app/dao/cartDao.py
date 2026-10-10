from app.models.model import Cart, CartItems, Dish
from app.extensions import db
from app.dao.systemConfigDao import SystemConfigDao


class CartDao:

    @staticmethod
    def _cart_total_items(cart_id, exclude_item_id=None):
        items = CartItems.query.filter_by(cart_id=cart_id).all()
        total = 0
        for item in items:
            if item.id != exclude_item_id:
                total += item.quantity
        return total

    @staticmethod
    def get_cart_by_user_and_restaurant(user_id, restaurant_id):
        return Cart.query.filter_by(user_id=user_id, restaurant_id=restaurant_id).first()

    @staticmethod
    def get_cart_by_id(cart_id):
        return Cart.query.options(
            db.joinedload(Cart.items).joinedload(CartItems.dish)
        ).get(cart_id)

    @staticmethod
    def get_or_create_cart(user_id, restaurant_id):
        cart = Cart.query.filter_by(user_id=user_id, restaurant_id=restaurant_id).first()
        if cart:
            return cart
        cart = Cart(name=f"cart-{user_id}-{restaurant_id}", user_id=user_id, restaurant_id=restaurant_id)
        db.session.add(cart)
        db.session.commit()
        return cart

    @staticmethod
    def add_item(user_id, restaurant_id, dish_id, quantity=1):
        dish = Dish.query.get(dish_id)
        if not dish or not dish.active:
            return None

        cart = CartDao.get_or_create_cart(user_id, restaurant_id)

        max_items = SystemConfigDao.get_max_cart_items(restaurant_id)
        if CartDao._cart_total_items(cart.id) + quantity > max_items:
            raise ValueError(f"Giỏ hàng chỉ được chứa tối đa {max_items} món.")

        item = CartItems.query.filter_by(cart_id=cart.id, dish_id=dish_id).first()
        if item:
            item.quantity += quantity
        else:
            voucher = dish.get_active_voucher()
            price = voucher.apply_discount(dish.price) if voucher else dish.price
            item = CartItems(
                name=dish.name,
                cart_id=cart.id,
                dish_id=dish_id,
                quantity=quantity,
                price=price,
            )
            db.session.add(item)

        db.session.commit()
        return item

    @staticmethod
    def get_item_by_id(cart_item_id):
        return CartItems.query.get(cart_item_id)

    @staticmethod
    def update_item_quantity(cart_item_id, quantity):
        item = CartItems.query.get(cart_item_id)
        if not item:
            return None
        if quantity <= 0:
            db.session.delete(item)
            db.session.commit()
            return None

        if quantity > item.quantity:
            max_items = SystemConfigDao.get_max_cart_items(item.cart.restaurant_id)
            others_total = CartDao._cart_total_items(item.cart_id, exclude_item_id=item.id)
            if others_total + quantity > max_items:
                raise ValueError(f"Giỏ hàng chỉ được chứa tối đa {max_items} món.")

        item.quantity = quantity
        db.session.commit()
        return item

    @staticmethod
    def remove_item(cart_item_id):
        item = CartItems.query.get(cart_item_id)
        if not item:
            return False
        db.session.delete(item)
        db.session.commit()
        return True

    @staticmethod
    def clear_cart(cart_id):
        cart = Cart.query.get(cart_id)
        if not cart:
            return False
        CartItems.query.filter_by(cart_id=cart_id).delete()
        db.session.commit()
        return True

    @staticmethod
    def get_carts_by_user(user_id):
        return Cart.query.options(
            db.joinedload(Cart.items).joinedload(CartItems.dish)
        ).filter_by(user_id=user_id).all()
