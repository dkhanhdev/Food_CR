from flask import Blueprint
from flask_login import login_required

from app.controllers.restaurantsControler import RestaurantsController

restaurant_bp = Blueprint('restaurant_bp', __name__)

restaurant_bp.add_url_rule('/<int:restaurant_id>', view_func=RestaurantsController.index)
