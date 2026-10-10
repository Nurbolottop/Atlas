Представьте бота для записи на курс. Он должен спросить имя, потом возраст, потом телефон — и всё это по очереди. Но каждый ответ пользователя приходит отдельным сообщением, и хэндлер не помнит, о чём бот спрашивал секунду назад.

Эту задачу решает **FSM** (Finite State Machine, конечный автомат) — механизм состояний. Бот запоминает для каждого пользователя: «сейчас я жду от тебя имя» или «сейчас жду возраст».

## Как это выглядит со стороны пользователя

```text
Пользователь: /register
Бот:          Как вас зовут?
Пользователь: Айбек
Бот:          Сколько вам лет?
Пользователь: двадцать
Бот:          Напишите возраст цифрами, например 20
Пользователь: 20
Бот:          Отправьте номер телефона
Пользователь: +996 555 123 456
Бот:          Готово! Айбек, 20 лет, +996 555 123 456
```

## Шаг 1. Описываем состояния

Состояния — это «шаги» анкеты. Описываются классом:

```python
from aiogram.fsm.state import State, StatesGroup


class Register(StatesGroup):
    name = State()    # ждём имя
    age = State()     # ждём возраст
    phone = State()   # ждём телефон
```

## Шаг 2. Пишем хэндлеры

Каждому хэндлеру aiogram может передать объект `state: FSMContext` — через него мы меняем состояние и храним ответы.

```python
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router()


@router.message(Command("register"))
async def start_register(message: Message, state: FSMContext):
    await state.set_state(Register.name)              # переходим к шагу «имя»
    await message.answer("Как вас зовут?")


@router.message(Register.name, F.text)
async def got_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)        # запоминаем ответ
    await state.set_state(Register.age)               # следующий шаг
    await message.answer("Сколько вам лет?")


@router.message(Register.age, F.text)
async def got_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        # Состояние не меняем — бот снова ждёт возраст
        await message.answer("Напишите возраст цифрами, например 20")
        return
    await state.update_data(age=int(message.text))
    await state.set_state(Register.phone)
    await message.answer("Отправьте номер телефона")


@router.message(Register.phone, F.text)
async def got_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    data = await state.get_data()                     # всё, что собрали
    await state.clear()                               # анкета закончена, сбрасываем состояние
    await message.answer(f"Готово! {data['name']}, {data['age']} лет, {data['phone']}")
```

Главное здесь — **фильтр по состоянию**: `@router.message(Register.age, F.text)` сработает, только если пользователь сейчас на шаге «возраст». Поэтому одно и то же слово «20» в разных состояниях попадёт в разные хэндлеры.

## Методы FSMContext

| Метод | Что делает |
| --- | --- |
| `await state.set_state(Register.age)` | Переключает пользователя на нужный шаг |
| `await state.update_data(age=20)` | Добавляет данные к уже собранным |
| `await state.get_data()` | Возвращает словарь со всеми собранными данными |
| `await state.get_state()` | Текущее состояние (или `None`) |
| `await state.clear()` | Сбрасывает и состояние, и данные |

## Кнопка «Отмена»

Пользователь должен иметь возможность выйти из анкеты в любой момент. Хэндлер отмены ставим **выше** остальных хэндлеров анкеты:

```python
from aiogram.filters import StateFilter


@router.message(StateFilter("*"), Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    if await state.get_state() is None:
        await message.answer("Отменять нечего 🙂")
        return
    await state.clear()
    await message.answer("Регистрация отменена")
```

`StateFilter("*")` означает «в любом состоянии».

## Где хранятся состояния

По умолчанию aiogram хранит состояния в оперативной памяти (`MemoryStorage`). Это удобно для разработки, но после перезапуска бота все незаконченные анкеты пропадут.

В продакшене состояния хранят в Redis — они переживут перезапуск:

```bash
pip install redis
```

```python
from aiogram.fsm.storage.redis import RedisStorage

storage = RedisStorage.from_url("redis://localhost:6379/0")
dp = Dispatcher(storage=storage)
```

Код хэндлеров при этом не меняется ни на строчку.

<aside class="callout" data-icon="💡" markdown="1">

FSM пригодится везде, где бот ведёт диалог из нескольких шагов: оформление заказа, анкета, квиз, обратная связь, создание поста админом.

</aside>

## Практика

1.  Добавьте в анкету шаг «город» между возрастом и телефоном.
2.  На шаге телефона покажите reply-кнопку «📱 Отправить номер» с `request_contact=True` и примите `F.contact`.
3.  В конце покажите inline-кнопки «✅ Всё верно» и «✏️ Заполнить заново».
