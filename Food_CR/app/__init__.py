import os
from flask import Flask
from app.config import config_map
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from app.extensions import db, migrate
from flask_admin import Admin
from app.models.model import User, Restaurant, Dish, SystemConfig
from app.admin import UserAdmin, RestaurantAdmin, DishAdmin, SystemConfigAdmin, AdminSecureIndexView
from flask_admin.theme import Bootstrap4Theme
from app.extensions import db, mail, init_firebase, mint_firebase_custom_token

from flask_mail import Mail, Message
import cloudinary


load_dotenv()

# Extensions
oauth = OAuth()
login_manager = LoginManager()
login_manager.login_view = 'login_bp.login_page'
login_manager.login_message = 'Vui lòng đăng nhập để truy cập trang này.'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    from app.models.model import User
    return User.query.get(int(user_id))


# Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)


def create_app(config_name='dev'):
    app = Flask(__name__)

    app.config.from_object(config_map[config_name])
    app.config['FIREBASE_CREDENTIALS_BASE64'] = os.getenv('FIREBASE_CREDENTIALS_BASE64')

    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    # Init extensions
    login_manager.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    init_firebase(app)  

    # Admin
    from app.models.model import User, Restaurant, Dish, SystemConfig
    from app.admin import UserAdmin, RestaurantAdmin, DishAdmin, SystemConfigAdmin, AdminSecureIndexView
    from flask_admin.theme import Bootstrap4Theme

    admin = Admin(app, name='KHM Foodie Admin', theme=Bootstrap4Theme(), index_view=AdminSecureIndexView())
    admin.add_view(UserAdmin(User, db.session))
    admin.add_view(RestaurantAdmin(Restaurant, db.session))
    admin.add_view(DishAdmin(Dish, db.session))
    admin.add_view(SystemConfigAdmin(SystemConfig, db.session))

    # OAuth
    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=os.getenv('CLIENT_ID_GOOGLE'),
        client_secret=os.getenv('CLIENT_SECRET_GOOGLE'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    # Routes
    from app.routes import register_routes
    register_routes(app)

    from app.routes.routes_API.index import route_api
    route_api(app)

    @app.context_processor
    def inject_firebase_token():
        from flask_login import current_user
        if current_user.is_authenticated:
            return dict(firebase_token=mint_firebase_custom_token(current_user.id))
        return dict(firebase_token=None)

    return app
