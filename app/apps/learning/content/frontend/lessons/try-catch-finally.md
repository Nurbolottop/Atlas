Ошибки в программе неизбежны: сервер не ответил, пользователь ввёл буквы вместо числа, в JSON пришёл мусор. Плохо, когда из-за одной ошибки «ломается» весь сайт. В этом уроке научимся **перехватывать ошибки** с помощью конструкции `try...catch...finally`, создавать свои ошибки через `throw` и правильно обрабатывать ошибки в асинхронном коде.

## Что происходит при ошибке

Если в коде возникает ошибка и её никто не обработал, JavaScript **останавливает** выполнение текущего скрипта:

```js
console.log("Начало");
const user = null;
console.log(user.name);   // TypeError: Cannot read properties of null
console.log("Конец");     // эта строка уже не выполнится
```

В консоли появится красное сообщение, а всё, что ниже ошибки, не выполнится. На реальном сайте это может означать неработающую кнопку или пустую страницу.

## Конструкция try...catch

`try...catch` — это «страховочная сетка». Мы говорим JavaScript: «Попробуй выполнить этот код. Если что-то сломается — не падай, а передай ошибку мне».

```js
try {
  // код, в котором может быть ошибка
} catch (error) {
  // что делать, если ошибка случилась
}
```

Перепишем пример:

```js
console.log("Начало");

try {
  const user = null;
  console.log(user.name);
  console.log("Эта строка не выполнится");
} catch (error) {
  console.log("Поймали ошибку:", error.message);
}

console.log("Конец"); // выполнится!
```

Результат:

```text
Начало
Поймали ошибку: Cannot read properties of null (reading 'name')
Конец
```

Как это работает:

1.  Выполняется код внутри `try`.
2.  Если ошибок нет — блок `catch` **пропускается**.
3.  Если ошибка возникла — выполнение `try` сразу прерывается, и управление переходит в `catch`.
4.  После `catch` программа продолжает работу как обычно.

Аналогия — акробат с сеткой. Если трюк получился — сетка не нужна. Если сорвался — сетка ловит, и представление продолжается.

### Объект ошибки

В `catch` попадает **объект ошибки** с полезными свойствами:

| Свойство | Что содержит | Пример |
| --- | --- | --- |
| `name` | тип ошибки | `"TypeError"` |
| `message` | понятное описание | `"Cannot read properties of null"` |
| `stack` | где именно произошла ошибка (цепочка вызовов) | для отладки |

```js
try {
  undefinedFunction();
} catch (error) {
  console.log(error.name);    // "ReferenceError"
  console.log(error.message); // "undefinedFunction is not defined"
}
```

Встроенные типы ошибок, которые вы будете встречать чаще всего:

-   `ReferenceError` — обращение к несуществующей переменной;
-   `TypeError` — действие не подходит для типа значения (например, вызвать не-функцию или прочитать свойство у `null`);
-   `SyntaxError` — неправильный синтаксис, например при `JSON.parse` некорректной строки;
-   `RangeError` — значение вне допустимого диапазона (например, переполнение стека при рекурсии).

## Практический пример: безопасный JSON.parse

Вспомните урок [про JSON и localStorage](lesson:json-storage-devtools). Если в `localStorage` лежит испорченная строка, `JSON.parse` выбросит ошибку — и весь скрипт остановится. Защитимся:

```js
function loadCart() {
  const raw = localStorage.getItem("cart");

  try {
    return JSON.parse(raw) ?? [];
  } catch (error) {
    console.warn("Корзина повреждена, начинаем с пустой:", error.message);
    localStorage.removeItem("cart");
    return [];
  }
}

localStorage.setItem("cart", "{это не json");
console.log(loadCart()); // [] — и сайт продолжает работать
```

Разбор:

-   Если в хранилище ничего нет, `getItem` вернёт `null`, `JSON.parse(null)` вернёт `null`, и оператор `??` подставит пустой массив.
-   Если строка испорчена, `JSON.parse` выбросит `SyntaxError`, мы попадём в `catch`, удалим мусор и вернём пустую корзину.

## Блок finally

`finally` выполняется **всегда**: была ошибка или нет, и даже если внутри `try` или `catch` сработал `return`.

```js
function divide(a, b) {
  try {
    if (b === 0) throw new Error("Делить на ноль нельзя");
    return a / b;
  } catch (error) {
    console.log("Ошибка:", error.message);
    return null;
  } finally {
    console.log("Операция деления завершена");
  }
}

console.log(divide(10, 2)); // "Операция деления завершена", потом 5
console.log(divide(10, 0)); // "Ошибка: ...", "Операция деления завершена", потом null
```

