Почти любой современный сайт получает данные с сервера: ленту новостей, список товаров, профиль пользователя. В этом уроке разберёмся, как браузер «разговаривает» с сервером по протоколу HTTP, научимся отправлять запросы через **fetch API**, писать асинхронный код понятно и красиво с помощью **async/await** и выведем на страницу данные, полученные **методом GET**.

## Коротко о JSON

Данные между браузером и сервером чаще всего передаются в формате **JSON**. Мы уже разбирали его в уроке [JSON, localStorage и DevTools](lesson:json-storage-devtools), поэтому только напомним главное:

-   JSON — это **текст**, который выглядит как объект JavaScript: ключи всегда в двойных кавычках, нет функций и `undefined`.
-   `JSON.stringify(объект)` превращает объект в строку JSON — чтобы отправить на сервер.
-   `JSON.parse(строка)` превращает строку JSON обратно в объект — чтобы работать с ответом.

```json
{
  "id": 1,
  "title": "Купить хлеб",
  "completed": false
}
```

## Как работают запросы на сервер

### Клиент и сервер

-   **Клиент** — тот, кто просит данные. В нашем случае это браузер с вашим JavaScript-кодом.
-   **Сервер** — компьютер, который хранит данные и отвечает на запросы.

Аналогия — ресторан. Вы (клиент) отдаёте официанту заказ (**запрос**), кухня (сервер) готовит блюдо, и официант приносит его вам (**ответ**).

### HTTP-запрос

Браузер и сервер общаются по правилам протокола **HTTP**. Каждый HTTP-запрос состоит из частей:

| Часть | Что это | Пример |
| --- | --- | --- |
| **URL** | адрес, куда отправляем запрос | `https://jsonplaceholder.typicode.com/users` |
| **Метод** | что мы хотим сделать | `GET` — получить данные |
| **Заголовки** (headers) | дополнительная информация | `Content-Type: application/json` |
| **Тело** (body) | данные, которые отправляем | для GET тела нет |

Ответ сервера тоже состоит из частей: **статус-код** (получилось или нет), заголовки и тело (сами данные).

Самые важные статус-коды:

| Код | Значение |
| --- | --- |
| `200 OK` | всё хорошо, данные в ответе |
| `201 Created` | новая запись создана |
| `400 Bad Request` | неправильный запрос (ошибка клиента) |
| `401 Unauthorized` | нужна авторизация |
| `404 Not Found` | такого ресурса нет |
| `500 Internal Server Error` | ошибка на сервере |

Запомнить просто: **2xx** — успех, **4xx** — ошибся клиент, **5xx** — ошибся сервер. Подробнее про HTTP и методы поговорим в уроке [про REST API](lesson:rest-api-put-delete).

### Тестовый сервер

Для практики используем бесплатный тестовый API **JSONPlaceholder** — `https://jsonplaceholder.typicode.com`. Он отдаёт ненастоящие данные: пользователей, посты, задачи. Попробуйте открыть в браузере адрес `https://jsonplaceholder.typicode.com/users/1` — вы увидите JSON. Браузер только что сделал GET-запрос.

Полезные адреса:

-   `/users` — список пользователей, `/users/1` — один пользователь;
-   `/posts` — посты, `/posts/1` — один пост;
-   `/todos` — задачи;
-   `/posts?userId=1` — посты только первого пользователя.

## fetch API

`fetch` — встроенная в браузер функция для HTTP-запросов. Устанавливать ничего не нужно.

```js
fetch("https://jsonplaceholder.typicode.com/users/1");
```

`fetch` **возвращает промис** (вспомните урок [про Promise](lesson:event-loop-i-promise)), потому что ответ придёт не сразу. Получим данные через `.then`:

```js
fetch("https://jsonplaceholder.typicode.com/users/1")
  .then((response) => response.json())
  .then((user) => {
    console.log(user.name);  // "Leanne Graham"
    console.log(user.email); // "Sincere@april.biz"
  })
  .catch((error) => console.log("Ошибка сети:", error.message));
```

