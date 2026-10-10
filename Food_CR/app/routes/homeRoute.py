from flask import Blueprint, send_from_directory
from flask_login import login_required
from app.controllers.homeController import index

home_bp = Blueprint("home_bp", __name__)
home_bp.add_url_rule("/", view_func=index)

import os
from flask import current_app

@home_bp.route("/templates/<path:filename>")
def serve_template(filename):
    return send_from_directory(os.path.join(current_app.root_path, "templates"), filename)


@home_bp.route("/order-detail/<int:restaurant_id>")
@login_required
def order_detail(restaurant_id):
    from app.controllers.homeController import order_detail_page
    return order_detail_page(restaurant_id)


@home_bp.route("/payment-countdown/<int:order_id>")
@login_required
def payment_countdown(order_id):
    from app.controllers.homeController import payment_countdown_page
    return payment_countdown_page(order_id)