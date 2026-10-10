from flask import Blueprint
from app.controllers.cartController import CartController
from app.middleware import role_required
from app.models.model import UserRole

cart_api = Blueprint("cart_api", __name__)

cart_api.add_url_rule(
    "/<int:restaurant_id>",
    view_func=role_required(UserRole.CUSTOMER)(CartController.get_cart),
    methods=["GET"]
)
cart_api.add_url_rule(
    "/<int:restaurant_id>/items",
    view_func=role_required(UserRole.CUSTOMER)(CartController.add_item),
    methods=["POST"]
)
cart_api.add_url_rule(
    "/<int:restaurant_id>/items/<int:cart_item_id>",
    view_func=role_required(UserRole.CUSTOMER)(CartController.update_item),
    methods=["PATCH"]
)
cart_api.add_url_rule(
    "/<int:restaurant_id>/items/<int:cart_item_id>",
    view_func=role_required(UserRole.CUSTOMER)(CartController.remove_item),
    methods=["DELETE"]
)
cart_api.add_url_rule(
    "/<int:restaurant_id>/clear",
    view_func=role_required(UserRole.CUSTOMER)(CartController.clear_cart),
    methods=["DELETE"]
)
cart_api.add_url_rule(
    "/<int:restaurant_id>/voucher/validate",
    view_func=role_required(UserRole.CUSTOMER)(CartController.validate_voucher),
    methods=["POST"]
)
