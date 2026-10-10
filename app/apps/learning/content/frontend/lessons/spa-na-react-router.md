В этом уроке разберёмся, чем одностраничное приложение (SPA) отличается от многостраничного сайта (MPA), и соберём SPA на React Router. Научимся передавать данные между страницами: через параметры пути, строку запроса (`useSearchParams`) и `state` навигации. А ещё узнаем, как загружать данные до показа страницы с помощью `loader` и `useLoaderData`.

## SPA и MPA: в чём разница

### MPA — многостраничное приложение

**MPA (Multi-Page Application)** — классический сайт: каждая страница — отдельный HTML с сервера. Клик по ссылке — браузер загружает новый HTML и перерисовывает всё: экран моргает, введённый в поля текст теряется.

### SPA — одностраничное приложение

**SPA (Single-Page Application)** — сервер отдаёт один `index.html` и JavaScript. При клике по ссылке JavaScript меняет адрес в строке браузера и подменяет только нужную часть страницы, без перезагрузки.

Аналогия: MPA — за каждой главой книги вы ходите в библиотеку, SPA — электронная читалка, где вы просто листаете экран.

| | MPA | SPA |
| --- | --- | --- |
| Переход между страницами | Полная перезагрузка | Подмена части страницы без перезагрузки |
| Состояние при переходе | Теряется | Сохраняется (шапка, плеер, корзина) |
| SEO | Проще | Сложнее (нужны SSR или пререндер) |
| Примеры | Блоги, новостные сайты | Gmail, Trello, админки, личные кабинеты |

<aside class="callout" data-icon="📌" markdown="1">

React сам по себе не умеет «переключать страницы». За это отвечает библиотека **React Router**: она смотрит на адрес в браузере и решает, какой компонент показать.

</aside>

## Подготовка проекта

Создадим проект через Vite и установим роутер:

```bash
npm create vite@latest my-spa -- --template react
cd my-spa
npm install
npm install react-router
npm run dev
```

<aside class="callout" data-icon="💡" markdown="1">

Как и в прошлом месяце, используем пакет `react-router` (v7). В старых проектах вы встретите `react-router-dom` — это то же API под прежним названием. Основы маршрутов мы разбирали в уроке [React Router](lesson:react-router).

</aside>

## Data router: createBrowserRouter

Современный способ описать маршруты — **data router**: создаём роутер функцией `createBrowserRouter` и передаём в `RouterProvider`. Он умеет ещё и загружать данные для страниц.

### Описываем маршруты

```jsx
// src/router.jsx
import { createBrowserRouter } from "react-router";
import RootLayout from "./layouts/RootLayout";
import HomePage from "./pages/HomePage";
import UsersPage, { usersLoader } from "./pages/UsersPage";
import UserPage, { userLoader } from "./pages/UserPage";
import ErrorPage from "./pages/ErrorPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <RootLayout />,
    errorElement: <ErrorPage />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "users", element: <UsersPage />, loader: usersLoader },
      { path: "users/:userId", element: <UserPage />, loader: userLoader },
    ],
  },
]);
```

Разберём по частям:

- `path: "/"` — корневой маршрут. Его `element` — общий каркас (шапка, меню), внутри которого меняются страницы.
- `errorElement` — что показать, если что-то сломалось: страница не найдена или loader выбросил ошибку.
- `children` — вложенные маршруты. Их адреса пишутся без ведущего `/` и считаются относительно родителя: `users` → `/users`.
- `index: true` — страница «по умолчанию» для родителя, то есть для адреса `/`.
- `:userId` — **динамический параметр**. Подойдёт `/users/1`, `/users/42` и т. д.
- `loader` — функция, которая загрузит данные до показа страницы.

### Подключаем роутер

```jsx
// src/main.jsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router";
import { router } from "./router";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>
);
```

### Общий каркас и Outlet

```jsx
// src/layouts/RootLayout.jsx
import { NavLink, Outlet, useNavigation } from "react-router";

export default function RootLayout() {
  const navigation = useNavigation();

  return (
    <div>
      <header>
        <nav style={{ display: "flex", gap: 16 }}>
          <NavLink to="/">Главная</NavLink>
          <NavLink to="/users">Пользователи</NavLink>
        </nav>
      </header>

      {navigation.state === "loading" && <p>Загрузка...</p>}

      <main>
        <Outlet />
      </main>
    </div>
  );
}
```

- `<Outlet />` — «окно», куда роутер подставит текущую дочернюю страницу. Шапка остаётся на месте.
- `NavLink` — ссылка, которая получает класс `active`, когда её адрес открыт.
- `useNavigation()` — пока loader следующей страницы грузит данные, `navigation.state` равен `"loading"`.

<aside class="callout" data-icon="⚠️" markdown="1">

Не используйте обычный `<a href="/users">` для внутренних переходов: он перезагрузит всю страницу и превратит SPA в MPA. Для переходов внутри приложения — только `Link`/`NavLink` или `useNavigate`.

</aside>

## Загрузка данных: loader и useLoaderData

### Зачем нужен loader

Раньше мы грузили данные в `useEffect`: страница сначала пустая, потом данные появляются. Минусы — «мигание» и много кода с `useState` для загрузки и ошибки.

