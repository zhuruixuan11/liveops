# -*- coding: utf-8 -*-
"""抖音直播弹幕采集 adapter（宿主机版 · 登录态 WSS）

路线 A 正式适配器：连接真实抖音直播间 WebSocket，解析 ChatMessage /
GiftMessage / MemberMessage 等事件，批量 POST 到本平台 /api/v1/ingest/danmaku。

为什么跑在宿主机而不是容器：
  容器 NAT IP 被抖音风控（im/fetch 返回空 body），宿主机住宅 IP 正常。
  脚本运行时会自动向 live.douyin.com 首页换取绑定本机 IP 的 ttwid。

依赖（宿主机）：
  pip install requests websocket-client protobuf PyExecJS
  Node.js v16+（execjs 计算 X-Bogus 签名）

用法：
  python scripts/host_danmaku_adapter.py --web-rid 928481163143 --session 18 --minutes 3
  python scripts/host_danmaku_adapter.py --room-id 7699785794780809999 --session 18 --minutes 0  # 常驻

  sessionid 通过参数或环境变量传入：
  python scripts/host_danmaku_adapter.py --web-rid 928481163143 --session 18 --sessionid <登录态>
  set DOUYIN_SESSIONID=xxx && python scripts/host_danmaku_adapter.py ...

注意：
  1. 无 sessionid 时匿名运行，只能收到系统消息（RoomStats/RoomRank 等），
     chat/gift/member 频道需要登录态。
  2. pb2 字段名为驼峰（logId/payloadType/nickname），与标准版 proto 不同。
"""
import argparse
import gzip
import hashlib
import json
import os
import random
import re
import string
import sys
import threading
import time
import urllib.parse
from pathlib import Path

import execjs
import requests
import websocket

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import douyin_webcast_pb2 as pb  # noqa: E402

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36 Edg/155.0.0.0")
DEFAULT_API = os.environ.get("LIVEOPS_API", "http://localhost:8000/api/v1")
DEFAULT_TOKEN = os.environ.get("INGEST_TOKEN", "liveops-ingest-2026")
BUFFER_FLUSH_COUNT = 20
BUFFER_FLUSH_SECONDS = 4


# ============================================================
# LiveOps 推送
# ============================================================
def push_to_liveops(items, room_id, session_id, api, token):
    if not items:
        return
    try:
        r = requests.post(
            f"{api}/ingest/danmaku",
            json={"session_id": session_id, "source": "douyin",
                  "room_id": room_id, "items": items},
            headers={"X-Ingest-Token": token}, timeout=10)
        j = r.json()
        print(f"  → LiveOps 入库 {j.get('accepted')} 过滤 {j.get('filtered')} 跳过 {j.get('skipped')}", flush=True)
    except Exception as e:
        print(f"  → LiveOps 推送失败：{e}", flush=True)


def heartbeat(room_id, session_id, collected, api, token):
    try:
        requests.post(
            f"{api}/ingest/heartbeat",
            json={"session_id": session_id, "source": "douyin", "room_id": room_id,
                  "collected": collected, "note": "host_danmaku_adapter online"},
            headers={"X-Ingest-Token": token}, timeout=5)
    except Exception:
        pass


