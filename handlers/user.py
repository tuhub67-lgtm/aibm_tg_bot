# -*- coding: utf-8 -*-
"""
handlers/user.py — вся логика общения с клиентом.
Тимур, это сердце бота: команда /start, прохождение брифа,
кнопки «Назад / Пропустить / Дальше», прогресс-бар и финал
(Grok → Notion → предложение клиенту → уведомление тебе).
"""

import json
from pathlib import Path

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from config import config
from keyboards.inline import finish_keyboard, nav_keyboard, start_keyboard
from services.grok import analyze_brief
from services.notion import save_to_notion
from services.storage import save_lead
from states.brief import Brief

# Создаём роутер — сюда подключаем все клиентские обработчики
router = Router()

# === Загружаем вопросы брифа один раз при импорте ===
QUESTIONS_FILE = Path(__file__).parent.parent / "data" / "questions.json"
with open(QUESTIONS_FILE, encoding="utf-8") as f:
    _data = json.load(f)
QUESTIONS: list[dict] = _data["questions"]
TOTAL = len(QUESTIONS)  # сколько всего вопросов

# Логируем при импорте, сколько вопросов и разделов загрузилось
logger.info(
    f"📝 Загружено {TOTAL} вопросов из "
    f"{len(set(q['section'] for q in QUESTIONS))} разделов"
)


def progress_bar(current: int) -> str:
    """Рисуем простой прогресс-бар: current — номер текущего вопроса (с 0)."""
    percent = int((current) / TOTAL * 100)
    filled = int(percent / 10)  # сколько квадратиков закрасить (из 10)
    bar = "🟩" * filled + "⬜" * (10 - filled)
    return f"{bar} {percent}%"


