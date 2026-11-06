import asyncio
import json
import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.redis_client import get_sync_redis
from app.models.all import Danmaku, AgentAction, MonitorEvent
from app.schemas.all import DanmakuIn, DanmakuOut, AgentActionOut, MonitorEventOut
from app.agent.graph import run_single

router = APIRouter()


@router.post("/{session_id}/danmaku", response_model=DanmakuOut)
def post_danmaku(session_id: int, payload: DanmakuIn, db: Session = Depends(get_db)):
    dm = Danmaku(
        session_id=session_id,
        user_id=payload.user_id,
        nickname=payload.nickname,
        content=payload.content,
    )
    db.add(dm)
    db.commit()
    db.refresh(dm)

    # XADD 到 Redis Stream
    try:
        r = get_sync_redis()
        r.xadd(
            f"danmaku:{session_id}",
            {
                "msg_id": str(dm.msg_id),
                "nickname": dm.nickname or "",
                "content": dm.content or "",
                "intent": dm.intent or "",
                "ts": dm.created_at.isoformat() if dm.created_at else datetime.utcnow().isoformat(),
            },
            maxlen=1000,
        )
    except Exception:
        # Redis 挂了不阻塞流程
        pass

    return DanmakuOut.model_validate(dm)


@router.get("/{session_id}/danmaku", response_model=list[DanmakuOut])
def list_danmaku(
    session_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(Danmaku).where(Danmaku.session_id == session_id)
        .order_by(Danmaku.msg_id.desc())
        .offset((page - 1) * size).limit(size)
    ).all()
    return [DanmakuOut.model_validate(r) for r in rows]


@router.get("/{session_id}/agent-actions", response_model=list[AgentActionOut])
def list_agent_actions(
    session_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(AgentAction).where(AgentAction.session_id == session_id)
        .order_by(AgentAction.action_id.desc())
        .offset((page - 1) * size).limit(size)
    ).all()
    return [AgentActionOut.model_validate(r) for r in rows]


@router.get("/{session_id}/monitor-events", response_model=list[MonitorEventOut])
def list_monitor_events(
    session_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(MonitorEvent).where(MonitorEvent.session_id == session_id)
        .order_by(MonitorEvent.event_id.desc())
        .offset((page - 1) * size).limit(size)
    ).all()
    return [MonitorEventOut.model_validate(r) for r in rows]


