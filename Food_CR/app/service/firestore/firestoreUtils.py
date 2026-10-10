from firebase_admin import firestore
from app.extensions import firestore_db
from datetime import datetime, timezone

FCM_COLLECTION = "fcm_tokens"
NOTIFICATIONS_COLLECTION = "notifications"


def save_fcm_token(user_id, token, device_id=None, platform="unknown"):
    doc_ref = firestore_db.collection(FCM_COLLECTION).document(str(user_id))
    doc_ref.set({
        "token": token,
        "platform": platform,
        "updated_at": datetime.now(timezone.utc)
    })


def get_fcm_tokens(user_id):
    doc = firestore_db.collection(FCM_COLLECTION).document(str(user_id)).get()
    if not doc.exists:
        return []

    data = doc.to_dict()
    token = data.get("token")
    return [token] if token else []


def delete_fcm_token(user_id, device_id=None):
    doc_ref = firestore_db.collection(FCM_COLLECTION).document(str(user_id))
    doc_ref.delete()


def delete_invalid_token(user_id, token):
    doc = firestore_db.collection(FCM_COLLECTION).document(str(user_id)).get()
    if not doc.exists:
        return

    if doc.to_dict().get("token") == token:
        delete_fcm_token(user_id)


def save_notification(user_id, title, body, data=None):
    """
    Lưu 1 thông báo cho user vào Firestore.

    Tham số:
        user_id (str/int): ID user nhận thông báo.
        title   (str): Tiêu đề thông báo.
        body    (str): Nội dung thông báo.
        data    (dict): Dữ liệu kèm theo, để app biết điều hướng khi click
                        (VD: {"registration_id": 5, "type": "assign_lecturer"}).

    Trả về: notification_id (str) vừa tạo.
    """
    doc_ref = firestore_db.collection(NOTIFICATIONS_COLLECTION) \
        .document(str(user_id)).collection("items").document()

    doc_ref.set({
        "title": title,
        "body": body,
        "data": data or {},
        "is_read": False,
        "created_at": datetime.now(timezone.utc),
    })

    return doc_ref.id


def get_notifications(user_id, limit=50):
    """
    Lấy danh sách thông báo của user, mới nhất trước.

    Trả về: list các dict, mỗi dict có thêm field "id".
    """
    query = firestore_db.collection(NOTIFICATIONS_COLLECTION) \
        .document(str(user_id)).collection("items") \
        .order_by("created_at", direction=firestore.Query.DESCENDING) \
        .limit(limit)

    results = []
    for doc in query.stream():
        item = doc.to_dict()
        item["id"] = doc.id
        if "created_at" in item and isinstance(item["created_at"], datetime):
            item["created_at"] = item["created_at"].isoformat()
        results.append(item)

    return results


def mark_notification_as_read(user_id, notification_id):
    """
    Đánh dấu 1 thông báo là đã đọc.
    """
    doc_ref = firestore_db.collection(NOTIFICATIONS_COLLECTION) \
        .document(str(user_id)).collection("items").document(notification_id)
    doc_ref.update({"is_read": True})


def get_unread_count(user_id):
    """
    Đếm số thông báo chưa đọc (dùng cho badge số trên icon chuông).
    """
    docs = firestore_db.collection(NOTIFICATIONS_COLLECTION) \
        .document(str(user_id)).collection("items") \
        .where("is_read", "==", False).stream()
    return len(list(docs))