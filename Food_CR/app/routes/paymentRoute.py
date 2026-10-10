from flask import Blueprint

from app.controllers.paymentController import PaymentController

payment_bp = Blueprint("payment_bp", __name__)

payment_bp.add_url_rule(
    "/<int:restaurant_id>",
    view_func=PaymentController.checkout,
    methods=["GET"]
)

payment_bp.add_url_rule(
    "/return",
    view_func=PaymentController.payment_return,
    methods=["GET"]
)

payment_bp.add_url_rule(
    "/vnpay/return",
    view_func=PaymentController.vnpay_return,
    methods=["GET"]
)
