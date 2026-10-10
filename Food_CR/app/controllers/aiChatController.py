import os
import json
import logging
from datetime import datetime

from flask import jsonify, request
from flask_login import current_user, login_required

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
#  System prompt template
# ──────────────────────────────────────────────
_SYSTEM_PROMPT_TEMPLATE = """Bạn là **Foodie AI** — trợ lý ẩm thực thông minh của nền tảng **CraveConnect** (KHM Foodie).
Nhiệm vụ của bạn là giúp khách hàng tìm kiếm món ăn, nhà hàng phù hợp và đưa ra gợi ý thực đơn cá nhân hóa.

## Nguyên tắc trả lời
- Luôn trả lời bằng **tiếng Việt** thân thiện, ngắn gọn và hữu ích.
- Ưu tiên gợi ý các nhà hàng và món ăn **có sẵn trong hệ thống** (danh sách bên dưới).
- Khi gợi ý món/nhà hàng, hãy kèm theo **giá tiền** (nếu có) và **loại ẩm thực**.
- Nếu khách hỏi về thứ không có trong hệ thống, hãy nói thật và gợi ý thay thế.
- Không bịa đặt thông tin không có trong dữ liệu.
- Giữ câu trả lời súc tích (tối đa 250 chữ), dùng emoji phù hợp để sinh động hơn.
- Khi gợi ý nhà hàng, format theo: **Tên nhà hàng** — *Loại ẩm thực* — địa chỉ (nếu có).
- Khi gợi ý món ăn, format theo: 🍜 **Tên món** — *Nhà hàng* — `XXX.000đ`.
- Thời điểm hiện tại: {current_time}

## Dữ liệu nhà hàng và món ăn trong hệ thống
{restaurant_context}
"""


def _build_restaurant_context() -> str:
    """Lấy danh sách nhà hàng và món ăn từ DB, chuyển thành text context cho Gemini."""
    try:
        from app.models.model import Restaurant, Dish, DishCategory
        from app.extensions import db

        restaurants = (
            Restaurant.query
            .options(
                db.joinedload(Restaurant.user),
                db.joinedload(Restaurant.dishes)
            )
            .filter(Restaurant.active == True)
            .limit(30)  # giới hạn để tránh prompt quá dài
            .all()
        )

        if not restaurants:
            return "Hiện tại chưa có nhà hàng nào trong hệ thống."

        lines = []
        for r in restaurants:
            opening = r.opening_time.strftime("%H:%M") if r.opening_time else "?"
            closing = r.closing_time.strftime("%H:%M") if r.closing_time else "?"
            cuisine = r.cuisine_type.value if r.cuisine_type else "Đa dạng"
            address = r.user.address if r.user else "Chưa cập nhật"
            is_open = "🟢 Đang mở" if r.status else "🔴 Đã đóng"

            lines.append(
                f"\n### {r.name} (ID:{r.id}) | {cuisine} | {is_open} | {opening}–{closing}\n"
                f"  Địa chỉ: {address}"
            )

            active_dishes = [d for d in r.dishes if d.active][:15]
            if active_dishes:
                lines.append("  Thực đơn:")
                for d in active_dishes:
                    price_str = f"{int(d.price):,}đ".replace(",", ".")
                    cat = d.category.value if d.category else ""
                    lines.append(f"    - {d.name} ({cat}) — {price_str}")
            else:
                lines.append("  Thực đơn: Chưa có món.")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"[AiChat] Không thể tải context DB: {e}")
        return "Không thể tải danh sách nhà hàng lúc này."




class AiChatController:

    @staticmethod
    def chat():
        """
        POST /api/ai/chat
        Body JSON:
          {
            "message": "Hôm nay ăn gì nhỉ?",
            "history": [
              {"role": "user", "parts": ["..."]},
              {"role": "model", "parts": ["..."]}
            ]
          }
        """
        data = request.get_json(silent=True) or {}
        user_message = (data.get("message") or "").strip()
        history = data.get("history") or []

        if not user_message:
            return jsonify({"success": False, "message": "Tin nhắn không được để trống."}), 400

        if len(user_message) > 500:
            return jsonify({"success": False, "message": "Tin nhắn quá dài (tối đa 500 ký tự)."}), 400

        try:
            import google.generativeai as genai  # type: ignore

            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                return jsonify({
                    "success": False,
                    "message": "GEMINI_API_KEY chưa được cấu hình trong .env. Liên hệ admin để kích hoạt Foodie AI."
                }), 503

            genai.configure(api_key=api_key)

            # Xây dựng system prompt với context nhà hàng/món ăn từ DB
            restaurant_context = _build_restaurant_context()
            current_time = datetime.now().strftime("%H:%M ngày %d/%m/%Y")
            system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
                restaurant_context=restaurant_context,
                current_time=current_time,
            )

            # Chuẩn hóa history (tối đa 10 turns gần nhất để tránh prompt quá dài)
            safe_history = []
            for turn in history[-10:]:
                role = turn.get("role")
                parts = turn.get("parts")
                if role in ("user", "model") and isinstance(parts, list) and parts:
                    safe_history.append({"role": role, "parts": parts})

            # Khởi tạo model với system_instruction (ưu tiên env GEMINI_MODEL, fallback gemini-3.8-flash / gemini-3.5-flash-lite)
            preferred_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
            candidate_models = list(dict.fromkeys([preferred_model, "gemini-3.8-flash", "gemini-3.5-flash-lite"]))

            reply_text = None
            last_err = None
            for m in candidate_models:
                try:
                    model_ctx = genai.GenerativeModel(
                        model_name=m,
                        system_instruction=system_prompt,
                        generation_config={
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "max_output_tokens": 512,
                        },
                    )

                    chat_session = model_ctx.start_chat(history=safe_history)
                    response = chat_session.send_message(user_message)
                    reply_text = response.text.strip()
                    if reply_text:
                        break
                except Exception as ex:
                    last_err = ex
                    logger.warning(f"[AiChat] Model {m} gặp lỗi: {ex}. Đang thử model tiếp theo...")

            if not reply_text:
                raise last_err or RuntimeError("Không thể nhận phản hồi từ Gemini model")

            return jsonify({
                "success": True,
                "reply": reply_text,
            }), 200

        except Exception as e:
            logger.error(f"[AiChat] Lỗi gọi Gemini API: {e}")
            return jsonify({
                "success": False,
                "message": "Trợ lý AI đang bận, vui lòng thử lại sau."
            }), 503


    @staticmethod
    def get_quick_prompts():
        """
        GET /api/ai/quick-prompts
        Trả về danh sách gợi ý câu hỏi nhanh cho người dùng.
        """
        prompts = [
            {"icon": "🌧️", "text": "Trời mưa hôm nay nên ăn gì ấm bụng?"},
            {"icon": "💸", "text": "Gợi ý món ngon dưới 50.000đ"},
            {"icon": "🥗", "text": "Tôi muốn ăn chay hôm nay"},
            {"icon": "🔥", "text": "Món nào đang hot nhất?"},
            {"icon": "🍜", "text": "Muốn ăn bún bò, có chỗ nào ngon không?"},
            {"icon": "⚡", "text": "Giao nhanh trong 20 phút, ăn gì?"},
        ]
        return jsonify({"success": True, "prompts": prompts}), 200
