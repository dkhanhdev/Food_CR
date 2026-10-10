from flask import Blueprint

from app.controllers.orderController import OrderController
from app.middleware import role_required
from app.models.model import UserRole

orders_bp = Blueprint('orders_bp', __name__)

orders_bp.add_url_rule(
    '/orders',
    view_func=role_required(UserRole.RESTAURANT)(OrderController.board),
)
