"""直播间弹幕采集器（独立进程，不依赖第三方库）

把"进入直播间拉弹幕"这一步和平台解耦：
  外部抓取进程（开源 DouyinLiveWebFetcher / 自研 ws 客户端 / 平台开放接口）
  → 统一输出 JSONL 或直接 POST → 本平台 /api/v1/ingest/danmaku → 意图识别 + 落库 + 推 Stream

三种用法：
  1) 演示/压测（不需要真实直播间）：
       python -m scripts.danmaku_collector --mode mock --session 1 --interval 4 --batch 2
  2) 对接抓取器落盘文件（推荐真实抖音直播场景）：
       python -m scripts.danmaku_collector --mode file --session 1 --file /data/danmaku.jsonl
     抓取器每行写一个 JSON：{"nickname":"小明","content":"有没有券","ts":1690000000}
  3) 对接抓取器 WebSocket（需安装 websocket-client）：
       python -m scripts.danmaku_collector --mode ws --session 1 --ws ws://127.0.0.1:8888

鉴权：--token 或环境变量 INGEST_TOKEN，需与后端 INGEST_TOKEN 一致（默认 liveops-ingest-2026）。
"""
import argparse
import json
import os
import random
import sys
import time
from datetime import datetime
from urllib import error, request

DEFAULT_API = os.environ.get("LIVEOPS_API", "http://localhost:8000/api/v1")
DEFAULT_TOKEN = os.environ.get("INGEST_TOKEN", "liveops-ingest-2026")

NICKNAMES = [
    "小丸子", "橘子汽水", "爱吃辣", "阿泽", "momo", "晚风", "十七", "Lily",
    "芝士就是力量", "一颗糖", "南风知我意", "小鹿乱撞", "早睡选手", "柚柚",
    "冲鸭", "柠檬不萌", "大橘为重", "一颗西柚", "夏日限定", "路过的",
]

DANMAKU_POOL = {
    "ask_coupon": ["有没有优惠券", "券怎么领", "再放点券吧", "满多少减多少", "还有券吗"],
    "ask_stock": ["还有货吗", "库存多少", "能拍吗", "补货了吗", "这个还有吗"],
    "logistics": ["什么时候发货", "发什么快递", "几天能到", "偏远地区发货吗"],
    "aftersale": ["怎么退货", "有质量问题怎么办", "支持换货吗", "拆封了能退吗"],
    "complaint": ["太差了", "我要投诉", "上次买的还没到", "客服不理人"],
    "ask_price": ["多少钱", "到手价多少", "比专柜便宜吗", "还有更划算的吗"],
    "faq_product": ["成分是什么", "敏感肌能用吗", "保质期多久", "怎么用", "适合什么肤质"],
    "faq_policy": ["活动规则是什么", "包邮吗", "怎么参加", "会员有额外优惠吗"],
    "spam": ["加微信私聊", "我这边有批发", "看我主页"],
    "general": ["主播好看", "支持一下", "已下单", "求上链接", "蹲一个", "冲冲冲", "刚拍了两件", "这个颜色好看"],
}

WEIGHTS = [16, 13, 10, 6, 3, 12, 11, 8, 2, 19]


def _post(api: str, path: str, payload: dict, token: str) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        f"{api.rstrip('/')}{path}",
        data=data,
        headers={"Content-Type": "application/json", "X-Ingest-Token": token},
        method="POST",
    )
    with request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _gen_items(n: int):
    intents = list(DANMAKU_POOL.keys())
    items = []
    for _ in range(n):
        intent = random.choices(intents, weights=WEIGHTS, k=1)[0]
        items.append({
            "nickname": random.choice(NICKNAMES),
            "content": random.choice(DANMAKU_POOL[intent]),
            "ts": datetime.utcnow().isoformat(),
        })
    return items


def _follow_file(path: str):
    """从文件末尾开始持续读取新增行；启动时先回放最后 20 行，避免冷启动空窗。"""
    while not os.path.exists(path):
        print(f"[collector] 等待文件出现：{path}")
        time.sleep(2)
    with open(path, "r", encoding="utf-8") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                yield None
                continue
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _normalize(raw: dict) -> dict:
    nickname = raw.get("nickname") or raw.get("nick") or raw.get("user") or raw.get("name") or "观众"
    content = raw.get("content") or raw.get("text") or raw.get("msg") or ""
    ts = raw.get("ts") or raw.get("timestamp") or raw.get("time")
    return {"nickname": str(nickname)[:64], "content": str(content), "ts": ts}


