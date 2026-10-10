from flask import Blueprint
from flask_login import login_required
from app.controllers.aiChatController import AiChatController

ai_api = Blueprint("ai_api", __name__)

ai_api.route("/chat", methods=["POST"])(AiChatController.chat)
ai_api.route("/quick-prompts", methods=["GET"])(AiChatController.get_quick_prompts)
