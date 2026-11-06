"""并行场控监控线：每 30s 巡检 living 场次，触发 monitor_event + Agent 主动响应。"""
import random
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select, func

from app.core.database import SessionLocal
from app.core.config import get_settings
from app.agent.classifier import classify_by_rules
from app.agent.graph import run_single
from app.models.all import (
    LiveSession, SkuInfo, LiveProduct, MonitorEvent, SalesOrder, Coupon,
    CouponIssue, Danmaku,
)
from app.tools.live_tools import issue_coupon, set_focus_product, _record

settings = get_settings()

VIEWER_DROP_THRESHOLD = 0.4      # 较 1 分钟前降 40%
STOCK_ALERT_PERCENT = 0.2        # 主推 SKU 库存低于 20%
LOW_CONVERSION = 0.05            # 转化率低于 5%
PEAK_FOCUS_RATIO = 0.9           # 当前达峰值 90% 以上

# 演示弹幕池：真实观众会说的话，按 intent 分类便于触发不同 Agent 路由
DEMO_DANMAKU_POOL = [
    ("柠檬不萌", "这个价格比专柜便宜好多啊"),
    ("小樱桃", "主播声音好好听"),
    ("购物车党", "购物车一号链接就是主推对吧"),
    ("夏日冰美式", "有没有优惠券可以发"),
    ("糖糖", "色号会显黑吗？"),
    ("小鱼干", "物流多久能到啊"),
    ("心动女孩", "库存还有多少啊，怕抢不到"),
    ("阿May", "这个品之前用过，真的好用"),
    ("匿名用户", "666666"),
    ("新人报到", "新人能领券吗"),
    ("好奇宝宝", "有没有试用装"),
    ("忠实粉丝", "主播今天状态好好"),
    ("秒付款", "我刚下单了一号链接"),
    ("回购王", "回购第三次了，真的好用"),
    ("爱占便宜", "能送个赠品吗"),
    ("纠结党", "一号和二号有啥区别"),
    ("爽快姐", "直接拍了，听主播讲完就想下单"),
    ("理性党", "成分党求解释一下功效"),
    ("老顾客", "上次买的还没用完，又来囤"),
    ("新粉", "第一次来，主播多介绍一下自己"),
]


_last_viewer_count: dict[int, int] = {}
_last_alert_at: dict[tuple[int, str], datetime] = {}
ALERT_COOLDOWN_SECONDS = 600   # 同类告警 10 分钟内只记录一次，避免每 30s 重复刷屏
_last_demo_inject: dict[int, datetime] = {}
DEMO_INJECT_INTERVAL_SECONDS = 20  # 每个 living 场次最小注入间隔


def _record_monitor(session_id, event_type, metric_value, threshold, response):
    key = (session_id, event_type)
    now = datetime.now()
    last = _last_alert_at.get(key)
    if last and (now - last).total_seconds() < ALERT_COOLDOWN_SECONDS:
        return
    _last_alert_at[key] = now
    with SessionLocal() as db:
        db.add(MonitorEvent(
            session_id=session_id, event_type=event_type,
            metric_value=metric_value, threshold=threshold,
            agent_response=response, status="notified",
        ))
        db.commit()


