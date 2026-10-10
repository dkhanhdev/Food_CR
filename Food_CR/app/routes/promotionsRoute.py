from flask import Blueprint
from app.controllers.homeController import promotions_page

promotions_bp = Blueprint("promotions_bp", __name__)
promotions_bp.add_url_rule("/promotions", view_func=promotions_page)
