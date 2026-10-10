from app.routes.routes_API.authRoute import auth_api
from app.routes.routes_API.restaurantRoute import restaurant_api
from app.routes.routes_API.searchRoute import search_api
from app.routes.routes_API.adminRoute import admin_api
from app.routes.routes_API.fcmRoute import fcm_api
from app.routes.routes_API.cartRoute import cart_api
from app.routes.routes_API.voucherRoute import voucher_api
from app.routes.routes_API.paymentRoute import payment_api
from app.routes.routes_API.ordersRoute import orders_api
from app.routes.routes_API.dishesRoute import dishes_api
from app.routes.routes_API.OrderForCustomerRoute import orderCustomer_api
from app.routes.routes_API.reviewRoute import review_api
from app.routes.routes_API.chatRoute import chat_api
from app.routes.routes_API.reportRoute import report_api
from app.routes.routes_API.aiChatRoute import ai_api


def route_api(app):
    app.register_blueprint(restaurant_api, url_prefix="/api/restaurants")
    app.register_blueprint(dishes_api, url_prefix="/api/dishes")
    app.register_blueprint(auth_api, url_prefix="/api/auth")
    app.register_blueprint(search_api, url_prefix="/api/search")
    app.register_blueprint(admin_api, url_prefix="/api/admin")
    app.register_blueprint(fcm_api, url_prefix="/api/fcm")
    app.register_blueprint(cart_api, url_prefix="/api/cart")
    app.register_blueprint(voucher_api, url_prefix="/api")
    app.register_blueprint(payment_api, url_prefix="/api/payment")
    app.register_blueprint(orders_api, url_prefix="/api/orders")
    app.register_blueprint(orderCustomer_api, url_prefix="/api/orders_customer")
    app.register_blueprint(review_api, url_prefix="/api/reviews")
    app.register_blueprint(chat_api, url_prefix="/api/chats")
    app.register_blueprint(report_api, url_prefix="/api/reports")
    app.register_blueprint(ai_api, url_prefix="/api/ai")