Зачем нужен `finally`? Для «уборки», которая должна произойти в любом случае:

-   спрятать индикатор загрузки (спиннер);
-   снова разблокировать кнопку отправки формы;
-   закрыть соединение или сбросить флаг.

```js
const button = document.querySelector("#save");

function save() {
  button.disabled = true;
  button.textContent = "Сохраняем...";
  try {
    // какая-то работа, которая может упасть
    saveToStorage();
  } catch (error) {
    alert("Не удалось сохранить");
  } finally {
    button.disabled = false;      // кнопка вернётся в любом случае
    button.textContent = "Сохранить";
  }
}
```

Можно писать `try...finally` и без `catch` — тогда ошибка не перехватится, но «уборка» всё равно выполнится.

## Создаём свои ошибки: throw

Оператор `throw` («бросить») позволяет **самим** создать ошибку, когда что-то пошло не по плану.

```js
function setAge(age) {
  if (typeof age !== "number" || Number.isNaN(age)) {
    throw new TypeError("Возраст должен быть числом");
  }
  if (age < 0 || age > 120) {
    throw new RangeError("Возраст должен быть от 0 до 120");
  }
  return age;
}

try {
  setAge(150);
} catch (error) {
  console.log(`${error.name}: ${error.message}`);
  // "RangeError: Возраст должен быть от 0 до 120"
}
```

-   `throw` немедленно прерывает функцию — как `return`, но с ошибкой.
-   Бросать можно что угодно, но правильно бросать **объект `Error`** (или его разновидности): у него есть `message` и `stack`.

<aside class="callout" data-icon="⚠️" markdown="1">

Не пишите `throw "Ошибка!"` строкой. У строки нет `message` и `stack`, и код вида `error.message` в `catch` вернёт `undefined`. Всегда используйте `throw new Error("...")`.

</aside>

### Свой класс ошибки

Когда ошибок много, удобно отличать их по типу. Для этого создают собственный класс, наследуя `Error`:

```js
class ValidationError extends Error {
  constructor(field, message) {
    super(message);              // передаём сообщение в родительский Error
    this.name = "ValidationError";
    this.field = field;          // дополнительная информация — какое поле
  }
}

function validateUser(user) {
  if (!user.email.includes("@")) {
    throw new ValidationError("email", "Неверный email");
  }
}

try {
  validateUser({ email: "anna.mail.com" });
} catch (error) {
  if (error instanceof ValidationError) {
    console.log(`Поле ${error.field}: ${error.message}`);
  } else {
    throw error; // неизвестную ошибку не «глотаем», а пробрасываем дальше
  }
}
```

-   `extends Error` — наш класс умеет всё, что умеет обычная ошибка.
-   `instanceof` проверяет, к какому классу относится ошибка.
-   **Проброс** (`throw error` в `catch`) — если ошибка не та, которую мы умеем обрабатывать, отдаём её выше. Так мы не скрываем настоящие баги.

## Ошибки в асинхронном коде

### Ловушка с setTimeout

`try...catch` работает **синхронно**. Он не поймает ошибку, которая случится позже, внутри колбэка:

```js
try {
  setTimeout(() => {
    throw new Error("Ошибка в таймере");
  }, 1000);
} catch (error) {
  console.log("Поймали?"); // НЕ выполнится
}
```

Почему так? Вспомните урок [про Event Loop](lesson:event-loop-i-promise): к моменту, когда сработает таймер, блок `try` давно закончился — стек вызовов пуст. Ловить ошибку надо **внутри** колбэка:

```js
setTimeout(() => {
  try {
    throw new Error("Ошибка в таймере");
  } catch (error) {
    console.log("Поймали:", error.message);
  }
}, 1000);
```

### Ошибки в промисах

У промисов есть свои аналоги: `.catch` вместо `catch`, `.finally` вместо `finally`. Если внутри `.then` выбросить ошибку через `throw`, промис станет `rejected` и ошибка уйдёт в ближайший `.catch`:

```js
function getUser(id) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      id > 0 ? resolve({ id, name: "Анна" }) : reject(new Error("Пользователь не найден"));
    }, 500);
  });
}

showLoader();

getUser(1)
  .then((user) => {
    if (!user.email) throw new Error("У пользователя нет email");
    return user;
  })
  .then((user) => console.log(user))
  .catch((error) => console.log("Ошибка:", error.message)) // "У пользователя нет email"
  .finally(() => hideLoader());
```

