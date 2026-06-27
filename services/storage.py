# -*- coding: utf-8 -*-
"""
services/storage.py — работа с локальной базой SQLite (один файл bot.db).
Тимур, сюда мы сохраняем КАЖДУЮ заявку, даже если Notion или Grok упадут.
Это твоя страховка: данные клиентов всегда останутся у тебя на диске.
"""

import json
from datetime import datetime

import aiosqlite
from loguru import logger

from config import config


async def init_db() -> None:
    """Создаём таблицу заявок при старте бота (если её ещё нет)."""
    async with aiosqlite.connect(config.db_path) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_user_id  INTEGER,
                tg_username TEXT,
                answers     TEXT,      -- ответы клиента в формате JSON
                grok_result TEXT,      -- анализ от Grok (если был)
                created_at  TEXT
            )
            """
        )
        await db.commit()
    logger.info("🗄  База SQLite готова к работе")


async def save_lead(
    tg_user_id: int,
    tg_username: str,
    answers: dict,
    grok_result: str = "",
) -> int:
    """
    Сохраняем заявку в базу. Возвращаем id записи.
    answers — словарь {ключ_вопроса: ответ}.
    """
    async with aiosqlite.connect(config.db_path) as db:
        cursor = await db.execute(
            """
            INSERT INTO leads (tg_user_id, tg_username, answers, grok_result, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                tg_user_id,
                tg_username or "",
                json.dumps(answers, ensure_ascii=False),
                grok_result,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        await db.commit()
        lead_id = cursor.lastrowid
    logger.info(f"💾 Заявка #{lead_id} сохранена в SQLite")
    return lead_id
