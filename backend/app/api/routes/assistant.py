"""智能助手：自然语言一键查询 / 直播内容规划 / 客服话术建议

全部基于本平台数据，不依赖外部模型即可运行；配置了 LLM 时会额外润色。
"""
import random
import re
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import jieba
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.llm_client import get_llm
from app.agent.platform_rules import get_platform_rules
from app.models.all import (
    Danmaku, SalesOrder, SalesOrderDetail, Product, SkuInfo,
    LiveSession, Staff, Store, Coupon, CouponIssue, MonitorEvent,
)

router = APIRouter()

PAID = "02"

INTENT_LABEL = {
    "faq_product": "商品咨询", "faq_policy": "活动规则", "ask_price": "价格咨询",
    "ask_coupon": "求优惠券", "ask_stock": "问库存", "logistics": "物流咨询",
    "aftersale": "售后问题", "complaint": "投诉", "spam": "广告刷屏", "general": "闲聊互动",
}

# 可插拔的"近期热点"库：真实环境可替换为巨量算数/热搜接口
HOT_TOPICS = [
    ("秋冬换季护肤", "换季敏感肌、屏障修护搜索量上升"),
    ("双11预售", "大促预售期，用户比价与囤货意愿强"),
    ("成分党", "用户关注成分表、浓度与功效实测"),
    ("以油养肤", "精华油类目热度持续"),
    ("直播专享价", "用户对「直播价 vs 专柜价」的对比更敏感"),
]

REPLY_TEMPLATE = {
    "ask_coupon": "宝子稍等，{name}已经在放券啦～点右下角小黄车领券，满 {threshold} 减 {discount}，仅限本场！",
    "ask_stock": "库存实时更新中，当前还有货，拍下就是你的～需要我帮你留一件吗？",
    "ask_price": "本场是直播专享价，比日常价低不少；再叠加优惠券更划算，我给你算一下到手价～",
    "faq_product": "这款的核心成分/参数我在讲解卡里放了，简单说：适合{scene}，用法是{usage}。还有想问的直接说～",
    "logistics": "默认发顺丰/中通，48 小时内出库，偏远地区会稍慢一点，我会帮你盯着物流。",
    "aftersale": "收到不满意支持 7 天无理由，我这边帮你登记，稍后客服私信你处理。",
    "complaint": "非常抱歉给你带来不好的体验，我马上安排专人跟进，请私信我订单号。",
    "spam": "（该条为广告，已自动屏蔽）",
    "general": "感谢{name}的支持～点点关注不迷路，等下还有福利场！",
}

STOPWORDS = {
    "这个", "那个", "还有", "可以", "什么", "怎么", "就是", "多少", "有没有", "一下",
    "我们", "你们", "他们", "主播", "直播", "直播间", "链接", "现在", "时候", "真的",
    "感觉", "有点", "已经", "支持", "好看", "一个", "这件", "那件", "刚拍", "两个",
    "吗", "呢", "啊", "吧", "的", "了", "是", "我", "你", "他", "它", "在", "有",
    "和", "就", "都", "也", "很", "不", "呀", "哦", "嗯",
}


class QueryIn(BaseModel):
    question: str
    days: int = 7


class PlanIn(BaseModel):
    store_id: Optional[int] = None
    host_id: Optional[int] = None
    session_id: Optional[int] = None
    duration_minutes: int = 60
    focus: Optional[str] = None      # 用户补充的方向，如"主推面霜"
    platform: str = "douyin"         # 推流平台，决定规则与节奏


def _money(v: Any) -> float:
    return float(Decimal(str(v or 0)))


def _parse_days(q: str, default: int = 7) -> int:
    m = re.search(r"(?:近|最近|过去)\s*(\d+)\s*天", q)
    if m:
        return max(1, min(365, int(m.group(1))))
    if "今天" in q or "今日" in q:
        return 1
    if "本周" in q or "这周" in q:
        return 7
    if "本月" in q or "这月" in q:
        return 30
    if "季度" in q:
        return 90
    return default


