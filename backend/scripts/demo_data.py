"""
一键填充演示数据：直播场次 / 弹幕 / Agent 决策 / 监控事件 / 订单 / 优惠券领取
用法: docker exec liveops-backend python -m scripts.demo_data
可重复执行：已有足够数据的场次会自动跳过。
"""
import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, func, delete

from app.core.database import SessionLocal
from app.models.all import (
    LiveSession, LiveProduct, Danmaku, AgentAction, MonitorEvent,
    SalesOrder, SalesOrderDetail, Coupon, CouponIssue, SkuInfo, Product, Staff,
)

random.seed(2026)

# ---------------- 演示语料 ----------------
DANMAKU_POOL = {
    "faq_product": [
        "这个适合敏感肌吗？", "成分里有酒精吗？", "和专柜版是同一个配方吗？",
        "油皮可以用吗？", "孕妇能用吗？", "保质期到什么时候？",
    ],
    "ask_price": [
        "多少钱？", "今天直播价多少？", "比店里便宜多少？", "还能再便宜点吗？",
        "平日价多少？", "这个价格是限时吗？",
    ],
    "ask_coupon": [
        "有没有优惠券？", "券怎么领？", "满300减多少？", "刚才那个券还有吗？",
        "新人有券吗？", "领了券怎么用？",
    ],
    "ask_stock": [
        "还有货吗？", "库存还剩多少？", "小码还有吗？", "白色还有吗？",
        "补货大概什么时候？", "拍多了能改地址吗？",
    ],
    "logistics": [
        "发什么快递？", "多久能到？", "能发新疆吗？", "今天拍今天发吗？",
        "能到付吗？", "包装严实吗，怕碎。",
    ],
    "aftersale": [
        "之前买的想换货怎么弄？", "用了过敏可以退吗？", "收到货有瑕疵找谁？",
        "七天无理由吗？",
    ],
    "complaint": [
        "上次买的用了过敏！", "客服怎么一直不回复？", "物流太慢了吧，一周了。",
    ],
    "spam": [
        "加我微信买同款更便宜", "【刷屏广告】某某网赚项目日入过千",
    ],
    "general": [
        "主播好美！", "刚来，在讲什么？", "666", "音乐不错哦", "扣1上车",
        "已拍，坐等发货～", "这家店线下去过，服务不错", "姐姐口红色号求链接",
        "蹲一个破壁机讲解", "家人们冲！",
    ],
}

INTENT_REPLY = {
    "faq_product": "已为您查询商品详情并发送讲解卡",
    "ask_price": "已推送直播间专属价说明",
    "ask_coupon": "已自动发放优惠券",
    "ask_stock": "已查询实时库存并回复",
    "logistics": "已转接人工客服跟进",
    "aftersale": "已生成售后工单并转人工",
    "complaint": "已转接人工客服优先处理",
    "spam": "已过滤该条弹幕",
    "general": "已回复欢迎语",
}

NICKNAMES = [
    "小红薯宝贝", "爱美的莉莉", "阿杰", "NJ_晓晓", "糖糖妈", "打工人小王",
    "mengmeng", "山茶花开", "Vicky酱", "老张头", "南音", "榴莲不甜",
    "一半海水", "早睡冠军", "奶茶三分糖", "Kiko", "慢慢来", "不吃香菜",
]

TOOL_BY_INTENT = {
    "faq_product": ("faq_search", "FAQ"),
    "ask_price": ("query_price", "FAQ"),
    "faq_policy": ("faq_search", "FAQ"),
    "ask_coupon": ("issue_coupon", "COUPON"),
    "ask_stock": ("query_stock", "STOCK"),
    "logistics": ("create_human_ticket", "HUMAN"),
    "aftersale": ("create_human_ticket", "HUMAN"),
    "complaint": ("create_human_ticket", "HUMAN"),
    "spam": ("filter_spam", "FILTER"),
    "general": ("send_danmaku_reply", "FAQ"),
}

MONITOR_TEMPLATES = [
    ("viewer_drop", "5分钟掉线率 {v}%，超阈值 15%", Decimal("18.40"), Decimal("15"), "已触发福袋抽奖拉留存，开播提醒老粉回归"),
    ("stock_alert", "主推商品库存仅剩 {v} 件", Decimal("8"), Decimal("10"), "已通知运营补货，主播口播改为预售模式"),
    ("low_conversion", "转化率仅 {v}%，低于同店均值", Decimal("1.20"), Decimal("3"), "已调整商品讲解顺序，插播爆款逼单"),
    ("peak_focus", "在线人数达峰值 {v}", Decimal("5280"), Decimal("5000"), "已自动投放优惠券冲量，并加大弹幕引导"),
]


def pick_danmaku_contents(n: int):
    """按真实直播间分布采样弹幕"""
    weights = [15, 15, 12, 12, 10, 8, 5, 3, 20]  # 对应 DANMAKU_POOL 顺序
    intents = list(DANMAKU_POOL.keys())
    out = []
    for _ in range(n):
        intent = random.choices(intents, weights=weights, k=1)[0]
        out.append((intent, random.choice(DANMAKU_POOL[intent])))
    return out


