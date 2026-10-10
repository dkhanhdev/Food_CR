from flask import redirect, url_for
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from wtforms.validators import NumberRange
from app.models.model import UserRole


class AdminSecureView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        if current_user.is_authenticated:
            if current_user.role == UserRole.RESTAURANT:
                return redirect(url_for('me_bp.me_page'))
            return redirect(url_for('home_bp.index'))
        return redirect(url_for('login_bp.login_page'))


class AdminSecureIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        if current_user.is_authenticated:
            if current_user.role == UserRole.RESTAURANT:
                return redirect(url_for('me_bp.me_page'))
            return redirect(url_for('home_bp.index'))
        return redirect(url_for('login_bp.login_page'))

    @expose('/')
    def index(self):
        return redirect('/admin/restaurants/pending')


class UserAdmin(AdminSecureView):
    column_exclude_list = ['password']
    form_excluded_columns = ['password']
    column_searchable_list = ['name', 'username', 'email']
    column_filters = ['role', 'active', 'auth_provider']
    column_labels = {
        'name': 'Tên',
        'username': 'Tên đăng nhập',
        'email': 'Email',
        'phonenumber': 'Số điện thoại',
        'role': 'Vai trò',
        'active': 'Kích hoạt',
        'created_at': 'Ngày tạo',
    }


class RestaurantAdmin(AdminSecureView):
    column_searchable_list = ['name']
    column_filters = ['cuisine_type', 'status', 'active']
    column_sortable_list = ['name', 'cuisine_type', 'active', 'created_at']
    column_default_sort = ('active', False)

    column_labels = {
        'name': 'Tên nhà hàng',
        'description': 'Mô tả',
        'cuisine_type': 'Loại ẩm thực',
        'status': 'Đang mở',
        'active': 'Duyệt',
        'opening_time': 'Giờ mở cửa',
        'closing_time': 'Giờ đóng cửa',
        'tax_code': 'Mã số thuế',
    }

    column_list = ['name', 'cuisine_type', 'active']


class DishAdmin(AdminSecureView):
    column_searchable_list = ['name']
    column_filters = ['category', 'active']
    column_labels = {
        'name': 'Tên món',
        'description': 'Mô tả',
        'price': 'Giá',
        'category': 'Danh mục',
        'restaurant': 'Nhà hàng',
    }


class SystemConfigAdmin(AdminSecureView):
    can_create = False
    can_delete = False
    column_labels = {
        'name': 'Tên',
        'max_cart_items': 'Số món tối đa mỗi giỏ',
    }
    form_args = {
        'max_cart_items': {'validators': [NumberRange(min=1, max=99)]},
    }
