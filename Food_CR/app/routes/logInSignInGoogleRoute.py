from app.controllers.LogInSignInControler.LogInSignInGoogleControler import LogInSignInGoogleControler
from flask import Blueprint

google_auth_bp = Blueprint('google_auth_bp', __name__)
controller = LogInSignInGoogleControler()

google_auth_bp.add_url_rule('/login/google', view_func=controller.login_google, methods=['GET'])
google_auth_bp.add_url_rule('/google/callback', view_func=controller.auth_callback, methods=['GET'])