def _run_ws(api: str, token: str, session_id: int, ws_url: str, room_id: str, interval: int):
    try:
        import websocket  # type: ignore
    except ImportError:
        print("[collector] ws 模式需要先安装 websocket-client：pip install websocket-client")
        sys.exit(2)

    buffer = []
    last_flush = time.time()

    def on_message(_ws, message):
        nonlocal last_flush
        try:
            raw = json.loads(message)
        except Exception:
            return
        item = _normalize(raw)
        if item["content"]:
            buffer.append(item)
        if len(buffer) >= 20 or time.time() - last_flush >= interval:
            _flush(api, token, session_id, buffer)
            buffer.clear()
            last_flush = time.time()

    print(f"[collector] 连接抓取器 WebSocket：{ws_url}")
    ws = websocket.WebSocketApp(ws_url, on_message=on_message)
    ws.run_forever()


def _flush(api: str, token: str, session_id: int, items: list, room_id: str = "", source: str = "collector"):
    if not items:
        return
    try:
        r = _post(api, "/ingest/danmaku", {
            "session_id": session_id, "source": source, "room_id": room_id, "items": items,
        }, token)
        print(f"[collector] 推送 {len(items)} 条 → 入库 {r.get('accepted')} / 过滤 {r.get('filtered')} / 跳过 {r.get('skipped')}")
    except error.HTTPError as e:
        print(f"[collector] 推送失败 {e.code}: {e.read().decode('utf-8', 'ignore')[:200]}")
    except Exception as e:
        print(f"[collector] 推送失败：{e}")


def _heartbeat(api: str, token: str, session_id: int, source: str, room_id: str, collected: int):
    try:
        _post(api, "/ingest/heartbeat", {
            "session_id": session_id, "source": source, "room_id": room_id,
            "collected": collected, "note": "collector running",
        }, token)
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser(description="LiveOps 直播间弹幕采集器")
    ap.add_argument("--mode", choices=["mock", "file", "ws"], default="mock")
    ap.add_argument("--session", type=int, required=True, help="本平台场次 ID")
    ap.add_argument("--api", default=DEFAULT_API, help="后端 API 根地址")
    ap.add_argument("--token", default=DEFAULT_TOKEN)
    ap.add_argument("--interval", type=int, default=4, help="批量推送间隔（秒）")
    ap.add_argument("--batch", type=int, default=2, help="mock 模式每批条数")
    ap.add_argument("--file", default="", help="file 模式：抓取器输出的 JSONL 文件")
    ap.add_argument("--ws", default="", help="ws 模式：抓取器 WebSocket 地址")
    ap.add_argument("--room-id", default="", help="外部直播间号，仅用于状态展示")
    ap.add_argument("--source", default="", help="来源标识，默认按 mode 推断")
    ap.add_argument("--minutes", type=int, default=0, help="运行时长（分钟），0 表示常驻")
    args = ap.parse_args()

    api = args.api
    source = args.source or {"mock": "mock", "file": "file", "ws": "ws"}[args.mode]
    deadline = time.time() + args.minutes * 60 if args.minutes else None

    print(f"[collector] mode={args.mode} session={args.session} api={api} source={source}")
    collected = 0

    if args.mode == "ws":
        if not args.ws:
            print("[collector] ws 模式需要 --ws")
            sys.exit(2)
        _run_ws(api, args.token, args.session, args.ws, args.room_id, args.interval)
        return

    if args.mode == "file":
        if not args.file:
            print("[collector] file 模式需要 --file")
            sys.exit(2)
        buffer, last_flush, last_hb = [], time.time(), 0.0
        for raw in _follow_file(args.file):
            if raw is not None:
                item = _normalize(raw)
                if item["content"]:
                    buffer.append(item)
            now = time.time()
            if (len(buffer) >= 20 or now - last_flush >= args.interval) and buffer:
                _flush(api, args.token, args.session, buffer, args.room_id, source)
                collected += len(buffer)
                buffer.clear()
                last_flush = now
            if now - last_hb >= 30:
                _heartbeat(api, args.token, args.session, source, args.room_id, collected)
                last_hb = now
            if deadline and now > deadline:
                _flush(api, args.token, args.session, buffer, args.room_id, source)
                break
        return

    # mock 模式
    last_hb = 0.0
    while True:
        items = _gen_items(args.batch)
        _flush(api, args.token, args.session, items, args.room_id, source)
        collected += len(items)
        now = time.time()
        if now - last_hb >= 30:
            _heartbeat(api, args.token, args.session, source, args.room_id, collected)
            last_hb = now
        if deadline and now > deadline:
            break
        time.sleep(max(1, args.interval))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[collector] 已停止")
