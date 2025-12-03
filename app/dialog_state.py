# app/dialog_state.py
import os
import json
import redis.asyncio as redis
from typing import Optional, Dict, Any

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def get_dialog_state(user_id: str) -> Optional[Dict[str, Any]]:
    data = await redis_client.get(f"dialog_state:{user_id}")
    return json.loads(data) if data else None

async def save_dialog_state(user_id: str, state: Dict[str, Any]):
    await redis_client.setex(f"dialog_state:{user_id}", 7200, json.dumps(state))  # 2 часа