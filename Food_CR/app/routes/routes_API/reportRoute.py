from flask import Blueprint

from app.controllers.reportController import ReportController
from app.middleware import role_required
from app.models.model import UserRole

report_api = Blueprint("report_api", __name__)

report_api.add_url_rule(
    "/summary",
    view_func=role_required(UserRole.RESTAURANT)(ReportController.get_summary),
    methods=["GET"],
)
report_api.add_url_rule(
    "/revenue-chart",
    view_func=role_required(UserRole.RESTAURANT)(ReportController.get_revenue_chart),
    methods=["GET"],
)
report_api.add_url_rule(
    "/top-dishes",
    view_func=role_required(UserRole.RESTAURANT)(ReportController.get_top_dishes),
    methods=["GET"],
)
report_api.add_url_rule(
    "/category-revenue",
    view_func=role_required(UserRole.RESTAURANT)(ReportController.get_category_revenue),
    methods=["GET"],
)
report_api.add_url_rule(
    "/status-distribution",
    view_func=role_required(UserRole.RESTAURANT)(ReportController.get_status_distribution),
    methods=["GET"],
)
