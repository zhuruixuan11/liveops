import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.deps import gen_request_id, request_id_var
from app.core.config import get_settings
from app.api.routes import (
    auth, stores, products, live_sessions, coupons, orders, sales, danmaku,
    health, analytics, assistant, pacing, ingest,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 外部平台接入表（老库自动补建）
    from app.integrations.sync import ensure_tables
    ensure_tables()
    # 启动场控消费者（后台）
    from app.agent.danmaku_consumer import run_all_consumers
    consumer_task = asyncio.create_task(run_all_consumers())
    # 启动监控线（APScheduler sync，放进线程池）
    from app.monitor.scheduler import start_scheduler
    sched = start_scheduler()
    try:
        yield
    finally:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        except Exception:
            pass
        try:
            sched.shutdown(wait=False)
        except Exception:
            pass


def create_app() -> FastAPI:
    app = FastAPI(
        title="连锁门店直播运营平台 API",
        version="1.0.0",
        description="门店直播运营中台 + 实时场控 Agent",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_id(request: FastAPI, call_next):
        rid = request.headers.get("X-Request-ID") or gen_request_id()
        request_id_var.set(rid)
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response

    @app.exception_handler(Exception)
    async def global_exc(request: FastAPI, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"code": 500, "detail": str(exc), "request_id": request_id_var.get()},
        )

    api_prefix = "/api/v1"
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(auth.router, prefix=f"{api_prefix}/auth", tags=["auth"])
    app.include_router(stores.router, prefix=f"{api_prefix}/stores", tags=["stores"])
    app.include_router(products.router, prefix=f"{api_prefix}", tags=["products"])
    app.include_router(live_sessions.router, prefix=f"{api_prefix}/live-sessions", tags=["live-sessions"])
    app.include_router(coupons.router, prefix=f"{api_prefix}/coupons", tags=["coupons"])
    app.include_router(orders.router, prefix=f"{api_prefix}/orders", tags=["orders"])
    app.include_router(sales.router, prefix=f"{api_prefix}/dashboard", tags=["sales"])
    app.include_router(danmaku.router, prefix=f"{api_prefix}/live", tags=["danmaku"])
    app.include_router(analytics.router, prefix=f"{api_prefix}/analytics", tags=["analytics"])
    app.include_router(assistant.router, prefix=f"{api_prefix}/assistant", tags=["assistant"])
    app.include_router(pacing.router, prefix=f"{api_prefix}/pacing", tags=["pacing"])
    app.include_router(ingest.router, prefix=f"{api_prefix}/ingest", tags=["ingest"])

    return app
