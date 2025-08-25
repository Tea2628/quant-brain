# 规格-GPT集成（结构化提案）v0.1 草案

> 目的：把**中文意图**转换为**结构化 Proposal JSON**，并在任意不确定/非法场景下“失败降级”为只读建议；严禁直接下单。

## 1. 输入与上下文
- 输入：中文意图 + 可选上下文（账户/仓位/阈值/行情摘要）
- 上下文最小集：{ positions[], risk_limits{}, whitelist[], blacklist[], time_window, max_drawdown }

## 2. 输出（Proposal JSON）
必须符合 `schemas/proposal.schema.json`（CI 强约束）。字段：
`symbol, side{buy|sell}, size(0,1], entry>0, tp>0, sl>0, time_in_force{GTC|IOC|FOK}, valid_until(ISO8601),
 rationale(≤120中文), risks(≤120中文), tags[string[]]`

### 示例
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
  "tags": ["gpt","schema-validated","dry-run"]
}
