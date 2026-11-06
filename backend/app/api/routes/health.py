from fastapi import APIRouter
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import text

from app.core.database import engine
from app.core.redis_client import get_sync_redis

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "service": "liveops-backend"}


@router.get("/health/ready")
def ready():
    errors = {}

    # MySQL ping
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        errors["mysql"] = str(exc)

    # Redis ping
    try:
        r = get_sync_redis()
        r.ping()
    except Exception as exc:
        errors["redis"] = str(exc)

    if errors:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "errors": errors})
    return {"status": "ready"}


@router.get("/metrics", response_class=PlainTextResponse)
def metrics():
    """Prometheus 格式指标：弹幕吞吐、意图分布、自动处理率、转人工率、库存告警。"""
    from sqlalchemy import func
    from app.models.all import Danmaku, AgentAction, MonitorEvent
    from app.core.database import SessionLocal

    lines = []
    try:
        with SessionLocal() as db:
            total = db.query(func.count(Danmaku.msg_id)).scalar() or 0
            ai_count = db.query(func.count(Danmaku.msg_id)).filter(Danmaku.handled_by == "AI").scalar() or 0
            human_count = db.query(func.count(Danmaku.msg_id)).filter(Danmaku.handled_by.in_(["HUMAN", "PENDING"])).scalar() or 0
            filtered = db.query(func.count(Danmaku.msg_id)).filter(Danmaku.handled_by == "FILTERED").scalar() or 0
            actions = db.query(func.count(AgentAction.action_id)).scalar() or 0
            stock_alerts = db.query(func.count(MonitorEvent.event_id)).filter(MonitorEvent.event_type == "stock_alert").scalar() or 0

            intent_counts = dict(db.query(Danmaku.intent, func.count(Danmaku.msg_id)).filter(Danmaku.intent.isnot(None)).group_by(Danmaku.intent).all())

        auto_rate = round(ai_count / total, 4) if total else 0.0
        human_rate = round(human_count / total, 4) if total else 0.0

        lines.append("# HELP danmaku_total Total danmaku messages received")
        lines.append("# TYPE danmaku_total counter")
        lines.append(f"danmaku_total {total}")
        lines.append("# HELP danmaku_handled_by_ai Danmaku handled by AI automatically")
        lines.append("# TYPE danmaku_handled_by_ai counter")
        lines.append(f"danmaku_handled_by_ai {ai_count}")
        lines.append("# HELP danmaku_handled_by_human Danmaku escalated to human")
        lines.append("# TYPE danmaku_handled_by_human counter")
        lines.append(f"danmaku_handled_by_human {human_count}")
        lines.append("# HELP danmaku_filtered Spam/filtered danmaku")
        lines.append("# TYPE danmaku_filtered counter")
        lines.append(f"danmaku_filtered {filtered}")
        lines.append("# HELP agent_action_total Total agent tool actions")
        lines.append("# TYPE agent_action_total counter")
        lines.append(f"agent_action_total {actions}")
        lines.append("# HELP auto_handling_rate AI auto-handling rate (0-1)")
        lines.append("# TYPE auto_handling_rate gauge")
        lines.append(f"auto_handling_rate {auto_rate}")
        lines.append("# HELP human_escalation_rate Human escalation rate (0-1)")
        lines.append("# TYPE human_escalation_rate gauge")
        lines.append(f"human_escalation_rate {human_rate}")
        lines.append("# HELP stock_alert_total Stock alert monitor events")
        lines.append("# TYPE stock_alert_total counter")
        lines.append(f"stock_alert_total {stock_alerts}")

        lines.append("# HELP danmaku_by_intent Danmaku count grouped by intent")
        lines.append("# TYPE danmaku_by_intent counter")
        for intent, cnt in intent_counts.items():
            lines.append(f'danmaku_by_intent{{intent="{intent}"}} {cnt}')
    except Exception as exc:
        lines.append(f"# ERROR: {exc}")

    return "\n".join(lines) + "\n"