async def show_question(message: Message, state: FSMContext) -> None:
    """Показываем клиенту текущий вопрос с навигацией и прогрессом."""
    data = await state.get_data()
    idx = data.get("idx", 0)  # индекс текущего вопроса
    q = QUESTIONS[idx]

    text = (
        f"<b>Раздел {q['section']}</b>\n"
        f"{progress_bar(idx)}\n\n"
        f"<b>Вопрос {idx + 1} из {TOTAL}:</b>\n"
        f"{q['text']}\n\n"
        f"<i>Напиши ответ сообщением 👇</i>"
    )
    kb = nav_keyboard(
        is_first=(idx == 0),
        is_last=(idx == TOTAL - 1),
        required=q.get("required", False),
    )
    # Если можем — редактируем прошлое сообщение, иначе шлём новое
    try:
        await message.edit_text(text, reply_markup=kb)
    except Exception:
        await message.answer(text, reply_markup=kb)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Команда /start — приветствие и кнопка запуска брифа."""
    await state.clear()
    text = (
        "Привет, на связи Тимур 🤝\n\n"
        "Я делаю под ключ и <b>сам, без команды</b> (поэтому всё лично и по-честному):\n"
        "1️⃣ ИИ Автоматизация — <b>35 000₽</b>\n"
        "2️⃣ Медиа и контент — <b>25 000₽</b>\n"
        "3️⃣ Продающий сайт + реклама — <b>45 000₽</b>\n\n"
        "Работаю по-братски, оплата <b>50/50</b> (предоплата/результат).\n\n"
        "Давай за пару минут заполним короткий бриф — и я лично подберу,"
        " что тебе реально нужно 👇"
    )
    await message.answer(text, reply_markup=start_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Команда /help — описание услуг и подсказка по командам."""
    text = (
        "🤝 <b>Я — Тимур, делаю под ключ и сам (без команды):</b>\n\n"
        "1️⃣ <b>ИИ Автоматизация — 35 000₽</b>\n"
        "Боты, автоответы, обработка заявок — рутину делает не ты.\n\n"
        "2️⃣ <b>Медиа и контент — 25 000₽</b>\n"
        "Видео, фото, тексты, ведение соцсетей — чтобы тебя видели.\n\n"
        "3️⃣ <b>Продающий сайт + реклама — 45 000₽</b>\n"
        "Сайт, который продаёт, плюс настройка рекламы.\n\n"
        "Оплата 50/50 (Сбер/Тинькофф), всё лично и по-честному.\n\n"
        "<b>Команды:</b>\n"
        "/start — начать и оставить заявку\n"
        "/cancel — отменить заполнение брифа\n"
        "/help — это сообщение"
    )
    await message.answer(text, reply_markup=start_keyboard())


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Команда /cancel — отменить бриф в любой момент."""
    current = await state.get_state()
    await state.clear()
    if current is None:
        await message.answer("Сейчас нечего отменять 🙂 Жми /start, когда будешь готов.")
    else:
        await message.answer("Бриф отменён. Захочешь вернуться — жми /start 🤝")


@router.callback_query(F.data == "show_services")
async def show_services(callback: CallbackQuery) -> None:
    """Показываем услуги и цены."""
    text = (
        "💼 <b>Мои услуги:</b>\n\n"
        "1️⃣ <b>ИИ Автоматизация — 35 000₽</b>\n"
        "Боты, автоответы, обработка заявок — чтобы рутину делал не ты.\n\n"
        "2️⃣ <b>Медиа и контент — 25 000₽</b>\n"
        "Видео, фото, тексты, ведение соцсетей — чтобы тебя видели.\n\n"
        "3️⃣ <b>Продающий сайт + реклама — 45 000₽</b>\n"
        "Сайт, который продаёт, плюс настройка рекламы.\n\n"
        "Оплата 50/50 (Сбер/Тинькофф). Делаю сам, лично довожу до результата 🤝"
    )
    await callback.message.answer(text, reply_markup=start_keyboard())
    await callback.answer()


@router.callback_query(F.data == "start_brief")
async def start_brief(callback: CallbackQuery, state: FSMContext) -> None:
    """Запускаем бриф: ставим state и показываем первый вопрос."""
    await state.clear()
    await state.set_state(Brief.filling)
    await state.update_data(idx=0, answers={})
    await show_question(callback.message, state)
    await callback.answer("Поехали! 🚀")


@router.message(Brief.filling)
async def handle_answer(message: Message, state: FSMContext) -> None:
    """Клиент прислал текстовый ответ на текущий вопрос — сохраняем и идём дальше."""
    data = await state.get_data()
    idx = data.get("idx", 0)
    answers = data.get("answers", {})
    q = QUESTIONS[idx]

    # Берём текст ответа. Если прислали стикер/фото/голосовое — text будет пустым.
    answer = (message.text or "").strip()

    # Валидация: на обязательный вопрос нельзя ответить пустотой
    if q.get("required", False) and not answer:
        await message.answer(
            "Это важный вопрос 🙏 Напиши, пожалуйста, ответ текстом — "
            "так я смогу подобрать тебе решение точнее."
        )
        return

    # Записываем ответ под ключом вопроса
    answers[q["key"]] = answer
    await state.update_data(answers=answers)

    # Двигаемся к следующему вопросу или завершаем
    await _go_next(message, state)


async def _go_next(message: Message, state: FSMContext) -> None:
    """Переход к следующему вопросу. Если вопросы кончились — финал."""
    data = await state.get_data()
    idx = data.get("idx", 0)

    if idx + 1 >= TOTAL:
        # Вопросы кончились — завершаем бриф
        await finish_brief(message, state)
    else:
        await state.update_data(idx=idx + 1)
        await show_question(message, state)


# === Кнопки навигации ===

@router.callback_query(Brief.filling, F.data == "nav_next")
async def nav_next(callback: CallbackQuery, state: FSMContext) -> None:
    """«Дальше» — переходим к следующему вопросу (если ответ уже был, не теряем его)."""
    await _go_next(callback.message, state)
    await callback.answer()


@router.callback_query(Brief.filling, F.data == "nav_skip")
async def nav_skip(callback: CallbackQuery, state: FSMContext) -> None:
    """«Пропустить» — для необязательных вопросов: ставим прочерк и идём дальше."""
    data = await state.get_data()
    idx = data.get("idx", 0)
    answers = data.get("answers", {})
    answers.setdefault(QUESTIONS[idx]["key"], "—")
    await state.update_data(answers=answers)
    await _go_next(callback.message, state)
    await callback.answer("Пропустили ⏭")


@router.callback_query(Brief.filling, F.data == "nav_back")
async def nav_back(callback: CallbackQuery, state: FSMContext) -> None:
    """«Назад» — возвращаемся к предыдущему вопросу."""
    data = await state.get_data()
    idx = data.get("idx", 0)
    if idx > 0:
        await state.update_data(idx=idx - 1)
    await show_question(callback.message, state)
    await callback.answer()


@router.callback_query(Brief.filling, F.data == "nav_cancel")
async def nav_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """«Отменить» — сбрасываем бриф."""
    await state.clear()
    await callback.message.edit_text(
        "Бриф отменён. Если что — жми /start, я на связи 🤝"
    )
    await callback.answer()


@router.callback_query(Brief.filling, F.data == "nav_finish")
async def nav_finish(callback: CallbackQuery, state: FSMContext) -> None:
    """«Готово» на последнем вопросе — завершаем бриф."""
    await finish_brief(callback.message, state)
    await callback.answer()


async def finish_brief(message: Message, state: FSMContext) -> None:
    """
    Финал брифа: Grok → Notion → SQLite → предложение клиенту → уведомление Тимуру.
    Каждый шаг обёрнут так, чтобы падение одного сервиса не сломало остальные.
    """
    data = await state.get_data()
    answers = data.get("answers", {})
    user = message.chat  # данные клиента

    # Сообщаем клиенту, что обрабатываем
    await message.answer("🔍 Спасибо! Анализирую твои ответы, пара секунд...")

    # 1) Анализ через Grok (если упадёт — grok_result будет пустым)
    grok_result = await analyze_brief(answers)

    # 2) Сохраняем в локальную базу (это надёжно и всегда)
    try:
        lead_id = await save_lead(
            tg_user_id=user.id,
            tg_username=user.username or "",
            answers=answers,
            grok_result=grok_result,
        )
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения в SQLite: {e}")
        lead_id = 0

    # 3) Сохраняем в Notion (необязательно — страховка уже есть в SQLite)
    await save_to_notion(answers, grok_result)

    # 4) Отправляем клиенту персональное предложение
    if grok_result:
        client_text = (
            "Готово! Вот что я для тебя подобрал 👇\n\n"
            f"{grok_result}\n\n"
            "Если откликается — пиши, обсудим. Работаю сам, по-братски,"
            " оплата 50/50 🤝"
        )
    else:
        # Запасной вариант, если Grok недоступен
        client_text = (
            "Спасибо, заявку получил! 🤝\n\n"
            "Я лично изучу твои ответы и в ближайшее время напишу тебе"
            " с конкретным предложением. Работаю сам, по-честному, оплата 50/50."
        )
    await message.answer(client_text, reply_markup=finish_keyboard())

    # 5) Уведомляем Тимура (админа) о новой заявке
    await _notify_admin(message, answers, grok_result, lead_id)

    await state.clear()


async def _notify_admin(message: Message, answers: dict, grok_result: str, lead_id: int) -> None:
    """Шлём тебе, Тимур, уведомление о новой заявке со всеми ответами."""
    user = message.chat
    username = f"@{user.username}" if user.username else f"id {user.id}"

    lines = [f"🔥 <b>Новая заявка #{lead_id}</b>", f"От: {username}", ""]
    for key, value in answers.items():
        lines.append(f"<b>{key}:</b> {value}")
    if grok_result:
        lines.append("")
        lines.append("🤖 <b>Анализ Grok:</b>")
        lines.append(grok_result)

    text = "\n".join(lines)
    try:
        # Telegram не любит сообщения длиннее 4096 символов — режем
        await message.bot.send_message(config.admin_id, text[:4000])
        logger.info(f"📨 Уведомил админа о заявке #{lead_id}")
    except Exception as e:
        logger.error(f"❌ Не смог уведомить админа: {e}")