@router.post("/{session_id}/danmaku/{msg_id}/manual-reply", response_model=DanmakuOut)
def manual_reply(session_id: int, msg_id: int, payload: DanmakuIn,
                 db: Session = Depends(get_db)):
    """主播人工接管：原弹幕标记为 HUMAN，并写入一条主播回复弹幕"""
    dm = db.scalar(
        select(Danmaku).where(Danmaku.msg_id == msg_id, Danmaku.session_id == session_id)
    )
    if not dm:
        raise HTTPException(status_code=404, detail="danmaku not found")

    dm.handled_by = "HUMAN"
    reply = Danmaku(
        session_id=session_id,
        nickname="主播",
        content=payload.content,
        intent="manual_reply",
        priority=3,
        handled_by="HUMAN",
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return DanmakuOut.model_validate(reply)


class AgentReplyReq(DanmakuIn):
    pass


@router.post("/agent/reply")
def agent_reply(
    msg_id: int,
    force_model: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    dm = db.scalar(select(Danmaku).where(Danmaku.msg_id == msg_id))
    if not dm:
        raise HTTPException(status_code=404, detail="danmaku not found")
    state = run_single(dm.session_id, dm.msg_id, dm.content)
    action = db.scalars(
        select(AgentAction).where(AgentAction.msg_id == dm.msg_id)
        .order_by(AgentAction.action_id.desc())
    ).first()
    return AgentActionOut.model_validate(action) if action else {"msg_id": dm.msg_id, "intent": state["intent"], "reply": state["reply"]}


@router.post("/{session_id}/agent/trigger")
def trigger_agent(
    session_id: int,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """主播直播间「AI 处理弹幕」：对最近未处理的弹幕批量跑一遍 Agent 链路。

    优先取尚未被 AI 处理（handled_by 为空 / PENDING）的弹幕；若都处理过了，
    则回放最近几条，便于演示时反复点击也能看到效果。
    """
    pending = db.scalars(
        select(Danmaku).where(
            Danmaku.session_id == session_id,
            (Danmaku.handled_by.is_(None)) | (Danmaku.handled_by == "PENDING"),
        ).order_by(Danmaku.msg_id.desc()).limit(limit)
    ).all()

    fallback = False
    if not pending:
        pending = db.scalars(
            select(Danmaku).where(Danmaku.session_id == session_id)
            .order_by(Danmaku.msg_id.desc()).limit(min(limit, 3))
        ).all()
        fallback = True

    results = []
    for dm in reversed(pending):
        try:
            st = run_single(session_id, dm.msg_id, dm.content or "")
            results.append({
                "msg_id": dm.msg_id,
                "nickname": dm.nickname,
                "content": dm.content,
                "intent": st.get("intent"),
                "reply": st.get("reply"),
            })
        except Exception as e:  # 单条失败不影响整体
            results.append({
                "msg_id": dm.msg_id,
                "nickname": dm.nickname,
                "content": dm.content,
                "error": str(e),
            })

    return {
        "session_id": session_id,
        "processed": len(results),
        "is_replay": fallback,
        "results": results,
    }


# ---------- WS ----------
@router.websocket("/{session_id}/stream")
async def stream_ws(websocket: WebSocket, session_id: int):
    await websocket.accept()
    last_msg_id = 0
    last_action_id = 0
    last_event_id = 0

    from app.core.database import SessionLocal
    try:
        while True:
            db = SessionLocal()
            try:
                # new danmaku
                dms = db.scalars(
                    select(Danmaku).where(
                        Danmaku.session_id == session_id,
                        Danmaku.msg_id > last_msg_id,
                    ).order_by(Danmaku.msg_id.asc())
                ).all()
                for dm in dms:
                    await websocket.send_text(json.dumps({
                        "type": "danmaku",
                        "data": DanmakuOut.model_validate(dm).model_dump(mode="json"),
                    }, ensure_ascii=False, default=str))
                if dms:
                    last_msg_id = dms[-1].msg_id

                # new agent_action
                actions = db.scalars(
                    select(AgentAction).where(
                        AgentAction.session_id == session_id,
                        AgentAction.action_id > last_action_id,
                    ).order_by(AgentAction.action_id.asc())
                ).all()
                for a in actions:
                    await websocket.send_text(json.dumps({
                        "type": "agent_action",
                        "data": AgentActionOut.model_validate(a).model_dump(mode="json"),
                    }, ensure_ascii=False, default=str))
                if actions:
                    last_action_id = actions[-1].action_id

                # new monitor_event
                events = db.scalars(
                    select(MonitorEvent).where(
                        MonitorEvent.session_id == session_id,
                        MonitorEvent.event_id > last_event_id,
                    ).order_by(MonitorEvent.event_id.asc())
                ).all()
                for e in events:
                    await websocket.send_text(json.dumps({
                        "type": "monitor_event",
                        "data": MonitorEventOut.model_validate(e).model_dump(mode="json"),
                    }, ensure_ascii=False, default=str))
                if events:
                    last_event_id = events[-1].event_id

            finally:
                db.close()

            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.close()
        except Exception:
            pass


# ---------- SSE 降级 ----------
@router.get("/{session_id}/stream/sse")
async def stream_sse(session_id: int):
    async def gen():
        last_msg_id = 0
        last_action_id = 0
        last_event_id = 0
        from app.core.database import SessionLocal
        while True:
            await asyncio.sleep(1)
            db = SessionLocal()
            try:
                dms = db.scalars(
                    select(Danmaku).where(
                        Danmaku.session_id == session_id,
                        Danmaku.msg_id > last_msg_id,
                    ).order_by(Danmaku.msg_id.asc())
                ).all()
                for dm in dms:
                    payload = json.dumps({
                        "type": "danmaku",
                        "data": DanmakuOut.model_validate(dm).model_dump(mode="json"),
                    }, ensure_ascii=False, default=str)
                    yield f"event: danmaku\ndata: {payload}\n\n"
                if dms:
                    last_msg_id = dms[-1].msg_id

                actions = db.scalars(
                    select(AgentAction).where(
                        AgentAction.session_id == session_id,
                        AgentAction.action_id > last_action_id,
                    ).order_by(AgentAction.action_id.asc())
                ).all()
                for a in actions:
                    payload = json.dumps({
                        "type": "agent_action",
                        "data": AgentActionOut.model_validate(a).model_dump(mode="json"),
                    }, ensure_ascii=False, default=str)
                    yield f"event: agent_action\ndata: {payload}\n\n"
                if actions:
                    last_action_id = actions[-1].action_id

                events = db.scalars(
                    select(MonitorEvent).where(
                        MonitorEvent.session_id == session_id,
                        MonitorEvent.event_id > last_event_id,
                    ).order_by(MonitorEvent.event_id.asc())
                ).all()
                for e in events:
                    payload = json.dumps({
                        "type": "monitor_event",
                        "data": MonitorEventOut.model_validate(e).model_dump(mode="json"),
                    }, ensure_ascii=False, default=str)
                    yield f"event: monitor_event\ndata: {payload}\n\n"
                if events:
                    last_event_id = events[-1].event_id
            finally:
                db.close()

    return StreamingResponse(gen(), media_type="text/event-stream")