Разбор по шагам:

1.  `fetch(url)` отправляет GET-запрос (GET — метод по умолчанию).
2.  Первый `.then` получает объект `response` — «конверт» с ответом: статус, заголовки. Сами данные ещё не прочитаны.
3.  `response.json()` читает тело ответа и превращает JSON в объект. Этот метод **тоже возвращает промис**, поэтому мы его возвращаем.
4.  Второй `.then` получает готовый объект `user`.
5.  `.catch` сработает при сетевой ошибке.

### Объект Response

Что полезного есть у `response`:

| Свойство / метод | Что даёт |
| --- | --- |
| `response.ok` | `true`, если статус от 200 до 299 |
| `response.status` | числовой код: `200`, `404`… |
| `response.json()` | промис с данными из JSON |
| `response.text()` | промис с ответом в виде обычного текста |

<aside class="callout" data-icon="⚠️" markdown="1">

Важная особенность `fetch`: он **не считает ошибкой** ответы 404 или 500. Промис отклоняется только при проблемах с сетью (нет интернета, неверный домен). Поэтому всегда проверяйте `response.ok` и сами выбрасывайте ошибку, если ответ неуспешный.

</aside>

```js
fetch("https://jsonplaceholder.typicode.com/users/9999")
  .then((response) => {
    if (!response.ok) {
      throw new Error(`Ошибка ${response.status}`); // "Ошибка 404"
    }
    return response.json();
  })
  .then((user) => console.log(user))
  .catch((error) => console.log(error.message));
```

## async/await — промисы, но проще

Цепочки `.then` работают, но когда шагов много, их тяжело читать. Для этого в JavaScript есть **async/await** — другой способ писать тот же код с промисами.

### Два ключевых слова

-   `async` ставится перед функцией. Такая функция **всегда возвращает промис**.
-   `await` ставится перед промисом и означает: «подожди, пока промис выполнится, и дай мне его результат». Писать `await` можно только внутри `async`-функции (или на верхнем уровне модуля).

```js
async function getNumber() {
  return 42;
}

getNumber().then((n) => console.log(n)); // 42 — async-функция вернула промис
```

### Сравним два способа

Тот же запрос на `.then`:

```js
function loadUser() {
  return fetch("https://jsonplaceholder.typicode.com/users/1")
    .then((response) => response.json())
    .then((user) => console.log(user.name));
}
```

И на `async/await`:

```js
async function loadUser() {
  const response = await fetch("https://jsonplaceholder.typicode.com/users/1");
  const user = await response.json();
  console.log(user.name);
}

loadUser();
```

Код читается сверху вниз, как обычный синхронный. Но под капотом это те же промисы: `await` не блокирует страницу. Пока ждём ответ, функция «ставится на паузу», а браузер спокойно обрабатывает клики и прокрутку. Когда промис выполнится, Event Loop продолжит функцию с того же места.

| `.then` | `async/await` |
| --- | --- |
| `promise.then((x) => ...)` | `const x = await promise` |
| `.catch((e) => ...)` | `try { ... } catch (e) { ... }` |
| `.finally(() => ...)` | `finally { ... }` |

### Обработка ошибок с try...catch

С `await` ошибки ловятся обычным `try...catch`, который мы изучили в уроке [try, catch, finally](lesson:try-catch-finally):

```js
async function loadUser(id) {
  try {
    const response = await fetch(`https://jsonplaceholder.typicode.com/users/${id}`);

    if (!response.ok) {
      throw new Error(`Не удалось загрузить: ${response.status}`);
    }

    const user = await response.json();
    return user;
  } catch (error) {
    console.error(error.message);
    return null;
  }
}

