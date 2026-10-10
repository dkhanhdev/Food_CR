from flask import Blueprint
from flask_login import login_required
from app.controllers.adminController import AdminController
from app.middleware import role_required
from app.models.model import UserRole

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

admin_bp.add_url_rule(
    '/restaurants/pending',
    view_func=login_required(role_required(UserRole.ADMIN)(AdminController.restaurant_pending_approval))
)