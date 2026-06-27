# -*- coding: utf-8 -*-
"""
states/brief.py — состояния FSM (конечного автомата).
Тимур, тут всё просто: у нас один-единственный state "заполняем бриф".
Номер текущего вопроса и все ответы храним в data-словаре FSM.
"""

from aiogram.fsm.state import State, StatesGroup


class Brief(StatesGroup):
    """Группа состояний брифа. Нам хватает одного состояния."""

    # Клиент находится в процессе прохождения брифа
    filling = State()