**Loader** — функция, которую роутер вызывает **до** того, как показать страницу. Аналогия: официант приносит блюдо уже готовым, а не ставит пустую тарелку и уходит на кухню.

### Список пользователей

```jsx
// src/pages/UsersPage.jsx
import { Link, useLoaderData } from "react-router";

export async function usersLoader() {
  const res = await fetch("https://jsonplaceholder.typicode.com/users");
  if (!res.ok) {
    throw new Response("Не удалось загрузить пользователей", { status: res.status });
  }
  return res.json();
}

export default function UsersPage() {
  const users = useLoaderData();

  return (
    <ul>
      {users.map((user) => (
        <li key={user.id}>
          <Link to={`/users/${user.id}`}>{user.name}</Link>
        </li>
      ))}
    </ul>
  );
}
```

Что происходит:

1. Клик на «Пользователи» — роутер вызывает `usersLoader`. Пока идёт запрос, видна старая страница и «Загрузка...».
2. Loader вернул данные — роутер рисует `UsersPage`, а `useLoaderData()` отдаёт ровно то, что вернул loader.
3. Loader бросил ошибку (`throw`) — вместо страницы покажется `errorElement`.

### Страница одного пользователя: params в loader

Loader получает объект с `params` (параметры пути) и `request` (сам запрос, из него можно достать URL):

```jsx
// src/pages/UserPage.jsx
import { Link, useLoaderData } from "react-router";

export async function userLoader({ params }) {
  const res = await fetch(
    `https://jsonplaceholder.typicode.com/users/${params.userId}`
  );
  if (res.status === 404) {
    throw new Response("Пользователь не найден", { status: 404 });
  }
  return res.json();
}

export default function UserPage() {
  const user = useLoaderData();

  return (
    <article>
      <h1>{user.name}</h1>
      <p>Email: {user.email}</p>
      <p>Город: {user.address.city}</p>
      <Link to="/users">← Назад к списку</Link>
    </article>
  );
}
```

`params.userId` — то, что стоит на месте `:userId` в адресе. Для `/users/3` это строка `"3"`.

### Страница ошибки

```jsx
// src/pages/ErrorPage.jsx
import { isRouteErrorResponse, Link, useRouteError } from "react-router";

export default function ErrorPage() {
  const error = useRouteError();

  if (isRouteErrorResponse(error)) {
    return (
      <div>
        <h1>{error.status}</h1>
        <p>{error.data}</p>
        <Link to="/">На главную</Link>
      </div>
    );
  }

  return <p>Что-то пошло не так: {error?.message}</p>;
}
```

- `useRouteError()` достаёт ошибку, а `isRouteErrorResponse` проверяет, что это наш `throw new Response(...)` со `status` и `data`.
- Несуществующий адрес (`/abracadabra`) тоже попадёт сюда со статусом 404.

## Передача данных между страницами

Страницы — не родитель и ребёнок, пропсы между ними не передашь. Вот какие есть способы.

| Способ | Пример адреса | Когда использовать |
| --- | --- | --- |
| Параметр пути (`useParams`) | `/users/5` | Идентификатор сущности: товар, пользователь, пост |
| Query-параметры (`useSearchParams`) | `/products?category=phones&page=2` | Фильтры, поиск, сортировка, пагинация |
| `state` навигации (`useLocation`) | адрес не меняется | Временные данные: «откуда пришли», сообщение об успехе |
| Глобальное состояние | — | Данные, нужные многим страницам: корзина, пользователь |

### Способ 1. Параметр пути

Уже видели выше: `/users/:userId`. В компоненте параметр достаётся хуком `useParams`:

```jsx
import { useParams } from "react-router";

function UserPage() {
  const { userId } = useParams();
  return <h1>Профиль пользователя №{userId}</h1>;
}
```

### Способ 2. Query-параметры и useSearchParams

**Query-параметры** — часть адреса после `?`: `?search=leanne&sort=name`, пары «ключ=значение» через `&`. Плюс: состояние хранится в адресе, ссылку можно отправить другу — он увидит тот же поиск.

`useSearchParams` работает как `useState`, только хранит значение в адресе:

```jsx
import { useSearchParams, useLoaderData, Link } from "react-router";

