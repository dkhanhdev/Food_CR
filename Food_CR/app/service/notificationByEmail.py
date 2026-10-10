from app.extensions import mail
from threading import Thread
from flask import current_app
from flask_mail import Mail, Message
import os


BASE_URL = os.getenv('APP_BASE_URL', 'http://localhost:5000')


def _send_async_email(app, msg):
    """Gửi mail trong thread riêng để không block request chính."""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            # Ghi log lỗi thay vì để crash thread ngầm im lặng
            current_app.logger.error(f"Gửi email thất bại: {e}")


def send_email(subject, recipients, body=None, html=None, sender=None,
               attachments=None, async_send=True):
    """
    Hàm gửi email tổng quát.

    Tham số:
        subject      (str): Tiêu đề email.
        recipients   (list[str]): Danh sách email người nhận.
        body         (str, optional): Nội dung dạng text thuần.
        html         (str, optional): Nội dung dạng HTML.
        sender       (str/tuple, optional): Người gửi, mặc định lấy MAIL_DEFAULT_SENDER.
        attachments  (list[tuple], optional): Danh sách (filename, content_type, data).
        async_send   (bool): True = gửi bất đồng bộ (không block request).

    Ví dụ:
        send_email(
            subject="Chào mừng",
            recipients=["user@example.com"],
            body="Cảm ơn bạn đã đăng ký!"
        )
    """
    if isinstance(recipients, str):
        recipients = [recipients]

    msg = Message(subject=subject, recipients=recipients, sender=sender)
    if body:
        msg.body = body
    if html:
        msg.html = html

    if attachments:
        for filename, content_type, data in attachments:
            msg.attach(filename, content_type, data)

    app = current_app._get_current_object()

    if async_send:
        Thread(target=_send_async_email, args=(app, msg)).start()
    else:
        mail.send(msg)

    return True


# ---------------------------------------------------------------------------
# TEMPLATE DÙNG CHUNG
# ---------------------------------------------------------------------------

