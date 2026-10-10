Функции — главный строительный блок JavaScript: они позволяют один раз описать действие и использовать его сколько угодно раз. В этом уроке разберём, как объявлять функции, что такое **параметры** и **return**, чем отличаются **анонимные** и **стрелочные** функции, как работают **замыкания** и **колбэки**. А в конце применим всё это к DOM и событиям, чтобы код интерактивных страниц стал короче и чище.

## Что такое функция

**Функция** — это именованный кусок кода, который можно вызвать в любой момент. Аналогия — рецепт: вы записали его один раз, а готовить по нему можете каждый день, подставляя разные продукты.

```js
function greet() {
  console.log("Привет!");
}

greet(); // Привет!
greet(); // Привет!
```

-   `function` — ключевое слово «объявляю функцию»;
-   `greet` — имя функции (обычно глагол: `show`, `calculate`, `get`);
-   `()` — место для параметров;
-   `{ ... }` — тело функции, код, который выполнится при вызове;
-   `greet()` — **вызов**: скобки после имени запускают функцию.

### Параметры и аргументы

Функции можно передавать данные:

```js
function greet(name) {
  console.log(`Привет, ${name}!`);
}

greet("Айбек");  // Привет, Айбек!
greet("Мээрим"); // Привет, Мээрим!
```

`name` — **параметр** (переменная внутри функции), а `"Айбек"` — **аргумент** (значение, переданное при вызове). Параметров может быть несколько, и им можно задать значения по умолчанию:

```js
function createUser(name, role = "student") {
  console.log(`${name} — ${role}`);
}

createUser("Данияр");           // Данияр — student
createUser("Асель", "mentor");  // Асель — mentor
```

### return — вернуть результат

Чаще всего функция не печатает, а **возвращает** значение, чтобы его можно было использовать дальше:

```js
function sum(a, b) {
  return a + b;
}

const result = sum(2, 3);
console.log(result);        // 5
console.log(sum(10, 20) * 2); // 60
```

`return` делает две вещи: отдаёт значение наружу и **сразу завершает** функцию — код после него не выполнится. Если `return` нет, функция возвращает `undefined`.

```js
function checkAge(age) {
  if (age < 18) {
    return "Доступ запрещён";
  }
  return "Добро пожаловать";
}
console.log(checkAge(15)); // Доступ запрещён
```

<aside class="callout" data-icon="⚠️" markdown="1">

Частая путаница: `console.log` внутри функции только **показывает** значение, но не возвращает его. `const x = greet("Ali")` даст `undefined`, если в `greet` нет `return`.

</aside>

### Область видимости

Переменные, объявленные внутри функции, **не видны снаружи**:

```js
function calc() {
  const secret = 42;
  return secret * 2;
}
console.log(calc());   // 84
// console.log(secret); // ReferenceError: secret is not defined
```

А вот функция видит переменные снаружи себя — это основа замыканий, о которых ниже.

## Способы объявить функцию

### Function Declaration

```js
function multiply(a, b) {
  return a * b;
}
```

Такую функцию можно вызвать **даже до** её объявления в коде — браузер заранее «поднимает» её (hoisting).

### Function Expression и анонимные функции

**Анонимная функция** — функция без имени. Её можно положить в переменную:

```js
const multiply = function (a, b) {
  return a * b;
};
console.log(multiply(3, 4)); // 12
```

Такую функцию можно вызвать только **после** строки, где она создана. Анонимные функции чаще всего передают в другие функции — например, в `addEventListener` или `setTimeout`:

```js
setTimeout(function () {
  console.log("Прошло 2 секунды");
}, 2000);
```

### Стрелочные функции

Короткий синтаксис из ES6:

```js
const multiply = (a, b) => {
  return a * b;
};

// если тело — одно выражение, можно без {} и return:
const square = (x) => x * x;
const sayHi = () => console.log("Hi");

console.log(square(5)); // 25
```

Правила записи:

-   нет параметров — пустые скобки `() => ...`;
-   один параметр — скобки можно опустить: `x => x * 2` (но с ними привычнее);
-   тело без `{}` автоматически возвращает результат;
-   чтобы вернуть объект без `return`, оберните его в скобки: `() => ({ id: 1 })`.

| | Declaration | Expression | Стрелочная |
| --- | --- | --- | --- |
| Синтаксис | `function f() {}` | `const f = function () {}` | `const f = () => {}` |
| Вызов до объявления | Можно | Нельзя | Нельзя |
| Свой `this` | Есть | Есть | Нет, берёт снаружи |

<aside class="callout" data-icon="💡" markdown="1">

