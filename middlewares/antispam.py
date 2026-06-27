# -*- coding: utf-8 -*-
"""
middlewares/antispam.py — простая защита от спама (троттлинг).
Тимур, смысл такой: если один человек жмёт кнопки/шлёт сообщения слишком
часто (чаще, чем раз в ANTISPAM_SECONDS), лишние действия мы тихо игнорируем.
Это защищает бота от случайных «дабл-кликов» и от флуда.
"""

import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from config import config


class AntiSpamMiddleware(BaseMiddleware):
    """Пропускает не чаще одного действия в ANTISPAM_SECONDS на пользователя."""

    def __init__(self) -> None:
        # Запоминаем время последнего действия каждого пользователя
        self._last_seen: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        if user is not None:
            now = time.monotonic()
            last = self._last_seen.get(user.id, 0.0)
            if now - last < config.antispam_seconds:
                # Слишком быстро — игнорируем это событие
                return None
            self._last_seen[user.id] = now
        # Всё в порядке — передаём управление дальше
        return await handler(event, data)
