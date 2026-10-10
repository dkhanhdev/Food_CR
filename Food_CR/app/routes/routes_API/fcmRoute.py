from flask import Blueprint, jsonify, request, current_app
from app.service.firestore.firestoreUtils import save_fcm_token, get_fcm_tokens, get_notifications, get_unread_count, mark_notification_as_read
from app.service.notificationByFCM import send_push_notification

fcm_api = Blueprint('fcm_api', __name__)


@fcm_api.route('/save-token', methods=['POST'])
def save_token():
    data = request.get_json()
    if not data or 'token' not in data:
        return jsonify({'error': 'Missing token'}), 400

    token = data['token']
    device_id = data.get('device_id', 'unknown')
    platform = data.get('platform', 'web')
    user_id = data.get('user_id', 'guest')

    save_fcm_token(user_id, token, device_id, platform)
    return jsonify({'message': 'Token saved'}), 200


@fcm_api.route('/list', methods=['GET'])
def list_notifications():
    user_id = request.args.get('user_id', 'guest')
    limit = request.args.get('limit', 50, type=int)
    notifications = get_notifications(user_id, limit)
    unread_count = get_unread_count(user_id)
    return jsonify({
        "notifications": notifications,
        "unread_count": unread_count
    }), 200


@fcm_api.route('/tokens/<user_id>', methods=['GET'])
def check_tokens(user_id):
    tokens = get_fcm_tokens(user_id)
    return jsonify({'user_id': user_id, 'token_count': len(tokens), 'tokens': tokens}), 200


@fcm_api.route('/test-push', methods=['POST'])
def test_push():
    data = request.get_json()
    user_id = data.get('user_id') if data else None
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    try:
        r = send_push_notification(user_id, "Test notification", "Hello từ server!")
        if r is None:
            return jsonify({'message': 'Không có FCM token để gửi push'}), 200
        return jsonify({'message': f'Push sent, {r.success_count}/{len(r.responses)} thành công'}), 200
    except Exception as e:
        current_app.logger.error(f"Test push error: {e}")
        return jsonify({'error': str(e)}), 500


@fcm_api.route('/unread-count', methods=['GET'])
def unread_count():
    user_id = request.args.get('user_id', 'guest')
    count = get_unread_count(user_id)
    return jsonify({"unread_count": count}), 200


@fcm_api.route('/read/<notification_id>', methods=['POST'])
def mark_read(notification_id):
    user_id = request.json.get('user_id', 'guest') if request.is_json else 'guest'
    mark_notification_as_read(user_id, notification_id)
    return jsonify({"message": "Đã đánh dấu đã đọc"}), 200
