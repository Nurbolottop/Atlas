Пока бот запущен у вас на компьютере, он работает, только когда компьютер включён. Чтобы бот был онлайн круглосуточно, его запускают на сервере. В этом уроке разберём два способа: простой (Docker + polling) и продакшен-вариант (webhook).

## Подготовка проекта

Зафиксируйте библиотеки, чтобы на сервере стояли те же версии, что у вас:

```bash
pip freeze > requirements.txt
```

Итоговая структура:

```text
my_bot/
├── bot.py
├── db.py
├── handlers/
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env            ← на сервер копируем отдельно, в git его нет
└── .gitignore
```

## Способ 1. Docker + polling

Docker упаковывает бота вместе с Python и всеми библиотеками в «контейнер», который одинаково запускается на любом сервере.

`Dockerfile`:

```docker
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

`docker-compose.yml`:

```yaml
services:
  bot:
    build: .
    env_file: .env
    restart: always          # бот сам поднимется после падения или перезагрузки сервера
    volumes:
      - ./data:/app/data     # база данных живёт снаружи контейнера и не пропадёт при обновлении
```

Если бот использует SQLite, поменяйте путь к базе на `data/bot.db`, чтобы файл попадал в подключённую папку.

### Запуск на сервере

```bash
# 1. Подключаемся к серверу
ssh root@ваш-сервер

# 2. Забираем код
git clone https://github.com/you/my_bot.git
cd my_bot

# 3. Создаём .env с токеном (в репозитории его нет)
nano .env

# 4. Собираем и запускаем в фоне
docker compose up --build -d

# Логи бота в реальном времени
docker compose logs -f bot
```

Обновление после новых коммитов:

```bash
git pull
docker compose up --build -d
```

<aside class="callout" data-icon="⚠️" markdown="1">

Один токен — один запущенный бот. Если бот одновременно запущен у вас на ноутбуке и на сервере, Telegram вернёт ошибку `Conflict: terminated by other getUpdates request`. Остановите локальную копию.

</aside>

## Способ 2. Webhook

При polling бот постоянно спрашивает Telegram о новых сообщениях. При webhook Telegram сам присылает каждое сообщение на ваш сервер — это быстрее и экономит ресурсы. Нужны: сервер, домен и HTTPS (например, nginx + бесплатный сертификат Let's Encrypt).

aiogram запускает небольшой веб-сервер на `aiohttp` (он ставится вместе с aiogram):

```python
import os

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv

from handlers import common, echo

load_dotenv()

BASE_URL = "https://bot.example.com"     # ваш домен
WEBHOOK_PATH = "/webhook"
SECRET = os.getenv("WEBHOOK_SECRET")     # случайная строка — защита от чужих запросов


async def on_startup(bot: Bot):
    await bot.set_webhook(f"{BASE_URL}{WEBHOOK_PATH}", secret_token=SECRET)


def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher()
    dp.include_routers(common.router, echo.router)
    dp.startup.register(on_startup)

    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=SECRET).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    web.run_app(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
```

Обратите внимание: хэндлеры и роутеры остались прежними — меняется только способ запуска.

nginx принимает HTTPS и передаёт запросы боту:

```nginx
location /webhook {
    proxy_pass http://127.0.0.1:8080;
}
```

## Polling или webhook?

| | Polling | Webhook |
| --- | --- | --- |
| Нужен домен и HTTPS | Нет | Да |
| Настройка | Минимальная | nginx, сертификат |
| Скорость ответа | Хорошая | Лучше |
| Для чего | Разработка, небольшие боты | Нагруженные боты |

Для большинства ботов polling в Docker с `restart: always` — надёжный и достаточный вариант.

## Чек-лист перед запуском

-   Токен лежит в `.env`, а `.env` — в `.gitignore`.
-   Включено логирование `logging.basicConfig(level=logging.INFO)`.
-   Состояния FSM хранятся в Redis, если важно не терять незаконченные диалоги.
-   База данных лежит в volume и не пропадёт при пересборке.
-   В `docker-compose.yml` стоит `restart: always`.

## Итоговый проект темы

Соберите всё, что прошли, в одного бота:

1.  `/start` регистрирует пользователя в базе и показывает главное меню из reply-кнопок.
2.  Кнопка «📚 Курсы» показывает каталог на inline-кнопках с `CallbackData`.
3.  Кнопка «Записаться» запускает анкету на FSM: имя → телефон → подтверждение.
4.  Заявки сохраняются в базу, а админ получает уведомление: `await bot.send_message(ADMIN_ID, текст)`.
5.  Middleware защищает от флуда.
6.  Бот запущен на сервере в Docker.
