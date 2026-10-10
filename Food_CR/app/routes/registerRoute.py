from flask import Blueprint
from app.controllers.homeController import register_page, register_page_restaurant

register_bp = Blueprint("register_bp", __name__)
register_bp.add_url_rule("/register", view_func=register_page)
register_bp.add_url_rule("/register-restaurant", view_func=register_page_restaurant)