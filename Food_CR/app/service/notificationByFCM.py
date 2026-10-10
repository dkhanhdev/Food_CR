from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError
from flask import current_app
from app.service.firestore.firestoreUtils import get_fcm_tokens, delete_invalid_token, save_notification


def send_push_notification(user_id, title, body, data=None):
    """
    Gửi push notification đến TẤT CẢ thiết bị của 1 user (lấy token từ Firestore).
    Tự động dọn token chết nếu gửi thất bại (app bị gỡ, token hết hạn...).
    """
    save_notification(user_id, title, body, data)

    tokens = get_fcm_tokens(user_id)
    if not tokens:
        current_app.logger.warning(f"User {user_id} không có FCM token, chỉ lưu notification.")
        return None

    current_app.logger.info(f"Đang gửi push cho user {user_id}, số token: {len(tokens)}")

    message = messaging.MulticastMessage(
        data={
            "title": title,
            "body": body,
            **(data or {})
        },
        tokens=tokens
    )

    try:
        response = messaging.send_each_for_multicast(message)
        current_app.logger.info(f"Kết quả gửi push: {response.success_count}/{len(tokens)} thành công")
    except FirebaseError as e:
        current_app.logger.error(f"Gửi push notification thất bại cho user {user_id}: {e}")
        return None

    # Dọn token không còn hợp lệ khỏi Firestore
    for idx, resp in enumerate(response.responses):
        if not resp.success:
            current_app.logger.warning(
                f"Token không hợp lệ, xóa khỏi Firestore: {tokens[idx]} - lỗi: {resp.exception}"
            )
            delete_invalid_token(user_id, tokens[idx])

    return response


def send_push_notification_multicast(tokens, title, body, data=None):
    """
    Gửi push notification tới danh sách token cụ thể (tối đa 500 token/lần).
    Dùng khi đã có sẵn danh sách token, không cần tra Firestore theo user_id.
    """
    if not tokens:
        return None

    message = messaging.MulticastMessage(
        data=data or {},
        tokens=tokens
    )

    try:
        return messaging.send_each_for_multicast(message)
    except FirebaseError as e:
        current_app.logger.error(f"Gửi multicast push notification thất bại: {e}")
        return None


def send_push_notification_to_topic(topic, title, body, data=None):
    """
    Gửi push notification broadcast tới 1 topic (nhóm user đã subscribe).
    """
    message = messaging.Message(
        data=data or {},
        topic=topic
    )

    try:
        return messaging.send(message)
    except FirebaseError as e:
        current_app.logger.error(f"Gửi push notification tới topic '{topic}' thất bại: {e}")
        return None