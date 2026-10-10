import os
from flask import Blueprint, send_from_directory
from app.routes.homeRoute import home_bp
from app.routes.loginRoute import login_bp
from app.routes.registerRoute import register_bp
from app.routes.searchRoute import search_bp
from app.routes.logInSignInGoogleRoute import google_auth_bp
from app.routes.restaurantRoute import restaurant_bp
from app.routes.meRoute import me_bp
from app.routes.adminRoute import admin_bp
from app.routes.notificationRoute import notification_bp
from app.routes.promotionsRoute import promotions_bp
from app.routes.paymentRoute import payment_bp
from app.routes.ordersRoute import orders_bp
from app.routes.restaurantMenuRoute import restaurantMenu_bp
from app.routes.OrderForCustomerRoute import orderCustomer_bp
from app.routes.chatRoute import chat_bp
from app.routes.reportRoute import report_bp


def route_web(app):
    @app.route('/firebase-messaging-sw.js')
    def serve_fcm_sw():
        return send_from_directory(
            os.path.join(app.root_path, 'static'),
            'firebase-messaging-sw.js',
            mimetype='application/javascript'
        )

    app.register_blueprint(home_bp, url_prefix='/')
    app.register_blueprint(login_bp, url_prefix='/')
    app.register_blueprint(register_bp, url_prefix='/')
    app.register_blueprint(google_auth_bp, url_prefix='/auth')
    app.register_blueprint(search_bp, url_prefix='/search_customer')
    app.register_blueprint(restaurant_bp, url_prefix='/restaurants')
    app.register_blueprint(orders_bp, url_prefix='/restaurants')
    app.register_blueprint(notification_bp, url_prefix='/notification')
    app.register_blueprint(me_bp, url_prefix='/')
    app.register_blueprint(promotions_bp, url_prefix='/')
    app.register_blueprint(orderCustomer_bp, url_prefix='/order_customer')
    app.register_blueprint(admin_bp)
    app.register_blueprint(payment_bp, url_prefix="/payment")
    app.register_blueprint(restaurantMenu_bp, url_prefix='/')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(report_bp, url_prefix='/restaurants')
