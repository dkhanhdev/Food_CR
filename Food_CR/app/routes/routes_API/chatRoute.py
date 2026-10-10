from flask import Blueprint
from flask_login import login_required
from app.controllers.ChatController import ChatController

chat_api = Blueprint("chat_api", __name__)
controller = ChatController()

chat_api.add_url_rule("/direct", view_func=login_required(controller.create_direct_chat), methods=["POST"])
chat_api.add_url_rule("/mine", view_func=login_required(controller.get_my_chats), methods=["GET"])
chat_api.add_url_rule("/logout", view_func=login_required(controller.revoke_firebase_session), methods=["POST"])
chat_api.add_url_rule("/<chat_id>/order", view_func=login_required(controller.get_chat_order), methods=["GET"])