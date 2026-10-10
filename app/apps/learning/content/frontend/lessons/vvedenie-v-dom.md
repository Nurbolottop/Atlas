До сих пор наш JavaScript писал только в консоль. Пора научить его менять саму страницу: менять текст, добавлять карточки, перекрашивать кнопки и реагировать на клики. Для этого есть **DOM** — представление HTML-страницы в виде объектов, с которыми умеет работать JavaScript. В этом уроке научимся находить элементы, изменять их и обрабатывать **события**, а в конце соберём небольшие интерактивные проекты.

## Что такое DOM

**DOM** (Document Object Model, «объектная модель документа») — это то, во что браузер превращает ваш HTML. Каждый тег становится **объектом-узлом**, а все узлы складываются в **дерево**:

```html
<body>
  <h1>Мой магазин</h1>
  <ul>
    <li>Футболка</li>
    <li>Кружка</li>
  </ul>
</body>
```

```text
document
└── html
    └── body
        ├── h1  → "Мой магазин"
        └── ul
            ├── li → "Футболка"
            └── li → "Кружка"
```

Аналогия: HTML-файл — это чертёж дома, а DOM — сам построенный дом, в котором JavaScript может переставлять мебель и перекрашивать стены. Важно: JavaScript меняет именно DOM, **сам файл `index.html` при этом не меняется** — после перезагрузки страница станет прежней.

Главная точка входа — объект `document`. Через него мы получаем доступ ко всему на странице.

### Где подключать скрипт

Скрипт должен запускаться, когда элементы уже есть на странице. Есть два надёжных варианта:

```html
<!-- Вариант 1: в конце body -->
<body>
  <h1 id="title">Привет</h1>
  <script src="script.js"></script>
</body>

<!-- Вариант 2: в head с атрибутом defer -->
<head>
  <script src="script.js" defer></script>
</head>
```

`defer` говорит браузеру: «скачай скрипт сразу, но выполни, когда HTML полностью разобран».

## Поиск элементов

Прежде чем что-то изменить, элемент нужно найти:

```js
const title = document.querySelector("#title");       // по id
const firstCard = document.querySelector(".card");    // первый элемент с классом card
const allCards = document.querySelectorAll(".card");  // ВСЕ элементы с классом card
const btn = document.getElementById("buy-btn");       // по id, без решётки
```

-   `querySelector(селектор)` — возвращает **первый** подходящий элемент или `null`. Селекторы те же, что в CSS: `#id`, `.class`, `tag`, `ul > li`.
-   `querySelectorAll(селектор)` — возвращает **список** (NodeList) всех подходящих. Его можно перебрать через `for...of` или `forEach`.
-   `getElementById("id")` — старый, но быстрый способ найти по id.

```js
const items = document.querySelectorAll("li");
for (const item of items) {
  console.log(item.textContent);
}
```

<aside class="callout" data-icon="⚠️" markdown="1">

Ошибка `Cannot read properties of null` почти всегда значит, что элемент не найден: опечатка в селекторе, забыли `#` или `.`, или скрипт запустился раньше, чем появился HTML. Проверьте найденное через `console.log(element)`.

</aside>

## Изменение элементов

### Текст и HTML

```js
const title = document.querySelector("#title");

title.textContent = "Добро пожаловать!";        // заменить текст
title.innerHTML = "Привет, <b>гость</b>!";       // вставить HTML-разметку
```

-   `textContent` — работает с чистым текстом, теги показываются как обычные символы. **Безопасен.**
-   `innerHTML` — разбирает строку как HTML.

<aside class="callout" data-icon="🔐" markdown="1">

Никогда не вставляйте через `innerHTML` то, что ввёл пользователь. Если там окажется `<img src=x onerror="...">`, браузер выполнит чужой код (атака XSS). Для пользовательского текста используйте `textContent`.

</aside>

### Стили и классы

```js
const box = document.querySelector(".box");

box.style.backgroundColor = "tomato"; // свойства CSS пишутся в camelCase
box.style.padding = "20px";

box.classList.add("active");      // добавить класс
box.classList.remove("hidden");   // убрать класс
box.classList.toggle("dark");     // есть — убрать, нет — добавить
box.classList.contains("active"); // true / false
```

Лучшая практика — описывать внешний вид в CSS, а в JavaScript только переключать классы:

