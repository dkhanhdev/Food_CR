from app import oauth
from flask import url_for, redirect
from flask_login import login_user, logout_user
from app.dao.userDao import add_user, check_userEmail
from app.models.model import UserRole

class LogInSignInGoogleControler:

    def login_google(self):
        redirect_uri = url_for('google_auth_bp.auth_callback', _external=True)
        return oauth.google.authorize_redirect(redirect_uri)

    def auth_callback(self):
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')

        email = user_info['email']
        name = user_info['name']
        avatar = user_info['picture']

        user = check_userEmail(email)

        if not user:
            user = add_user(
                email=email,
                name=name,
                avatar=avatar,
                auth_provider='google',
            )

        login_user(user)

        if user.role == UserRole.RESTAURANT:
            return redirect('/me')
        return redirect("/")