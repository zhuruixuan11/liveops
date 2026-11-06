"""抖音直播弹幕采集 adapter（路线 A）

独立进程，不依赖本平台后端运行。连接真实抖音直播间 WebSocket，
解析 ChatMessage / GiftMessage / MemberMessage 等事件，把 ChatMessage
批量 POST 到本平台 /api/v1/ingest/danmaku。

依赖：f2 (pip install f2)、httpx
用法：
  # 直播中测试（session_id=18, 跑 3 分钟收 1 条弹幕就够了）
  python -m scripts.douyin_fetcher --web-rid 108749646314 --session 18 --minutes 3

  # 常驻采集（--minutes 0 = 一直跑）
  python -m scripts.douyin_fetcher --web-rid 108749646314 --session 18 --minutes 0
"""
import argparse
import asyncio
import json
import os
import sys
import time
from typing import Optional

import httpx

from f2.apps.douyin.handler import DouyinHandler

DEFAULT_API = os.environ.get("LIVEOPS_API", "http://localhost:8000/api/v1")
DEFAULT_TOKEN = os.environ.get("INGEST_TOKEN", "liveops-ingest-2026")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0"
)

# 已经被 f2 解析过的 JSON ChatMessage 里的昵称 / 内容字段
# preserving_proto_field_name=True，所以字段名是 snake_case
# ChatMessage.user.nick_name, ChatMessage.content
def _extract(data: dict):
    """从 f2 的回调 JSON 里拿昵称和弹幕文本。"""
    user = data.get("user") or {}
    nick = (
        user.get("nick_name")
        or data.get("nick_name")
        or data.get("nickname")
        or data.get("nick")
        or data.get("user", {}).get("nickname")
        or "观众"
    )
    content = (
        data.get("content")
        or data.get("chat_content")
        or data.get("text")
        or ""
    )
    user_id = user.get("id") or user.get("user_id") or None
    return {"nickname": str(nick)[:64], "content": str(content), "user_id": user_id}


def _flush(api: str, token: str, session_id: int, items: list, source: str, room_id: str):
    if not items:
        return
    try:
        with httpx.Client(timeout=10) as client:
            r = client.post(
                f"{api.rstrip('/')}/ingest/danmaku",
                json={
                    "session_id": session_id,
                    "source": source,
                    "room_id": room_id,
                    "items": items,
                },
                headers={"X-Ingest-Token": token},
            )
            r.raise_for_status()
            body = r.json()
            print(
                f"[douyin_fetcher] 推送 {len(items)} 条 "
                f"→ 入库 {body.get('accepted')} / 过滤 {body.get('filtered')} / 跳过 {body.get('skipped')}"
            )
    except httpx.HTTPError as e:
        print(f"[douyin_fetcher] 推送失败：{e}")


def _heartbeat(api: str, token: str, session_id: int, source: str, room_id: str, collected: int):
    try:
        with httpx.Client(timeout=5) as client:
            client.post(
                f"{api.rstrip('/')}/ingest/heartbeat",
                json={
                    "session_id": session_id,
                    "source": source,
                    "room_id": room_id,
                    "collected": collected,
                    "note": "douyin_fetcher online",
                },
                headers={"X-Ingest-Token": token},
            )
    except Exception:
        pass