```css
.hidden {
  display: none;
}
.active {
  border: 2px solid #4f46e5;
}
```

### Атрибуты

```js
const img = document.querySelector("img");
img.src = "cat.jpg";
img.alt = "Рыжий кот";

const link = document.querySelector("a");
link.setAttribute("target", "_blank");
console.log(link.getAttribute("href"));
```

### Создание и удаление элементов

```js
const list = document.querySelector("#list");

const li = document.createElement("li"); // 1. создать
li.textContent = "Новый пункт";          // 2. наполнить
li.classList.add("item");
list.append(li);                         // 3. вставить в конец списка

const first = document.createElement("li");
first.textContent = "Самый первый пункт";
list.prepend(first);                     // вставить в начало списка

li.remove();                             // удалить элемент со страницы
```

Элемент, созданный через `createElement`, существует «в воздухе», пока вы не вставите его на страницу с помощью `append` или `prepend`.

## События

**Событие** — сигнал о том, что что-то произошло: пользователь кликнул, нажал клавишу, ввёл текст, страница загрузилась. JavaScript может «подписаться» на событие и выполнить код в ответ.

Аналогия: вы ставите дверной звонок. Пока никто не нажал — ничего не происходит. Нажали — звенит. Обработчик события — это то, что «звенит».

### addEventListener

```html
<button id="hello-btn">Нажми меня</button>
<p id="output"></p>
```

```js
const button = document.querySelector("#hello-btn");
const output = document.querySelector("#output");

button.addEventListener("click", function () {
  output.textContent = "Кнопка нажата!";
});
```

Разбор:

-   `button.addEventListener(...)` — «слушай события на этой кнопке»;
-   `"click"` — тип события;
-   `function () { ... }` — **обработчик**: функция, которую браузер вызовет при каждом клике. Мы её не вызываем сами — мы её **передаём** браузеру. Подробнее о таком приёме — в уроке [Функции, замыкания и колбэки](lesson:funkcii-zamykaniya-kolbeki).

Тот же код можно записать короче, стрелочной функцией:

```js
button.addEventListener("click", () => {
  output.textContent = "Кнопка нажата!";
});
```

### Популярные события

| Событие | Когда срабатывает |
| --- | --- |
| `click` | Клик по элементу |
| `dblclick` | Двойной клик |
| `mouseenter` / `mouseleave` | Курсор зашёл на элемент / ушёл |
| `input` | Изменилось значение поля ввода (на каждый символ) |
| `change` | Значение поля изменено и подтверждено (для select, checkbox) |
| `submit` | Отправка формы |
| `keydown` | Нажата клавиша |
| `DOMContentLoaded` | HTML загружен и разобран |

### Объект события event

Браузер передаёт в обработчик объект с информацией о событии:

```js
const input = document.querySelector("#name");
const preview = document.querySelector("#preview");

input.addEventListener("input", (event) => {
  preview.textContent = event.target.value;
});

document.addEventListener("keydown", (event) => {
  console.log("Нажата клавиша:", event.key);
});
```

-   `event.target` — элемент, на котором произошло событие;
-   `event.target.value` — текущее значение поля ввода;
-   `event.key` — какая клавиша нажата (`"Enter"`, `"a"`, `"Escape"`).

### preventDefault — отменить действие по умолчанию

Форма при отправке перезагружает страницу, ссылка — переходит по адресу. Чтобы этого не было, вызывают `event.preventDefault()`:

```html
<form id="login-form">
  <input id="email" type="email" placeholder="Email" />
  <button type="submit">Войти</button>
</form>
<p id="message"></p>
```

```js
const form = document.querySelector("#login-form");
const email = document.querySelector("#email");
const message = document.querySelector("#message");

form.addEventListener("submit", (event) => {
  event.preventDefault(); // страница не перезагрузится

  if (email.value.trim() === "") {
    message.textContent = "Введите email";
    message.style.color = "red";
  } else {
    message.textContent = `Добро пожаловать, ${email.value}!`;
    message.style.color = "green";
  }
});
```

Подписывайтесь на `submit` формы, а не на `click` кнопки: так форма отправится и по клавише Enter.

## Практика с менторами: мини-проекты

На занятии ментор разберёт с вами похожие задачи вживую. Ниже — два проекта, которые используют всё изученное.