def _render_email(heading, heading_color, body_lines, button_text=None,
                   button_url=None, button_color="#2c3e50", subheading=None):
    """
    Dựng HTML email đồng nhất cho toàn bộ hệ thống KHM Foodie.

    Tham số:
        heading       (str): Tiêu đề lớn hiển thị đầu email.
        heading_color (str): Màu chữ tiêu đề (phân biệt sắc thái: thành công/lỗi/thông tin).
        subheading    (str, optional): Dòng phụ nhỏ dưới tiêu đề (badge trạng thái).
        body_lines    (list[str]): Danh sách đoạn văn (mỗi phần tử là 1 <p>).
        button_text   (str, optional): Chữ trên nút bấm.
        button_url    (str, optional): Link khi bấm nút.
        button_color  (str, optional): Màu nền nút.
    """
    paragraphs_html = "".join(
        f'<p style="color:#444; font-size:15px; line-height:1.7; margin:0 0 14px 0;">{line}</p>'
        for line in body_lines
    )

    subheading_html = ""
    if subheading:
        subheading_html = f"""
        <p style="color:rgba(255,255,255,0.85); font-size:13px; margin:6px 0 0 0;">
            {subheading}
        </p>
        """

    button_html = ""
    if button_text and button_url:
        button_html = f"""
        <div style="text-align:center; margin:28px 0 8px 0;">
            <a href="{button_url}"
               style="background:{button_color}; color:#ffffff; padding:12px 30px;
                      text-decoration:none; border-radius:6px; font-size:14px;
                      font-weight:bold; display:inline-block;">
                {button_text}
            </a>
        </div>
        """

    return f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 540px; margin: 0 auto;
                background:#f4f6f8; padding: 24px;">
        <div style="background:#ffffff; border-radius:10px; overflow:hidden;
                    box-shadow: 0 1px 4px rgba(0,0,0,0.08);">

            <div style="background:{heading_color}; padding:24px 28px;">
                <p style="color:rgba(255,255,255,0.75); font-size:12px; letter-spacing:1px;
                          text-transform:uppercase; margin:0 0 6px 0;">
                    KHM Foodie
                </p>
                <h2 style="color:#ffffff; margin:0; font-size:20px; font-weight:600;">
                    {heading}
                </h2>
                {subheading_html}
            </div>

            <div style="padding:28px 28px 8px 28px;">
                {paragraphs_html}
                {button_html}
            </div>

            <div style="padding:18px 28px; border-top:1px solid #eee; margin-top:14px;">
                <p style="color:#999; font-size:12px; margin:0 0 4px 0;">
                    Đây là email tự động từ hệ thống KHM Foodie, vui lòng không trả lời email này.
                </p>
                <p style="color:#bbb; font-size:11px; margin:0;">
                    Nếu cần hỗ trợ, vui lòng liên hệ đội ngũ chăm sóc khách hàng qua ứng dụng.
                </p>
            </div>
        </div>
    </div>
    """


# ---------------------------------------------------------------------------
# CÁC HÀM GỬI EMAIL THEO TÌNH HUỐNG NGHIỆP VỤ
# ---------------------------------------------------------------------------

def send_account_registration_email(recipient, username, login_url=None):
    """
    Gửi email thông báo đăng ký tài khoản thành công.
    """
    login_url = login_url or f"{BASE_URL}/login"

    html_content = _render_email(
        heading=f"Chào mừng {username} đến với KHM Foodie!",
        heading_color="#2c3e50",
        subheading="Tài khoản đã được kích hoạt",
        body_lines=[
            "Cảm ơn bạn đã tin tưởng và đăng ký tài khoản trên KHM Foodie — nền tảng kết nối "
            "bạn với hàng trăm nhà hàng, quán ăn yêu thích chỉ trong vài cú chạm.",
            "Tài khoản của bạn đã được tạo và kích hoạt thành công. Từ bây giờ, bạn có thể "
            "khám phá thực đơn đa dạng, đặt món yêu thích, theo dõi đơn hàng theo thời gian thực "
            "và tận hưởng nhiều ưu đãi hấp dẫn dành riêng cho thành viên mới.",
            "Nếu đây không phải là bạn hoặc bạn không thực hiện việc đăng ký này, vui lòng bỏ qua "
            "email hoặc liên hệ với đội ngũ hỗ trợ để được trợ giúp kịp thời."
        ],
        button_text="Đăng nhập & khám phá ngay",
        button_url=login_url,
        button_color="#2c3e50"
    )
    return send_email(
        subject="Chào mừng bạn đến với KHM Foodie - Đăng ký thành công",
        recipients=[recipient],
        html=html_content
    )


def send_restaurant_registration_pending_email(recipient, restaurant_name, dashboard_url=None):
    """
    Gửi email thông báo đăng ký nhà hàng thành công, đang chờ duyệt.
    """
    dashboard_url = dashboard_url or f"{BASE_URL}/restaurant/dashboard"

    html_content = _render_email(
        heading="Đăng ký nhà hàng thành công",
        heading_color="#f39c12",
        subheading="Trạng thái: Đang chờ xét duyệt",
        body_lines=[
            f"Cảm ơn bạn đã đăng ký đưa nhà hàng <b>{restaurant_name}</b> lên nền tảng KHM Foodie. "
            f"Chúng tôi rất vui khi được đồng hành cùng bạn trên hành trình phát triển kinh doanh ẩm thực.",
            "Hồ sơ đăng ký của bạn đã được ghi nhận và hiện đang trong quá trình <b>xét duyệt bởi "
            "đội ngũ quản trị viên</b>. Việc này thường mất từ 1-3 ngày làm việc để đảm bảo thông tin "
            "nhà hàng, giấy phép kinh doanh và thực đơn đều chính xác, mang lại trải nghiệm tốt nhất "
            "cho khách hàng.",
            "Trong thời gian chờ duyệt, bạn có thể tranh thủ chuẩn bị hình ảnh món ăn, hoàn thiện "
            "thực đơn và thông tin cửa hàng để khi được phê duyệt, nhà hàng của bạn có thể lên sàn "
            "và bắt đầu nhận đơn ngay lập tức.",
            "Chúng tôi sẽ gửi email thông báo ngay khi có kết quả xét duyệt. Cảm ơn sự kiên nhẫn "
            "và hợp tác của bạn!"
        ],
        button_text="Xem trạng thái đăng ký",
        button_url=dashboard_url,
        button_color="#f39c12"
    )
    return send_email(
        subject="Đăng ký nhà hàng thành công - Đang chờ duyệt",
        recipients=[recipient],
        html=html_content
    )


def send_restaurant_approved_email(recipient, restaurant_name, dashboard_url=None):
    """
    Gửi email thông báo nhà hàng đã được admin duyệt.
    """
    dashboard_url = dashboard_url or f"{BASE_URL}/login"

    html_content = _render_email(
        heading="Chúc mừng! Nhà hàng đã được duyệt",
        heading_color="#27ae60",
        subheading="Trạng thái: Đã phê duyệt & hoạt động",
        body_lines=[
            f"Tin vui dành cho bạn! Sau quá trình xét duyệt, nhà hàng <b>{restaurant_name}</b> "
            f"đã chính thức được <b>phê duyệt</b> và hiện đã có mặt trên nền tảng KHM Foodie.",
            "Kể từ bây giờ, khách hàng trên toàn hệ thống có thể tìm thấy nhà hàng của bạn, xem "
            "thực đơn và bắt đầu đặt món. Đây là thời điểm tốt để bạn kiểm tra lại thực đơn, cập nhật "
            "hình ảnh món ăn thật hấp dẫn và đảm bảo giờ hoạt động được thiết lập chính xác nhằm "
            "mang đến trải nghiệm tốt nhất cho khách hàng.",
            "Đội ngũ KHM Foodie luôn sẵn sàng đồng hành, hỗ trợ bạn trong suốt quá trình vận hành — "
            "từ quản lý đơn hàng, thực đơn cho đến các chương trình khuyến mãi giúp tăng doanh thu.",
            "Chúc nhà hàng của bạn kinh doanh thật thuận lợi và đón nhiều đơn hàng!"
        ],
        button_text="Vào trang quản lý nhà hàng",
        button_url=dashboard_url,
        button_color="#27ae60"
    )
    return send_email(
        subject=f"{restaurant_name} đã được duyệt trên KHM Foodie",
        recipients=[recipient],
        html=html_content
    )


def send_restaurant_rejected_email(recipient, restaurant_name, reason=None, register_url=None):
    """
    Gửi email thông báo nhà hàng bị admin từ chối.

    Tham số:
        reason (str, optional): Lý do từ chối, nếu có thì hiển thị cho chủ nhà hàng biết.
    """
    register_url = register_url or f"{BASE_URL}"

    body_lines = [
        f"Cảm ơn bạn đã quan tâm và gửi hồ sơ đăng ký nhà hàng <b>{restaurant_name}</b> lên "
        f"nền tảng KHM Foodie. Sau khi xem xét kỹ lưỡng, rất tiếc chúng tôi phải thông báo rằng "
        f"hồ sơ đăng ký lần này <b>chưa được phê duyệt</b>."
    ]
    if reason:
        body_lines.append(
            f'<span style="display:block; background:#fdecea; border-left:3px solid #c0392b; '
            f'padding:12px 14px; border-radius:4px;"><b>Lý do:</b> {reason}</span>'
        )
    body_lines.append(
        "Đây không phải là quyết định cuối cùng — bạn hoàn toàn có thể cập nhật, bổ sung thông tin "
        "còn thiếu (giấy phép kinh doanh, hình ảnh nhà hàng, thực đơn...) và gửi lại hồ sơ đăng ký "
        "để được xét duyệt lại."
    )
    body_lines.append(
        "Nếu có bất kỳ thắc mắc nào về lý do từ chối hoặc cần hướng dẫn hoàn thiện hồ sơ, đội ngũ "
        "hỗ trợ của KHM Foodie luôn sẵn sàng giúp đỡ bạn."
    )

    html_content = _render_email(
        heading="Hồ sơ đăng ký nhà hàng chưa được duyệt",
        heading_color="#c0392b",
        subheading="Trạng thái: Từ chối - Có thể đăng ký lại",
        body_lines=body_lines,
        button_text="Cập nhật & đăng ký lại",
        button_url=register_url,
        button_color="#c0392b"
    )
    return send_email(
        subject=f"Hồ sơ đăng ký {restaurant_name} chưa được duyệt",
        recipients=[recipient],
        html=html_content
    )


def send_order_payment_success_email(recipient, order_id, total_amount,
                                      restaurant_name=None, order_url=None):
    """
    Gửi email thông báo thanh toán đơn hàng thành công, đang chờ giao hàng.

    Tham số:
        recipient       (str): Email người nhận.
        order_id        (str/int): Mã đơn hàng.
        total_amount    (str/number): Tổng tiền đã thanh toán.
        restaurant_name (str, optional): Tên nhà hàng đặt món.
        order_url       (str, optional): Link tới trang chi tiết đơn hàng.
    """
    order_url = order_url or f"{BASE_URL}/order_customer/"

    body_lines = [
        f"Cảm ơn bạn đã đặt món trên KHM Foodie! Đơn hàng <b>#{order_id}</b> của bạn đã được "
        f"<b>thanh toán thành công</b> và đang được nhà hàng chuẩn bị."
    ]
    if restaurant_name:
        body_lines.append(f"<b>Nhà hàng:</b> {restaurant_name}")
    body_lines.append(f"<b>Tổng tiền đã thanh toán:</b> {total_amount} đ")
    body_lines.append(
        "Món ăn của bạn hiện đang được nhà bếp chế biến cẩn thận để đảm bảo hương vị và độ tươi "
        "ngon khi đến tay bạn. Ngay khi tài xế nhận đơn và bắt đầu di chuyển, chúng tôi sẽ gửi "
        "thông báo cập nhật để bạn có thể theo dõi hành trình giao hàng theo thời gian thực."
    )
    body_lines.append(
        "Vui lòng giữ điện thoại ở chế độ có thể liên lạc để tài xế dễ dàng bàn giao đơn hàng "
        "đến đúng địa chỉ. Nếu có bất kỳ thay đổi nào về đơn hàng, hãy liên hệ hỗ trợ càng sớm "
        "càng tốt."
    )
    body_lines.append("Cảm ơn bạn đã lựa chọn KHM Foodie. Chúc bạn ngon miệng!")

    html_content = _render_email(
        heading="Thanh toán thành công!",
        heading_color="#27ae60",
        subheading="Trạng thái: Đang chuẩn bị món - Chờ giao hàng",
        body_lines=body_lines,
        button_text="Theo dõi đơn hàng",
        button_url=order_url,
        button_color="#27ae60"
    )
    return send_email(
        subject=f"Thanh toán đơn hàng #{order_id} thành công",
        recipients=[recipient],
        html=html_content
    )


def send_password_reset_email(recipient, reset_link):
    """
    Gửi email đặt lại mật khẩu.
    """
    html_content = _render_email(
        heading="Yêu cầu đặt lại mật khẩu",
        heading_color="#2980b9",
        subheading="Bảo mật tài khoản",
        body_lines=[
            "Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản KHM Foodie của bạn. "
            "Nhấn vào nút bên dưới để tạo mật khẩu mới.",
            "Vì lý do bảo mật, liên kết này sẽ hết hạn sau một khoảng thời gian nhất định. "
            "Nếu liên kết hết hạn, bạn có thể yêu cầu gửi lại từ trang đăng nhập.",
            "Nếu bạn không thực hiện yêu cầu này, có thể ai đó đã nhập nhầm email của bạn — "
            "bạn có thể yên tâm bỏ qua email này, mật khẩu hiện tại của bạn vẫn an toàn."
        ],
        button_text="Đặt lại mật khẩu",
        button_url=reset_link,
        button_color="#2980b9"
    )
    return send_email(
        subject="Yêu cầu đặt lại mật khẩu - KHM Foodie",
        recipients=recipient,
        html=html_content
    )


# ---------------------------------------------------------------------------
# Mẫu file .env cần tạo cùng thư mục (KHÔNG commit file .env thật lên git):
#
# MAIL_SERVER=smtp.gmail.com
# MAIL_PORT=587
# MAIL_USE_TLS=True
# MAIL_USE_SSL=False
# MAIL_USERNAME=yourname@gmail.com
# MAIL_PASSWORD=fpsqamwommspxxxx
# MAIL_DEFAULT_SENDER=yourname@gmail.com
# APP_BASE_URL=https://khmfoodie.com     # dùng để build link redirect trong email
# ---------------------------------------------------------------------------