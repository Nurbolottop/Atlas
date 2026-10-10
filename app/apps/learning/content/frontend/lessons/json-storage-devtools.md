В этом уроке три темы, которые пригодятся каждый день. **JSON** — универсальный формат, в котором программы обмениваются данными. **localStorage** и **sessionStorage** — хранилища в браузере, благодаря которым список дел или тёмная тема не пропадают после перезагрузки страницы. А **DevTools** — инструменты разработчика, с помощью которых ищут и исправляют ошибки в коде.

## Формат JSON

**JSON** (JavaScript Object Notation) — текстовый формат для хранения и передачи данных. Сервер присылает данные в JSON, приложения сохраняют настройки в JSON, файл `package.json` в любом проекте — тоже JSON. Аналогия: JSON — это «общий язык» программ, как английский в аэропорту: на чём бы ни была написана программа, JSON она понимает.

Выглядит JSON почти как объект JavaScript:

```json
{
  "id": 1,
  "name": "Алина",
  "age": 21,
  "isStudent": true,
  "skills": ["HTML", "CSS", "JavaScript"],
  "address": {
    "city": "Бишкек",
    "zip": null
  }
}
```

### Правила JSON

JSON строже, чем объекты JavaScript:

-   ключи **всегда** в двойных кавычках: `"name"`, а не `name`;
-   строки — только в **двойных** кавычках, одинарные запрещены;
-   **нет** запятой после последнего элемента;
-   **нет** комментариев;
-   разрешённые значения: строка, число, `true`/`false`, `null`, массив, объект. Функций, `undefined`, дат как объектов в JSON нет.

| JavaScript-объект | JSON |
| --- | --- |
| `{ name: 'Ali' }` | `{ "name": "Ali" }` |
| `{ a: 1, }` (запятая в конце) | `{ "a": 1 }` |
| `{ fn() {} }` | функции недопустимы |
| `{ x: undefined }` | свойство пропадает |

### JSON.stringify — объект в строку

```js
const user = { name: "Алина", age: 21, skills: ["HTML", "CSS"] };

const json = JSON.stringify(user);
console.log(json);        // '{"name":"Алина","age":21,"skills":["HTML","CSS"]}'
console.log(typeof json); // "string"
```

`JSON.stringify` превращает объект или массив в **строку** — её можно отправить на сервер или сохранить. Для красивого вывода с отступами передайте третий аргумент:

```js
console.log(JSON.stringify(user, null, 2));
```

### JSON.parse — строка в объект

```js
const text = '{"title":"Кружка","price":350,"tags":["посуда","подарок"]}';
const product = JSON.parse(text);

console.log(product.title);   // "Кружка"
console.log(product.tags[1]); // "подарок"
```

`JSON.parse` делает обратное: из строки получает настоящий объект, с которым можно работать.

```text
Объект  —— JSON.stringify ——>  Строка
Объект  <——   JSON.parse   ——  Строка
```

### Ошибки разбора

Если строка — не корректный JSON, `JSON.parse` выбросит ошибку и остановит скрипт. Поэтому данные из ненадёжных источников разбирают внутри `try...catch` (подробно о нём — в уроке [try, catch, finally](lesson:try-catch-finally)):

```js
const broken = "{ name: 'Ali' }"; // ключ без кавычек, одинарные кавычки

try {
  const data = JSON.parse(broken);
  console.log(data);
} catch (error) {
  console.log("Не получилось разобрать JSON:", error.message);
}
```

## Хранилища браузера: localStorage и sessionStorage

Обычно все переменные JavaScript **исчезают** при перезагрузке страницы. Если пользователь добавил задачи в список и нажал F5 — всё пропало. Чтобы данные сохранялись, браузер даёт два хранилища — **Web Storage**.

Аналогия: переменные — это записи мелом на доске (стираются после урока), а localStorage — тетрадь, которая остаётся у вас.

### Чем они отличаются

