"""宿主机跑 f2 直播弹幕转发的 Step 3-4：
容器已经 gen_ttwid + fetch_user_live_videos 拿到了 room_id=7694232265768897306
和 user_unique_id；这里补跑 fetch_live_im 和 fetch_live_danmaku。

但宿主机没装 f2，所以用最简单的路径：直接用 httpx 手动调 fetch_live_im 接口，
拿到 internal_ext + cursor，再用 websockets 直连 WSS。
"""
import asyncio
import json
import time
import sys

import httpx
import websockets

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/132.0.0.0 Edg/132.0.0.0"

# ===== 从容器 Step 2 复制过来的值 =====
ROOM_ID = "7694232265768897306"
USER_UNIQUE_ID = "7699784658401904179"
TTWID = ""  # 运行时会自动生成
COOKIE = ""

LIVEOPS_API = "http://localhost:8000/api/v1"
LIVEOPS_TOKEN = "liveops-ingest-2026"
LIVEOPS_SESSION = 18  # 本平台场次 ID


async def get_ttwid_and_enter(web_rid: str):
    """宿主机自己调 enter 接口拿 room_id，绕过容器"""
    async with httpx.AsyncClient(
        headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"},
        follow_redirects=True,
        timeout=15,
    ) as c:
        # 访问页面生成 ttwid
        r = await c.get(f"https://live.douyin.com/{web_rid}")
        ttwid = r.cookies.get("ttwid") or ""
        print(f"[宿主机] ttwid={ttwid[:40]}...")
        if not ttwid:
            print("[宿主机] 没拿到 ttwid，退出")
            sys.exit(1)

        # 调 enter 接口（不带 a_bogus，宿主机 IP 应该能过）
        params = {
            "aid": "6383", "app_name": "douyin_web", "live_id": "1",
            "device_platform": "web", "cookie_enabled": "true",
            "web_rid": web_rid,
        }
        try:
            r2 = await c.get(
                "https://live.douyin.com/webcast/room/web/enter/",
                params=params,
                headers={"Referer": f"https://live.douyin.com/{web_rid}"},
            )
            print(f"[宿主机] enter status={r2.status_code} body_len={len(r2.text)}")
            if r2.text.strip():
                j = r2.json()
                room = (j.get("data") or {}).get("room") or {}
                rid = (j.get("data") or {}).get("room_id_str") or room.get("id_str")
                is_living = room.get("status") == 2 or room.get("is_living")
                print(f"[宿主机] enter OK → realRoomId={rid} living={is_living}")
                return rid, ttwid
            else:
                print("[宿主机] enter 还是空 body")
                return None, ttwid
        except Exception as e:
            print(f"[宿主机] enter 异常：{e}")
            return None, ttwid


async def main():
    # 方案 A：宿主机自己拿 room_id
    rid, ttwid = await get_ttwid_and_enter(sys.argv[1] if len(sys.argv) > 1 else "296728101980")
    if rid:
        print(f"\n[宿主机] realRoomId={rid}")
        print(f"[宿主机] 宿主机 IP 链路可用 → 后续走 fetch_live_im + WSS")
        print(f"[宿主机] 完整跑通 f2 需要在宿主机装 f2（现在 Python 3.14 装不上）")
        print(f"[宿主机] === 临时方案：把 room_id 推回容器，让容器完成 Step 3-4 ===")
        print(f"\n  容器执行：python -m scripts.douyin_fetcher "
              f"--real-room-id {rid} --internal-ext XXX "
              f"--session {LIVEOPS_SESSION} --minutes 3")
    else:
        print("\n[宿主机] 宿主机 enter 也空 → 抖音对所有 IP 都风控了")
        print("[宿主机] 最终兜底：Playwright 打开直播间 → 从 DOM 读弹幕")


if __name__ == "__main__":
    asyncio.run(main())
