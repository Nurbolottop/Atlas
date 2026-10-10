Напишем бота, который здоровается по команде `/start`, подсказывает по `/help` и повторяет всё, что ему пишут. Это классический «эхо-бот» — на нём хорошо видно, как aiogram устроен изнутри.

## Полный код

Создайте файл `bot.py`:

```python
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()

dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    name = message.from_user.first_name
    await message.answer(f"Привет, {name}! Я эхо-бот. Напиши мне что-нибудь.")


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("Я повторяю твои сообщения. Команды: /start, /help")


@dp.message(F.text)
async def echo(message: Message):
    await message.answer(message.text)


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
```

Запустите:

```bash
python bot.py
```

Откройте своего бота в Telegram, нажмите «Запустить» — бот поздоровается по имени. Остановить бота можно сочетанием `Ctrl+C` в терминале.

## Разбираем по строчкам

### Диспетчер

```python
dp = Dispatcher()
```

Диспетчер — центр бота. Он получает обновления от Telegram и по очереди проверяет хэндлеры: «подходит ли это сообщение тебе?». Первый подходящий хэндлер и обработает сообщение.

### Хэндлер команды /start

```python
@dp.message(CommandStart())
async def cmd_start(message: Message):
    ...
```

-   `@dp.message(...)` — декоратор, который регистрирует функцию как обработчик **сообщений**. Если вы не помните, как работают декораторы, — загляните в урок [Декораторы](lesson:dekoratory).
-   `CommandStart()` — **фильтр**: хэндлер сработает только на команду `/start`.
-   `async def` — функция асинхронная, потому что внутри она ждёт ответа от Telegram.
-   `message: Message` — aiogram сам передаёт объект сообщения. В нём есть всё: текст, автор, чат, время.

### Ответ пользователю

```python
await message.answer("Привет!")
```

`message.answer()` отправляет новое сообщение в тот же чат. `await` означает «отправь и дождись, пока Telegram подтвердит». Без `await` сообщение не уйдёт.

Есть и другие способы ответить:

```python
await message.answer("Просто ответ в чат")
await message.reply("Ответ с цитатой исходного сообщения")
await message.answer_photo(photo="https://picsum.photos/400", caption="Картинка")
```

### Эхо

```python
@dp.message(F.text)
async def echo(message: Message):
    await message.answer(message.text)
```

`F.text` — «у сообщения есть текст». Значит, хэндлер сработает на любой текст, но не на стикер или фото.

<aside class="callout" data-icon="⚠️" markdown="1">

**Порядок хэндлеров важен.** Диспетчер проверяет их сверху вниз. Если поставить `echo` первым, он перехватит и `/start` — ведь `/start` тоже текст. Поэтому конкретные хэндлеры (команды) пишем выше общих.

</aside>

### Запуск

```python
async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    await dp.start_polling(bot)
```

-   `logging` выводит в терминал, что происходит с ботом, — без этого ошибки легко пропустить.
-   `Bot(token=...)` — объект для общения с Telegram API.
-   `start_polling` запускает бесконечный цикл опроса Telegram. Пока он работает — бот онлайн.

## Что лежит внутри message

Объект `Message` — ваш главный источник информации. Самые нужные поля:

| Поле | Что внутри |
| --- | --- |
| `message.text` | Текст сообщения (или `None`, если это фото/стикер) |
| `message.from_user.id` | Уникальный id пользователя — пригодится для базы данных |
| `message.from_user.first_name` | Имя пользователя |
| `message.from_user.username` | @username (может отсутствовать) |
| `message.chat.id` | id чата, куда пришло сообщение |
| `message.date` | Дата и время отправки |

## Команды с аргументами

Иногда команде нужен параметр, например `/weather Бишкек`. Аргументы достаются через `CommandObject`:

```python
from aiogram.filters import Command, CommandObject


@dp.message(Command("weather"))
async def cmd_weather(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("Напиши город: /weather Бишкек")
        return
    await message.answer(f"Смотрю погоду в городе {command.args}…")
```

`command.args` — всё, что написано после команды. Если пользователь ничего не написал, там `None`.

## Практика

1.  Добавьте команду `/about`, которая рассказывает о боте.
2.  Сделайте так, чтобы эхо отвечало текстом в верхнем регистре (`message.text.upper()`).
3.  Добавьте команду `/sum 2 3`, которая складывает два числа. Подсказка: `command.args.split()`.