loadUser(1).then((user) => console.log(user?.name)); // "Leanne Graham"
loadUser(999).then((user) => console.log(user));     // null, в консоли — ошибка 404
```

<aside class="callout" data-icon="⚠️" markdown="1">

Частая ошибка — забыть `await`. Тогда в переменной окажется промис, а не данные: `const user = response.json()` → `Promise {<pending>}`. Если видите в консоли `Promise` вместо объекта — проверьте, не пропущен ли `await`.

</aside>

### Параллельные запросы с await

`await` в строчку выполняет запросы **по очереди**. Если они независимы — объединяйте их через `Promise.all`:

```js
async function loadDashboard() {
  const [users, posts] = await Promise.all([
    fetch("https://jsonplaceholder.typicode.com/users").then((r) => r.json()),
    fetch("https://jsonplaceholder.typicode.com/posts").then((r) => r.json()),
  ]);

  console.log(`Пользователей: ${users.length}, постов: ${posts.length}`); // 10 и 100
}

loadDashboard();
```

Здесь пригодилась деструктуризация массива из урока [про деструктуризацию](lesson:destrukturizaciya-spread-rest).

## Метод GET на практике: список пользователей

Соберём мини-приложение: кнопка «Загрузить», индикатор загрузки, список карточек и сообщение об ошибке.

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Пользователи</title>
  <style>
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 12px; margin: 8px 0; }
    .hidden { display: none; }
    .error { color: crimson; }
  </style>
</head>
<body>
  <button id="load">Загрузить пользователей</button>
  <p id="loader" class="hidden">Загрузка...</p>
  <p id="error" class="error"></p>
  <div id="list"></div>

  <script src="main.js"></script>
</body>
</html>
```

```js
// main.js
const API_URL = "https://jsonplaceholder.typicode.com";

const loadBtn = document.querySelector("#load");
const loader = document.querySelector("#loader");
const errorText = document.querySelector("#error");
const list = document.querySelector("#list");

async function getUsers() {
  const response = await fetch(`${API_URL}/users`);
  if (!response.ok) {
    throw new Error(`Сервер ответил ошибкой ${response.status}`);
  }
  return response.json();
}

function renderUsers(users) {
  list.innerHTML = "";
  users.forEach((user) => {
    const card = document.createElement("div");
    card.className = "card";

    const name = document.createElement("h3");
    name.textContent = user.name;

    const info = document.createElement("p");
    info.textContent = `${user.email} · ${user.address.city}`;

    card.append(name, info);
    list.append(card);
  });
}

loadBtn.addEventListener("click", async () => {
  loader.classList.remove("hidden");
  errorText.textContent = "";
  loadBtn.disabled = true;

  try {
    const users = await getUsers();
    renderUsers(users);
  } catch (error) {
    errorText.textContent = "Не удалось загрузить данные. Попробуйте позже.";
    console.error(error);
  } finally {
    loader.classList.add("hidden");
    loadBtn.disabled = false;
  }
});
```

Разберём по частям:

-   **`API_URL`** — базовый адрес вынесен в константу. Если сервер поменяется, править нужно одну строку.
-   **`getUsers`** отвечает только за запрос: отправляет GET, проверяет `ok`, возвращает данные. Обратите внимание: `return response.json()` возвращает промис, и `await getUsers()` дождётся его.
-   **`renderUsers`** отвечает только за отрисовку. Мы создаём элементы через `createElement` и заполняем `textContent` — как в уроке [про DOM](lesson:vvedenie-v-dom).
-   **Обработчик клика** — `async`-функция. Перед запросом показываем «Загрузка...» и блокируем кнопку, чтобы не отправить десять запросов подряд. В `finally` всё возвращаем обратно.

<aside class="callout" data-icon="🔐" markdown="1">

Данные с сервера выводите через `textContent`, а не через `innerHTML`. Если в данных окажется строка вида `<img src=x onerror=alert(1)>`, `innerHTML` выполнит её как HTML — это уязвимость XSS. `textContent` всегда показывает текст как текст.

</aside>

### Query-параметры

Часто серверу нужно передать уточнение: фильтр, номер страницы, лимит. Для этого используют **query-параметры** — часть URL после знака `?`:

