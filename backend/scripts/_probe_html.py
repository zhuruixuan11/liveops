"""路线 A 的第二步：从直播间 HTML 里扒内嵌 room JSON（绕过 enter 签名）。

页面 URL: https://live.douyin.com/{web_rid}
HTML 里有一段 window.__INITIAL_STATE__ = {...}，里面有完整的 room 信息
（包括 real_room_id, internal_ext, cursor, is_living, 主播昵称 等）。
这段数据可以被 Python re 提取出来，不需要 a_bogus 签名。
"""
import asyncio
import json
import re
import sys

import httpx

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0"
)


def _pick(d: dict, *keys):
    for k in keys:
        if d.get(k):
            return d[k]
    return None


async def main(web_rid: str):
    async with httpx.AsyncClient(
        headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"},
        follow_redirects=True,
        timeout=15,
    ) as c:
        url = f"https://live.douyin.com/{web_rid}"
        r = await c.get(url)
        print(f"[1] GET {url}  → status={r.status_code}, html_len={len(r.text)}")

        # --- 抓 ttwid cookie ---
        ttwid = r.cookies.get("ttwid") or ""
        print(f"[1] ttwid = {ttwid[:40]}{'...' if len(ttwid) > 40 else ''}")

        # --- 扒 INITIAL_STATE ---
        m = re.search(r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*</script>", r.text, re.DOTALL)
        if not m:
            print("[X] 找不到 window.__INITIAL_STATE__，页面结构可能变了")
            print(r.text[:300])
            sys.exit(1)
        try:
            state = json.loads(m.group(1))
        except Exception as e:
            print(f"[X] INITIAL_STATE JSON 解析失败：{e}")
            sys.exit(1)

        # state 结构可能是 {room: {...}} 或 {liveRoom: {...}} 或直接 room 对象，兜一层
        room = (
            _pick(state, "room", "liveRoom", "roomInfo", "live_room")
            or _pick(state, "Room", "LiveRoom")
            or state
        )
        # 如果 room 下还有一层 _raw，取出来
        room = room.get("room") or room

        print(f"[2] state keys top-level = {list(state.keys())[:10]}")
        print(f"[2] room keys = {list(room.keys())[:20] if isinstance(room, dict) else type(room)}")

        if not isinstance(room, dict) or not room:
            print("[X] room 结构异常")
            sys.exit(1)

        owner = room.get("owner") or room.get("anchor") or room.get("user") or {}

        rid = (
            _pick(room, "id_str", "room_id_str", "id", "room_id")
            or _pick(state, "roomIdStr", "room_id_str")
        )
        ext = _pick(room, "internal_ext") or _pick(state, "internal_ext")
        cursor = _pick(room, "cursor", "live_cursor") or _pick(state, "cursor")
        is_living = (
            room.get("status") == 2
            or room.get("is_living")
            or _pick(state, "isLiving")
            or _pick(state, "is_living")
        )

        print(f"[2] 主播={owner.get('nickname') or owner.get('nick_name') or '?'} "
              f"unique_id={owner.get('unique_id') or owner.get('sec_uid') or ''}")
        print(f"[2] real_room_id  = {rid}")
        print(f"[2] internal_ext  = {ext}")
        print(f"[2] cursor        = {cursor}")
        print(f"[2] 直播中        = {is_living}")

        # --- 额外：试一下 /webcast/room/web/enter 用 ttwid cookie 直接调 ---
        enter_url = "https://live.douyin.com/webcast/room/web/enter/"
        params = {
            "aid": "6383",
            "app_name": "douyin_web",
            "live_id": "1",
            "device_platform": "web",
            "web_rid": web_rid,
        }
        try:
            r2 = await c.get(enter_url, params=params, headers={"Referer": url})
            print(f"[3] enter(no a_bogus) → status={r2.status_code} body_len={len(r2.text)}")
            if r2.text.strip():
                print(f"[3] enter body 开头: {r2.text[:300]}")
        except Exception as e:
            print(f"[3] enter 异常：{e}")

        # --- 输出给 douyin_fetcher 用 ---
        if rid and ext:
            print("\n=== fetcher kwargs (宿主机上用) ===")
            print(f"python -m scripts.douyin_fetcher "
                  f"--real-room-id {rid} "
                  f"--internal-ext \"{ext}\" "
                  f"--session 18 --minutes 3 "
                  f"# ttwid={ttwid[:40]}...")
        else:
            print("[X] 关键字段缺失，跳过 WS 直连")
            sys.exit(1)


if __name__ == "__main__":
    rid = sys.argv[1] if len(sys.argv) > 1 else "296728101980"
    asyncio.run(main(rid))
