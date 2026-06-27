# -*- coding: utf-8 -*-
"""
keyboards/inline.py — все инлайн-кнопки бота.
Тимур, тут собраны клавиатуры: стартовая, навигация по брифу и финальная.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def start_keyboard() -> InlineKeyboardMarkup:
    """Кнопка на главном экране — запустить бриф."""
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Оставить заявку", callback_data="start_brief")
    kb.button(text="💼 Услуги и цены", callback_data="show_services")
    kb.adjust(1)  # по одной кнопке в ряд
    return kb.as_markup()


def nav_keyboard(is_first: bool, is_last: bool, required: bool) -> InlineKeyboardMarkup:
    """
    Навигация во время брифа.
    is_first — это первый вопрос (тогда «Назад» не нужен).
    is_last  — последний вопрос (тогда вместо «Дальше» — «Готово»).
    required — обязательный ли вопрос (если нет, показываем «Пропустить»).
    """
    kb = InlineKeyboardBuilder()
    row: list[InlineKeyboardButton] = []

    # Кнопка «Назад» — есть везде, кроме первого вопроса
    if not is_first:
        row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data="nav_back"))

    # Кнопка «Пропустить» — только для необязательных вопросов
    if not required:
        row.append(InlineKeyboardButton(text="⏭ Пропустить", callback_data="nav_skip"))

    # Кнопка «Дальше» / «Готово»
    if is_last:
        row.append(InlineKeyboardButton(text="✅ Готово", callback_data="nav_finish"))
    else:
        row.append(InlineKeyboardButton(text="➡️ Дальше", callback_data="nav_next"))

    kb.row(*row)
    # Отдельной строкой — отмена всего брифа
    kb.row(InlineKeyboardButton(text="❌ Отменить", callback_data="nav_cancel"))
    return kb.as_markup()


def finish_keyboard() -> InlineKeyboardMarkup:
    """Финальная клавиатура после отправки заявки."""
    kb = InlineKeyboardBuilder()
    kb.button(text="🔁 Заполнить заново", callback_data="start_brief")
    kb.adjust(1)
    return kb.as_markup()
