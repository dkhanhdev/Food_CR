from flask import Blueprint
from flask_login import login_required
from app.controllers.adminController import AdminController
from app.middleware import role_required
from app.models.model import UserRole

admin_api = Blueprint("admin_api", __name__)

admin_api.add_url_rule(
    "/restaurants",
    view_func=login_required(role_required(UserRole.ADMIN)(AdminController.list_restaurants)),
    methods=["GET"]
)
admin_api.add_url_rule(
    "/restaurants/<int:restaurant_id>/approve",
    view_func=login_required(role_required(UserRole.ADMIN)(AdminController.approve_restaurant)),
    methods=["PATCH"]
)
admin_api.add_url_rule(
    "/restaurants/<int:restaurant_id>/reject",
    view_func=login_required(role_required(UserRole.ADMIN)(AdminController.reject_restaurant)),
    methods=["PATCH"]
)
