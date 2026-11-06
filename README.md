# 连锁门店直播运营平台

业务中台 + 实时场控 Agent 的全栈项目。门店/商品/直播/券/订单/销售看板主链路 + 弹幕削峰 → 意图路由 → AI 自动处理/转人工的场控 Agent + 并行监控线（人数/库存/转化自动响应）。

---

## 快速启动

```powershell
cd liveops                       # 进入解压后的项目根目录
Copy-Item .env.example .env      # 可选：填 LLM_API_KEY（无 Key 自动降级 jieba 规则分类）
docker compose --profile ui up -d --build
```

启动后：
- 前端：http://localhost
- 后端健康：http://localhost/api/health
- 后端就绪：http://localhost/api/health/ready
- Prometheus 指标：http://localhost/api/metrics

默认账号（密码均为 `123456`）：
| 用户名 | 角色 |
|--------|------|
| admin1 | ADMIN 管理员 |
| op1 ~ op12 | OPERATOR 场控坐席 |
| host1 ~ host12 | HOST 主播 |
| customer1 ~ customer5 | CUSTOMER 顾客 |

启动 Milvus 向量库（RAG 增强，可选）：
```powershell
docker compose --profile tools up -d
```

启动弹幕回放（驱动 Agent 演示）：
```powershell
docker compose --profile replay up -d
```

---

## 架构

```
弹幕流入 → Redis Streams 削峰/背压 → Supervisor 意图分类(小模型/jieba降级)
  ├ FAQ  → RAG/商品库自动回复
  ├ COUPON → 发券工具(超预算转HITL)
  ├ STOCK → 查库存实时回复
  ├ HUMAN → 转人工待办
  └ FILTER → 静默过滤
并行监控线(APScheduler 30s): viewer_drop / stock_alert / low_conversion / peak_focus
```

- MySQL 8：门店/商品/直播/券/订单/弹幕/agent_action/monitor_event
- Redis 7：弹幕队列削峰 + 缓存/限流
- PostgreSQL 16：Agent 记忆/决策/审计（已部署，当前版本 Agent 数据与业务统一存 MySQL，可配置切换）
- Milvus + etcd + MinIO：知识库向量检索（profile tools，可选）

---

## API 接口

前缀 `/api/v1`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/stores` | 门店列表（城市/状态/分页） |
| GET/POST/PUT | `/stores/{id}` | 门店详情/增改 |
| GET | `/products` | 商品列表（分类/搜索/排序/分页） |
| GET | `/products/{id}` | 商品详情（含 SKU/库存） |
| GET | `/products/categories` | 分类树 |
| GET/POST | `/live-sessions` | 直播场次列表/创建 |
| PUT | `/live-sessions/{id}/status` | 开播/结束状态流转 |
| GET | `/live-sessions/{id}/dashboard` | 场次实时看板 |
| GET/POST | `/coupons` | 优惠券配置 |
| GET | `/orders` `/orders/{id}` | 订单列表/详情 |
| POST | `/orders/{id}/pay` | 模拟支付 |
| GET | `/dashboard/sales` | 销售看板（异常门店高亮） |
| POST | `/auth/register` `/auth/login` | 认证 |
| POST | `/live/{session_id}/danmaku` | 投递弹幕 |
| WS | `/live/{session_id}/stream` | 实时弹幕流+Agent决策推送 |
| GET | `/live/{session_id}/agent-actions` | Agent 决策日志 |
| GET | `/live/{session_id}/monitor-events` | 监控事件 |
| GET | `/operator/tickets` | 人工待办队列（OPERATOR） |
| POST | `/operator/tickets/{msg_id}/claim/resolve/close` | 领取/处置/关闭 |

---

## 直播场控 Agent 演示脚本

### 场景 1：弹幕自动分流全链路

1. 用 `admin1` 登录，进入「直播场次」→ 找到 living 场次 →「进入场控」
2. 启动弹幕回放（或手动发弹幕）：
   ```powershell
   docker compose --profile replay up -d
   ```
3. 场控页中栏实时显示弹幕，每条标注意图 tag（咨询/要券/库存/转人工/垃圾）
4. 右栏滚动 Agent 决策日志：`intent_classify → send_danmaku_reply / issue_coupon / query_stock / create_human_ticket`

### 场景 2：自动发券 + 预算护栏转人工

1. 弹幕输入「有没有优惠券」→ Agent 自动调 `issue_coupon` 发券
2. 当本场发券累计成本超 `COUPON_DAILY_BUDGET`（默认 5000）→ 强制转人工待办
3. 用 `op1` 登录 →「坐席工作台」→ 领取待办 → 处置 → 关闭

### 场景 3：并行监控线自动响应

种子数据预置了 2 场 living：
- session 1（美妆场）：主推 SKU 库存仅剩 8 → 触发 `stock_alert` 监控事件
- session 2（家居场）：转化率 0.02 → 触发 `low_conversion` → Agent 自动发券促转化

监控线每 30s 巡检，事件实时推送到场控页右栏。

### 场景 4：恶意刷屏静默过滤

弹幕输入广告内容（含「加微信」「扫码」等关键词）→ 意图分类为 `spam` → `FILTER` 静默，前端不显示回复，`handled_by=FILTERED`。

### 场景 5：投诉/退换货转人工

弹幕输入「我要退货」「你们这是假货」→ `aftersale`/`complaint` → `HUMAN` → 生成坐席待办，弹幕回复「已转人工处理」。

---

## 降级说明

无 `LLM_API_KEY` 时：
- 意图分类走 jieba 关键词规则（`intent.classify`）
- FAQ 回复走商品库静态模板
- 主链路完全可演示，仅无 LLM 智能感

Milvus 未启动时：
- RAG 检索跳过，FAQ 返回商品描述
- 不影响其他功能
