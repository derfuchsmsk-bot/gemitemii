import time
import asyncio
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: float = 1.0):
        self.limit = limit
        self.last_user_time: Dict[int, float] = {}
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user: User = data.get("event_from_user")
        
        if user:
            user_id = user.id
            current_time = time.time()
            
            if user_id in self.last_user_time:
                elapsed = current_time - self.last_user_time[user_id]
                if elapsed < self.limit:
                    # Too fast!
                    return
            
            self.last_user_time[user_id] = current_time
            
        return await handler(event, data)