export default function UsersPage() {
  const users = useLoaderData();
  const [searchParams, setSearchParams] = useSearchParams();

  const search = searchParams.get("search") ?? "";

  const filtered = users.filter((u) =>
    u.name.toLowerCase().includes(search.toLowerCase())
  );

  function handleChange(e) {
    const value = e.target.value;
    if (value) {
      setSearchParams({ search: value });
    } else {
      setSearchParams({});
    }
  }

  return (
    <div>
      <input value={search} onChange={handleChange} placeholder="Поиск по имени" />
      <ul>
        {filtered.map((u) => (
          <li key={u.id}>
            <Link to={`/users/${u.id}`}>{u.name}</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

Разбор:

- `searchParams` — встроенный объект `URLSearchParams`. `.get("search")` вернёт `null`, если параметра нет, поэтому `?? ""`.
- `setSearchParams({ search: value })` меняет адрес на `/users?search=value` и перерисовывает компонент; `{}` убирает все параметры.

Если параметров несколько и нужно поменять только один, используйте функцию-обновлятор:

```jsx
setSearchParams((prev) => {
  prev.set("page", "2");
  return prev;
});
```

<aside class="callout" data-icon="📌" markdown="1">

Все значения из адреса — **строки**. `searchParams.get("page")` вернёт `"2"`, а не `2`. Для вычислений превращайте в число: `Number(searchParams.get("page") ?? 1)`.

</aside>

#### Query-параметры в loader

Loader тоже может читать строку запроса — через `request.url`. Тогда фильтрация произойдёт на сервере:

```jsx
export async function usersLoader({ request }) {
  const url = new URL(request.url);
  const search = url.searchParams.get("search") ?? "";

  // адрес вашего API, который умеет искать по параметру search
  const res = await fetch(
    `https://api.example.com/users?search=${encodeURIComponent(search)}`
  );
  return res.json();
}
```

`encodeURIComponent` делает пробелы и русские буквы безопасными для адреса. Когда вызывается `setSearchParams`, роутер **заново запускает loader** — данные обновятся сами.

### Способ 3. state навигации

Данные, которые не должны быть в адресе (например, «Заказ оформлен!» после отправки формы), передают через опцию `state` у `navigate` или `Link`:

```jsx
import { useNavigate } from "react-router";

function OrderForm() {
  const navigate = useNavigate();

  function handleSubmit(e) {
    e.preventDefault();
    // ...отправили заказ на сервер
    navigate("/", { state: { message: "Заказ №123 оформлен!" } });
  }

  return (
    <form onSubmit={handleSubmit}>
      <button>Оформить</button>
    </form>
  );
}
```

Принимаем на другой странице через `useLocation`:

```jsx
import { useLocation } from "react-router";

function HomePage() {
  const location = useLocation();
  const message = location.state?.message;

  return (
    <div>
      {message && <p className="success">{message}</p>}
      <h1>Главная</h1>
    </div>
  );
}
```

<aside class="callout" data-icon="⚠️" markdown="1">

`state` живёт только в истории текущей вкладки. Если пользователь откроет ссылку в новой вкладке или отправит её другу, `location.state` будет `null`. Поэтому всегда пишите `location.state?.message` с `?.` и не храните в `state` то, без чего страница не может работать.

</aside>

### Способ 4. Глобальное состояние

Данные, нужные многим страницам (пользователь, корзина), кладут в общее хранилище — об этом уроки [обзор менеджеров состояния](lesson:obzor-state-manager) и [Zustand](lesson:zustand).

## Типичные ошибки

- **Ссылки через `<a href>`** — приложение перезагружается. Используйте `Link`.
- **Ведущий `/` у дочерних маршрутов.** `path: "/users"` внутри `children` сделает путь абсолютным. Для вложенных пишите `path: "users"`.
- **Забыли `<Outlet />`** в layout — дочерние страницы не отображаются.
- **`useLoaderData()` в маршруте без `loader`** вернёт `undefined`, и `users.map` упадёт.
- **Сравнение числа со строкой из адреса:** `user.id === params.userId` всегда `false`. Используйте `Number(params.userId)`.
- **404 на хостинге при обновлении страницы.** Сервер ищет файл `/users/5` и не находит — настройте хостинг отдавать `index.html` на все адреса (правило rewrites).

## Практика

1. **Каркас SPA.** Создайте проект на Vite с маршрутами `/`, `/about` и `/posts` и общим layout с меню на `NavLink`. Ожидаемый результат: переходы без перезагрузки, активный пункт подсвечен классом `.active`.
2. **Список постов через loader.** Для `/posts` напишите loader, который загружает `https://jsonplaceholder.typicode.com/posts`, и выведите заголовки через `useLoaderData`. Добавьте индикатор загрузки на `useNavigation`.
3. **Детальная страница.** Сделайте маршрут `/posts/:postId` с loader, который загружает один пост. Для несуществующего поста выбросьте `Response` со статусом 404 и покажите понятную страницу ошибки.
4. **Поиск в адресе.** Добавьте на `/posts` поле поиска по заголовку, значение которого хранится в `?search=`. После обновления страницы поиск должен сохраняться.
5. **Сообщение после действия.** Сделайте страницу `/posts/new` с формой. По кнопке «Сохранить» переходите на `/posts` с `state: { message: "Пост создан" }` и показывайте это сообщение над списком.

## Итоги

- SPA загружает один HTML и меняет содержимое без перезагрузки, MPA загружает новую страницу при каждом переходе.
- Маршруты описываются через `createBrowserRouter` и подключаются через `RouterProvider`; общий каркас — layout с `<Outlet />`.
- `loader` загружает данные до показа страницы, `useLoaderData` их получает, `errorElement` + `useRouteError` обрабатывают ошибки.
- Идентификаторы передаём в пути (`useParams`), фильтры и поиск — в query-параметрах (`useSearchParams`).
- Временные данные можно передать через `state` у `navigate`/`Link` и прочитать в `useLocation`.
- Все значения из адреса — строки.
