"""Tích hợp cổng thanh toán MoMo.

Port từ app/utils/momo_util.py của project QuanLySuaXe_CNPM, điều chỉnh để:
- Đọc partner/access/secret key từ biến môi trường (giống cách vnpayService.py
  cũ đọc VNP_*), thay vì hard-code trong source.
- Trả thêm request_id để lưu lại, phục vụ xác thực chữ ký ở bước return/IPN.
- Có thêm verify_momo_signature (QuanLySuaXe không có) để chống giả mạo kết
  quả thanh toán qua URL redirect.
"""
import os
import hmac
import hashlib
import uuid

import requests

MOMO_ENDPOINT_DEFAULT = "https://test-payment.momo.vn/v2/gateway/api/create"


def _get_required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} environment variable is not set")
    return value


def create_momo_payment(amount, order_info, redirect_url, ipn_url):
    """Tạo yêu cầu thanh toán MoMo.

    Trả về (response_json: dict, order_id: str, request_id: str).
    response_json["resultCode"] == 0 nghĩa là tạo thành công, có payUrl.
    """
    partner_code = _get_required_env("MOMO_PARTNER_CODE")
    access_key = _get_required_env("MOMO_ACCESS_KEY")
    secret_key = _get_required_env("MOMO_SECRET_KEY")
    endpoint = os.getenv("MOMO_ENDPOINT", MOMO_ENDPOINT_DEFAULT)

    try:
        order_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())

        raw_signature = (
            f"accessKey={access_key}&amount={amount}&extraData=&"
            f"ipnUrl={ipn_url}&orderId={order_id}&orderInfo={order_info}&"
            f"partnerCode={partner_code}&redirectUrl={redirect_url}&"
            f"requestId={request_id}&requestType=payWithATM"
        )

        signature = hmac.new(
            secret_key.encode("utf-8"),
            raw_signature.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        payload = {
            "partnerCode": partner_code,
            "accessKey": access_key,
            "requestId": request_id,
            "amount": str(amount),
            "orderId": order_id,
            "orderInfo": order_info,
            "redirectUrl": redirect_url,
            "ipnUrl": ipn_url,
            "extraData": "",
            "requestType": "payWithATM",
            "signature": signature,
            "lang": "vi"
        }

        response = requests.post(
            endpoint,
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )

        # Log đầy đủ request/response ra console để debug khi MoMo trả lỗi
        # (không có log này thì chỉ biết mã HTTP, không biết MoMo phàn nàn gì).
        print("[momoService] MoMo request payload:", {**payload, "signature": "***"})
        print("[momoService] MoMo response status:", response.status_code)
        print("[momoService] MoMo response body:", response.text)

        if response.status_code != 200:
            # Cố lấy message chi tiết MoMo trả về (nếu có body JSON) thay vì chỉ mã HTTP
            detail = response.text
            try:
                detail = response.json().get("message", response.text)
            except ValueError:
                pass
            return {
                "resultCode": -1,
                "message": f"MoMo API: HTTP {response.status_code} - {detail}"
            }, None, None

        response_data = response.json()
        return response_data, order_id, request_id

    except Exception as e:
        return {"resultCode": -1, "message": f"Lỗi không xác định: {e}"}, None, None


def verify_momo_signature(params: dict) -> bool:
    """Xác thực chữ ký MoMo gửi kèm khi redirect (return) hoặc gọi IPN.

    MoMo ký trên các field: accessKey, amount, extraData, message, orderId,
    orderInfo, orderType, partnerCode, payType, requestId, responseTime,
    resultCode, transId (ghép theo đúng thứ tự này bằng '&', không urlencode)
    rồi HMAC-SHA256 bằng secret key.

    Lưu ý: thứ tự/field chính xác cần đối chiếu lại với tài liệu MoMo
    (developers.momo.vn) và test bằng request thật ở sandbox trước khi dùng
    thật, vì MoMo có nhiều luồng API (payWithATM/captureWallet) với field
    hơi khác nhau.
    """
    secret_key = _get_required_env("MOMO_SECRET_KEY")
    access_key = _get_required_env("MOMO_ACCESS_KEY")

    signature = params.get("signature")
    if not signature:
        return False

    raw_signature = (
        f"accessKey={access_key}"
        f"&amount={params.get('amount', '')}"
        f"&extraData={params.get('extraData', '')}"
        f"&message={params.get('message', '')}"
        f"&orderId={params.get('orderId', '')}"
        f"&orderInfo={params.get('orderInfo', '')}"
        f"&orderType={params.get('orderType', '')}"
        f"&partnerCode={params.get('partnerCode', '')}"
        f"&payType={params.get('payType', '')}"
        f"&requestId={params.get('requestId', '')}"
        f"&responseTime={params.get('responseTime', '')}"
        f"&resultCode={params.get('resultCode', '')}"
        f"&transId={params.get('transId', '')}"
    )

    expected_signature = hmac.new(
        secret_key.encode("utf-8"),
        raw_signature.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)