У стрелочных функций нет собственного `this`. Поэтому для **методов объекта** (где нужен `this`) используйте обычную запись `method() {}`, а стрелки — для колбэков и коротких функций.

</aside>

## Колбэки

**Колбэк** (callback, «обратный вызов») — функция, которую передают другой функции как аргумент, чтобы та вызвала её позже. Аналогия: вы оставляете в кафе номер телефона — «перезвоните, когда заказ будет готов». Номер телефона — это колбэк.

```js
function processOrder(dish, onReady) {
  console.log(`Готовим: ${dish}...`);
  onReady(dish); // вызываем переданную функцию
}

processOrder("плов", (name) => {
  console.log(`${name} готов, забирайте!`);
});
```

Разбор:

1.  `processOrder` принимает второй параметр `onReady` — это функция.
2.  При вызове мы передаём туда стрелочную функцию — **не вызывая её**.
3.  Внутри `processOrder` в нужный момент делаем `onReady(dish)`.

Одну и ту же функцию можно использовать с разными колбэками — это делает код гибким:

```js
function repeat(times, action) {
  for (let i = 1; i <= times; i++) {
    action(i);
  }
}

repeat(3, (n) => console.log("Шаг", n));
repeat(2, (n) => console.log("★".repeat(n)));
```

Колбэки вы уже использовали: обработчик в `addEventListener` — колбэк, функция в `setTimeout` — тоже. Методы массивов `map`, `filter`, `forEach` тоже принимают колбэки — их разберём в уроке [Методы перебора массива](lesson:metody-perebora-massiva).

<aside class="callout" data-icon="📌" markdown="1">

Передаём колбэк **без скобок**: `button.addEventListener("click", handleClick)`. Со скобками `handleClick()` функция выполнится сразу, а в обработчик попадёт её результат (обычно `undefined`).

</aside>

## Замыкания

**Замыкание** — это способность функции **помнить переменные** того места, где она была создана, даже когда это место уже «закончило работу».

```js
function createCounter() {
  let count = 0;

  return function () {
    count++;
    return count;
  };
}

const counter = createCounter();
console.log(counter()); // 1
console.log(counter()); // 2
console.log(counter()); // 3

const another = createCounter();
console.log(another()); // 1 — у него свой count
```

Разбор по шагам:

1.  `createCounter()` создаёт переменную `count = 0` и возвращает внутреннюю функцию.
2.  `createCounter` закончила работу, но внутренняя функция **по-прежнему видит** `count` — она «замкнула» её в себе.
3.  Каждый вызов `counter()` увеличивает именно этот `count`.
4.  Новый вызов `createCounter()` создаёт **новую** переменную `count` — у `another` свой независимый счётчик.

Аналогия: функция уходит из дома с рюкзаком, в котором лежат переменные этого дома. Куда бы она ни пошла, рюкзак при ней.

### Зачем нужны замыкания

-   **Скрыть данные**: к `count` нельзя обратиться снаружи и случайно испортить — только через функцию.
-   **Создавать настроенные функции**:

```js
function makeDiscount(percent) {
  return (price) => price - (price * percent) / 100;
}

const sale10 = makeDiscount(10);
const sale50 = makeDiscount(50);

console.log(sale10(1000)); // 900
console.log(sale50(1000)); // 500
```

`sale10` и `sale50` — разные функции, каждая помнит свой `percent`.

## DOM и события на функциях

В уроке [Введение в DOM](lesson:vvedenie-v-dom) мы писали обработчики прямо внутри `addEventListener`. Теперь вынесем логику в функции — код станет понятнее и его можно переиспользовать.

### Именованные обработчики

```html
<button id="like-btn">♡ Нравится</button>
<span id="likes">0</span>
```

```js
const likeBtn = document.querySelector("#like-btn");
const likesEl = document.querySelector("#likes");
let likes = 0;
let liked = false;

function render() {
  likesEl.textContent = likes;
  likeBtn.textContent = liked ? "♥ Нравится" : "♡ Нравится";
}

function handleLike() {
  liked = !liked;
  likes += liked ? 1 : -1;
  render();
}

likeBtn.addEventListener("click", handleLike);
render();
```

-   `render` отвечает только за отображение;
-   `handleLike` — за логику;
-   у обработчика есть имя, поэтому его можно снять: `likeBtn.removeEventListener("click", handleLike)`. Анонимную функцию так снять нельзя — на неё нет ссылки.

### Фабрика обработчиков через замыкание

Нужно сделать несколько кнопок, которые меняют размер шрифта:

```html
<button class="size-btn" data-size="14">Мелкий</button>
<button class="size-btn" data-size="18">Средний</button>
<button class="size-btn" data-size="24">Крупный</button>
<p id="article">Пример текста статьи.</p>
```

