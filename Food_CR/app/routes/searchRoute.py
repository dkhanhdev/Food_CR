from flask import Blueprint

from app.controllers.searchController import SearchController

search_bp = Blueprint('search_bp', __name__)

search_bp.add_url_rule('/', view_func=SearchController.search_web, methods=['GET'])
