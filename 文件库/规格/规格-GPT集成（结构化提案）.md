# 规格-GPT集成（结构化提案）v0.2 草案

> 目的：将**中文意图**稳定转换为**结构化 Proposal JSON**；若不确定/非法则返回“缺口清单”或只读建议，严禁自然语言直接下单。

## 1. 输入与上下文
- 输入：intent:string（中文） + context?:{ positions[], risk_limits{}, whitelist[], blacklist[], time_window, max_drawdown }
- 约束：上下文不足时，不生成 Proposal，返回“缺口清单”。

## 2. 输出（Proposal JSON · 必须符合 schemas/proposal.schema.json）
必填字段：symbol, side{buy|sell}, size∈(0,1], entry>0, tp>0, sl>0, time_in_force{GTC|IOC|FOK}, valid_until(ISO8601), rationale≤120中文, risks≤120中文, tags[string[]]  
示例：
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
