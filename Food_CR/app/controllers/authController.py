from flask import request, jsonify, redirect, current_app, flash
from app.models.model import hash_password, CuisineType, UserRole
from app.dao.userDao import add_user, check_userEmail
from app.dao.userDao import UserDao
from app.dao.systemConfigDao import SystemConfigDao
from flask_login import login_user, logout_user, login_required, current_user
from app.service.notificationByFCM import send_push_notification
import cloudinary.uploader
from app.service.notificationByEmail import send_account_registration_email, send_restaurant_registration_pending_email 
from app.extensions import mint_firebase_custom_token


class LoginController:

    @staticmethod
    def login():
        data = request.get_json()
        if not data:
            return jsonify({"message": "Invalid JSON"}), 400

        username = data.get("username")
        password = data.get("password")
        remember = data.get("remember", False)

        if not username or not password:
            return jsonify({"message": "Vui lòng nhập tên đăng nhập và mật khẩu"}), 400

        user = UserDao.get_by_username(username)
        if not user:
            return jsonify({"message": "Tên đăng nhập hoặc mật khẩu không đúng"}), 401

        check_active = UserDao.check_userActive(user)
        if check_active is False:
            return jsonify({"message": "Tài khoản đã bị vô hiệu hóa"}), 403

        if user.password != hash_password(password):
            return jsonify({"message": "Tên đăng nhập hoặc mật khẩu không đúng"}), 401

        login_user(user, remember=remember)
        firebase_token = mint_firebase_custom_token(user.id)

        if user.role == UserRole.ADMIN:
            redirect_url = '/admin/restaurants/pending'
        elif user.role == UserRole.RESTAURANT:
            redirect_url = '/me'
        else:
            redirect_url = '/'
        flash(f"Chào mừng trở lại, {user.name}!", "success")
        return jsonify({
            "message": "Login successful",
            "redirect": redirect_url,
            "firebase_token": firebase_token,
            "user": {
                "id": user.id,
                "name": user.name,
                "role": user.role.value if user.role else None
            }
        }), 200

    @staticmethod
    def logout():
        logout_user()
        flash(f"Đăng xuất thành công!", "success")
        return redirect('/')

    @staticmethod
    def update_profile():
        data = request.get_json()
        if not data:
            return jsonify({"message": "Invalid JSON"}), 400

        allowed_fields = ['name', 'phonenumber', 'email', 'address', 'avatar', 'description', 'cover_image', 'cuisine_type', 'opening_time', 'closing_time', 'tax_code', 'status']
        update_data = {k: v for k, v in data.items() if k in allowed_fields and v is not None}

        if 'max_cart_items' in data and current_user.role == UserRole.RESTAURANT:
            value = data['max_cart_items']
            if value is None:
                update_data['max_cart_items'] = value
            else:
                result = SystemConfigDao.set_restaurant_max_cart_items(current_user.id, int(value))
                if result is None:
                    admin_max = SystemConfigDao.get_max_cart_items(None)
                    return jsonify({
                        "message": f"Giới hạn giỏ hàng tối đa phải từ 1 đến {admin_max} (theo cấu hình hệ thống)."
                    }), 400
                update_data['max_cart_items'] = result

        if not update_data:
            return jsonify({"message": "No valid fields to update"}), 400

        user = UserDao.update_profile(current_user.id, update_data)
        if not user:
            return jsonify({"message": "User not found"}), 404

        return jsonify({
            "message": "Profile updated successfully",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phonenumber": user.phonenumber,
                "address": user.address,
                "avatar": user.avatar,
                "role": user.role.value if user.role else None
            }
        }), 200


    @staticmethod
    def register():
        data = request.get_json()
        if not data:
            flash("Dữ liệu gửi lên không hợp lệ.", "error")
            return jsonify({"message": "Invalid JSON"}), 400

        name = data.get("name")
        username = data.get("username")
        email = data.get("email")
        phone = data.get("phone")
        password = data.get("password")
        confirm_password = data.get("confirm_password")

        if not all([name, username, email, phone, password, confirm_password]):
            flash("Vui lòng điền đầy đủ tất cả các trường.", "warning")
            return jsonify({"message": "All fields are required"}), 400

        if password != confirm_password:
            flash("Mật khẩu xác nhận không khớp.", "error")
            return jsonify({"message": "Passwords do not match"}), 400

        if UserDao.get_by_username(username):
            flash("Tên đăng nhập đã tồn tại, vui lòng chọn tên khác.", "error")
            return jsonify({"message": "Username already exists"}), 409

        user = add_user(name, phone, username, password, email)
        try:
            send_push_notification(user.id, "Chào mừng bạn đến với CraveConnect!",
                                "Cảm ơn bạn đã đăng ký tài khoản. Hãy khám phá hàng ngàn món ngon nhé!")
        except Exception as e:
            current_app.logger.error(f"Gửi notification đăng ký thất bại: {e}")

        send_account_registration_email(
            recipient=email,
            username=name
        )

        flash(f"Đăng ký thành công! Chào mừng {name} đến với CraveConnect. Vui lòng đăng nhập để trải nghiệm", "success")
        return jsonify({"message": "Registration successful"}), 201

    @staticmethod
    def register_restaurant():
        data = request.form.to_dict() if request.form else request.get_json()
        if not data:
            return jsonify({"message": "Invalid JSON"}), 400

        name = data.get("name")
        username = data.get("username")
        email = data.get("email")
        phone = data.get("phone")
        password = data.get("password")
        address = data.get("address")
        cuisine_type = data.get("cuisine_type")
        tax_code = data.get("tax_code")
        description = data.get("description")

        if not all([name, username, email, phone, password, address]):
            return jsonify({"message": "Vui lòng điền đầy đủ thông tin bắt buộc"}), 400

        if UserDao.get_by_username(username):
            return jsonify({"message": "Tên đăng nhập đã tồn tại"}), 409

        if check_userEmail(email):
            return jsonify({"message": "Email đã được sử dụng"}), 409

        cuisine_enum = None
        if cuisine_type:
            try:
                cuisine_enum = CuisineType[cuisine_type]
            except (KeyError, ValueError):
                pass

        avatar_path = None
        avatar_file = request.files.get("avatar")
        if avatar_file and avatar_file.filename:
            res = cloudinary.uploader.upload(avatar_file)
            avatar_path = res["secure_url"]

        user = add_user(
            name=name,
            phonenumber=phone,
            username=username,
            password=password,
            email=email,
            address=address,
            is_restaurant=True,
            role=UserRole.RESTAURANT,
            description=description,
            cuisine_type=cuisine_enum,
            tax_code=tax_code,
            avatar=avatar_path,
            cover_image=avatar_path,
        )
        try:
            send_push_notification(user.id, "Đăng ký nhà hàng thành công!",
                                   "Nhà hàng của bạn đang chờ được duyệt. Chúng tôi sẽ thông báo khi có kết quả.")
        except Exception as e:
            current_app.logger.error(f"Gửi notification đăng ký nhà hàng thất bại: {e}")

        admins = UserDao.get_admin_users()
        for admin in admins:
            try:
                send_push_notification(
                    admin.id,
                    "Có nhà hàng mới đăng ký!",
                    f"Nhà hàng '{name}' vừa đăng ký đối tác và đang chờ được phê duyệt.",
                    data={"url": "/admin/restaurants/pending", "type": "restaurant_pending"}
                )
            except Exception as e:
                current_app.logger.error(f"Gửi notification cho admin {admin.id} thất bại: {e}")

        send_restaurant_registration_pending_email(
            recipient=email,
            restaurant_name=name
        )
        flash(f"Đăng ký thành công! Chào mừng {name} đến với CraveConnect. Vui lòng chờ admin duyệt để trải nghiệm", "success")
        return jsonify({"message": "Đăng ký nhà hàng thành công!"}), 201
