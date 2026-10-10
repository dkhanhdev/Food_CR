
import os
import time
import hashlib
import hmac
import urllib.parse
from datetime import datetime

VNP_PAYMENT_URL_DEFAULT = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"


def _get_required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} environment variable is not set")
    return value


def build_vnpay_url(order_id, amount, order_info, ip_addr):
    """Tạo URL thanh toán VNPay cho một order.

    Trả về (payment_url: str, txn_ref: str). txn_ref có dạng
    "<order_id>_<unix_timestamp>" — dùng get_order_id_from_txn_ref để tách
    lại order_id từ callback (return/IPN).
    """
    tmn_code = _get_required_env("VNP_TMN_CODE")
    hash_secret = _get_required_env("VNP_HASH_SECRET")
    return_url = _get_required_env("VNP_RETURN_URL")
    payment_url_base = os.getenv("VNP_PAYMENT_URL", VNP_PAYMENT_URL_DEFAULT)

    txn_ref = f"{order_id}_{int(time.time())}"

    vnp_params = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": tmn_code,
        "vnp_Amount": str(int(amount) * 100),
        "vnp_CurrCode": "VND",
        "vnp_TxnRef": txn_ref,
        "vnp_OrderInfo": order_info,
        "vnp_OrderType": "other",
        "vnp_Locale": "vn",
        "vnp_ReturnUrl": return_url,
        "vnp_IpAddr": ip_addr,
        "vnp_CreateDate": datetime.now().strftime("%Y%m%d%H%M%S"),
        # Không set vnp_BankCode: để VNPay tự hiện màn hình cho khách chọn
        # phương thức (QR / thẻ nội địa / thẻ quốc tế). Từng ép cứng
        # "VNPAYQR" nhưng merchant test hiện tại chưa được bật kênh QR
        # trên sandbox (lỗi "Ngân hàng thanh toán không được hỗ trợ"), và
        # sandbox miễn phí cũng không hỗ trợ test QR bằng thẻ test thông
        # thường - nên tạm để trống, dùng thẻ ATM nội địa (NCB) để test.
    }

    sorted_params = sorted(vnp_params.items())
    query_string = urllib.parse.urlencode(sorted_params)

    secure_hash = hmac.new(
        hash_secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha512
    ).hexdigest()

    payment_url = f"{payment_url_base}?{query_string}&vnp_SecureHash={secure_hash}"
    return payment_url, txn_ref


def verify_vnpay_signature(params: dict) -> bool:
    """Xác thực chữ ký VNPay gửi kèm khi redirect (return) hoặc gọi IPN.

    Loại vnp_SecureHash/vnp_SecureHashType khỏi params, sort phần còn lại,
    urlencode, ký lại HMAC-SHA512, so bằng hmac.compare_digest.
    """
    hash_secret = _get_required_env("VNP_HASH_SECRET")

    vnp_secure_hash = params.get("vnp_SecureHash", "")
    if not vnp_secure_hash:
        return False

    filtered = {
        k: v for k, v in params.items()
        if k not in ("vnp_SecureHash", "vnp_SecureHashType")
    }

    sorted_params = sorted(filtered.items())
    query_string = urllib.parse.urlencode(sorted_params)

    expected_hash = hmac.new(
        hash_secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha512
    ).hexdigest()

    return hmac.compare_digest(expected_hash, vnp_secure_hash)


def get_order_id_from_txn_ref(txn_ref):
    """Tách order_id gốc từ vnp_TxnRef dạng "<order_id>_<timestamp>".

    Trả về None nếu parse lỗi (txn_ref rỗng, sai định dạng, ...).
    """
    if not txn_ref:
        return None
    try:
        return int(str(txn_ref).split("_")[0])
    except (ValueError, IndexError):
        return None
