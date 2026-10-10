from flask import render_template, redirect, url_for
from flask_login import current_user
from app.models.model import UserRole


class NotificationController:
    @staticmethod
    def index():
        return render_template(
            "notification.html",
            title="Thông báo"
        )