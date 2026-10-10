from flask import Blueprint
from flask_login import login_required
from app.controllers.ChatController import ChatController

chat_bp = Blueprint('chat_bp', __name__)

chat_bp.add_url_rule('/', view_func=login_required(ChatController.index))
