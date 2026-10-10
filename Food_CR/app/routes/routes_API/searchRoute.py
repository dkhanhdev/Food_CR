from flask import Blueprint
from app.controllers.searchController import SearchController

search_api = Blueprint('search_api', __name__)

search_api.add_url_rule("/", view_func = SearchController.search_restaurants, methods = ["GET"])
