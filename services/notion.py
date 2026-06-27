# -*- coding: utf-8 -*-
"""
services/notion.py — сохранение заявки в базу Notion «Клиенты».
Тимур, тут мы создаём новую страницу (строку) в твоей базе Notion.

ВАЖНО про свойства базы Notion:
В твоей базе должно быть свойство-заголовок (Title). Обычно оно называется "Name".
Остальные данные мы складываем одним большим текстовым полем "Бриф",
чтобы тебе не пришлось вручную создавать 35 колонок. Если такого поля нет —
мы просто запишем заголовок, а текст брифа уйдёт в тело страницы.
Если токена/ID базы нет — шаг тихо пропускается, заявка всё равно цела в SQLite.
"""

import httpx
from loguru import logger

from config import config

# Адрес API и версия (Notion требует указывать дату версии)
NOTION_API = "https://api.notion.com/v1/pages"
NOTION_VERSION = "2022-06-28"


async def save_to_notion(answers: dict, grok_result: str = "") -> bool:
    """
    Создаём страницу в базе Notion. Возвращаем True при успехе.
    answers — словарь ответов клиента, grok_result — анализ от Grok.
    """
    if not config.notion_enabled:
        logger.warning("⚠️  Notion отключён (нет токена/ID базы) — пропускаем")
        return False

    # Заголовок страницы: имя клиента + тип бизнеса
    title = answers.get("name", "Новый клиент")
    business = answers.get("business_type", "")
    page_title = f"{title} — {business}".strip(" —")

    # Собираем весь бриф в один читаемый текст
    brief_lines = [f"{key}: {value}" for key, value in answers.items()]
    brief_text = "\n".join(brief_lines)
    if grok_result:
        brief_text += f"\n\n--- АНАЛИЗ GROK ---\n{grok_result}"

    # Notion ограничивает текстовый блок ~2000 символами — подстрахуемся
    brief_text = brief_text[:1900]

    payload = {
        "parent": {"database_id": config.notion_database_id},
        "properties": {
            # "Name" — стандартное имя свойства-заголовка в Notion
            "Name": {
                "title": [{"text": {"content": page_title[:200]}}]
            }
        },
        # Тело страницы: туда кладём полный бриф абзацем
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": brief_text}}]
                },
            }
        ],
    }
    headers = {
        "Authorization": f"Bearer {config.notion_token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(NOTION_API, json=payload, headers=headers)
            response.raise_for_status()
            logger.info("📒 Заявка записана в Notion")
            return True
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ Notion вернул ошибку {e.response.status_code}: {e.response.text[:300]}")
    except Exception as e:
        logger.error(f"❌ Не смог записать в Notion: {e}")

    return False
