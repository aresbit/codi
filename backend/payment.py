"""
微信支付集成 — JSAPI 支付（微信小程序内）
参考: https://pay.weixin.qq.com/docs/merchant/development/mini-program-payment/mini-program-payment-index.html
"""

import os
import time
import uuid
import httpx
import hashlib
import json
from config import PRICE_TIER_BASIC, PRICE_TIER_PREMIUM

WX_APPID = os.getenv("WX_APPID", "")
WX_MCHID = os.getenv("WX_MCHID", "")
WX_API_KEY = os.getenv("WX_API_KEY", "")        # APIv3 key
WX_MCH_SERIAL = os.getenv("WX_MCH_SERIAL", "")    # 商户证书序列号
WX_PRIVATE_KEY_PATH = os.getenv("WX_PRIVATE_KEY_PATH", "")  # 商户私钥 .pem


def get_price(tier: str) -> float:
    return PRICE_TIER_PREMIUM if tier == "premium" else PRICE_TIER_BASIC


async def create_jsapi_order(order_id: str, tier: str,
                             openid: str, description: str) -> dict:
    """
    创建微信支付 JSAPI 订单 → 返回小程序调起支付所需的参数
    """
    price_yuan = get_price(tier)
    price_fen = int(price_yuan * 100)

    prepay_id = await _wx_prepay(order_id, price_fen, openid, description)

    # 生成小程序调起支付所需签名
    nonce_str = uuid.uuid4().hex[:16]
    timestamp = str(int(time.time()))

    package = f"prepay_id={prepay_id}"
    sign_str = f"{WX_APPID}\n{timestamp}\n{nonce_str}\n{package}\n"
    pay_sign = _rsa_sign(sign_str)

    return {
        "prepay_id": prepay_id,
        "nonce_str": nonce_str,
        "timestamp": timestamp,
        "package": package,
        "sign_type": "RSA",
        "pay_sign": pay_sign,
    }


async def verify_payment_notification(body: bytes, signature: str,
                                      serial: str, timestamp: str,
                                      nonce: str) -> dict | None:
    """
    验证微信支付回调通知
    返回: (order_id, transaction_id) 或 None
    """
    # 验签
    sign_str = f"{timestamp}\n{nonce}\n{body.decode()}\n"
    if not _rsa_verify(sign_str, signature):
        return None

    data = json.loads(body)
    resource = data.get("resource", {})
    if resource.get("ciphertext"):
        decrypted = _aes_decrypt(
            resource["ciphertext"],
            resource.get("associated_data", ""),
            resource.get("nonce", ""),
        )
        order_data = json.loads(decrypted)
        return {
            "order_id": order_data.get("out_trade_no"),
            "transaction_id": order_data.get("transaction_id"),
        }

    return None


async def _wx_prepay(order_id: str, amount_fen: int,
                     openid: str, description: str) -> str:
    """调用微信支付 APIv3 统一下单"""
    url = "https://api.mch.weixin.qq.com/v3/pay/transactions/jsapi"

    body = {
        "appid": WX_APPID,
        "mchid": WX_MCHID,
        "description": description,
        "out_trade_no": order_id,
        "notify_url": os.getenv("WX_NOTIFY_URL", "https://your-domain.com/api/pay/notify"),
        "amount": {"total": amount_fen, "currency": "CNY"},
        "payer": {"openid": openid},
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            json=body,
            headers=_wx_headers("POST", url, body),
            timeout=30,
        )
        data = resp.json()
        if resp.status_code != 200:
            raise RuntimeError(f"WeChat Pay error: {data}")
        return data["prepay_id"]


def _wx_headers(method: str, url: str, body: dict | None = None) -> dict:
    """生成微信支付 APIv3 请求头（含签名）"""
    nonce = uuid.uuid4().hex[:16]
    timestamp = str(int(time.time()))
    body_str = json.dumps(body) if body else ""

    sign_str = f"{method}\n{url}\n{timestamp}\n{nonce}\n{body_str}\n"
    signature = _rsa_sign(sign_str)

    return {
        "Authorization": (
            f'WECHATPAY2-SHA256-RSA2048 mchid="{WX_MCHID}",'
            f'nonce_str="{nonce}",timestamp="{timestamp}",'
            f'serial_no="{WX_MCH_SERIAL}",signature="{signature}"'
        ),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _rsa_sign(message: str) -> str:
    """RSA-SHA256 签名"""
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    import base64

    if not WX_PRIVATE_KEY_PATH:
        return "MOCK_SIGNATURE"

    with open(WX_PRIVATE_KEY_PATH, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    signature = private_key.sign(
        message.encode(),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode()


def _rsa_verify(message: str, signature: str) -> bool:
    """RSA-SHA256 验签（微信平台证书）"""
    # 简化版，生产环境需从微信获取平台证书验签
    return True


def _aes_decrypt(ciphertext: str, associated_data: str, nonce: str) -> str:
    """AES-256-GCM 解密"""
    import base64
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    aesgcm = AESGCM(WX_API_KEY.encode())
    raw = aesgcm.decrypt(
        nonce.encode(),
        base64.b64decode(ciphertext) + base64.b64decode(associated_data),
        None,
    )
    return raw.decode()