### Счётчик

```html
<div class="counter">
  <button id="minus">−</button>
  <span id="value">0</span>
  <button id="plus">+</button>
</div>
```

```js
const minusBtn = document.querySelector("#minus");
const plusBtn = document.querySelector("#plus");
const valueEl = document.querySelector("#value");

let count = 0;

plusBtn.addEventListener("click", () => {
  count++;
  valueEl.textContent = count;
});

minusBtn.addEventListener("click", () => {
  if (count > 0) {
    count--;
    valueEl.textContent = count;
  }
});
```

Обратите внимание: число хранится в переменной `count`, а на странице мы только **показываем** его. Это хороший принцип — данные в JavaScript, страница их отображает.

### Список дел

```html
<form id="todo-form">
  <input id="todo-input" placeholder="Что нужно сделать?" />
  <button type="submit">Добавить</button>
</form>
<ul id="todo-list"></ul>
```

```js
const todoForm = document.querySelector("#todo-form");
const todoInput = document.querySelector("#todo-input");
const todoList = document.querySelector("#todo-list");

todoForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = todoInput.value.trim();
  if (!text) return; // пустую задачу не добавляем

  const li = document.createElement("li");
  li.textContent = text;

  const deleteBtn = document.createElement("button");
  deleteBtn.textContent = "✕";
  deleteBtn.addEventListener("click", () => li.remove());

  li.addEventListener("click", () => li.classList.toggle("done"));

  li.append(deleteBtn);
  todoList.append(li);
  todoInput.value = ""; // очищаем поле
});
```

```css
.done {
  text-decoration: line-through;
  opacity: 0.6;
}
```

Разбор:

1.  По отправке формы берём текст, убираем пробелы и пропускаем пустой ввод (`return` прекращает выполнение обработчика).
2.  Создаём `li` с текстом через `textContent` — безопасно.
3.  Создаём кнопку удаления и сразу вешаем на неё обработчик, который удаляет **свой** `li`.
4.  Клик по задаче переключает класс `done` — задача зачёркивается.
5.  Вставляем всё в список и очищаем поле.

## Типичные ошибки

-   **`querySelector` вернул `null`** — проверьте селектор и место подключения скрипта.
-   **`addEventListener` на списке** из `querySelectorAll` — у NodeList нет этого метода, перебирайте элементы и вешайте обработчик на каждый.
-   **Вызов функции вместо передачи**: `btn.addEventListener("click", showMessage())` — функция выполнится сразу. Нужно `showMessage` без скобок.
-   **Забытый `preventDefault`** в форме — страница перезагружается, и всё «пропадает».
-   **`value` у не-поля**: у `div` нет `value`, текст читается через `textContent`.

## Практика

1.  **Смена заголовка.** На странице есть `h1` и кнопка. По клику заголовок меняется на «Текст изменён!». Ожидаемый результат: текст меняется без перезагрузки.
2.  **Тёмная тема.** Кнопка переключает класс `dark` у `body` через `classList.toggle`; в CSS для `.dark` задайте тёмный фон и светлый текст. Ожидаемый результат: повторные клики включают и выключают тему.
3.  **Живой предпросмотр.** Поле ввода и абзац: при вводе абзац показывает текст и количество символов. Ожидаемый результат: «Привет (6 символов)», обновляется на каждую букву.
4.  **Счётчик с границами.** Доработайте счётчик: максимум 10, кнопка «Сброс», а при значении 10 число становится красным. Ожидаемый результат: кнопки не выводят счётчик за пределы 0–10.
5.  **Список дел+.** Доработайте ToDo: показывайте под списком «Всего задач: N», не добавляйте дубликаты, по Escape очищайте поле. Ожидаемый результат: счётчик обновляется при добавлении и удалении.

## Итоги

-   DOM — дерево объектов, в которое браузер превращает HTML; доступ через `document`.
-   `querySelector` находит первый элемент, `querySelectorAll` — все.
-   `textContent`, `classList`, `style`, `setAttribute` меняют элементы; `createElement` + `append` создают новые.
-   Пользовательский текст вставляйте через `textContent`, а не `innerHTML`.
-   `addEventListener(тип, обработчик)` подписывает на событие; в обработчик приходит объект `event`.
-   `event.preventDefault()` отменяет перезагрузку при отправке формы.
