from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class Proposal(BaseModel):
    id: Optional[str] = None
    symbol: str
    side: Literal["buy", "sell"]
    size: float = Field(..., gt=0, le=1)
    entry: float = Field(..., gt=0)
    tp: float = Field(..., gt=0)
    sl: float = Field(..., gt=0)
    time_in_force: Literal["GTC", "IOC", "FOK"]
    valid_until: datetime
    rationale: str = Field(..., max_length=120)
    risks: str = Field(..., max_length=120)
    tags: List[str] = []
    state: Optional[str] = None

class ApprovalRequest(BaseModel):
    step: Literal["dry-1","dry-2","live-1","live-2","live-3"]
    decision: Literal["approved","rejected"]
    reason: Optional[str] = None

class ExecutionResult(BaseModel):
    id: str
    proposal_id: str
    mode: Literal["dry"]
    status: Literal["started","done","failed"]
    tx_ref: Optional[str] = None
    ts: datetime

class AuditEvent(BaseModel):
    id: str
    trace_id: str
    actor: Dict[str, Any]
    action: str
    object: Dict[str, Any]
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    ts: datetime