# ---------------- 提问分类：先判断"跟不跟直播/业务有关" ----------------
# 业务数据类主题（顺序即优先级，命中即用该主题的数据回答）
BUSINESS_TOPICS: List[Tuple[str, Tuple[str, ...]]] = [
    ("host", ("主播", "谁播得", "谁最", "排名", "绩效")),
    ("product", ("商品", "卖得", "爆款", "销量", "哪个好卖")),
    ("stock", ("库存", "缺货", "没货", "补货", "还剩")),
    ("coupon", ("券", "优惠券", "优惠", "发放", "核销")),
    ("trend", ("流水", "趋势", "每天", "日销", "营收", "环比")),
    ("orders", ("订单", "客单价", "gmv", "销售额", "成交", "整体", "概况", "情况")),
]

# 跟直播相关、但不是查具体数据的问法
LIVE_HINTS = ("直播", "开播", "下播", "场控", "直播间", "弹幕", "在线人数", "在线", "这场", "几场")
GREETING_HINTS = ("你好", "您好", "在吗", "在么", "hi", "hello", "哈喽", "早上好", "晚上好", "下午好")
THANKS_HINTS = ("谢谢", "感谢", "辛苦", "thanks", "多谢")
IDENTITY_HINTS = ("你是谁", "你能干", "你会什么", "你能做什么", "怎么用", "介绍下你", "你是干")
CHAT_HINTS = ("哈哈", "笑死", "厉害", "牛", "666", "无聊", "天气", "吃饭", "吃了吗", "几点",
              "晚安", "早安", "心情", "累不累", "喝奶茶", "周末", "音乐", "电影", "游戏")

CHAT_REPLIES = {
    "greeting": [
        "你好呀～我是这个直播运营平台的 AI 助手，可以查主播表现、商品销量、库存预警、优惠券和流水趋势，也能陪你随便聊聊。",
        "在的～有什么想看的数？说「近 7 天主播排名」「库存预警」「这个月流水」都行，不想查数据聊两句也可以。",
        "嗨～来了就聊聊吧，想看哪块数据？主播、商品、券、库存、流水我都能查。",
    ],
    "thanks": [
        "不客气～有需要随时喊我。",
        "客气啦，这是我该做的。还想看哪个数据直接说就行。",
        "应该的～祝你这几场直播场场爆单。",
    ],
    "identity": [
        "我是直播间背后的 AI 运营助手：能答数据查询（主播排名、商品销量、库存、券、流水、订单），也能做直播规划，还能解读弹幕情绪。",
        "简单说，我是你的直播运营小助手——看数据、排脚本、盯弹幕三件事都能帮上忙。",
    ],
    "chitchat": [
        "哈哈，这个我陪聊～不过要说正经的，我还能帮你看直播数据，想看哪块？",
        "这个问题有意思，不过我更擅长直播运营。要不要看看今天的场次和流水？",
        "聊得来～顺便提一句，最近的弹幕里问券的人挺多，券的节奏可以前置一点。",
        "我听着呢～你要是想了解哪场直播的表现，我也能马上给你数。",
    ],
    "offtopic": [
        "这个超出我的专长了（我只懂直播运营这块）。不过直播间相关的数据我都很熟，比如主播排名、库存预警、流水趋势。",
        "这个问题我可能答不专业，不敢瞎编。换成直播相关的问题我就能帮上忙了。",
        "我不太懂这个，但直播的事儿可以问我：场次、弹幕、券、库存、销售额都能查。",
    ],
}


def _classify_question(q: str) -> str:
    """把用户问题分成三类：业务数据(host/product/stock/coupon/trend/orders)、直播相关(live)、闲聊(chat)"""
    text = (q or "").lower()
    for topic, keys in BUSINESS_TOPICS:
        if any(k.lower() in text for k in keys):
            return topic
    if any(k in text for k in LIVE_HINTS):
        return "live"
    return "chat"


def _chat_kind(q: str) -> str:
    text = (q or "").lower()
    if any(k in text for k in IDENTITY_HINTS):
        return "identity"
    if any(k in text for k in THANKS_HINTS):
        return "thanks"
    if any(k in text for k in GREETING_HINTS):
        return "greeting"
    if any(k in text for k in CHAT_HINTS):
        return "chitchat"
    return "offtopic"