| | `localStorage` | `sessionStorage` |
| --- | --- | --- |
| Сколько хранится | Пока не удалят (код или пользователь) | Пока открыта вкладка |
| После перезагрузки | Сохраняется | Сохраняется |
| После закрытия вкладки | Сохраняется | Удаляется |
| В других вкладках сайта | Доступно | У каждой вкладки своё |
| Объём | Около 5 МБ на сайт | Около 5 МБ на сайт |

Данные привязаны к **сайту** (домену): `localStorage` одного сайта не видят другие сайты.

### Основные методы

У обоих хранилищ одинаковые методы:

```js
localStorage.setItem("theme", "dark");     // сохранить: ключ и значение
const theme = localStorage.getItem("theme"); // прочитать → "dark"
localStorage.removeItem("theme");          // удалить один ключ
localStorage.clear();                       // удалить всё хранилище сайта

console.log(localStorage.getItem("unknown")); // null — такого ключа нет
```

Для `sessionStorage` всё то же самое: `sessionStorage.setItem("step", "2")`.

### Хранятся только строки

Главная особенность: хранилище умеет сохранять **только строки**. Числа превращаются в строки, а объекты — в бесполезное `"[object Object]"`:

```js
localStorage.setItem("count", 5);
console.log(typeof localStorage.getItem("count")); // "string"

localStorage.setItem("user", { name: "Ali" });
console.log(localStorage.getItem("user")); // "[object Object]" — данные потеряны
```

Решение — **JSON**: при сохранении `JSON.stringify`, при чтении `JSON.parse`.

```js
const todos = [
  { id: 1, text: "Выучить JSON", done: true },
  { id: 2, text: "Сделать ToDo", done: false },
];

localStorage.setItem("todos", JSON.stringify(todos));

const saved = JSON.parse(localStorage.getItem("todos")) ?? [];
console.log(saved[1].text); // "Сделать ToDo"
```

`?? []` здесь подстраховывает: если ключа нет, `getItem` вернёт `null`, `JSON.parse(null)` тоже даст `null`, и мы подставим пустой массив (оператор `??` разбирали в уроке [Деструктуризация, spread, rest, ?. и ??](lesson:destrukturizaciya-spread-rest)).

### Удобные функции-помощники

```js
function saveToStorage(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function loadFromStorage(key, defaultValue) {
  try {
    const raw = localStorage.getItem(key);
    return raw === null ? defaultValue : JSON.parse(raw);
  } catch {
    return defaultValue; // в хранилище оказался «битый» JSON
  }
}

saveToStorage("settings", { theme: "dark", fontSize: 18 });
const settings = loadFromStorage("settings", { theme: "light", fontSize: 16 });
console.log(settings.theme); // "dark"
```

### Пример: тема, которая запоминается

```html
<button id="theme-btn">Сменить тему</button>
```

```css
body.dark {
  background: #111827;
  color: #f9fafb;
}
```

```js
const themeBtn = document.querySelector("#theme-btn");

if (localStorage.getItem("theme") === "dark") {
  document.body.classList.add("dark");
}

themeBtn.addEventListener("click", () => {
  document.body.classList.toggle("dark");
  const isDark = document.body.classList.contains("dark");
  localStorage.setItem("theme", isDark ? "dark" : "light");
});
```

1.  При загрузке страницы читаем сохранённую тему и сразу применяем её.
2.  По клику переключаем класс `dark` у `body` (как в уроке [Введение в DOM](lesson:vvedenie-v-dom)).
3.  Записываем новое значение в `localStorage` — после перезагрузки тема останется.

### Пример: sessionStorage для черновика формы

`sessionStorage` подходит для временных данных, которые нужны только в текущей вкладке, — например, черновик формы:

```js
const textarea = document.querySelector("#comment");

textarea.value = sessionStorage.getItem("draft") ?? "";

textarea.addEventListener("input", () => {
  sessionStorage.setItem("draft", textarea.value);
});
```

Пользователь случайно обновил страницу — текст на месте. Закрыл вкладку — черновик исчез, как и должно быть.

