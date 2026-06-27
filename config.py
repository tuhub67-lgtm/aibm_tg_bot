# -*- coding: utf-8 -*-
"""
config.py — все настройки бота в одном месте.
Тимур, здесь ничего сложного: все секреты берутся из файла .env,
а тут мы просто читаем их и проверяем, что всё на месте.
"""

import os
import sys
from dataclasses import dataclass, field

from dotenv import load_dotenv
from loguru import logger

# Подгружаем переменные из файла .env (он лежит рядом с main.py)
load_dotenv()


def _get(name: str, default: str | None = None, required: bool = False) -> str:
    """Достаём переменную окружения. Если она обязательна и пуста — ругаемся и выходим."""
    value = os.getenv(name, default)
    if required and not value:
        logger.error(f"❌ В .env не заполнена обязательная переменная: {name}")
        sys.exit(1)
    return value or ""


@dataclass
class Config:
    """Все настройки бота. Меняешь .env — меняется поведение, код трогать не надо."""

    # --- Telegram ---
    bot_token: str = field(default_factory=lambda: _get("BOT_TOKEN", required=True))
    # Твой личный Telegram ID (число). Узнать можно у @userinfobot
    admin_id: int = field(default_factory=lambda: int(_get("ADMIN_ID", "0", required=True)))

    # --- Grok API (xAI) ---
    grok_api_key: str = field(default_factory=lambda: _get("GROK_API_KEY"))
    grok_model: str = field(default_factory=lambda: _get("GROK_MODEL", "grok-2-latest"))
    grok_base_url: str = field(default_factory=lambda: _get("GROK_BASE_URL", "https://api.x.ai/v1"))

    # --- Notion ---
    notion_token: str = field(default_factory=lambda: _get("NOTION_TOKEN"))
    notion_database_id: str = field(default_factory=lambda: _get("NOTION_DATABASE_ID"))

    # --- База и прочее ---
    db_path: str = field(default_factory=lambda: _get("DB_PATH", "bot.db"))
    # Антиспам: минимум секунд между действиями одного пользователя
    antispam_seconds: float = field(default_factory=lambda: float(_get("ANTISPAM_SECONDS", "0.5")))

    @property
    def grok_enabled(self) -> bool:
        """Включён ли анализ через Grok (если ключ не задан — просто пропустим этот шаг)."""
        return bool(self.grok_api_key)

    @property
    def notion_enabled(self) -> bool:
        """Включена ли запись в Notion (если токена нет — сохраним только в SQLite)."""
        return bool(self.notion_token and self.notion_database_id)


# Единый объект конфига, его импортируем по всему проекту
config = Config()