```text
https://jsonplaceholder.typicode.com/posts?userId=1&_limit=5
```

-   `?` начинает параметры, `&` разделяет их;
-   `userId=1` — только посты пользователя 1;
-   `_limit=5` — не больше пяти записей (особенность JSONPlaceholder).

Собирать такие адреса вручную неудобно, особенно с пробелами и русскими буквами. Используйте `URLSearchParams`:

```js
async function getPosts(userId, limit) {
  const params = new URLSearchParams({ userId, _limit: limit });
  const response = await fetch(`${API_URL}/posts?${params}`);
  if (!response.ok) throw new Error(`Ошибка ${response.status}`);
  return response.json();
}

getPosts(1, 3).then((posts) => {
  posts.forEach((post) => console.log(post.title));
});
```

`URLSearchParams` сам правильно закодирует значения, например превратит пробел в `+`.

### Смотрим запросы в DevTools

Откройте DevTools (`F12`) → вкладка **Network** (Сеть) → фильтр **Fetch/XHR**. Нажмите кнопку загрузки — появится строка запроса. Кликнув по ней, вы увидите:

-   **Headers** — URL, метод, статус-код;
-   **Response** / **Preview** — что именно ответил сервер.

Это главный инструмент, когда «данные не приходят»: сразу видно, ушёл ли запрос и что вернул сервер.

## Типичные ошибки

-   **Забыли `await`** перед `fetch` или `response.json()` — получили промис вместо данных.
-   **Не проверили `response.ok`** — код пытается работать с ответом 404 как с данными.
-   **`await` вне `async`-функции** — `SyntaxError` в обычном скрипте.
-   **Открыли HTML-файл двойным кликом** и подключили скрипт с `type="module"` — модули не работают по протоколу `file://`. Используйте расширение Live Server в VS Code.
-   **Ошибка CORS** в консоли — сервер не разрешает запросы с вашего сайта. Это настраивается на сервере; JSONPlaceholder разрешает запросы отовсюду.

Документация: [MDN: использование Fetch](https://developer.mozilla.org/ru/docs/Web/API/Fetch_API/Using_Fetch), [MDN: async function](https://developer.mozilla.org/ru/docs/Web/JavaScript/Reference/Statements/async_function).

## Практика

1.  **Первый запрос.** Через `fetch` и `.then` получите `https://jsonplaceholder.typicode.com/todos/1` и выведите в консоль `title` и `completed`.
2.  **Переписать на async/await.** Перепишите первое задание через `async/await` с `try...catch` и проверкой `response.ok`. Проверьте, что запрос на `/todos/99999` выводит понятное сообщение об ошибке.
3.  **Список постов.** Сделайте страницу, которая при загрузке получает первые 10 постов (`/posts?_limit=10`) и выводит их карточками: заголовок и текст.
4.  **Выбор пользователя.** Добавьте `<select>` с вариантами 1–10. При выборе загружайте посты этого пользователя (`/posts?userId=N`) и перерисовывайте список. Пока идёт загрузка — показывайте «Загрузка...».
5.  **Профиль целиком.** По кнопке загрузите одновременно `/users/1` и `/todos?userId=1` через `Promise.all` и выведите имя пользователя и количество выполненных задач (`completed: true`).

## Итоги

-   Браузер (клиент) и сервер общаются по HTTP: запрос с методом и URL, ответ со статус-кодом и телом.
-   `fetch(url)` возвращает промис с объектом `Response`; данные достаются через `await response.json()`.
-   `fetch` не считает 404 и 500 ошибкой — проверяйте `response.ok` сами.
-   `async/await` — удобная запись промисов: `await` ждёт результат, ошибки ловит `try...catch`.
-   GET — метод для получения данных; уточнения передаются query-параметрами через `URLSearchParams`.
-   Данные с сервера выводите через `textContent`, а запросы проверяйте во вкладке Network.
