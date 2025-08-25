import asyncio, time
from typing import Dict, Any, Set

class EventBus:
    def __init__(self) -> None:
        self.subscribers: Set[asyncio.Queue] = set()
        self._id = 0

    async def publish(self, evt: Dict[str, Any]) -> None:
        self._id += 1
        payload = dict(evt)
        payload.setdefault("ts", time.time())
        payload["event_id"] = self._id
        for q in list(self.subscribers):
            await q.put(payload)

    async def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self.subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self.subscribers.discard(q)

bus = EventBus()
