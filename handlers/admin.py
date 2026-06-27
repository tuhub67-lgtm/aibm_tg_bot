# -*- coding: utf-8 -*-
"""
handlers/admin.py — команды для тебя, Тимур (только для админа).
Сейчас тут одна полезная команда /stats — посмотреть количество заявок.
Доступ есть только у того, чей ID совпадает с ADMIN_ID из .env.
"""

import csv
import io
import json

import aiosqlite
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message
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


@router.message(Command("export"))
async def cmd_export(message: Message) -> None:
    """Выгрузить все заявки в CSV-файл и прислать его тебе."""
    try:
        async with aiosqlite.connect(config.db_path) as db:
            async with db.execute(
                "SELECT id, tg_user_id, tg_username, answers, grok_result, created_at "
                "FROM leads ORDER BY id"
            ) as cur:
                rows = await cur.fetchall()
    except Exception as e:
        logger.error(f"❌ Ошибка экспорта: {e}")
        await message.answer("Не смог прочитать базу для экспорта 😕")
        return

    if not rows:
        await message.answer("Заявок пока нет — экспортировать нечего 🙂")
        return

    # Собираем все ключи ответов, чтобы сделать ровные колонки в CSV
    answer_keys: list[str] = []
    for row in rows:
        try:
            data = json.loads(row[3]) if row[3] else {}
        except json.JSONDecodeError:
            data = {}
        for k in data:
            if k not in answer_keys:
                answer_keys.append(k)

    # Пишем CSV в память (без временных файлов на диске)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "tg_user_id", "tg_username", "created_at", *answer_keys, "grok_result"])
    for row in rows:
        try:
            data = json.loads(row[3]) if row[3] else {}
        except json.JSONDecodeError:
            data = {}
        writer.writerow(
            [row[0], row[1], row[2], row[5], *[data.get(k, "") for k in answer_keys], row[4]]
        )

    # Кодируем в UTF-8 с BOM — чтобы Excel корректно показал кириллицу
    csv_bytes = buffer.getvalue().encode("utf-8-sig")
    file = BufferedInputFile(csv_bytes, filename="leads.csv")
    await message.answer_document(file, caption=f"📤 Экспорт: {len(rows)} заявок")
    logger.info(f"📤 Экспортировал {len(rows)} заявок в CSV")


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    """Подсказка по админ-командам."""
    await message.answer(
        "🛠 <b>Команды для тебя:</b>\n"
        "/stats — статистика заявок\n"
        "/export — выгрузить все заявки в CSV\n\n"
        "Все заявки также падают тебе в личку и сохраняются в bot.db и Notion."
    )