def ensure_session(db, store_id, host_id, title, status, hours_ago, viewer_base):
    s = LiveSession(
        store_id=store_id, host_id=host_id, title=title,
        start_time=datetime.utcnow() - timedelta(hours=hours_ago),
        status=status,
        viewer_count=viewer_base if status == "living" else 0,
        peak_viewer=int(viewer_base * 1.35) if status == "living" else 0,
    )
    db.add(s)
    db.flush()
    # 挂 4-6 个商品
    products = db.scalars(select(Product).order_by(Product.product_id).limit(8)).all()
    chosen = random.sample(products, k=min(6, len(products)))
    for i, p in enumerate(chosen):
        skus = db.scalars(select(SkuInfo).where(SkuInfo.product_id == p.product_id)).all()
        sku = random.choice(skus) if skus else None
        db.add(LiveProduct(
            session_id=s.session_id, product_id=p.product_id,
            sku_id=sku.sku_id if sku else None,
            explain_status=random.choice(["explained", "explaining", "pending"]),
            order_in_session=random.randint(0, 25) if status == "living" else 0,
            is_focus=1 if i == 0 else 0,
        ))
    db.flush()
    return s


def fill_danmaku_and_agent(db, s, n=45):
    exists = db.scalar(select(func.count()).select_from(Danmaku).where(Danmaku.session_id == s.session_id)) or 0
    if exists >= 15:
        print(f"  session {s.session_id}: 弹幕已有 {exists} 条，跳过")
        return
    base_time = datetime.utcnow() - timedelta(hours=1.5)
    rows = []
    for i, (intent, content) in enumerate(pick_danmaku_contents(n)):
        created = base_time + timedelta(seconds=i * random.randint(80, 160))
        rows.append((intent, content, created))
        db.add(Danmaku(
            session_id=s.session_id,
            nickname=random.choice(NICKNAMES),
            content=content,
            intent=intent,
            priority=1 if intent in ("complaint", "aftersale") else (2 if intent in ("ask_coupon", "ask_stock") else 3),
            handled_by="HUMAN" if intent in ("logistics", "aftersale", "complaint") else ("FILTERED" if intent == "spam" else "AI"),
            confidence=Decimal("0.75"),
            created_at=created,
        ))
    db.flush()

    # Agent 决策日志：取前 20 条生成
    dms = db.scalars(
        select(Danmaku).where(Danmaku.session_id == s.session_id).order_by(Danmaku.msg_id)
    ).all()[:20]
    for dm in dms:
        tool, _route = TOOL_BY_INTENT.get(dm.intent, ("send_danmaku_reply", "FAQ"))
        db.add(AgentAction(
            session_id=s.session_id, msg_id=dm.msg_id,
            tool_name=tool,
            tool_args={"content": dm.content, "intent": dm.intent},
            tool_result=INTENT_REPLY.get(dm.intent, "已回复"),
            decision_reason=f"规则分类命中 {dm.intent}，路由处理",
            latency_ms=random.randint(80, 900),
            model_used="rule+jieba",
            token_cost=random.randint(0, 60),
            created_at=dm.created_at + timedelta(seconds=random.randint(1, 5)),
        ))

    # 监控事件
    for etype, tpl, val, th, resp in random.sample(MONITOR_TEMPLATES, k=3):
        db.add(MonitorEvent(
            session_id=s.session_id, event_type=etype,
            metric_value=val, threshold=th,
            agent_response=resp,
            status=random.choice(["notified", "acted", "acted"]),
            created_at=datetime.utcnow() - timedelta(minutes=random.randint(3, 90)),
        ))
    print(f"  session {s.session_id}: 弹幕 {len(rows)} 条 + 决策 {min(20, len(dms))} 条 + 监控 3 条")


