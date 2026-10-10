from flask import jsonify, request, render_template
from app.dao.restaurantsDao import RestaurantsDao


class AdminController:
    """Controller cho toàn bộ admin domain: duyệt nhà hàng, system config, ...

    Edge cases đã biết (chưa xử lý — TODO):
    - User bị reject muốn re-register: userDao.add_user check unique
      username/email, sẽ fail. Cần luồng "re-submit after reject" riêng.
    - Restaurant đã APPROVED rồi admin reject lại: sẽ khoá login luôn
      (user.active = False). Nếu muốn cho phép "tạm khoá" thay vì
      "reject vĩnh viễn", cần status trung gian.
    - approval_status <-> user.active phải sync qua DAO. Nếu update
      trực tiếp DB (Flask-Admin ModelView) sẽ mất sync.
    """

    @staticmethod
    def restaurant_pending_approval():
        return render_template('admin/restaurant_pending_approval.html')

    # ---------------- Restaurants ----------------
    @staticmethod
    def list_restaurants():
        status = request.args.get("status", "pending")
        try:
            page = int(request.args.get("page", 1))
        except ValueError:
            page = 1
        per_page = 10

        pagination = RestaurantsDao.get_restaurants_by_status(
            status=status, page=page, per_page=per_page
        )

        items = []
        for r in pagination.items:
            user = r.user
            items.append({
                "id": r.id,
                "name": r.name,
                "cover_image": r.cover_image,
                "description": r.description,
                "cuisine_type": r.cuisine_type.value if r.cuisine_type else None,
                "approval_status": r.approval_status.value if r.approval_status else None,
                "rejection_reason": r.rejection_reason,
                "tax_code": r.tax_code,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "owner": {
                    "name": user.name if user else None,
                    "username": user.username if user else None,
                    "email": user.email if user else None,
                    "phonenumber": user.phonenumber if user else None,
                    "address": user.address if user else None,
                    "avatar": user.avatar if user else None,
                } if user else None,
            })

        return jsonify({
            "items": items,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }), 200

    @staticmethod
    def approve_restaurant(restaurant_id):
        # Approve: mở login (user.active=True) + đánh dấu APPROVED.
        # Nếu restaurant đã APPROVED trước đó thì đây là no-op semantically,
        # nhưng vẫn re-set active=True để đảm bảo consistency.
        r = RestaurantsDao.approve_restaurant(restaurant_id)
        if not r:
            return jsonify({"success": False, "message": "Restaurant not found"}), 404
        return jsonify({
            "success": True,
            "id": r.id,
            "approval_status": r.approval_status.value,
        }), 200

    @staticmethod
    def reject_restaurant(restaurant_id):
        # Reject: khoá login (user.active=False) + đánh dấu REJECTED.
        # Áp dụng cho cả trường hợp restaurant đang PENDING lẫn đã APPROVED —
        # admin có toàn quyền revoke. Không có luồng "undo reject", muốn mở
        # lại phải gọi approve.
        data = request.get_json() 
        reason = data.get("reason", "")
        if not str(reason).strip():
            return jsonify({"success": False, "message": "Reject reason is required"}), 400

        r = RestaurantsDao.reject_restaurant(restaurant_id, reason=reason)
        if not r:
            return jsonify({"success": False, "message": "Restaurant not found"}), 404
        return jsonify({
            "success": True,
            "id": r.id,
            "approval_status": r.approval_status.value,
            "rejection_reason": r.rejection_reason,
        }), 200