<aside class="callout" data-icon="🔐" markdown="1">

Не храните в `localStorage` пароли, номера карт и другие секреты: любой скрипт на странице может прочитать хранилище. Для токенов авторизации в реальных проектах выбирают способ хранения вместе с бэкенд-разработчиками — подробнее в уроке [JWT-авторизация](lesson:jwt-avtorizaciya-swagger).

</aside>

## DevTools — инструменты разработчика

**DevTools** — встроенный в браузер набор инструментов для изучения и отладки страницы. Открывается клавишей `F12` или `Ctrl + Shift + I` (на Mac — `Cmd + Option + I`). Также можно кликнуть правой кнопкой по элементу и выбрать «Просмотреть код» (Inspect). Ниже — названия вкладок в Chrome, в других браузерах они похожи.

### Основные вкладки

| Вкладка | Для чего |
| --- | --- |
| **Elements** | Дерево DOM и стили: можно менять HTML и CSS прямо на лету |
| **Console** | Вывод `console.log`, ошибки, выполнение JS-команд |
| **Sources** | Файлы скриптов, точки останова, пошаговая отладка |
| **Network** | Все запросы страницы: файлы, картинки, запросы к API |
| **Application** | localStorage, sessionStorage, cookies |

### Console: больше, чем console.log

```js
const users = [
  { name: "Ali", age: 25 },
  { name: "Aida", age: 22 },
];

console.log("Обычный вывод");
console.warn("Предупреждение — жёлтым");
console.error("Ошибка — красным");
console.table(users);   // красивая таблица из массива объектов
console.log({ users }); // выводит переменную вместе с её именем
```

В консоли можно и выполнять код: напишите `document.title` или `localStorage` и нажмите Enter.

Когда в коде ошибка, консоль показывает её текст и ссылку на файл и строку, например `script.js:12`. Кликните по ссылке — DevTools откроет нужное место во вкладке Sources. **Читайте текст ошибки целиком** — обычно в нём уже сказано, что не так:

```text
Uncaught TypeError: Cannot read properties of null (reading 'addEventListener')
    at script.js:3
```

Перевод: «на строке 3 вы вызвали `addEventListener` у `null`» — значит, `querySelector` не нашёл элемент.

### Application: смотрим хранилища

Во вкладке **Application** слева есть раздел **Storage → Local storage** и **Session storage**. Выберите адрес сайта — увидите таблицу ключей и значений. Значения можно редактировать двойным кликом и удалять, а это удобно, чтобы проверить, как приложение ведёт себя с пустым или «сломанным» хранилищем.

### Debugging: пошаговая отладка

**Отладка** (debugging) — поиск и исправление ошибок. `console.log` хорош, но когда логика сложная, удобнее **остановить программу** в нужном месте и посмотреть значения всех переменных.

Возьмём функцию с ошибкой:

```js
function getTotal(cart) {
  let total = 0;
  for (let i = 0; i <= cart.length; i++) {
    total += cart[i].price * cart[i].qty;
  }
  return total;
}

console.log(getTotal([{ price: 100, qty: 2 }, { price: 50, qty: 1 }]));
```

Код падает с ошибкой `Cannot read properties of undefined (reading 'price')`. Найдём причину:

1.  **Точка останова (breakpoint)**. Откройте **Sources**, найдите `script.js` и кликните по номеру строки `total += ...` — появится синяя метка. Или напишите в коде строку `debugger;` — браузер остановится на ней, когда DevTools открыты.
2.  **Перезагрузите страницу**. Выполнение остановится на метке, а справа в панели **Scope** будут видны значения `i`, `total`, `cart`.
3.  **Шаг вперёд**. Кнопка **Step over** (или `F10`) выполняет одну строку. Кнопка **Resume** (`F8`) — продолжить до следующей точки.
4.  **Наблюдение**. Видим: `cart.length` равно `2`, а цикл доходит до `i = 2`. Элемента `cart[2]` нет — это `undefined`.
5.  **Исправление**: условие должно быть `i < cart.length`.

