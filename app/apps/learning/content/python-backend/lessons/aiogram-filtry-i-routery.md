Пока бот маленький, все хэндлеры можно держать в одном файле. Но когда команд становится двадцать, файл превращается в кашу. В этом уроке научимся точно выбирать, какие сообщения ловит хэндлер (**фильтры**), и раскладывать код по файлам (**роутеры**).

## Магический фильтр F

`F` — это «шаблон» для проверки сообщения. Вы описываете условие, а aiogram сам проверяет его для каждого апдейта.

```python
from aiogram import F

@router.message(F.text == "Привет")          # текст ровно «Привет»
@router.message(F.text.lower() == "привет")  # «привет», «ПРИВЕТ», «Привет»
@router.message(F.text.startswith("/"))      # любая команда
@router.message(F.photo)                     # фото
@router.message(F.sticker)                   # стикер
@router.message(F.document)                  # файл
@router.message(F.voice)                     # голосовое
@router.message(F.from_user.id == 123456789) # только от конкретного пользователя
```

Каждая строка выше — отдельный пример; к одному хэндлеру обычно вешают один фильтр.

Условия можно комбинировать: `&` — «и», `|` — «или», `~` — «не»:

```python
@router.message(F.text & ~F.text.startswith("/"))   # текст, но не команда
async def only_text(message: Message):
    ...

@router.message(F.photo | F.document)               # фото или файл
async def media(message: Message):
    ...
```

## Пример: бот, который понимает фото

```python
@router.message(F.photo)
async def got_photo(message: Message):
    photo = message.photo[-1]  # Telegram присылает несколько размеров, последний — самый большой
    await message.answer(
        f"Красивое фото! Размер: {photo.width}×{photo.height}\n"
        f"file_id: {photo.file_id}"
    )
```

`file_id` — это «адрес» файла на серверах Telegram. Сохраните его, и потом сможете отправить то же фото без повторной загрузки: `await message.answer_photo(photo=file_id)`.

## Свой фильтр

Если встроенных условий не хватает, напишите фильтр-класс. Например, пропускать только админов:

```python
from aiogram.filters import BaseFilter
from aiogram.types import Message

ADMINS = {123456789, 987654321}


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMINS
```

Используется как любой другой фильтр:

```python
@router.message(Command("stats"), IsAdmin())
async def admin_stats(message: Message):
    await message.answer("Статистика только для админов 📊")
```

Если передать в декоратор несколько фильтров через запятую, хэндлер сработает, только когда **все** они вернут `True`.

<aside class="callout" data-icon="💡" markdown="1">

Свой id в Telegram можно узнать у бота [@userinfobot](https://t.me/userinfobot) — или вывести его в своём боте: `await message.answer(str(message.from_user.id))`.

</aside>

## Роутеры: раскладываем код по файлам

`Router` — это контейнер для хэндлеров. Каждый файл создаёт свой роутер, а в главном файле все роутеры подключаются к диспетчеру.

Удобная структура проекта:

```text
my_bot/
├── bot.py              ← точка входа: создаём Bot и Dispatcher
├── .env
└── handlers/
    ├── __init__.py
    ├── common.py       ← /start, /help
    ├── admin.py        ← команды для админов
    └── echo.py         ← всё остальное
```

`handlers/common.py`:

```python
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет! Набери /help, чтобы узнать, что я умею.")


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("/start — начать\n/help — помощь")
```

`handlers/echo.py`:

```python
from aiogram import F, Router
from aiogram.types import Message

router = Router()


@router.message(F.text)
async def echo(message: Message):
    await message.answer(message.text)
```

`bot.py`:

```python
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from handlers import admin, common, echo

load_dotenv()


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher()

    # Порядок подключения = порядок проверки. Эхо — последним.
    dp.include_routers(common.router, admin.router, echo.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
```

Теперь каждый файл отвечает за своё, а `bot.py` остаётся коротким, как бы ни рос бот.

## Фильтр на весь роутер

Чтобы не писать `IsAdmin()` в каждом админском хэндлере, фильтр можно повесить на весь роутер сразу:

```python
# handlers/admin.py
router = Router()
router.message.filter(IsAdmin())   # все хэндлеры сообщений этого роутера — только для админов
```

## Практика

1.  Разложите эхо-бота из прошлого урока по структуре выше.
2.  Сделайте хэндлер, который на любой стикер отвечает «Классный стикер!».
3.  Добавьте админскую команду `/ping`, которая отвечает «pong» только вам.
