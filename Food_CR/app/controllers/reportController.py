from datetime import datetime, timedelta

from flask import jsonify, render_template, request
from flask_login import current_user

from app.dao.reportDao import ReportDao


class ReportController:

    @staticmethod
    def _get_restaurant_id():
        restaurant = current_user.restaurant
        if not restaurant:
            return None
        return restaurant.id

    @staticmethod
    def _parse_date(value, default=None):
        if not value:
            return default
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def index():
        now = datetime.utcnow()
        default_start = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        default_end = now.replace(hour=23, minute=59, second=59, microsecond=0)

        return render_template(
            "restaurantReport.html",
            title="Thống kê báo cáo",
            default_start=default_start.strftime("%Y-%m-%d"),
            default_end=default_end.strftime("%Y-%m-%d"),
        )

    @staticmethod
    def get_summary():
        restaurant_id = ReportController._get_restaurant_id()
        if not restaurant_id:
            return jsonify({"success": False, "message": "Nhà hàng không tồn tại"}), 403

        now = datetime.utcnow()
        default_start = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        default_end = now.replace(hour=23, minute=59, second=59, microsecond=0)

        start_date = ReportController._parse_date(request.args.get("start_date"), default_start)
        end_date = ReportController._parse_date(request.args.get("end_date"), default_end)

        summary = ReportDao.get_revenue_summary(restaurant_id, start_date, end_date)
        return jsonify({"success": True, "data": summary}), 200

    @staticmethod
    def get_revenue_chart():
        restaurant_id = ReportController._get_restaurant_id()
        if not restaurant_id:
            return jsonify({"success": False, "message": "Nhà hàng không tồn tại"}), 403

        now = datetime.utcnow()
        default_start = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        default_end = now.replace(hour=23, minute=59, second=59, microsecond=0)

        start_date = ReportController._parse_date(request.args.get("start_date"), default_start)
        end_date = ReportController._parse_date(request.args.get("end_date"), default_end)

        data = ReportDao.get_revenue_by_date(restaurant_id, start_date, end_date)
        return jsonify({"success": True, "data": data}), 200

    @staticmethod
    def get_top_dishes():
        restaurant_id = ReportController._get_restaurant_id()
        if not restaurant_id:
            return jsonify({"success": False, "message": "Nhà hàng không tồn tại"}), 403

        now = datetime.utcnow()
        default_start = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        default_end = now.replace(hour=23, minute=59, second=59, microsecond=0)

        start_date = ReportController._parse_date(request.args.get("start_date"), default_start)
        end_date = ReportController._parse_date(request.args.get("end_date"), default_end)
        limit = request.args.get("limit", 10, type=int)

        data = ReportDao.get_top_dishes(restaurant_id, start_date, end_date, limit)
        return jsonify({"success": True, "data": data}), 200

    @staticmethod
    def get_category_revenue():
        restaurant_id = ReportController._get_restaurant_id()
        if not restaurant_id:
            return jsonify({"success": False, "message": "Nhà hàng không tồn tại"}), 403

        now = datetime.utcnow()
        default_start = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        default_end = now.replace(hour=23, minute=59, second=59, microsecond=0)

        start_date = ReportController._parse_date(request.args.get("start_date"), default_start)
        end_date = ReportController._parse_date(request.args.get("end_date"), default_end)

        data = ReportDao.get_revenue_by_category(restaurant_id, start_date, end_date)
        return jsonify({"success": True, "data": data}), 200

    @staticmethod
    def get_status_distribution():
        restaurant_id = ReportController._get_restaurant_id()
        if not restaurant_id:
            return jsonify({"success": False, "message": "Nhà hàng không tồn tại"}), 403

        now = datetime.utcnow()
        default_start = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        default_end = now.replace(hour=23, minute=59, second=59, microsecond=0)

        start_date = ReportController._parse_date(request.args.get("start_date"), default_start)
        end_date = ReportController._parse_date(request.args.get("end_date"), default_end)

        data = ReportDao.get_order_status_distribution(restaurant_id, start_date, end_date)
        return jsonify({"success": True, "data": data}), 200
