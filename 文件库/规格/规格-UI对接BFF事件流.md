# 规格-UI 对接 BFF 事件流（v0.1）
## 1. REST 契约
- POST /api/gpt/proposals:from-intent → {proposal?|gaps?}
- POST /api/proposals → {id,state,trace_id}
- POST /api/proposals/{id}/validate → {status:"valid"|"rejected",reasons?}
- POST /api/proposals/{id}/approve → {status,trace_id}
- POST /api/proposals/{id}/execute?mode=dry → ExecutionResult
- GET  /api/positions | /api/trades?limit=&from= | /api/health

## 2. WS 事件（/ws/events）
proposal.created | proposal.validated | risk.rejected |
approval.requested | approval.granted | approval.rejected |
execution.started | execution.done

## 3. 组件契约
- 提案卡片（Proposal）：展示 symbol/side/size/entry/tp/sl/tif/valid_until/rationale/risks/tags
- 审批对话框：step ∈ {"dry-1","dry-2","live-1","live-2","live-3"}，decision ∈ {"approved","rejected"}, reason?
- 审计时间线：按 trace_id 聚合，按 ts 升序渲染事件

## 4. 流程（关键路径）
意图→from-intent 得 proposal→创建→validate（可被拒绝）→dry-1→dry-2→execute(dry)→回执；事件流同步更新。

## 5. 错误码与边界
- PROPOSAL_SCHEMA_INVALID / APPROVAL_REQUIRED / PERMISSION_DENIED
- 断线：WS 指南采用指数退避重连，支持 last_event_id 增量回放（后续扩展）
## 6. A11y
- 键盘可达；对话框焦点管理；AA 对比度；错误可读中文文案
## 7. 验收（DoD）
- 通过 REST/WS 完成“查看→提案→审批→干跑→时间线回放”的演示；事件顺序正确
