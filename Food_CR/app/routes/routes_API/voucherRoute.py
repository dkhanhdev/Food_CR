from flask import Blueprint
from flask_login import login_required
from app.controllers.voucherController import VoucherController
from app.middleware import role_required
from app.models.model import UserRole


voucher_api = Blueprint("voucher_api", __name__)

voucher_api.add_url_rule("/promotions", view_func=login_required(role_required(UserRole.RESTAURANT)(VoucherController.list_vouchers)), methods=["GET"])
voucher_api.add_url_rule("/promotions", view_func=login_required(role_required(UserRole.RESTAURANT)(VoucherController.create_voucher)), methods=["POST"])
voucher_api.add_url_rule("/promotions/dishes", view_func=login_required(role_required(UserRole.RESTAURANT)(VoucherController.list_dishes)), methods=["GET"])
voucher_api.add_url_rule("/promotions/<int:voucher_id>", view_func=login_required(role_required(UserRole.RESTAURANT)(VoucherController.update_voucher)), methods=["PUT"])
voucher_api.add_url_rule("/promotions/<int:voucher_id>", view_func=login_required(role_required(UserRole.RESTAURANT)(VoucherController.delete_voucher)), methods=["DELETE"])
