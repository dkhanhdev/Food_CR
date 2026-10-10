from flask import Blueprint
from app.controllers.OrderForCustomerController import OrderForCustomerController
from app.middleware import role_required
from app.models.model import UserRole

orderCustomer_api = Blueprint("orderCustomer_api", __name__)
controller = OrderForCustomerController()

orderCustomer_api.add_url_rule("/", view_func=role_required(UserRole.CUSTOMER)(controller.loadOrders), methods=["GET"])
orderCustomer_api.add_url_rule("/<int:order_id>", view_func=role_required(UserRole.CUSTOMER)(controller.get_order_detail_customer), methods=["GET"])
orderCustomer_api.add_url_rule("/create", view_func=role_required(UserRole.CUSTOMER)(controller.create_order), methods=["POST"])
orderCustomer_api.add_url_rule("/<int:order_id>/expire", view_func=role_required(UserRole.CUSTOMER)(controller.expire_order), methods=["POST"])


