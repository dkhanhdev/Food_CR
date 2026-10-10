from flask import Blueprint
from app.controllers.restaurantMenuController import RestaurantMenuController
from app.middleware import role_required
from app.models.model import UserRole

restaurantMenu_bp = Blueprint('restaurantMenu_bp', __name__)

restaurantMenu_bp.add_url_rule('/restaurant_menu', view_func=role_required(UserRole.RESTAURANT)(RestaurantMenuController.index))