| Кнопка | Клавиша | Что делает |
| --- | --- | --- |
| Resume | `F8` | Продолжить до следующей точки останова |
| Step over | `F10` | Выполнить строку, не заходя внутрь функций |
| Step into | `F11` | Зайти внутрь вызываемой функции |
| Step out | `Shift + F11` | Выйти из текущей функции |

Ещё полезно: в панели **Watch** можно добавить выражение (например, `cart[i]`) и следить, как оно меняется на каждом шаге.

<aside class="callout" data-icon="💡" markdown="1">

Не забудьте убрать `debugger;` и лишние `console.log` перед коммитом — это «мусор» отладки, который не должен попадать в готовый проект.

</aside>

### Network: что загрузилось

Во вкладке **Network** видно все запросы страницы: статус (200 — успешно, 404 — не найдено), размер и время загрузки. Если стили или картинка не применились, проверьте здесь, не стоит ли у файла 404 — обычно это ошибка в пути. Запросы к серверу через `fetch` будем разбирать в уроке [fetch, async/await и GET](lesson:fetch-async-await-get), и Network станет главным помощником.

Подробное руководство — в официальной [документации Chrome DevTools](https://developer.chrome.com/docs/devtools).

## Типичные ошибки

-   **Сохранение объекта без `JSON.stringify`** — в хранилище окажется `"[object Object]"`.
-   **Забыли `JSON.parse` при чтении** — работаете со строкой вместо массива, `todos.map` не существует.
-   **Одинарные кавычки или запятая в конце** в JSON-строке — `SyntaxError` при разборе.
-   **Ожидание числа из хранилища** — `getItem` всегда возвращает строку или `null`, приводите через `Number()`.
-   **Секреты в localStorage** — их может прочитать любой скрипт на странице.
-   **Игнорирование текста ошибки в консоли** — в нём почти всегда есть ответ.

## Практика

1.  **Туда и обратно.** Создайте объект книги с массивом авторов, превратите его в JSON через `JSON.stringify(book, null, 2)`, выведите, затем разберите обратно и выведите второго автора. Ожидаемый результат: красиво отформатированный JSON и имя автора.
2.  **Счётчик посещений.** При каждой загрузке страницы увеличивайте число в `localStorage` и выводите «Вы были здесь N раз». Ожидаемый результат: число растёт после каждой перезагрузки и не сбрасывается после закрытия браузера.
3.  **Шаг формы в sessionStorage.** Сделайте форму из трёх шагов (кнопки «Далее»/«Назад»), текущий шаг храните в `sessionStorage`. Ожидаемый результат: после перезагрузки вы остаётесь на том же шаге, в новой вкладке — снова на первом.
4.  **ToDo с сохранением.** Возьмите список дел из урока про DOM и сохраняйте массив задач в `localStorage` при каждом изменении. Ожидаемый результат: после перезагрузки задачи и их статус «выполнено» на месте; в Application → Local storage виден JSON.
5.  **Охота на баг.** Скопируйте функцию `getTotal` с ошибкой, поставьте breakpoint в DevTools, пройдите цикл через Step over и найдите причину. Ожидаемый результат: вы исправили условие цикла и можете объяснить, на каком шаге появился `undefined`.

## Итоги

-   JSON — текстовый формат данных: ключи и строки в двойных кавычках, без комментариев и функций.
-   `JSON.stringify` превращает объект в строку, `JSON.parse` — строку обратно в объект.
-   `localStorage` хранит данные бессрочно, `sessionStorage` — пока открыта вкладка; оба — только строки.
-   Объекты и массивы сохраняйте через `JSON.stringify`, читайте через `JSON.parse` с запасным значением.
-   DevTools: Elements — DOM и стили, Console — ошибки и вывод, Sources — отладка, Network — запросы, Application — хранилища.
-   Breakpoint и пошаговое выполнение помогают увидеть значения переменных в момент ошибки.
