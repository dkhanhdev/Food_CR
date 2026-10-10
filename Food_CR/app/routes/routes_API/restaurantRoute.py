from flask import Blueprint
from flask_login import login_required
from app.controllers.restaurantsControler import RestaurantsController

restaurant_api = Blueprint("restaurant_api", __name__)
controller = RestaurantsController()

restaurant_api.add_url_rule("/", view_func=controller.get_all_restaurants, methods=["GET"])
restaurant_api.add_url_rule("/<int:restaurant_id>", view_func=controller.get_restaurant_by_id, methods=["GET"])
restaurant_api.add_url_rule("/<int:restaurant_id>/dishes", view_func=controller.get_list_dishes, methods=["GET"])
restaurant_api.add_url_rule("/<int:restaurant_id>/vouchers", view_func=controller.get_active_vouchers, methods=["GET"])
restaurant_api.add_url_rule("/<int:restaurant_id>/recommendations", view_func=controller.get_recommended_dishes, methods=["GET"])
restaurant_api.add_url_rule("/<int:restaurant_id>/open_restaurant", view_func=login_required(controller.open_restaurant), methods=["PATCH"])
restaurant_api.add_url_rule("/<int:restaurant_id>/close_restaurant", view_func=login_required(controller.close_restaurant), methods=["PATCH"])