# ============================================================
# 抖音侧
# ============================================================
class DouyinWS:
    def __init__(self, room_id, sessionid, on_event):
        self.room_id = room_id
        self.sessionid = sessionid
        self.on_event = on_event
        self.http = requests.Session()
        self.http.headers.update({"User-Agent": UA})
        self.did = str(random.randint(7600000000000000000, 7699999999999999999))
        self.ws = None
        self.stats = {"chat": 0, "gift": 0, "member": 0, "like": 0, "social": 0, "other": 0}

    def prepare(self):
        # 1. 换取绑定本机 IP 的 ttwid（防风控关键）
        self.http.get("https://live.douyin.com/", timeout=15)
        self.ttwid = self.http.cookies.get("ttwid")
        ms_token = "".join(random.choice(string.ascii_letters + string.digits + "=_") for _ in range(107))
        self.cookie = f"ttwid={self.ttwid}; msToken={ms_token}"
        if self.sessionid:
            self.cookie += f"; sessionid={self.sessionid}"
        print(f"[init] ttwid={str(self.ttwid)[:30]}... 登录态={'有' if self.sessionid else '无（匿名）'}", flush=True)

        # 2. 拿真实 cursor
        params = self._im_params(cursor="", internal_ext="")
        r = self.http.get("https://live.douyin.com/webcast/im/fetch/", params=params,
                          headers={"Referer": "https://live.douyin.com/", "Cookie": self.cookie}, timeout=15)
        self.cursor = (r.json().get("extra") or {}).get("cursor") or ""
        print(f"[init] cursor={self.cursor}", flush=True)

        # 3. 组装 WSS URL + X-Bogus 签名
        ts = int(time.time() * 1000)
        internal_ext = (f"internal_src:dim|wss_push_room_id:{self.room_id}|wss_push_did:{self.did}"
                        f"|first_req_ms:{ts}|fetch_time:{ts}|seq:1|wss_info:0-{ts}-0-0|"
                        f"wrds_v:7392094459690748497")
        wss = ("wss://webcast5-ws-web-hl.douyin.com/webcast/im/push/v2/?app_name=douyin_web"
               "&version_code=180800&webcast_sdk_version=1.0.14-beta.0"
               "&update_version_code=1.0.14-beta.0&compress=gzip&device_platform=web&cookie_enabled=true"
               "&screen_width=1920&screen_height=1080&browser_language=zh-CN&browser_platform=Win32"
               "&browser_name=Mozilla"
               f"&browser_version={urllib.parse.quote(UA)}"
               "&browser_online=true&tz_name=Asia/Shanghai"
               f"&cursor={urllib.parse.quote(self.cursor)}"
               f"&internal_ext={urllib.parse.quote(internal_ext)}"
               "&host=https://live.douyin.com&aid=6383&live_id=1&did_rule=3&endpoint=live_pc&support_wrds=1"
               f"&user_unique_id={self.did}&im_path=/webcast/im/fetch/&identity=audience"
               f"&need_persist_msg_count=15&insert_task_id=&live_reason=&room_id={self.room_id}&heartbeatDuration=0")
        wss += f"&signature={urllib.parse.quote(self._sign())}"
        self.wss_url = wss

    def _im_params(self, cursor, internal_ext):
        return {
            "app_name": "douyin_web", "version_code": "180800", "device_platform": "web",
            "cookie_enabled": "true", "screen_width": "1920", "screen_height": "1080",
            "browser_language": "zh-CN", "browser_platform": "Win32", "browser_name": "Mozilla",
            "browser_version": UA, "browser_online": "true", "tz_name": "Asia/Shanghai",
            "host": "https://live.douyin.com", "aid": "6383", "live_id": "1", "did_rule": "3",
            "endpoint": "live_pc", "support_wrds": "1", "identity": "audience",
            "need_persist_msg_count": "15", "insert_task_id": "", "live_reason": "",
            "resp_content_type": "json", "fetch_rule": "1", "last_rtt": "0",
            "cursor": cursor, "internal_ext": internal_ext,
            "room_id": self.room_id, "user_unique_id": self.did,
        }

    def _sign(self):
        js_code = (SCRIPT_DIR / "webcast_signature.js").read_text(encoding="utf-8")
        js_code = f'_navigator = {{userAgent: "{UA}"}};\n' + js_code
        ctx = execjs.compile(js_code)
        raw = (f"live_id=1,aid=6383,version_code=180800,webcast_sdk_version=1.0.14-beta.0,"
               f"room_id={self.room_id},sub_room_id=,sub_channel_id=,did_rule=3,"
               f"user_unique_id={self.did},device_platform=web,device_type=,ac=,identity=audience")
        stub = hashlib.md5(raw.encode()).hexdigest()
        return ctx.call("get_signature", stub)["X-Bogus"]

    def run(self):
        self.ws = websocket.WebSocketApp(
            self.wss_url,
            header={"Cookie": self.cookie, "User-Agent": UA},
            on_open=lambda ws: print("[wss] ✅ 已连接抖音直播间", flush=True),
            on_message=self._on_message,
            on_error=lambda ws, e: print(f"[wss] 错误：{e}", flush=True),
            on_close=lambda ws, *a: print(f"[wss] 连接关闭 {a}", flush=True),
        )
        self.ws.run_forever(ping_interval=10, ping_timeout=5)

    def stop(self):
        if self.ws:
            self.ws.close()

    def _on_message(self, ws, message):
        try:
            frame = pb.PushFrame()
            frame.ParseFromString(message)
            payload = frame.payload
            try:
                payload = gzip.decompress(payload)
            except Exception:
                pass
            resp = pb.Response()
            resp.ParseFromString(payload)
            if resp.need_ack:
                ack = pb.PushFrame(logId=frame.logId, payloadType="ack",
                                   payload=resp.internal_ext.encode("utf-8"))
                ws.send(ack.SerializeToString(), websocket.ABNF.OPCODE_BINARY)
            for msg in resp.messages:
                self._dispatch(msg)
        except Exception as e:
            print(f"[wss] 解析异常：{type(e).__name__}: {e}", flush=True)

    def _dispatch(self, msg):
        md = msg.method
        if md == "WebcastChatMessage":
            m = pb.ChatMessage()
            m.ParseFromString(msg.payload)
            nick = m.user.nickname if m.user else "观众"
            if m.content:
                print(f"[chat] {nick}: {m.content[:60]}", flush=True)
                self.on_event("chat", str(nick)[:64], str(m.content))
                self.stats["chat"] += 1
        elif md == "WebcastGiftMessage":
            m = pb.GiftMessage()
            m.ParseFromString(msg.payload)
            nick = m.user.nickname if m.user else "观众"
            desc = m.common.describe if m.common else "礼物"
            self.on_event("gift", str(nick)[:64], f"送了 {desc}")
            self.stats["gift"] += 1
        elif md == "WebcastMemberMessage":
            self.stats["member"] += 1
        elif md == "WebcastLikeMessage":
            self.stats["like"] += 1
        elif md == "WebcastSocialMessage":
            self.stats["social"] += 1
        else:
            self.stats["other"] += 1