| Синхронный код | Промисы |
| --- | --- |
| `try { ... }` | `.then(...)` |
| `catch (error) { ... }` | `.catch((error) => ...)` |
| `finally { ... }` | `.finally(() => ...)` |
| `throw new Error()` | `throw` внутри `.then` или `reject(new Error())` |

### Забегая вперёд: try...catch с await

Есть способ писать асинхронный код так, чтобы обычный `try...catch` работал и для промисов. Для этого функцию помечают словом `async`, а перед промисом пишут `await` — «дождись результата». Подробно разберём это в уроке [про fetch и async/await](lesson:fetch-async-await-get), а пока просто посмотрите, как это выглядит:

```js
async function showUser() {
  showLoader();
  try {
    const user = await getUser(-1); // ждём промис
    console.log(user.name);
  } catch (error) {
    console.log("Ошибка:", error.message); // "Пользователь не найден"
  } finally {
    hideLoader();
  }
}

showUser();
```

Здесь `await` превращает отклонённый промис в обычную ошибку, которую ловит `catch`. Код читается как синхронный — сверху вниз.

<aside class="callout" data-icon="💡" markdown="1">

Функции `showLoader()`, `hideLoader()` и `saveToStorage()` в примерах — заглушки, в проекте вы напишете их сами. Например, `showLoader` и `hideLoader` могут добавлять и убирать класс `hidden` у элемента со спиннером, а `saveToStorage` — записывать данные в `localStorage`.

</aside>

## Как правильно обрабатывать ошибки

-   **Не оборачивайте в `try` всё подряд.** Ставьте его там, где ошибка реально возможна: разбор JSON, запросы к серверу, работа с данными от пользователя.
-   **Не «глотайте» ошибки.** Пустой `catch {}` скрывает баги. Хотя бы выведите `console.error(error)`.
-   **Показывайте пользователю понятное сообщение**, а технические детали — в консоль.
-   **Используйте `finally`** для действий, которые нужны в любом исходе.

```js
try {
  riskyOperation();
} catch (error) {
  console.error(error);                                     // для разработчика
  showMessage("Что-то пошло не так. Попробуйте ещё раз.");  // для пользователя
}
```

<aside class="callout" data-icon="🔐" markdown="1">

Не показывайте пользователю `error.stack` и внутренние подробности ошибок сервера: они могут раскрыть устройство вашей системы. Пользователю — простой текст, подробности — только в консоль или в систему логирования.

</aside>

Справка: [MDN: try...catch](https://developer.mozilla.org/ru/docs/Web/JavaScript/Reference/Statements/try...catch).

## Практика

1.  **Безопасное число.** Напишите функцию `parseNumber(str)`, которая возвращает число из строки, а если строка не число — выбрасывает `Error("Это не число")`. Вызовите её с `"42"` и `"abc"` внутри `try...catch` и выведите результат или сообщение об ошибке.
2.  **finally.** Добавьте к первому заданию блок `finally`, который выводит «Проверка завершена». Убедитесь, что он срабатывает в обоих случаях.
3.  **Загрузка настроек.** Напишите `loadSettings()`, которая читает объект `settings` из `localStorage`. Если там испорченный JSON — вернуть объект по умолчанию `{ theme: "light", lang: "ru" }`. Проверьте, записав в хранилище строку `"{oops"`.
4.  **Свой класс.** Создайте класс `NotFoundError` и функцию `findProduct(id)`, которая ищет товар в массиве и выбрасывает `NotFoundError`, если не нашла. В `catch` выведите разное сообщение для `NotFoundError` и для остальных ошибок.
5.  **Промис с обработкой.** Используя `getUser` из урока, напишите цепочку, которая показывает текст «Загрузка...» в элементе на странице, затем имя пользователя или текст ошибки, а в `.finally` выводит в консоль «Готово».

## Итоги

-   Необработанная ошибка останавливает выполнение скрипта.
-   `try` — пробуем, `catch` — обрабатываем ошибку, `finally` — выполняем в любом случае.
-   У объекта ошибки есть `name`, `message` и `stack`.
-   `throw new Error("...")` создаёт свою ошибку; можно наследовать `Error` для своих типов.
-   Обычный `try...catch` не ловит ошибки из колбэков `setTimeout` — их ловят внутри колбэка.
-   В промисах роль `catch` и `finally` играют `.catch()` и `.finally()`, а с `await` работает обычный `try...catch`.