```js
const article = document.querySelector("#article");

function makeSizeHandler(size) {
  return () => {
    article.style.fontSize = `${size}px`;
  };
}

const buttons = document.querySelectorAll(".size-btn");
for (const btn of buttons) {
  btn.addEventListener("click", makeSizeHandler(btn.dataset.size));
}
```

`makeSizeHandler(size)` возвращает функцию-обработчик, которая через замыкание помнит свой `size`. Атрибут `data-size` в HTML читается в JavaScript как `btn.dataset.size`.

### Делегирование событий

Если элементов много или они добавляются динамически, удобно повесить **один** обработчик на родителя. События «всплывают» от элемента вверх по дереву, поэтому родитель узнает о клике по любому ребёнку:

```html
<ul id="menu">
  <li data-page="home">Главная</li>
  <li data-page="catalog">Каталог</li>
  <li data-page="contacts">Контакты</li>
</ul>
<p id="current"></p>
```

```js
const menu = document.querySelector("#menu");
const current = document.querySelector("#current");

function handleMenuClick(event) {
  const item = event.target.closest("li");
  if (!item) return; // клик мимо пункта

  for (const li of menu.children) {
    li.classList.remove("active");
  }
  item.classList.add("active");
  current.textContent = `Открыта страница: ${item.dataset.page}`;
}

menu.addEventListener("click", handleMenuClick);
```

`event.target.closest("li")` находит ближайший `li` от места клика вверх по дереву — это работает, даже если внутри пункта будут иконки или `span`.

### Задержка и debounce

Комбинация замыкания и колбэка — функция, которая запускает действие только после паузы во вводе (полезно для поиска). На странице есть поле `<input id="search" />`:

```js
function debounce(callback, delay) {
  let timerId;
  return (...args) => {
    clearTimeout(timerId);
    timerId = setTimeout(() => callback(...args), delay);
  };
}

const search = document.querySelector("#search");
const handleSearch = debounce((event) => {
  console.log("Ищем:", event.target.value);
}, 500);

search.addEventListener("input", handleSearch);
```

Замыкание хранит `timerId` между вызовами: каждое новое нажатие отменяет прошлый таймер, и поиск срабатывает только через 500 мс тишины. Запись `...args` («собрать все аргументы») подробно разберём в уроке [Деструктуризация, spread и rest](lesson:destrukturizaciya-spread-rest).

## Типичные ошибки

-   **Забыли `return`** — функция возвращает `undefined`.
-   **Код после `return`** никогда не выполняется.
-   **Вызов вместо передачи**: `addEventListener("click", handle())`.
-   **Вызов function expression до объявления** — `ReferenceError` (для `const`).
-   **Стрелка как метод объекта** с `this` — `this` окажется не тем объектом.
-   **Стрелка с `{}` без `return`**: `(x) => { x * 2 }` вернёт `undefined`.

## Практика

1.  **Площадь.** Напишите функцию `getArea(width, height)`, возвращающую площадь прямоугольника, и стрелочную `getPerimeter`. Ожидаемый результат: `getArea(3, 4)` → `12`, `getPerimeter(3, 4)` → `14`.
2.  **Калькулятор с колбэком.** Функция `calculate(a, b, operation)` вызывает колбэк `operation`. Передайте разные стрелочные функции для `+`, `-`, `*`. Ожидаемый результат: `calculate(6, 3, (x, y) => x - y)` → `3`.
3.  **Счётчик-замыкание.** Сделайте `createCounter(start, step)`, возвращающую объект с методами `inc`, `dec`, `get`. Ожидаемый результат: два счётчика работают независимо.
4.  **Цветные кнопки.** Создайте 4 кнопки с `data-color`. Через фабрику обработчиков сделайте так, чтобы клик менял фон страницы на этот цвет. Ожидаемый результат: фон меняется, обработчики созданы в цикле.
5.  **Список с делегированием.** Список задач, где удаление по кнопке «✕» и отметка «выполнено» обрабатываются **одним** обработчиком на `ul`. Ожидаемый результат: работает и для задач, добавленных после загрузки страницы.

## Итоги

-   Функция — переиспользуемый блок кода; параметры принимают данные, `return` отдаёт результат.
-   Есть три формы: declaration, expression (анонимная функция в переменной) и стрелочная.
-   Колбэк — функция, переданная в другую функцию, чтобы её вызвали позже.
-   Замыкание — функция помнит переменные места, где её создали.
-   Обработчики событий лучше выносить в именованные функции, а для многих элементов использовать делегирование.
