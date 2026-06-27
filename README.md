# 🤖 AiBM — Telegram-бот для приёма заявок (Тимур, Новороссия)

Бот принимает заявки, проводит клиента через бриф из **35 вопросов** в 6 разделах,
анализирует ответы через **Grok API (xAI)**, сохраняет в **SQLite** и **Notion**,
отправляет клиенту персональное предложение и уведомляет тебя в Telegram.

## 🚀 Быстрый старт

### Локальный запуск:
1. Клонируй репозиторий
2. Создай `.env` из `.env.example` и заполни ключи (`BOT_TOKEN`, `ADMIN_ID` — обязательны)
3. Установи зависимости: `pip install -r requirements.txt`
4. Запусти: `python main.py`
5. Открой бота в Telegram и отправь `/start`

### Деплой на Railway:
1. Подключи репозиторий к Railway (New Project → Deploy from GitHub repo)
2. Добавь переменные окружения из `.env` в Railway → Variables
3. Railway сам запустит бота по `Procfile` (`worker: python main.py`)

### Тестирование:
- Отправь боту `/start`
- Пройди бриф целиком (кнопки ⬅️ Назад / ⏭ Пропустить / ➡️ Дальше / ✅ Готово)
- Проверь, что тебе пришло уведомление в Telegram с ответами и анализом Grok
- Проверь, что данные сохранились в `bot.db` (команда `/stats`)

## 🛠 Команды

**Клиент:**
- `/start` — начать и оставить заявку
- `/help` — услуги и список команд
- `/cancel` — отменить бриф в любой момент

**Админ (только ты, по `ADMIN_ID`):**
- `/stats` — статистика заявок
- `/export` — выгрузить все заявки в CSV
- `/admin` — список админ-команд

## 📂 Структура

```
main.py                 — точка входа
config.py               — настройки из .env
data/questions.json     — 35 вопросов брифа (правится без кода)
states/brief.py         — FSM-состояние
keyboards/inline.py     — инлайн-кнопки
handlers/user.py        — логика клиента
handlers/admin.py       — команды админа
services/grok.py        — анализ через Grok API
services/notion.py      — запись в Notion
services/storage.py     — SQLite (bot.db)
middlewares/antispam.py — защита от флуда
```

## ⚙️ Переменные окружения

| Переменная | Обязательна | Описание |
|---|---|---|
| `BOT_TOKEN` | да | токен бота от @BotFather |
| `ADMIN_ID` | да | твой Telegram ID (от @userinfobot) |
| `GROK_API_KEY` | нет | ключ xAI; без него бот работает, но без ИИ-анализа |
| `NOTION_TOKEN` / `NOTION_DATABASE_ID` | нет | без них заявки только в SQLite |
| `DB_PATH` | нет | путь к базе (по умолчанию `bot.db`) |
| `ANTISPAM_SECONDS` | нет | минимум секунд между действиями (по умолчанию 0.5) |

> ⚠️ `.env` с реальными ключами **не коммитится** в git (он в `.gitignore`).
