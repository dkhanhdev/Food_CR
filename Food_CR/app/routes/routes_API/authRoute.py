from flask import Blueprint
from flask_login import login_required
from app.controllers.authController import LoginController

auth_api = Blueprint("auth_api", __name__)

auth_api.add_url_rule("/login", view_func=LoginController.login, methods=["POST"])
auth_api.add_url_rule("/logout", view_func=LoginController.logout, methods=["GET"])
auth_api.add_url_rule("/register", view_func=LoginController.register, methods=["POST"])
auth_api.add_url_rule("/update-profile", view_func=login_required(LoginController.update_profile), methods=["PUT"])
auth_api.add_url_rule("/register-restaurant", view_func=LoginController.register_restaurant, methods=["POST"])
