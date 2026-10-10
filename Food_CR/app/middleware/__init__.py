from functools import wraps
from flask_login import current_user


def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return "Vui lòng đăng nhập để truy cập trang này.", 401
            if current_user.role not in allowed_roles:
                return "Bạn không có quyền truy cập trang này.", 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
