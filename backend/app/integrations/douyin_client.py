"""抖音开放平台（抖店 OpenAPI）客户端

真实环境使用 app_key/app_secret 签名调用；未配置凭证时走 MOCK 演示模式，
返回结构与真实接口保持一致，便于演示与联调。
"""
import hashlib
import hmac
import json
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx

OPENAPI_HOST = "https://openapi-fxg.jinritemai.com"
OAUTH_URL = "https://fxg.jinritemai.com/ffa/mshop/openapi/oauth"


class DouyinApiError(RuntimeError):
    pass


class DouyinOpenClient:
    def __init__(self, app_key: str, app_secret: str, access_token: Optional[str] = None):
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = access_token

    # ---------- 签名 ----------
    def _sign(self, params: Dict[str, str]) -> str:
        """抖店签名规则：参数按 key 升序拼接 key+value，再以 app_secret 做 HMAC-SHA256"""
        ordered = "".join(f"{k}{params[k]}" for k in sorted(params) if k != "sign")
        sign_str = f"{self.app_secret}{ordered}{self.app_secret}"
        return hmac.new(
            self.app_secret.encode("utf-8"),
            sign_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    # ---------- 调用 ----------
    def call(self, method: str, param_json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = {
            "app_key": self.app_key,
            "method": method,
            "param_json": json.dumps(param_json or {}, ensure_ascii=False, separators=(",", ":")),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "v": "2",
            "sign_method": "hmac-sha256",
        }
        if self.access_token:
            params["access_token"] = self.access_token
        params["sign"] = self._sign(params)

        url = f"{OPENAPI_HOST}/{method}?{urlencode(params)}"
        try:
            resp = httpx.get(url, timeout=20)
            resp.raise_for_status()
            body = resp.json()
        except Exception as e:  # noqa: BLE001
            raise DouyinApiError(f"请求失败: {e}") from e

        if str(body.get("err_no", 0)) not in ("0", "None", ""):
            raise DouyinApiError(f"平台返回错误 {body.get('err_no')}: {body.get('message')}")
        return body.get("data") or {}

    def token_create(self, shop_id: str, code: Optional[str] = None,
                     grant_type: str = "authorization_self") -> Dict[str, Any]:
        payload = {
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            "grant_type": grant_type,
            "shop_id": shop_id,
        }
        if code:
            payload["code"] = code
            payload["grant_type"] = "authorization_code"
        resp = httpx.post(f"{OPENAPI_HOST}/token/create", json=payload, timeout=20)
        resp.raise_for_status()
        body = resp.json()
        if body.get("err_no") not in (0, "0", None):
            raise DouyinApiError(f"授权失败: {body.get('message')}")
        return body.get("data") or {}

    # ---------- 业务数据 ----------
    def fetch_orders(self, page: int = 0, size: int = 50) -> List[Dict[str, Any]]:
        """order.searchList：拉取店铺订单"""
        data = self.call("order.searchList", {
            "page": page,
            "size": size,
            "order_by": "create_time",
            "is_desc": "1",
        })
        return data.get("shop_order_list") or []

    def fetch_products(self, page: int = 0, size: int = 50) -> List[Dict[str, Any]]:
        """product.listV2：拉取店铺商品"""
        data = self.call("product.listV2", {"page": page, "size": size, "status": 0})
        return data.get("data") or data.get("product_list") or []

    def fetch_live_rooms(self) -> List[Dict[str, Any]]:
        """直播间列表（需直播权限；无权限时返回空）"""
        try:
            data = self.call("live.room.list", {"page": 0, "size": 20})
            return data.get("room_list") or []
        except DouyinApiError:
            return []


# ---------------- MOCK 演示数据 ----------------
_MOCK_PRODUCTS = [
    ("抖音同款氨基酸洁面乳", "30g 旅行装", 39.90, 120),
    ("抖音爆款玻尿酸面膜", "10片/盒", 99.00, 260),
    ("轻氧裸妆气垫BB", "自然色 15g", 159.00, 88),
    ("养肤防晒乳 SPF50+", "50ml", 129.00, 150),
    ("便携式榨汁杯", "350ml 白色", 89.00, 200),
]
_MOCK_NICKNAMES = ["抖友小张", "爱吃辣的猫", "阿May", "直播间常客", "新粉001", "橙子汽水"]


def mock_orders(n: int = 12) -> List[Dict[str, Any]]:
    out = []
    now = datetime.now()
    for i in range(n):
        pname, spec, price, _ = random.choice(_MOCK_PRODUCTS)
        qty = random.choices([1, 2, 3], weights=[65, 25, 10], k=1)[0]
        created = now - timedelta(minutes=random.randint(5, 240), seconds=random.randint(0, 59))
        out.append({
            "order_id": f"DY{created.strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}",
            "create_time": created.strftime("%Y-%m-%d %H:%M:%S"),
            "pay_time": (created + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "order_status": random.choices([2, 3, 4], weights=[70, 20, 10], k=1)[0],
            "pay_amount": round(price * qty, 2),
            "buyer_nick": random.choice(_MOCK_NICKNAMES),
            "items": [{"product_name": pname, "spec": spec, "price": price, "qty": qty}],
        })
    return out


def mock_products() -> List[Dict[str, Any]]:
    out = []
    for i, (name, spec, price, stock) in enumerate(_MOCK_PRODUCTS):
        out.append({
            "product_id": f"DY_P_{1000 + i}",
            "name": name,
            "price": price,
            "skus": [{
                "sku_id": f"DY_S_{2000 + i}",
                "spec": spec,
                "price": price,
                "stock": stock,
                "code": f"DY{2000 + i}",
            }],
        })
    return out


def mock_live_rooms() -> List[Dict[str, Any]]:
    return [{
        "room_id": "DY_LIVE_9001",
        "title": "抖音号直播 · 美妆爆款专场",
        "status": 2,
        "start_time": (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
        "online_count": random.randint(300, 1800),
    }]
