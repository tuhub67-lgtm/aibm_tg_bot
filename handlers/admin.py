# -*- coding: utf-8 -*-
"""
handlers/admin.py — команды для тебя, Тимур (только для админа).
Сейчас тут одна полезная команда /stats — посмотреть количество заявок.
Доступ есть только у того, чей ID совпадает с ADMIN_ID из .env.
"""

import aiosqlite
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

from config import config

router = Router()

# Фильтр: пускаем в эти обработчики только тебя (по твоему Telegram ID)
router.message.filter(F.from_user.id == config.admin_id)


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Показать статистику: сколько всего заявок и последние 5."""
    try:
        async with aiosqlite.connect(config.db_path) as db:
            # Всего заявок
            async with db.execute("SELECT COUNT(*) FROM leads") as cur:
                total = (await cur.fetchone())[0]
            # Последние 5 заявок
            async with db.execute(
                "SELECT id, tg_username, created_at FROM leads ORDER BY id DESC LIMIT 5"
            ) as cur:
                rows = await cur.fetchall()
    except Exception as e:
        logger.error(f"❌ Ошибка чтения статистики: {e}")
        await message.answer("Не смог прочитать базу 😕")
        return

    lines = [f"📊 <b>Всего заявок:</b> {total}", "", "<b>Последние:</b>"]
    for row in rows:
        lead_id, username, created = row
        who = f"@{username}" if username else "—"
        lines.append(f"#{lead_id} · {who} · {created}")
    await message.answer("\n".join(lines))


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    """Подсказка по админ-командам."""
    await message.answer(
        "🛠 <b>Команды для тебя:</b>\n"
        "/stats — статистика заявок\n\n"
        "Все заявки также падают тебе в личку и сохраняются в bot.db и Notion."
    )
