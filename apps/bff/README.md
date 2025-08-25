# BFF Mock 实施清单（v0.1）

目标：提供最小可运行的 Mock 接口与事件流，**不触达实盘**，支撑 M2→M3 干跑闭环。
对齐文档：文件库/规格/规格-M2最小Mock与联调.md、规格-风控与审批.md、规格-GPT集成（结构化提案）.md

## 路由（FastAPI 推荐）
- POST /gpt/proposals:from-intent → 返回 proposal 或 gaps（本地 schema 校验）
- POST /proposals → 生成 {id, state, trace_id} 并发 WS: proposal.created
- POST /proposals/{id}/validate → 风控检查，valid/rejected（WS: risk.rejected）
- POST /proposals/{id}/approve → 干跑 dry-1/dry-2 / 实盘 1/2/3（WS: approval.*）
- POST /proposals/{id}/execute?mode=dry → 生成干跑 ExecutionResult（WS: execution.*）
- GET /positions | /trades | /health
- /ws/events → 广播上述事件（内存队列，带 last_event_id）

## 数据与状态
- 内存存储：proposals/approvals/executions/audits
- 生成 trace_id：UUIDv4；所有写操作必须写 AuditEvent

## 风控规则（Mock）
- size>0.5、黑名单、非 08:00–22:00(UTC+8)、drawdown<-10% → RISK_REJECTED

## 日志与指标
- 每个路由 log：{trace_id, action, object, result, ts}
- 指标：请求 p95、事件发送速率、队列深度

## 验收
- 通过 文件库/测试/测试-干跑闭环与事件.md 的 12 条用例
- /health 全绿；/ws/events 稳定
