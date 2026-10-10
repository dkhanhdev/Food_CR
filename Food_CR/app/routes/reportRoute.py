from flask import Blueprint

from app.controllers.reportController import ReportController
from app.middleware import role_required
from app.models.model import UserRole

report_bp = Blueprint('report_bp', __name__)

report_bp.add_url_rule(
    '/reports',
    view_func=role_required(UserRole.RESTAURANT)(ReportController.index),
)
