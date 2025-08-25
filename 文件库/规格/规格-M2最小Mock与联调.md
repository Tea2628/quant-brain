# 规格-M2 最小 Mock 与联调（v0.1 草案）

> 目标：在不触达实盘的前提下，用可控 Mock 跑通“查看→提案→风控→审批→干跑→审计回放”，为 M3 真接入做演练。

## 1. 范围
- 数据只读：持仓/订单/收益为 Mock；不连接交易所
- 仅结构化 Proposal：必须符合 schemas/proposal.schema.json
- 风控/审批：按《规格-风控与审批》执行（仓位/名单/时段/回撤；干跑 2 步、实盘 3 步）
- 执行：仅生成干跑回执 ExecutionResult；不下真实单
- 审计：全链路 AuditEvent，可按 TraceID 回放

## 2. Mock REST/WS 契约（/api, /ws/events）
- POST /gpt/proposals:from-intent → {proposal?|gaps?}
- POST /proposals → {id,state:"submitted",trace_id}
- POST /proposals/{id}/validate → {status:"valid"|"rejected",reasons?}
- POST /proposals/{id}/approve → {status,trace_id}
- POST /proposals/{id}/execute?mode=dry → {execution_id,status,tx_ref:null,trace_id}
- GET /positions | GET /trades?limit=&from= | GET /health
- WS 事件：proposal.created | risk.rejected | approval.requested | approval.granted | approval.rejected | execution.started | execution.done | audit.logged

## 3. 数据模型（最小字段）
Proposal{id?,symbol,side,size,entry,tp,sl,time_in_force,valid_until,rationale,risks,tags}
Approval{id,proposal_id,step,actor{id,name,role},decision,reason?,ts}
ExecutionResult{id,proposal_id,mode:"dry",status,tx_ref:null,ts}
AuditEvent{id,trace_id,actor,action,object{type,id},before?,after?,ts}

## 4. 风控与审批（Mock 行为）
- size>0.5 → RISK_REJECTED
- symbol 在黑名单 → RISK_REJECTED
- 非允许时段（UTC+8 08:00–22:00 外）→ RISK_REJECTED
- 账户回撤<-10%（Mock）→ RISK_REJECTED
- 审批：干跑 dry-1→dry-2；未完成前置步骤禁止 execute，返回 APPROVAL_REQUIRED

## 5. 观测性
- 必打点：{trace_id,user_id,action,object,result,ts}
- 错误上报：{error_code,message,route,ts}
- 性能：/api p95、WS 重连次数；前端 TTI/互动时延写入日志

## 6. 验收（DoD）
- 全链路 12 条联调用例可复现且通过
- 关键路径可演示（只读 + 干跑），任一 Schema/风控/审批未过均不会执行
- 审计可按 trace_id 回放每一步；默认仅内网/VPN访问
