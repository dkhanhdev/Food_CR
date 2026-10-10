from flask_migrate import Migrate
import json
import base64
from flask_sqlalchemy import SQLAlchemy
import firebase_admin
from flask_mail import Mail
from firebase_admin import credentials, firestore, auth as fb_auth

import logging

logger = logging.getLogger(__name__)

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
firestore_db = None


def init_firebase(app):
    global firestore_db
    cred_b64 = app.config.get('FIREBASE_CREDENTIALS_BASE64')
    if not cred_b64:
        logger.warning("[Firebase] FIREBASE_CREDENTIALS_BASE64 is not configured. Firebase features will be disabled.")
        return

    try:
        if not firebase_admin._apps:
            cred_json = json.loads(base64.b64decode(cred_b64).decode('utf-8'))
            cred = credentials.Certificate(cred_json)
            firebase_admin.initialize_app(cred)
        firestore_db = firestore.client()
        logger.info("[Firebase] Initialized successfully.")
    except Exception as e:
        logger.warning(f"[Firebase] Initialization failed: {e}. Firebase features will be disabled.")


def mint_firebase_custom_token(user_id):
    """user_id là int từ SQLAlchemy (User.id) -> ép về string vì Firebase
    uid luôn là string."""
    try:
        if not firebase_admin._apps:
            return None
        uid = str(user_id)
        token = fb_auth.create_custom_token(uid)
        if isinstance(token, bytes):
            return token.decode('utf-8')
        return str(token)
    except Exception as e:
        logger.warning(f"[Firebase] mint_firebase_custom_token failed: {e}")
        return None