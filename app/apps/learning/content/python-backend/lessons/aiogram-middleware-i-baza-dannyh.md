Пока бот всё забывает после перезапуска. Настоящему боту нужно хранить пользователей, заказы, баллы. В этом уроке подключим базу данных и научимся **middleware** — коду, который выполняется до или после каждого хэндлера.

## База данных: aiosqlite

Для старта возьмём SQLite — база данных в одном файле, ничего не нужно устанавливать отдельно. Так как бот асинхронный, используем асинхронную обёртку `aiosqlite`:

```bash
pip install aiosqlite
```

<aside class="callout" data-icon="⚠️" markdown="1">

Не используйте в асинхронном боте обычный `sqlite3` или `psycopg2`: пока они ждут ответа базы, весь бот «замирает» и не отвечает остальным пользователям. Нужны асинхронные библиотеки: `aiosqlite`, `asyncpg`, SQLAlchemy в async-режиме.

</aside>

Создадим файл `db.py` со всеми запросами к базе. Если SQL пока непривычен — повторите тему [Создание таблиц](lesson:sozdanie-tablic) и [Вставка и модификация данных](lesson:vstavka-i-modifikaciya-dannyh).

```python
import aiosqlite

DB_PATH = "bot.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY,   -- id пользователя в Telegram
                name       TEXT,
                points     INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def add_user(user_id: int, name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        # INSERT OR IGNORE — не упадёт, если пользователь уже есть
        await db.execute("INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)", (user_id, name))
        await db.commit()


async def add_points(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET points = points + ? WHERE id = ?", (amount, user_id))
        await db.commit()


async def get_points(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT points FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def count_users() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            return (await cursor.fetchone())[0]
```

Обратите внимание на `?` в запросах: значения передаются отдельно, и библиотека сама их экранирует. **Никогда не подставляйте данные пользователя в SQL через f-строку** — это прямой путь к SQL-инъекции.

Таблицу создаём один раз при старте бота:

```python
async def main():
    await init_db()
    ...
    await dp.start_polling(bot)
```

## Используем базу в хэндлерах

```python
import db


@router.message(CommandStart())
async def cmd_start(message: Message):
    await db.add_user(message.from_user.id, message.from_user.first_name)
    await message.answer("Вы зарегистрированы! За каждое сообщение — 1 балл. Баланс: /points")


@router.message(Command("points"))
async def cmd_points(message: Message):
    points = await db.get_points(message.from_user.id)
    await message.answer(f"У вас {points} баллов ⭐")


@router.message(Command("stats"), IsAdmin())
async def cmd_stats(message: Message):
    await message.answer(f"Пользователей в боте: {await db.count_users()}")
```

## Middleware: код для каждого апдейта

Хотим начислять балл за **каждое** сообщение. Можно вписать `add_points` в каждый хэндлер — но это повторение кода, и где-нибудь обязательно забудем. Правильнее — middleware.

Middleware — это «прослойка» вокруг хэндлеров. Каждый апдейт сначала проходит через неё:

```text
Апдейт → middleware (до) → хэндлер → middleware (после)
```

```python
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

import db


class PointsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        await db.add_points(event.from_user.id, 1)   # до хэндлера
        result = await handler(event, data)          # вызываем сам хэндлер
        return result                                # после хэндлера можно что-то сделать ещё
```

Подключаем к сообщениям:

```python
dp.message.middleware(PointsMiddleware())
```

Ключевая строка — `await handler(event, data)`. Если её не вызвать, хэндлер не выполнится вовсе. Так, например, делают антиспам: «если пользователь пишет слишком часто — не вызываем handler».

## Пример: антифлуд

```python
import time


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.last_time: dict[int, float] = {}

    async def __call__(self, handler, event: Message, data):
        user_id = event.from_user.id
        now = time.monotonic()
        if now - self.last_time.get(user_id, 0) < self.delay:
            return  # слишком часто — молча игнорируем
        self.last_time[user_id] = now
        return await handler(event, data)


dp.message.middleware(ThrottlingMiddleware(delay=1.0))
```

## Передаём данные из middleware в хэндлер

Всё, что middleware положит в словарь `data`, aiogram передаст в хэндлер как аргумент с тем же именем:

```python
class UserMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data):
        data["points"] = await db.get_points(event.from_user.id)
        return await handler(event, data)


@router.message(Command("me"))
async def cmd_me(message: Message, points: int):   # points пришёл из middleware
    await message.answer(f"Ваши баллы: {points}")
```

## Когда SQLite станет мало

SQLite отлично подходит для небольших ботов. Когда пользователей станет много или бот будет работать в нескольких экземплярах, переходите на PostgreSQL через `asyncpg` или SQLAlchemy — принципы останутся теми же, поменяется только код в `db.py`.

## Практика

1.  Добавьте команду `/top`, которая показывает 5 пользователей с наибольшим числом баллов (`ORDER BY points DESC LIMIT 5`).
2.  Напишите middleware, которая выводит в лог: кто и что написал боту.
3.  Сохраняйте результаты анкеты из прошлого урока в отдельную таблицу.
