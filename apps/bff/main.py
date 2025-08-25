import os, json, uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jsonschema import Draft202012Validator
from .models import Proposal, ApprovalRequest, ExecutionResult, AuditEvent
from .events import bus

app = FastAPI(title="quant-brain BFF Mock", version="0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_WHITELIST","http://localhost:5173,http://127.0.0.1:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCHEMA_PATH = os.path.join(ROOT, "schemas", "proposal.schema.json")
if not os.path.exists(SCHEMA_PATH):
    raise RuntimeError(f"Schema not found: {SCHEMA_PATH}")
SCHEMA = json.loads(open(SCHEMA_PATH, "r", encoding="utf-8").read())
VALIDATOR = Draft202012Validator(SCHEMA)

PROPOSALS: Dict[str, Dict[str, Any]] = {}
APPROVALS: Dict[str, Dict[str, str]] = {}
EXECUTIONS: Dict[str, Dict[str, Any]] = {}
AUDITS: Dict[str, Dict[str, Any]] = {}

BLACKLIST = {"LUNA/USDT", "XYZ/USDT"}
MAX_SIZE = 0.5
ALLOW_START_HOUR = 8
ALLOW_END_HOUR = 22
ACCOUNT_DRAWDOWN = -0.05

def now_cst_hour() -> int:
    return int((datetime.utcnow() + timedelta(hours=8)).strftime("%H"))

def schema_validate(data: Dict[str, Any]) -> None:
    VALIDATOR.validate(data)

def audit(trace_id: str, action: str, obj: Dict[str, Any], before=None, after=None) -> None:
    evt = AuditEvent(
        id=f"a_{uuid.uuid4().hex[:8]}",
        trace_id=trace_id,
        actor={"id":"mock","name":"mock-user","role":"Trader"},
        action=action,
        object=obj,
        before=before, after=after,
        ts=datetime.utcnow()
    ).dict()
    AUDITS[evt["id"]] = evt

class IntentPayload(BaseModel):
    intent: str
    context: Optional[Dict[str, Any]] = None

@app.get("/api/health")
def health():
    return {"status":"ok","deps":{"gpt":"mock","freqtrade":"disconnected"}}

@app.get("/api/positions")
def positions():
    return [{"symbol":"BTC/USDT","qty":0.10,"avg_entry":60000.0,"pnl":50.2}]

@app.get("/api/trades")
def trades(limit: int = Query(20, ge=1, le=200)):
    return [{"id": f"t_{i:03d}", "symbol":"BTC/USDT","side":"buy" if i%2==0 else "sell","price":60000+i,"qty":0.01} for i in range(limit)]

@app.post("/api/gpt/proposals:from-intent")
def from_intent(payload: IntentPayload):
    intent = payload.intent.strip()
    if "缺口" in intent or "gaps" in intent.lower():
        gaps = [
            "symbol:str 非空","side:{buy|sell}","size:float(0,1]",
            "entry:float>0","tp/sl:float>0","time_in_force:{GTC|IOC|FOK}",
            "valid_until:ISO8601","rationale/risks:≤120中文"
        ]
        return {"gaps": gaps}
    side = "buy" if "空" not in intent else "sell"
    data = {
        "symbol": "BTC/USDT",
        "side": side,
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
    schema_validate(data)
    return {"proposal": data, "score": 0.7}

@app.post("/api/proposals")
async def create_proposal(p: Proposal):
    data = p.dict()
    schema_validate(data)
    pid = f"p_{uuid.uuid4().hex[:8]}"
    data.update({"id": pid, "state": "submitted"})
    PROPOSALS[pid] = data
    APPROVALS.setdefault(pid, {})
    await bus.publish({"type":"proposal.created","proposal_id":pid})
    audit(pid, "proposal.created", {"type":"proposal","id":pid}, after=data)
    return {"id": pid, "state":"submitted", "trace_id": pid}

@app.post("/api/proposals/{pid}/validate")
async def validate_proposal(pid: str):
    p = PROPOSALS.get(pid)
    if not p: raise HTTPException(404, "NOT_FOUND")
    reasons = []
    if p["size"] > MAX_SIZE: reasons.append("size exceeds limit")
    if p["symbol"] in BLACKLIST: reasons.append("symbol in blacklist")
    h = now_cst_hour()
    if not (ALLOW_START_HOUR <= h < ALLOW_END_HOUR): reasons.append("outside allowed hours")
    if ACCOUNT_DRAWDOWN < -0.10: reasons.append("account drawdown beyond limit")
    if reasons:
        await bus.publish({"type":"risk.rejected","proposal_id":pid,"reasons":reasons})
        audit(pid, "risk.rejected", {"type":"proposal","id":pid}, after={"reasons":reasons})
        return {"status":"rejected","reasons":reasons}
    await bus.publish({"type":"proposal.validated","proposal_id":pid})
    audit(pid, "proposal.validated", {"type":"proposal","id":pid})
    return {"status":"valid"}

@app.post("/api/proposals/{pid}/approve")
async def approve(pid: str, req: ApprovalRequest):
    if pid not in PROPOSALS: raise HTTPException(404, "NOT_FOUND")
    APPROVALS.setdefault(pid, {})
    APPROVALS[pid][req.step] = req.decision
    evt_type = "approval.granted" if req.decision == "approved" else "approval.rejected"
    await bus.publish({"type":evt_type,"proposal_id":pid,"step":req.step,"reason":req.reason})
    audit(pid, evt_type, {"type":"proposal","id":pid}, after={"step":req.step,"decision":req.decision})
    return {"status": req.decision, "trace_id": pid}

@app.post("/api/proposals/{pid}/execute")
async def execute(pid: str, mode: str = "dry"):
    if pid not in PROPOSALS: raise HTTPException(404, "NOT_FOUND")
    steps = APPROVALS.get(pid, {})
    if not (steps.get("dry-1") == "approved" and steps.get("dry-2") == "approved"):
        raise HTTPException(status_code=400, detail={"error_code":"APPROVAL_REQUIRED","message":"approve dry-1 & dry-2 first"})
    eid = f"e_{uuid.uuid4().hex[:8]}"
    await bus.publish({"type":"execution.started","proposal_id":pid,"execution_id":eid,"mode":mode})
    res = ExecutionResult(id=eid, proposal_id=pid, mode="dry", status="done", tx_ref=None, ts=datetime.utcnow()).dict()
    EXECUTIONS[eid] = res
    await bus.publish({"type":"execution.done","proposal_id":pid,"execution_id":eid})
    audit(pid, "execution.done", {"type":"execution","id":eid}, after=res)
    return res

@app.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    await ws.accept()
    q = await bus.subscribe()
    try:
        while True:
            event = await q.get()
            await ws.send_json(event)
    except WebSocketDisconnect:
        bus.unsubscribe(q)

# === patch: normalize datetime for JSON-Schema ===
import json as _json
from datetime import datetime as _dt

def _normalize_for_schema(obj):
    if isinstance(obj, _dt):
        # 序列化为 ISO8601，并统一加 Z（与 schema 的 date-time 匹配）
        return obj.replace(tzinfo=None).isoformat() + "Z"
    if isinstance(obj, dict):
        return {k: _normalize_for_schema(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalize_for_schema(v) for v in obj]
    return obj

# 覆盖同名函数：先规范化，再交给 JSON-Schema 校验
def schema_validate(data):
    payload = _normalize_for_schema(data)
    payload = _json.loads(_json.dumps(payload, default=str))
    VALIDATOR.validate(payload)