def resolve_room_id(web_rid):
    """宿主机抓直播间网页提取 realRoomId"""
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    s.get("https://live.douyin.com/", timeout=15)
    r = s.get(f"https://live.douyin.com/{web_rid}",
              headers={"Cookie": f"ttwid={s.cookies.get('ttwid')}"}, timeout=15)
    m = re.search(r'roomId\\?":\\?"(\d+)\\?"', r.text)
    if not m:
        raise RuntimeError(f"无法从 web_rid={web_rid} 解析 realRoomId")
    return m.group(1)


def main():
    ap = argparse.ArgumentParser(description="抖音弹幕采集（宿主机登录态版）")
    ap.add_argument("--web-rid", help="直播间短号（URL 里的数字）")
    ap.add_argument("--room-id", help="realRoomId（跳过解析）")
    ap.add_argument("--session", type=int, required=True, help="LiveOps session_id")
    ap.add_argument("--minutes", type=int, default=0, help="运行分钟数（0=常驻）")
    ap.add_argument("--sessionid", default=os.environ.get("DOUYIN_SESSIONID", ""), help="抖音登录态 sessionid")
    ap.add_argument("--api", default=DEFAULT_API)
    ap.add_argument("--token", default=DEFAULT_TOKEN)
    args = ap.parse_args()

    room_id = args.room_id
    if not room_id:
        if not args.web_rid:
            print("❌ 必须指定 --web-rid 或 --room-id")
            sys.exit(1)
        room_id = resolve_room_id(args.web_rid)
        print(f"[init] web_rid={args.web_rid} → realRoomId={room_id}", flush=True)

    buffer = []
    lock = threading.Lock()
    collected = {"n": 0}

    def on_event(kind, nick, content):
        with lock:
            buffer.append({"nickname": nick, "content": content})
            collected["n"] += 1

    def flusher():
        last_hb = 0
        while True:
            time.sleep(BUFFER_FLUSH_SECONDS)
            with lock:
                items = buffer[:]
                buffer.clear()
            push_to_liveops(items, room_id, args.session, args.api, args.token)
            if time.time() - last_hb > 30:
                heartbeat(room_id, args.session, collected["n"], args.api, args.token)
                last_hb = time.time()

    d = DouyinWS(room_id, args.sessionid, on_event)
    d.prepare()

    t_flush = threading.Thread(target=flusher, daemon=True)
    t_flush.start()

    t_ws = threading.Thread(target=d.run, daemon=True)
    t_ws.start()

    try:
        if args.minutes > 0:
            t_ws.join(args.minutes * 60)
            d.stop()
            time.sleep(1)
        else:
            while t_ws.is_alive():
                t_ws.join(1)
    except KeyboardInterrupt:
        d.stop()
    finally:
        with lock:
            items = buffer[:]
            buffer.clear()
        push_to_liveops(items, room_id, args.session, args.api, args.token)
        print(f"\n[done] 共采集 {collected['n']} 条事件，统计: {json.dumps(d.stats)}", flush=True)


if __name__ == "__main__":
    main()