def check_sessions():
    with SessionLocal() as db:
        living = db.execute(select(LiveSession).where(LiveSession.status == "living")).scalars().all()
        for s in living:
            # 1) viewer_drop
            prev = _last_viewer_count.get(s.session_id)
            if prev and prev > 0 and (prev - s.viewer_count) / prev > VIEWER_DROP_THRESHOLD:
                _record_monitor(
                    s.session_id, "viewer_drop",
                    metric_value=s.viewer_count, threshold=int(prev * (1 - VIEWER_DROP_THRESHOLD)),
                    response=f"在线人数从 {prev} 降到 {s.viewer_count}，建议主播切下一个品或发券拉停留",
                )
            _last_viewer_count[s.session_id] = s.viewer_count

            # 2) peak_focus
            if s.peak_viewer > 0 and s.viewer_count >= int(s.peak_viewer * PEAK_FOCUS_RATIO):
                _record_monitor(
                    s.session_id, "peak_focus",
                    metric_value=s.viewer_count, threshold=int(s.peak_viewer * PEAK_FOCUS_RATIO),
                    response="峰值接近，建议推高客单商品或上限定款",
                )

            # 3) stock_alert
            focus = db.execute(select(LiveProduct).where(
                LiveProduct.session_id == s.session_id, LiveProduct.is_focus == 1
            )).scalar_one_or_none()
            if focus and focus.sku_id:
                sku = db.get(SkuInfo, focus.sku_id)
                if sku and sku.stock < max(20, 100 * STOCK_ALERT_PERCENT):
                    _record_monitor(
                        s.session_id, "stock_alert",
                        metric_value=sku.stock, threshold=20,
                        response=f"{sku.sku_code} 库存仅剩 {sku.stock}，建议主播提醒加库存或切品",
                    )

            # 4) low_conversion
            orders = db.execute(select(func.count(SalesOrder.order_id)).where(
                SalesOrder.session_id == s.session_id,
                SalesOrder.status.in_(["01", "02"]),
            )).scalar() or 0
            conv = orders / max(s.viewer_count, 1) if s.viewer_count else 0
            if conv < LOW_CONVERSION and s.viewer_count >= 10:
                # 自动发券（预算内）
                coupon = db.execute(select(Coupon).where(
                    Coupon.session_id == s.session_id, Coupon.stock > Coupon.issued
                ).order_by(Coupon.discount.asc())).scalars().first()
                agent_reply = "未触发自动发券"
                if coupon:
                    res = issue_coupon(s.session_id, coupon.coupon_id, float(coupon.discount),
                                      issued_by="AGENT")
                    agent_reply = f"转化率 {conv:.2%}，自动发券：{res}"
                _record_monitor(
                    s.session_id, "low_conversion",
                    metric_value=conv, threshold=LOW_CONVERSION,
                    response=agent_reply,
                )


def demo_inject_danmaku():
    """演示弹幕注入：living 场次每 20~45s 自动塞一条真实观众弹幕，走完整 Agent 链路。"""
    if not settings.demo_mode:
        return
    now = datetime.now()
    with SessionLocal() as db:
        living = db.execute(select(LiveSession).where(LiveSession.status == "living")).scalars().all()
    for s in living:
        last = _last_demo_inject.get(s.session_id)
        if last and (now - last).total_seconds() < DEMO_INJECT_INTERVAL_SECONDS + random.randint(0, 25):
            continue
        _last_demo_inject[s.session_id] = now
        # 间隔太久或首次启动时一次塞 2 条，让弹幕流密集
        batch = 2 if (last is None or (now - last).total_seconds() > 90) else 1
        for _ in range(batch):
            nickname, content = random.choice(DEMO_DANMAKU_POOL)
            with SessionLocal() as db:
                dm = Danmaku(
                    session_id=s.session_id,
                    nickname=nickname,
                    content=content,
                    intent="general",
                    priority=3,
                    handled_by="PENDING",
                )
                db.add(dm)
                db.commit()
                db.refresh(dm)
                mid = dm.msg_id
            # 同步跑完整 Agent 链路 → send_danmaku_reply 同时产出 AI 回复弹幕
            try:
                run_single(s.session_id, mid, content)
            except Exception:
                pass


def start_scheduler() -> BackgroundScheduler:
    sched = BackgroundScheduler(timezone="Asia/Shanghai")
    sched.add_job(check_sessions, "interval", seconds=30, id="monitor-check")
    if settings.demo_mode:
        sched.add_job(demo_inject_danmaku, "interval", seconds=15, id="demo-inject")
    sched.start()
    return sched