CHAT_SYSTEM_PROMPT = (
    "你是直播运营平台的 AI 助手。先判断用户问题是否与直播/电商运营相关："
    "相关就给专业、具体的建议；不相关（闲聊、天气、情感等）就自然、简短、有温度地回应，"
    "绝对不要编造平台里的数字或订单数据。回答控制在 120 字以内，语气轻松口语化。"
)


def _chat_answer(q: str, db: Session) -> str:
    """闲聊/无关问题：有 LLM 就用 LLM 自然回答，没有就用内置语料随机兜底。"""
    try:
        settings = get_settings()
        if settings.llm_api_key:
            r = get_llm().chat(
                model=settings.llm_light_model,
                messages=[
                    {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                    {"role": "user", "content": q},
                ],
                temperature=0.7,
            )
            content = (r.get("content") or "").strip()
            if content:
                return content
    except Exception:
        pass
    return random.choice(CHAT_REPLIES[_chat_kind(q)])


def _live_answer(db: Session, result, days: int) -> Dict[str, Any]:
    """跟直播相关、但不是查具体数据的问法：给当前在播场次 + 今日实时概况。"""
    living = db.scalars(select(LiveSession).where(LiveSession.status == "living")).all()
    store_map = {s.store_id: s.name for s in db.scalars(select(Store)).all()}
    staff_map = {s.staff_id: s.name for s in db.scalars(select(Staff)).all()}
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    paid_today = db.scalars(
        select(SalesOrder).where(SalesOrder.status == PAID, SalesOrder.create_time >= today)
    ).all()
    gmv_today = sum(_money(o.pay_amount) for o in paid_today)
    dm_today = db.scalar(
        select(func.count()).select_from(Danmaku).where(Danmaku.created_at >= today)
    ) or 0

    rows = [
        [f"#{s.session_id}", s.title, store_map.get(s.store_id, "-"),
         staff_map.get(s.host_id, "-"), int(getattr(s, "viewer_count", 0) or 0)]
        for s in living
    ]
    if rows:
        answer = (f"现在有 {len(rows)} 场在播：{'、'.join(r[1] for r in rows[:3])}。"
                  f"今日已成交 {len(paid_today)} 单、GMV ¥{gmv_today:.2f}，今日弹幕 {dm_today} 条。"
                  "想看画面就去「直播场次」点进任意一场。")
    else:
        answer = (f"当前没有正在进行的场次。今日已成交 {len(paid_today)} 单、"
                  f"GMV ¥{gmv_today:.2f}，今日弹幕 {dm_today} 条。")
    chart = ({"type": "bar", "x": [r[1] for r in rows], "y": [r[4] for r in rows], "name": "在线人数"}
             if rows else None)
    return result(answer, ["场次", "标题", "门店", "主播", "在线"], rows, chart, "live")




# ---------------- 一键查询 ----------------
@router.post("/query")
def assistant_query(payload: QueryIn, db: Session = Depends(get_db),
                    _: dict = Depends(get_current_user)):
    q = (payload.question or "").strip()
    days = _parse_days(q, payload.days)
    since = datetime.utcnow() - timedelta(days=days)
    paid_orders = db.scalars(
        select(SalesOrder).where(SalesOrder.status == PAID, SalesOrder.create_time >= since)
    ).all()
    gmv = sum(_money(o.pay_amount) for o in paid_orders)

    def result(answer: str, columns: List[str], rows: List[List[Any]],
               chart: Optional[Dict[str, Any]] = None,
               topic_override: Optional[str] = None) -> Dict[str, Any]:
        return {
            "question": q, "days": days, "answer": answer,
            "topic": topic_override or topic_name,
            "table": {"columns": columns, "rows": rows},
            "chart": chart,
        }

    # 先判断问题跟不跟直播/业务有关：闲聊和无关问题不再落进"订单概况"兜底
    topic_name = _classify_question(q)

    if topic_name == "chat":
        return result(_chat_answer(q, db), [], [], None, "chat")

    if topic_name == "live":
        return _live_answer(db, result, days)

    # 1. 主播表现
    if topic_name == "host":
        sessions = db.scalars(select(LiveSession).where(LiveSession.start_time >= since)).all()
        staff_map = {s.staff_id: s.name for s in db.scalars(select(Staff)).all()}
        agg = defaultdict(lambda: {"sessions": 0, "orders": 0, "gmv": 0.0, "peak": 0})
        for s in sessions:
            if not s.host_id:
                continue
            a = agg[s.host_id]
            a["sessions"] += 1
            a["peak"] = max(a["peak"], s.peak_viewer or 0)
            orders = db.scalars(select(SalesOrder).where(
                SalesOrder.session_id == s.session_id, SalesOrder.status == PAID)).all()
            a["orders"] += len(orders)
            a["gmv"] += sum(_money(o.pay_amount) for o in orders)
        rows = sorted(
            [[staff_map.get(h, f"主播#{h}"), v["sessions"], v["orders"],
              round(v["gmv"], 2), v["peak"]] for h, v in agg.items()],
            key=lambda x: -x[3],
        )
        top = rows[0] if rows else None
        answer = (f"近 {days} 天表现最好的是 {top[0]}：{top[1]} 场、{top[2]} 单、GMV ¥{top[3]}，峰值在线 {top[4]} 人。"
                  if top else f"近 {days} 天暂无主播场次数据。")
        return result(answer, ["主播", "场次", "成交单", "GMV", "峰值在线"], rows,
                      {"type": "bar", "x": [r[0] for r in rows[:8]], "y": [r[3] for r in rows[:8]], "name": "GMV"})

    # 2. 商品销量
    if topic_name == "product":
        rows_db = db.execute(
            select(SalesOrderDetail.product_name, func.sum(SalesOrderDetail.qty),
                   func.sum(SalesOrderDetail.subtotal))
            .join(SalesOrder, SalesOrder.order_id == SalesOrderDetail.order_id)
            .where(SalesOrder.status == PAID, SalesOrder.create_time >= since)
            .group_by(SalesOrderDetail.product_name)
            .order_by(func.sum(SalesOrderDetail.subtotal).desc())
            .limit(10)
        ).all()
        rows = [[r[0], int(r[1] or 0), round(_money(r[2]), 2)] for r in rows_db]
        top = rows[0] if rows else None
        answer = (f"近 {days} 天最好卖的是「{top[0]}」，卖出 {top[1]} 件，销售 ¥{top[2]}。"
                  if top else f"近 {days} 天暂无成交商品。")
        return result(answer, ["商品", "件数", "销售额"], rows,
                      {"type": "bar", "x": [r[0] for r in rows[:8]], "y": [r[2] for r in rows[:8]], "name": "销售额"})

    # 3. 库存
    if topic_name == "stock":
        rows_db = db.execute(
            select(Product.product_name, SkuInfo.sku_code, SkuInfo.stock, SkuInfo.price)
            .join(SkuInfo, SkuInfo.product_id == Product.product_id)
            .order_by(SkuInfo.stock.asc()).limit(15)
        ).all()
        rows = [[r[0], r[1], int(r[2] or 0), _money(r[3])] for r in rows_db]
        low = [r for r in rows if r[2] < 10]
        answer = (f"当前 {len(low)} 个 SKU 库存低于 10 件，最低的是「{rows[0][0]}」仅剩 {rows[0][2]} 件，建议立即补货或改预售。"
                  if low else "当前库存整体健康，暂无低于 10 件的 SKU。")
        return result(answer, ["商品", "SKU", "库存", "单价"], rows)

    # 4. 优惠券
    if topic_name == "coupon":
        coupons = db.scalars(select(Coupon)).all()
        rows = []
        for c in coupons:
            issued = db.scalar(select(func.count()).select_from(CouponIssue)
                               .where(CouponIssue.coupon_id == c.coupon_id)) or 0
            rows.append([f"券#{c.coupon_id}", c.type, _money(c.threshold), _money(c.discount),
                         int(c.stock or 0), int(issued)])
        total_issued = sum(r[5] for r in rows)
        answer = f"共 {len(rows)} 种优惠券，累计发放 {total_issued} 张；发放最多的是 {max(rows, key=lambda r: r[5])[0]}。" if rows else "暂无优惠券。"
        return result(answer, ["优惠券", "类型", "门槛", "面额", "库存", "已发放"], rows)

    # 5. 流水趋势
    if topic_name == "trend":
        buckets = defaultdict(float)
        cnt = defaultdict(int)
        for o in paid_orders:
            if not o.create_time:
                continue
            key = o.create_time.strftime("%m-%d")
            buckets[key] += _money(o.pay_amount)
            cnt[key] += 1
        days_sorted = [(datetime.utcnow() - timedelta(days=i)).strftime("%m-%d")
                       for i in range(days - 1, -1, -1)]
        rows = [[d, cnt.get(d, 0), round(buckets.get(d, 0), 2)] for d in days_sorted]
        answer = (f"近 {days} 天合计 GMV ¥{gmv:.2f}，{len(paid_orders)} 笔成交，"
                  f"日均 ¥{gmv / max(days, 1):.2f}。")
        return result(answer, ["日期", "成交单", "流水"], rows,
                      {"type": "line", "x": days_sorted, "y": [r[2] for r in rows], "name": "流水"})

    # 6. 订单概况（默认兜底）
    all_orders = db.scalars(select(SalesOrder).where(SalesOrder.create_time >= since)).all()
    status_cnt = defaultdict(int)
    channel_cnt = defaultdict(int)
    for o in all_orders:
        status_cnt[o.status or "-"] += 1
        channel_cnt[o.channel or "-"] += 1
    status_label = {"01": "待支付", "02": "已支付", "03": "已取消", "07": "已完成"}
    rows = [[status_label.get(k, k), v] for k, v in sorted(status_cnt.items())]
    answer = (f"近 {days} 天共 {len(all_orders)} 笔订单，其中已支付 {status_cnt.get(PAID, 0)} 笔，"
              f"GMV ¥{gmv:.2f}，客单价 ¥{gmv / max(status_cnt.get(PAID, 0), 1):.2f}。")
    return result(answer, ["状态", "订单数"], rows)


# ---------------- 直播内容规划 ----------------
@router.post("/plan")
def assistant_plan(payload: PlanIn, db: Session = Depends(get_db),
                   _: dict = Depends(get_current_user)):
    since = datetime.utcnow() - timedelta(days=14)

    # 热销商品
    sales_rows = db.execute(
        select(SalesOrderDetail.product_name, func.sum(SalesOrderDetail.qty),
               func.sum(SalesOrderDetail.subtotal))
        .join(SalesOrder, SalesOrder.order_id == SalesOrderDetail.order_id)
        .where(SalesOrder.status == PAID, SalesOrder.create_time >= since)
        .group_by(SalesOrderDetail.product_name)
        .order_by(func.sum(SalesOrderDetail.subtotal).desc())
        .limit(6)
    ).all()
    hot_products = [{"name": r[0], "qty": int(r[1] or 0), "gmv": round(_money(r[2]), 2)} for r in sales_rows]

    # 库存紧张
    low_stock = db.execute(
        select(Product.product_name, SkuInfo.stock)
        .join(SkuInfo, SkuInfo.product_id == Product.product_id)
        .where(SkuInfo.stock < 30).order_by(SkuInfo.stock.asc()).limit(5)
    ).all()
    low_stock = [{"name": r[0], "stock": int(r[1] or 0)} for r in low_stock]

    # 高频弹幕意图
    intent_rows = db.execute(
        select(Danmaku.intent, func.count(Danmaku.msg_id))
        .where(Danmaku.created_at >= since, Danmaku.intent.isnot(None))
        .group_by(Danmaku.intent).order_by(func.count(Danmaku.msg_id).desc()).limit(5)
    ).all()
    intents = [{"intent": INTENT_LABEL.get(k, k), "count": int(v)} for k, v in intent_rows]

    # 节奏分配
    total = max(15, payload.duration_minutes)
    seg = {
        "开场留人": max(5, int(total * 0.1)),
        "主推讲解": max(10, int(total * 0.35)),
        "福利逼单": max(8, int(total * 0.25)),
        "异议答疑": max(5, int(total * 0.15)),
        "返场收尾": max(3, total - int(total * 0.85)),
    }

    focus = payload.focus or (hot_products[0]["name"] if hot_products else "门店主推款")
    topics = [{"topic": t, "reason": r} for t, r in HOT_TOPICS[:3]]
    rules = get_platform_rules(payload.platform)

    script = []
    for phase, minutes in seg.items():
        if phase == "开场留人":
            action = ("冷启动先做互动：口令/选择题/抽奖预热，前 3 分钟不急着讲品；"
                      "前 30 分钟每 3-5 分钟互动一次，把停留拉起来")
        elif phase == "主推讲解":
            action = f"主推「{focus}」：成分/参数 → 使用场景 → 实拍演示 → 到手价对比；单款不超过 8 分钟，讲完立刻报库存"
        elif phase == "福利逼单":
            action = "福利节点：福袋/券间隔 15-20 分钟一次，报库存 + 报倒计时；憋单不超过 2 轮"
        elif phase == "异议答疑":
            action = "集中回答高频问题：" + "、".join(i["intent"] for i in intents[:3] or [{"intent": "价格/物流/售后"}])
        else:
            action = "返场 2 款 + 组合优惠，预告下一场福利，引导关注"
        script.append({"phase": phase, "minutes": minutes, "action": action})

    risks = []
    if low_stock:
        risks.append(f"「{low_stock[0]['name']}」仅剩 {low_stock[0]['stock']} 件，本场建议改为预售或限量开抢")
    if intents and intents[0]["intent"] == "求优惠券":
        risks.append("求券需求最集中，券的发放节奏要前置，否则前 10 分钟容易流失")
    if not hot_products:
        risks.append("近 14 天缺少成交数据，建议先做 1 场测款，确定主推后再排大场")
    if total < rules["schedule"]["min_minutes"]:
        risks.append(
            f"{rules['name']}单场建议不短于 {rules['schedule']['min_minutes']} 分钟，"
            "当前计划偏短，频繁短开播不利于流量累积"
        )

    recommendations = []
    if hot_products:
        recommendations.append({
            "title": f"主推「{focus}」",
            "reason": f"近 14 天热销第一：{hot_products[0]['qty']} 件 / ¥{hot_products[0]['gmv']}",
            "action": "安排 15-20 分钟讲解，讲完立刻报库存",
        })
    if intents:
        recommendations.append({
            "title": f"集中回应「{intents[0]['intent']}」",
            "reason": f"近 14 天相关弹幕 {intents[0]['count']} 条，是观众最关心的问题",
            "action": "开场 5 分钟内统一回应，减少重复提问和流失",
        })
    topic = HOT_TOPICS[0]
    recommendations.append({
        "title": f"借势热点「{topic[0]}」",
        "reason": topic[1],
        "action": "把热点作为讲解切入点，结合主推款场景口播",
    })
    if low_stock:
        recommendations.append({
            "title": f"限量开抢「{low_stock[0]['name']}」",
            "reason": f"库存仅 {low_stock[0]['stock']} 件，适合制造稀缺",
            "action": "放到福利逼单段，报库存 + 报倒计时",
        })

    return {
        "duration_minutes": total,
        "focus_product": focus,
        "platform": rules["name"],
        "platform_key": rules["key"],
        "platform_rules": {
            "algorithm": rules["algorithm"],
            "cold_start": rules["cold_start"],
            "schedule": rules["schedule"],
            "rhythm": rules["rhythm"],
            "compliance": rules["compliance"],
            "welfare": rules["welfare"],
        },
        "recommendations": recommendations,
        "hot_products": hot_products,
        "low_stock": low_stock,
        "hot_intents": intents,
        "hot_topics": topics,
        "script": script,
        "risks": risks,
        "checklist": [
            f"开播前 30 分钟：确认主推商品库存与到手价，核对优惠券库存（{rules['name']}冷启动窗口）",
            "开播前 10 分钟：测试推流与商品挂车，准备好话术板",
            "开播前：过一遍合规红线——极限词、站外导流、功效宣称、划线价依据",
            "直播中：每 5 分钟看一次在线曲线，掉线立即触发福袋",
            "下播后：1 小时内完成复盘，确定下一场主推",
        ],
    }


# ---------------- 客服话术建议 ----------------
@router.get("/replies")
def reply_suggestions(session_id: int = Query(..., ge=1),
                      size: int = Query(20, ge=1, le=100),
                      db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    rows = db.scalars(
        select(Danmaku).where(Danmaku.session_id == session_id)
        .order_by(Danmaku.msg_id.desc()).limit(size)
    ).all()

    coupons = db.scalars(select(Coupon).where(Coupon.session_id == session_id)).all()
    best_coupon = coupons[0] if coupons else None

    items = []
    for d in rows:
        intent = d.intent or "general"
        tpl = REPLY_TEMPLATE.get(intent, REPLY_TEMPLATE["general"])
        reply = tpl.format(
            name=d.nickname or "宝子",
            threshold=int(_money(best_coupon.threshold)) if best_coupon else 0,
            discount=int(_money(best_coupon.discount)) if best_coupon else 0,
            scene="日常护肤/敏感肌可用",
            usage="洁面后取适量涂抹，早晚各一次",
        )
        items.append({
            "msg_id": d.msg_id,
            "nickname": d.nickname or "观众",
            "content": d.content,
            "intent": INTENT_LABEL.get(intent, intent),
            "priority": d.priority or 3,
            "handled_by": d.handled_by or "AI",
            "suggested_reply": reply,
            "need_human": intent in ("complaint", "aftersale"),
        })
    return {"session_id": session_id, "items": items}


# ---------------- 弹幕洞察 ----------------
@router.get("/danmaku-insights")
def danmaku_insights(session_id: int = Query(..., ge=1),
                     minutes: int = Query(30, ge=5, le=240),
                     db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    now = datetime.utcnow()
    since = now - timedelta(minutes=minutes)
    rows = db.scalars(
        select(Danmaku).where(
            Danmaku.session_id == session_id,
            Danmaku.created_at >= since,
            Danmaku.handled_by != "FILTERED",
        ).order_by(Danmaku.msg_id.desc())
    ).all()

    intent_cnt: Dict[str, int] = defaultdict(int)
    intent_samples: Dict[str, List[str]] = defaultdict(list)
    keywords: Dict[str, int] = defaultdict(int)
    negative_samples: List[str] = []

    for d in rows:
        intent = d.intent or "general"
        intent_cnt[intent] += 1
        if len(intent_samples[intent]) < 2 and d.content not in intent_samples[intent]:
            intent_samples[intent].append(d.content)
        if intent in ("complaint", "aftersale") and len(negative_samples) < 3:
            negative_samples.append(d.content)
        for w in jieba.lcut(d.content or ""):
            w = w.strip()
            if len(w) >= 2 and w not in STOPWORDS and not re.fullmatch(r"[0-9a-zA-Z]+", w):
                keywords[w] += 1

    by_intent = [
        {
            "intent": INTENT_LABEL.get(k, k),
            "count": v,
            "samples": intent_samples[k],
            "need_human": k in ("complaint", "aftersale"),
        }
        for k, v in sorted(intent_cnt.items(), key=lambda x: -x[1])
        if k != "general"
    ][:5]

    # 近 N 分钟切成 6 段，便于看互动起伏
    buckets = [0] * 6
    span = max(1, minutes / 6)
    for d in rows:
        if not d.created_at:
            continue
        idx = int((d.created_at - since).total_seconds() / 60 / span)
        buckets[min(max(idx, 0), 5)] += 1
    timeline = [
        {"label": f"{int(minutes - (i + 1) * span)}-{int(minutes - i * span)}分前", "count": buckets[i]}
        for i in range(6)
    ]

    top_keywords = [{"word": k, "count": v} for k, v in sorted(keywords.items(), key=lambda x: -x[1])[:8]]
    negative_count = intent_cnt.get("complaint", 0) + intent_cnt.get("aftersale", 0)

    if not rows:
        summary = f"近 {minutes} 分钟没有新弹幕，建议先确认采集器是否在线，或主动抛话题拉互动。"
    else:
        hot = by_intent[0] if by_intent else {"intent": "闲聊互动", "count": len(rows)}
        summary = (f"近 {minutes} 分钟共 {len(rows)} 条弹幕，最集中的是「{hot['intent']}」（{hot['count']} 条）；"
                   f"负面/售后 {negative_count} 条。")
        if negative_count:
            summary += " 建议优先处理投诉与售后，避免影响直播间氛围。"

    return {
        "session_id": session_id,
        "minutes": minutes,
        "total": len(rows),
        "summary": summary,
        "by_intent": by_intent,
        "keywords": top_keywords,
        "negative": {"count": negative_count, "samples": negative_samples},
        "timeline": timeline,
    }
