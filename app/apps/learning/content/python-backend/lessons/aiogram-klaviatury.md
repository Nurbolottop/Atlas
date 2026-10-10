Писать команды руками неудобно — пользователи любят кнопки. В Telegram есть два вида клавиатур, и они работают по-разному:

| | Reply-клавиатура | Inline-клавиатура |
| --- | --- | --- |
| Где появляется | Вместо обычной клавиатуры телефона | Прямо под сообщением бота |
| Что отправляет | Обычное текстовое сообщение с текстом кнопки | Невидимый сигнал `callback_query` |
| Когда использовать | Главное меню, «Отправить номер» | Выбор в сообщении, «Купить», «Далее →» |

## Reply-клавиатура

```python
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 Курсы"), KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="❓ Помощь")],
    ],
    resize_keyboard=True,                 # кнопки компактные, а не на пол-экрана
    input_field_placeholder="Выберите пункт меню",
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Главное меню:", reply_markup=main_menu)
```

Каждый вложенный список — это ряд кнопок. Нажатие на кнопку просто отправляет её текст, поэтому ловим его обычным фильтром:

```python
@router.message(F.text == "📚 Курсы")
async def show_courses(message: Message):
    await message.answer("Скоро здесь будет список курсов")
```

Убрать клавиатуру:

```python
from aiogram.types import ReplyKeyboardRemove

await message.answer("Клавиатура скрыта", reply_markup=ReplyKeyboardRemove())
```

### Запросить номер телефона

Reply-кнопка умеет попросить у пользователя контакт — Telegram сам покажет окно подтверждения:

```python
phone_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Отправить номер", request_contact=True)]],
    resize_keyboard=True,
)


@router.message(F.contact)
async def got_contact(message: Message):
    await message.answer(f"Спасибо! Ваш номер: {message.contact.phone_number}")
```

## Inline-клавиатура

Inline-кнопки висят под сообщением. Каждая кнопка либо открывает ссылку (`url`), либо отправляет боту `callback_data` — короткую строку до 64 байт.

```python
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👍 Нравится", callback_data="like"),
     InlineKeyboardButton(text="👎 Не нравится", callback_data="dislike")],
    [InlineKeyboardButton(text="Сайт курса", url="https://example.com")],
])


@router.message(Command("vote"))
async def cmd_vote(message: Message):
    await message.answer("Как вам урок?", reply_markup=kb)
```

Нажатие ловится хэндлером **callback_query**, а не message:

```python
from aiogram.types import CallbackQuery


@router.callback_query(F.data == "like")
async def on_like(callback: CallbackQuery):
    await callback.message.edit_text("Спасибо за оценку! 👍")
    await callback.answer()


@router.callback_query(F.data == "dislike")
async def on_dislike(callback: CallbackQuery):
    await callback.answer("Жаль 😔 Напишите, что улучшить", show_alert=True)
```

-   `callback.data` — та самая строка из `callback_data`.
-   `callback.message.edit_text()` — меняет текст сообщения с кнопками, вместо того чтобы присылать новое. Так чат остаётся чистым.
-   `callback.answer()` — **обязательно** вызывайте его: иначе на кнопке ещё ~15 секунд будут крутиться «часики». С `show_alert=True` пользователь увидит всплывающее окно.

## Билдеры: клавиатуры из данных

Когда кнопок много или они берутся из базы, удобнее «строить» клавиатуру в цикле:

```python
from aiogram.utils.keyboard import InlineKeyboardBuilder

COURSES = ["Python", "Django", "Базы данных", "Git", "aiogram"]


def courses_kb():
    builder = InlineKeyboardBuilder()
    for index, title in enumerate(COURSES):
        builder.button(text=title, callback_data=f"course_{index}")
    builder.adjust(2)  # по 2 кнопки в ряд
    return builder.as_markup()
```

Для reply-клавиатуры есть такой же `ReplyKeyboardBuilder` — только в конце `builder.as_markup(resize_keyboard=True)`.

## CallbackData: данные в кнопках без путаницы

Строки вида `course_3` приходится вручную разбирать через `split`. aiogram умеет делать это за вас — описываем структуру данных кнопки классом:

```python
from aiogram.filters.callback_data import CallbackData


class ProductCb(CallbackData, prefix="product"):
    action: str   # что сделать: "buy" или "info"
    id: int       # какой товар
```

Создаём кнопки:

```python
def product_kb(product_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="ℹ️ Подробнее", callback_data=ProductCb(action="info", id=product_id))
    builder.button(text="🛒 Купить", callback_data=ProductCb(action="buy", id=product_id))
    return builder.as_markup()
```

И ловим нажатия — aiogram сам разберёт строку обратно в объект:

```python
@router.callback_query(ProductCb.filter(F.action == "buy"))
async def buy(callback: CallbackQuery, callback_data: ProductCb):
    await callback.answer(f"Товар №{callback_data.id} добавлен в корзину 🛒")


@router.callback_query(ProductCb.filter(F.action == "info"))
async def info(callback: CallbackQuery, callback_data: ProductCb):
    await callback.message.answer(f"Описание товара №{callback_data.id}")
    await callback.answer()
```

Внутри кнопки хранится строка `product:buy:7`, но вы работаете с удобным объектом `callback_data.action` и `callback_data.id`.

## Практика

1.  Сделайте главное меню из трёх reply-кнопок и ответ на каждую.
2.  Сделайте inline-счётчик: кнопки «−» и «+», которые меняют число в сообщении через `edit_text`.
3.  Сделайте каталог из 5 товаров через `InlineKeyboardBuilder` и `CallbackData`.