async def run(web_rid: str, session_id: int, api: str, token: str, minutes: int):
    source = "douyin"
    kwargs = {
        "headers": {"User-Agent": USER_AGENT, "Referer": "https://live.douyin.com/"},
        "proxies": {"http://": None, "https://": None},
        # cookie 可空：f2 会用匿名 ttwid 工作
    }
    handler = DouyinHandler(kwargs)

    print(f"[douyin_fetcher] 正在获取房间信息 web_rid={web_rid} …")
    try:
        live = await handler.fetch_user_live_videos(webcast_id=web_rid)
    except Exception as e:
        print(f"[douyin_fetcher] 获取房间信息失败：{e}")
        print("[douyin_fetcher] 可能原因：web_rid 错误、直播间未开播、或 IP 被限制")
        sys.exit(1)

    raw = live._to_raw() if hasattr(live, "_to_raw") else {}
    room_entry = raw.get("room") or raw
    real_room_id = str(
        raw.get("id_str")
        or raw.get("room_id_str")
        or raw.get("id")
        or room_entry.get("id_str")
        or room_entry.get("id")
        or web_rid
    )
    unique_id = str(raw.get("owner", {}).get("unique_id") or raw.get("owner", {}).get("short_id") or "")
    internal_ext = str(raw.get("internal_ext") or "")
    cursor = str(raw.get("cursor") or raw.get("live_cursor") or "0")
    nickname = raw.get("owner", {}).get("nickname") or "主播"
    is_living = raw.get("is_living") or raw.get("status") == 2

    print(
        f"[douyin_fetcher] 房间信息："
        f"主播={nickname}({unique_id}) realRoomId={real_room_id} "
        f"直播中={'是' if is_living else '否'}"
    )
    if not is_living:
        print("[douyin_fetcher] 直播间未开播，退出")
        sys.exit(0)
    if not internal_ext:
        print("[douyin_fetcher] 缺少 internal_ext，可能接口返回结构变更，退出")
        sys.exit(1)

    buffer: list = []
    last_flush = 0.0
    last_hb = 0.0
    collected = 0
    deadline = time.time() + minutes * 60 if minutes else None

    def chat_cb(cls, data: bytes):
        """被 DouyinWebSocketCrawler 调用：拿到 ChatMessage 原始字节。"""
        try:
            parsed = cls.WebcastChatMessage(data)  # dict
            extracted = _extract(parsed)
            if not extracted["content"]:
                return
            buffer.append(extracted)
            nonlocal last_flush
            now = time.time()
            if len(buffer) >= 20 or now - last_flush >= 4:
                _flush(api, token, session_id, buffer, source, real_room_id)
                collected += len(buffer)
                buffer.clear()
                last_flush = now
        except Exception as e:
            print(f"[douyin_fetcher] ChatMessage 解析异常：{e}")

    def gift_cb(cls, data: bytes):
        parsed = cls.WebcastGiftMessage(data)
        user = (parsed.get("user") or {}).get("nick_name", "观众")
        gift = (parsed.get("common") or {}).get("describe", "礼物")
        content = f"送了 {gift}"
        buffer.append({"nickname": user, "content": content})

    def member_cb(cls, data: bytes):
        parsed = cls.WebcastMemberMessage(data)
        user = (parsed.get("user") or {}).get("nick_name", "观众")
        content = "进入直播间"
        buffer.append({"nickname": user, "content": content})

    wss_callbacks = {
        "WebcastChatMessage": chat_cb,
        "WebcastGiftMessage": gift_cb,
        "WebcastMemberMessage": member_cb,
    }

    # 心跳任务
    async def hb_task():
        while True:
            _heartbeat(api, token, session_id, source, real_room_id, collected)
            await asyncio.sleep(30)

    hb = asyncio.create_task(hb_task())

    print(f"[douyin_fetcher] 正在连接真实 WebSocket …（room_id={real_room_id}）")

    try:
        # f2 的 fetch_live_danmaku 是阻塞式的 async context manager
        await handler.fetch_live_danmaku(
            room_id=real_room_id,
            user_unique_id=unique_id,
            internal_ext=internal_ext,
            cursor=cursor,
            wss_callbacks=wss_callbacks,
        )
    except Exception as e:
        print(f"[douyin_fetcher] WebSocket 异常：{e}")
    finally:
        hb.cancel()
        if buffer:
            _flush(api, token, session_id, buffer, source, real_room_id)
        print(f"[douyin_fetcher] 采集结束，累计 {collected} 条弹幕")


def main():
    ap = argparse.ArgumentParser(description="LiveOps 抖音弹幕采集 adapter")
    ap.add_argument("--web-rid", required=True, help="直播间短号（live.douyin.com/后面那串数字）")
    ap.add_argument("--session", type=int, required=True, help="本平台场次 ID")
    ap.add_argument("--api", default=DEFAULT_API)
    ap.add_argument("--token", default=DEFAULT_TOKEN)
    ap.add_argument("--minutes", type=int, default=5, help="运行时长（分钟），0 表示常驻")
    args = ap.parse_args()

    try:
        asyncio.run(run(
            web_rid=str(args.web_rid),
            session_id=args.session,
            api=args.api,
            token=args.token,
            minutes=args.minutes,
        ))
    except KeyboardInterrupt:
        print("\n[douyin_fetcher] 已停止")


if __name__ == "__main__":
    main()