def fill_orders(db, s, n=15):
    exists = db.scalar(select(func.count()).select_from(SalesOrder).where(SalesOrder.session_id == s.session_id)) or 0
    if exists >= 8:
        print(f"  session {s.session_id}: 订单已有 {exists} 单，跳过")
        return
    lps = db.scalars(select(LiveProduct).where(LiveProduct.session_id == s.session_id)).all()
    if not lps:
        return
    coupons = db.scalars(select(Coupon).where(Coupon.session_id == s.session_id)).all()
    gmv = Decimal("0")
    made = 0
    for i in range(n):
        lp = random.choice(lps)
        if not lp.sku_id:
            continue
        sku = db.scalar(select(SkuInfo).where(SkuInfo.sku_id == lp.sku_id))
        product = db.scalar(select(Product).where(Product.product_id == lp.product_id))
        if not sku or not product:
            continue
        qty = random.choices([1, 2, 3], weights=[60, 28, 12], k=1)[0]
        subtotal = Decimal(sku.price) * qty
        discount = Decimal("0")
        coupon = random.choice(coupons) if coupons and random.random() < 0.35 else None
        if coupon and subtotal >= Decimal(coupon.threshold):
            if coupon.type == "discount":
                discount = Decimal(coupon.discount)
            elif coupon.type == "percent":
                discount = (subtotal * Decimal(coupon.discount)).quantize(Decimal("0.01"))
        pay = subtotal - discount
        created = datetime.utcnow() - timedelta(minutes=random.randint(2, 110))
        order_id = f"SO{created.strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}{i}"
        db.add(SalesOrder(
            order_id=order_id, session_id=s.session_id, store_id=s.store_id,
            user_id=random.randint(7, 11), coupon_id=coupon.coupon_id if coupon else None,
            total_amount=subtotal, pay_amount=pay, discount_amount=discount,
            status="02" if random.random() < 0.85 else "01",
            channel="LIVE", create_time=created,
            pay_time=created + timedelta(minutes=1),
        ))
        db.add(SalesOrderDetail(
            order_id=order_id, sku_id=sku.sku_id, product_name=product.product_name,
            spec=sku.spec, price=sku.price, qty=qty, subtotal=subtotal,
            coupon_applied=1 if coupon else 0,
        ))
        lp.order_in_session = (lp.order_in_session or 0) + qty
        gmv += pay
        made += 1
    if made:
        s.viewer_count = max(s.viewer_count or 0, random.randint(300, 900))
    print(f"  session {s.session_id}: 订单 {made} 单")


def fill_coupon_issues(db, s):
    coupons = db.scalars(select(Coupon).where(Coupon.session_id == s.session_id)).all()
    for c in coupons:
        have = db.scalar(select(func.count()).select_from(CouponIssue).where(CouponIssue.coupon_id == c.coupon_id)) or 0
        need = min((c.issued or 0), 30) - have
        for _ in range(max(0, need)):
            db.add(CouponIssue(
                coupon_id=c.coupon_id, session_id=s.session_id,
                user_id=random.randint(7, 11),
                issued_by=random.choice(["AGENT", "MANUAL"]),
                amount_cost=Decimal(c.discount) * Decimal("0.6"),
                create_time=datetime.utcnow() - timedelta(minutes=random.randint(1, 100)),
            ))
    print(f"  session {s.session_id}: 优惠券领取记录已补齐")


def clean_garbled(db):
    """清理历史测试产生的乱码弹幕（内容全是问号）"""
    dms = db.scalars(select(Danmaku)).all()
    bad = [d for d in dms if d.content and set(d.content) <= {"?", "？"}]
    for d in bad:
        db.delete(d)
    if bad:
        print(f"清理乱码弹幕 {len(bad)} 条")


def main():
    db = SessionLocal()
    try:
        clean_garbled(db)

        living = db.scalars(select(LiveSession).where(LiveSession.status == "living")).all()
        print(f"当前直播中场次: {[s.session_id for s in living]}")

        # 若只有不足 3 场在播，补 1 场
        if len(living) < 3:
            host = db.scalar(select(Staff).where(Staff.role == "HOST").order_by(Staff.staff_id))
            s = ensure_session(db, store_id=host.store_id or 3, host_id=host.staff_id,
                               title="【晚场福利】爆款返场宠粉节", status="living",
                               hours_ago=1, viewer_base=random.randint(600, 1500))
            db.flush()
            living.append(s)
            print(f"新增直播中场次 {s.session_id}: {s.title}")

        for s in living:
            print(f"填充 session {s.session_id} ...")
            fill_danmaku_and_agent(db, s)
            fill_orders(db, s)
            fill_coupon_issues(db, s)

        # 补 2 场待播 + 1 场已结束（若不足）
        planned_cnt = db.scalar(select(func.count()).select_from(LiveSession).where(LiveSession.status == "planned")) or 0
        if planned_cnt < 2:
            host = db.scalar(select(Staff).where(Staff.role == "HOST").order_by(Staff.staff_id.desc()))
            ensure_session(db, store_id=host.store_id or 1, host_id=host.staff_id,
                           title="【明日预告】秋冬新品首发专场", status="planned",
                           hours_ago=-20, viewer_base=0)
            print("新增待播场次 1 场")
        ended_cnt = db.scalar(select(func.count()).select_from(LiveSession).where(LiveSession.status == "ended")) or 0
        if ended_cnt < 1:
            host = db.scalar(select(Staff).where(Staff.role == "HOST").order_by(Staff.staff_id))
            s2 = ensure_session(db, store_id=host.store_id or 2, host_id=host.staff_id,
                                title="【回顾】早安美妆福利场", status="ended",
                                hours_ago=26, viewer_base=0)
            fill_orders(db, s2, n=10)
            print(f"新增已结束场次 {s2.session_id}")

        # 商品销量同步（演示观感）
        for p in db.scalars(select(Product)).all():
            if not p.sales_count:
                p.sales_count = random.randint(50, 900)

        db.commit()
        print("✅ 演示数据填充完成")
    except Exception as e:
        db.rollback()
        print(f"❌ 填充失败: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
