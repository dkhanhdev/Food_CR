from flask import Blueprint
from app.controllers.homeController import login_page

login_bp = Blueprint("login_bp", __name__)
login_bp.add_url_rule("/login", view_func=login_page)