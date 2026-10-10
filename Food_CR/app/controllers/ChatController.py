from flask import jsonify, request, render_template
from flask_login import current_user
from firebase_admin import firestore
from app.models.model import UserRole
from app.extensions import firestore_db
from firebase_admin import auth as fb_auth

class ChatController:

    def revoke_firebase_session(self):
        """Gọi khi user logout khỏi Flask -> thu hồi luôn refresh token
        bên Firebase, tránh phiên Firebase 'mồ côi' khi Flask session
        đã hết nhưng tab trình duyệt vẫn còn mở."""
        uid = str(current_user.id)
        try:
            fb_auth.revoke_refresh_tokens(uid)
        except Exception as e:
            print(f"Không revoke được Firebase session cho uid {uid}: {e}")

        return jsonify({"ok": True})

    def create_direct_chat(self):
        data = request.get_json(force=True)
        other_id = data.get("other_user_id")
        if not other_id:
            return jsonify({"error": "Thiếu other_user_id"}), 400

        my_id = str(current_user.id)
        other_id = str(other_id)
        chat_id = "dm_" + "_".join(sorted([my_id, other_id]))
        order_id = data.get("order_id")
        order_id = str(order_id) if order_id else None

        chat_ref = firestore_db.collection("chats").document(chat_id)
        snapshot = chat_ref.get()

        if not snapshot.exists:
            doc = {
                "type": "direct",
                "members": sorted([my_id, other_id]),
                "createdAt": firestore.SERVER_TIMESTAMP,
            }
            if order_id:
                doc["orderId"] = order_id
                doc["orderIds"] = firestore.ArrayUnion([order_id])
            chat_ref.set(doc)
        elif order_id and snapshot.to_dict().get("orderId") != order_id:
            chat_ref.update({
                "orderId": order_id,
                "orderIds": firestore.ArrayUnion([order_id]),
                "updatedAt": firestore.SERVER_TIMESTAMP,
            })

        return jsonify({"chatId": chat_id})

    def get_my_chats(self):
        my_id = str(current_user.id)
        docs = firestore_db.collection("chats").where(
            "members", "array_contains", my_id
        ).stream()

        from app.dao.userDao import UserDao

        chats = []
        for d in docs:
            item = d.to_dict()
            item["id"] = d.id

            other_id = next((m for m in item["members"] if m != my_id), None)
            if other_id:
                other_user = UserDao.get_by_id(int(other_id))
                if other_user:
                    item["otherUserName"] = other_user.name
                    item["otherUserAvatar"] = other_user.avatar

            chats.append(item)
        return jsonify(chats)

    @staticmethod
    def get_chat_order(chat_id):
        chat_doc = firestore_db.collection("chats").document(chat_id).get()
        if not chat_doc.exists:
            return jsonify({"error": "Chat not found"}), 404

        chat = chat_doc.to_dict()
        order_id = chat.get("orderId")
        if not order_id:
            return jsonify({"orderId": None, "order": None})

        from app.dao.ordersDao import OrdersDao
        if current_user.role == UserRole.RESTAURANT:
            order = OrdersDao.get_order_by_id_and_customer(int(order_id), isRestaurant=True)
        else:
            order = OrdersDao.get_order_by_id_and_customer(int(order_id))
        return jsonify({"orderId": order_id, "order": order})

    @staticmethod
    def index():
        return render_template(
            "chatPage.html",
            title="Nhắn tin"
        )