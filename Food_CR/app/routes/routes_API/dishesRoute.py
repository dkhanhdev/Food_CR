from flask import Blueprint
from app.controllers.restaurantMenuController import RestaurantMenuController
from app.middleware import role_required
from app.models.model import UserRole

dishes_api = Blueprint("dishes_api", __name__)
controller = RestaurantMenuController()

dishes_api.add_url_rule("/top-recommendations", view_func=controller.get_top_recommended_dishes, methods=["GET"])
dishes_api.add_url_rule("/stats", view_func=role_required(UserRole.RESTAURANT)(controller.get_dishes_stats), methods=["GET"])
dishes_api.add_url_rule("/", view_func=role_required(UserRole.RESTAURANT)(controller.create_dishes), methods=["POST"])
dishes_api.add_url_rule("/<int:dishes_id>", view_func=role_required(UserRole.RESTAURANT)(controller.delete_dishes), methods=["DELETE"])
dishes_api.add_url_rule("/", view_func=role_required(UserRole.RESTAURANT)(controller.change_dishes_status), methods=["PATCH"])

