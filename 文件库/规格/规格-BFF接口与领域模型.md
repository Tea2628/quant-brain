# 规格-BFF接口与领域模型（v0.1 草案）

> 目的：统一前端与后端的“契约（Contract）”，BFF 聚合 Freqtrade 与 GPT，只接受**结构化交易提案（Proposal）**；严禁自然语言直接下单。默认干跑，实盘需多级确认。

## 1. 领域对象（Domain）
- **Proposal**：{ id, created_at, symbol, side, size, entry, tp, sl, time_in_force, valid_until, rationale, risks, tags, state }
- **Approval**：{ id, proposal_id, step, actor, decision{approved|rejected}, reason, ts }
- **ExecutionResult**：{ id, proposal_id, mode{dry|live}, status{started|partial|done|failed}, tx_ref, ts }
- **AuditEvent**：{ id, trace_id, actor, action, object_type, object_id, before?, after?, ts }
- **Read-only 对象**：Bot / Strategy / Trade / Position（只读查询）

### Proposal（参考 JSON 示例）
```json
{
  "symbol": "BTC/USDT",
  "side": "buy",
  "size": 0.25,
  "entry": 60000.0,
  "tp": 61800.0,
  "sl": 58800.0,
  "time_in_force": "GTC",
  "valid_until": "2025-12-31T23:59:59Z",
  "rationale": "突破回踩确认，量能放大，遵守风控。",
  "risks": "宏观事件波动、假突破、滑点扩大。",
  "tags": ["demo","schema-validated","dry-run"]
}
