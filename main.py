# -*- coding: utf-8 -*-
"""
main.py — точка входа. Запускаешь этот файл — и бот работает.
Тимур, тут мы: настраиваем логи, создаём базу, подключаем обработчики
и middleware, и запускаем бота в режиме long-polling (без вебхуков —
так проще всего, ничего настраивать не надо).
"""

import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from config import config
from handlers import admin, user
from middlewares.antispam import AntiSpamMiddleware
from services.storage import init_db


def setup_logging() -> None:
    """Настраиваем loguru: красивый вывод в консоль + запись в файл bot.log."""
    logger.remove()  # убираем стандартный обработчик
    logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}")
    # Логи в файл с ротацией: новый файл каждые 10 МБ, храним 10 дней
    logger.add("bot.log", level="INFO", rotation="10 MB", retention="10 days", encoding="utf-8")


async def main() -> None:
    """Главная асинхронная функция запуска бота."""
    setup_logging()
    logger.info("🚀 Запускаю бота AiBM...")

    # Готовим базу данных
    await init_db()

    # Создаём бота. parse_mode=HTML — чтобы работали <b>жирный</b> и т.п.
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Подключаем антиспам ко всем сообщениям и нажатиям кнопок
    antispam = AntiSpamMiddleware()
    dp.message.middleware(antispam)
    dp.callback_query.middleware(antispam)

    # Подключаем обработчики. admin — первым, чтобы его команды имели приоритет.
    dp.include_router(admin.router)
    dp.include_router(user.router)

    # Сбрасываем «зависшие» апдейты, накопившиеся пока бот был выключен
    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("✅ Бот готов и слушает сообщения")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("👋 Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Остановка по Ctrl+C")
