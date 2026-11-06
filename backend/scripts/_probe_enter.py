"""第一步：宿主机上拿抖音匿名游客 cookie (ttwid)，并验证 enter 接口能否返回数据。

独立运行，不依赖本平台，只用来确认抖音匿名 API 链路在当前 Windows 机器上能跑通。
成功后会输出 real_room_id / internal_ext / cursor，这些就是连 WebSocket 必须的字段。
"""
import asyncio
import sys
import httpx

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0"
)
REFERER = "https://live.douyin.com/"


async def main(web_rid: str):
    async with httpx.AsyncClient(
        headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"},
        follow_redirects=True,
        timeout=15,
    ) as c:
        # --- 1. 访问直播间页面拿 ttwid cookie ---
        page_url = f"https://live.douyin.com/{web_rid}"
        r = await c.get(page_url)
        print(f"[1] GET {page_url}  → status={r.status_code}")
        ttwid = r.cookies.get("ttwid")
        print(f"[1] ttwid = {ttwid!r}")
        if not ttwid:
            # 也许 ttwid 走的是 set-cookie 头在重定向链上
            ttwid = next((c.cookies for c in r.history if "ttwid" in c.cookies), None)
            if isinstance(ttwid, dict):
                ttwid = ttwid.get("ttwid")
            print(f"[1b] ttwid via history = {ttwid!r}")
        if not ttwid:
            print("[X] 没拿到 ttwid，后面都会失败，先手工访问一次直播间再跑")
            sys.exit(1)

        # --- 2. 调 enter 接口拿 realRoomId / internal_ext / cursor ---
        enter_url = "https://live.douyin.com/webcast/room/web/enter/"
        params = {
            "aid": "6383",
            "app_name": "douyin_web",
            "live_id": "1",
            "device_platform": "web",
            "language": "zh-CN",
            "cookie_enabled": "true",
            "web_rid": web_rid,
            "a_bogus": "",  # 空的也能过，抖音对 cookie 用户不强制校验
        }
        r2 = await c.get(enter_url, params=params, headers={"Referer": REFERER})
        print(f"[2] GET enter  → status={r2.status_code}, body_len={len(r2.text)}")
        try:
            j = r2.json()
        except Exception:
            print(f"[X] enter 返回不是 JSON：{r2.text[:200]}")
            sys.exit(1)

        data = j.get("data") or {}
        room = data.get("room") or {}
        owner = room.get("owner") or {}
        rid = data.get("room_id_str") or room.get("id_str") or room.get("id")
        ext = data.get("internal_ext")
        cursor = data.get("cursor") or data.get("live_cursor")
        is_living = room.get("status") == 2 or room.get("is_living")

        print(f"[2] enter code={j.get('status_code')} msg={j.get('status_msg')}")
        print(f"[2] 主播={owner.get('nickname')} unique_id={owner.get('unique_id')}")
        print(f"[2] real_room_id = {rid}")
        print(f"[2] internal_ext = {ext}")
        print(f"[2] cursor = {cursor}")
        print(f"[2] 直播中 = {is_living}")
        if not ext or not rid:
            print("[X] 关键字段缺失，可能直播间已下播或 IP 被风控")
            sys.exit(1)

        # --- 3. 把 f2 的 kwargs 也写出来，便于下一步直接复用 ---
        kwargs = {
            "headers": {"User-Agent": UA, "Referer": REFERER},
            "proxies": {"http://": None, "https://": None},
            "cookie": f"ttwid={ttwid}",
        }
        print("\n=== f2 kwargs ===")
        print(f"kwargs={kwargs}")
        print(f"room_id={rid}")
        print(f"user_unique_id={owner.get('unique_id') or owner.get('short_id') or ''}")
        print(f"internal_ext={ext}")
        print(f"cursor={cursor}")


if __name__ == "__main__":
    rid = sys.argv[1] if len(sys.argv) > 1 else "296728101980"
    asyncio.run(main(rid))
