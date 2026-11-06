# 临时 patch：让 DouyinWebcastSignature 绕开 execjs（容器没 Node.js）
# 直接在脚本开头 import 即可：
#   import patch_signature
#   或
#   from scripts.patch_signature import *

from f2.apps.douyin.algorithm.webcast_signature import DouyinWebcastSignature as _Cls

_orig = _Cls.get_signature


def _patched(self, room_id: str, user_unique_id: str) -> str:
    # 让 WSS 连接先尝试用空 signature——大多数匿名 WS 客户端都这么做
    print(f"[patch_signature] returning empty sig for room={room_id}", flush=True)
    return ""


_Cls.get_signature = _patched
