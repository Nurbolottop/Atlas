Загружать данные через `useEffect` и `useState` мы уже умеем, но это много однотипного кода: состояние загрузки, ошибки, повторные запросы, устаревшие данные. Библиотека **TanStack Query** (её часто называют React Query) берёт всю эту рутину на себя. В этом уроке установим TanStack Query v5, сделаем первые GET-запросы через `useQuery` и разберёмся, что такое кэш и ключи запросов.

## Зачем нужен React Query

### Как мы делали раньше

```jsx
import { useEffect, useState } from "react";

function UsersList() {
  const [users, setUsers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("https://jsonplaceholder.typicode.com/users")
      .then((res) => {
        if (!res.ok) throw new Error("Ошибка загрузки");
        return res.json();
      })
      .then(setUsers)
      .catch((err) => setError(err.message))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <p>Загрузка...</p>;
  if (error) return <p>{error}</p>;
  return <ul>{users.map((u) => <li key={u.id}>{u.name}</li>)}</ul>;
}
```

Работает, но:

- три `useState` в каждом компоненте с запросом;
- ушли со страницы и вернулись — запрос летит заново, пользователь снова видит «Загрузка...»;
- два компонента просят одни и те же данные — уходят два одинаковых запроса;
- данные на сервере изменились — у нас висят старые, пока не обновим страницу;
- нет повторной попытки при сбое сети.

### Что даёт TanStack Query

**TanStack Query** — библиотека для работы с **серверным состоянием**: данными, которые живут на сервере, а у нас лишь их копия. Она:

- сама хранит `data`, загрузку и ошибку;
- **кэширует** ответы: повторный переход на страницу показывает данные мгновенно;
- объединяет одинаковые запросы в один;
- обновляет данные в фоне (например, когда вы вернулись во вкладку);
- повторяет неудачный запрос (по умолчанию 3 раза).

Аналогия: **кэш** — это холодильник. Сходили в магазин (сервер) один раз, положили продукты в холодильник. Следующий раз берёте из холодильника сразу, а в магазин идёте, только когда продукты «устарели».

## Установка и настройка

```bash
npm create vite@latest query-demo -- --template react
cd query-demo
npm install
npm install @tanstack/react-query axios
npm install -D @tanstack/react-query-devtools
```

- `@tanstack/react-query` — сама библиотека;
- `axios` — HTTP-клиент, который мы использовали в уроке [ToDoList: axios и json-server](lesson:todolist-axios-json-server);
- `@tanstack/react-query-devtools` — панель для просмотра кэша (только для разработки).

### QueryClient и QueryClientProvider

```jsx
// src/main.jsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import App from "./App";

const queryClient = new QueryClient();

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </StrictMode>
);
```

- `QueryClient` — «мозг» библиотеки: хранит кэш всех запросов и настройки.
- `QueryClientProvider` раздаёт этот клиент всем компонентам приложения.
- `ReactQueryDevtools` добавляет в угол экрана кнопку с цветком. Нажмите — увидите все запросы, их ключи, статус и данные.

<aside class="callout" data-icon="⚠️" markdown="1">

Создавайте `QueryClient` **вне** компонента (как выше). Если написать `new QueryClient()` внутри `App`, при каждой перерисовке будет создаваться новый клиент с пустым кэшем.

</aside>

## Первый запрос: useQuery

### Функция запроса

Удобно вынести запросы в отдельный файл:

```js
// src/api/users.js
import axios from "axios";

const api = axios.create({
  baseURL: "https://jsonplaceholder.typicode.com",
});

export async function getUsers() {
  const { data } = await api.get("/users");
  return data;
}

export async function getUserById(id) {
  const { data } = await api.get(`/users/${id}`);
  return data;
}
```

`axios` сам превращает ответ в JSON и сам бросает ошибку, если статус 4xx или 5xx. Это важно: TanStack Query понимает, что запрос неудачен, только когда функция **бросает ошибку** (или возвращает отклонённый Promise).

### Компонент со списком

```jsx
// src/components/UsersList.jsx
import { useQuery } from "@tanstack/react-query";
import { getUsers } from "../api/users";

export function UsersList() {
  const { data, isPending, isError, error } = useQuery({
    queryKey: ["users"],
    queryFn: getUsers,
  });

  if (isPending) return <p>Загрузка...</p>;
  if (isError) return <p>Ошибка: {error.message}</p>;

  return (
    <ul>
      {data.map((user) => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}
```

Разбор:

- `useQuery({ ... })` принимает **один объект** с настройками (в v5 только так).
- `queryKey: ["users"]` — **ключ запроса**: уникальное имя данных в кэше. Если другой компонент вызовет `useQuery` с тем же ключом, он получит те же данные из кэша, без нового запроса.
- `queryFn: getUsers` — функция, которая загружает данные и возвращает Promise.
- `isPending` — `true`, пока данных ещё нет совсем (первая загрузка).
- `isError` и `error` — запрос завершился ошибкой; `error.message` — её текст.
- `data` — результат `queryFn`. После проверок `isPending` и `isError` он точно есть.

Сравните с вариантом на `useEffect`: ни одного `useState`, а возможностей больше.

## Состояния запроса

| Поле | Что значит |
| --- | --- |
| `status` | `"pending"`, `"error"` или `"success"` |
| `isPending` | Данных ещё нет (первая загрузка) |
| `isSuccess` | Данные получены |
| `isError` | Ошибка; подробности в `error` |
| `isFetching` | Идёт запрос прямо сейчас — в том числе фоновое обновление, когда данные уже есть |
| `isLoading` | `isPending && isFetching` — первая загрузка, которая действительно идёт |
| `refetch` | Функция, чтобы вручную запросить данные заново |

<aside class="callout" data-icon="📌" markdown="1">

Разница между `isPending` и `isFetching`: `isPending` — «данных нет, показываю скелетон», `isFetching` — «данные есть, но я тихо обновляю их в фоне». Для фонового обновления хватит маленького значка, а не замены всего экрана.

</aside>

```jsx
function UsersHeader() {
  const { isFetching, refetch } = useQuery({
    queryKey: ["users"],
    queryFn: getUsers,
  });

  return (
    <div>
      <h2>Пользователи {isFetching && "🔄"}</h2>
      <button onClick={() => refetch()}>Обновить</button>
    </div>
  );
}
```

Этот компонент использует тот же ключ `["users"]`, что и `UsersList`. Запрос уйдёт один, а оба компонента получат одни данные.

## Запрос с параметром

Для страницы одного пользователя в ключ добавляем его `id`:

```jsx
// src/pages/UserPage.jsx
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router";
import { getUserById } from "../api/users";

export function UserPage() {
  const { userId } = useParams();

  const { data: user, isPending, isError, error } = useQuery({
    queryKey: ["users", userId],
    queryFn: () => getUserById(userId),
  });

  if (isPending) return <p>Загрузка...</p>;
  if (isError) return <p>Ошибка: {error.message}</p>;

  return (
    <article>
      <h1>{user.name}</h1>
      <p>{user.email}</p>
      <p>{user.company.name}</p>
    </article>
  );
}
```

- `queryKey: ["users", userId]` — у каждого пользователя свой кэш: `["users", "1"]`, `["users", "2"]`… Когда `userId` меняется, TanStack Query видит новый ключ и сам делает новый запрос.
- `queryFn: () => getUserById(userId)` — нужна стрелочная функция, потому что передаём аргумент.
- `data: user` — переименовываем `data` при деструктуризации, чтобы код читался понятнее.

<aside class="callout" data-icon="⚠️" markdown="1">

Правило: **всё, от чего зависит запрос, должно быть в `queryKey`.** Если забыть `userId` в ключе, то при переходе с первого пользователя на второго вы увидите данные первого — для библиотеки это «тот же самый» запрос.

</aside>

### Зависимые запросы: enabled

Иногда запрос нельзя делать сразу: например, ждём, пока пользователь выберет город. Опция `enabled` включает и выключает запрос:

```jsx
import { useQuery } from "@tanstack/react-query";
import axios from "axios";

function UserPosts({ userId }) {
  const { data: posts, isPending } = useQuery({
    queryKey: ["posts", { userId }],
    queryFn: async () => {
      const res = await axios.get("https://jsonplaceholder.typicode.com/posts", {
        params: { userId },
      });
      return res.data;
    },
    enabled: Boolean(userId),
  });

  if (!userId) return <p>Выберите пользователя</p>;
  if (isPending) return <p>Загрузка постов...</p>;
  return <ul>{posts.map((p) => <li key={p.id}>{p.title}</li>)}</ul>;
}
```

Пока `userId` пустой, запрос не отправляется. Обратите внимание: `axios` с опцией `params` сам соберёт адрес `/posts?userId=1`.

## Как работает кэш: staleTime и gcTime

Две главные настройки времени:

- **`staleTime`** — сколько данные считаются **свежими**. Пока они свежие, TanStack Query не идёт на сервер повторно. По умолчанию `0` — данные сразу «несвежие», и при новом монтировании компонента или возврате во вкладку произойдёт фоновое обновление.
- **`gcTime`** (garbage collection time) — сколько хранить в кэше данные, которые **никто не использует**. По умолчанию 5 минут. Потом они удаляются из памяти. В v4 эта опция называлась `cacheTime`.

```jsx
const { data } = useQuery({
  queryKey: ["users"],
  queryFn: getUsers,
  staleTime: 1000 * 60,     // 1 минута данные свежие — без повторных запросов
  gcTime: 1000 * 60 * 10,   // 10 минут храним в кэше после ухода со страницы
});
```

Что видит пользователь при `staleTime: 0`: он уходит со страницы списка и возвращается — список появляется **мгновенно** из кэша, а в фоне летит запрос, и если данные изменились — они тихо обновляются. Это называется **stale-while-revalidate**: «показывай старое, пока проверяешь новое».

### Настройки по умолчанию для всего приложения

```js
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 30,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
```

- `retry: 1` — при ошибке повторить один раз (по умолчанию 3).
- `refetchOnWindowFocus: false` — не обновлять данные при возврате во вкладку. Удобно на время разработки, когда это мешает.

## Свой хук для запроса

Чтобы не повторять `queryKey` и `queryFn` в каждом компоненте, оборачивают запрос в свой хук:

```js
// src/hooks/useUsers.js
import { useQuery } from "@tanstack/react-query";
import { getUsers, getUserById } from "../api/users";

export function useUsers() {
  return useQuery({ queryKey: ["users"], queryFn: getUsers });
}

export function useUser(id) {
  return useQuery({
    queryKey: ["users", id],
    queryFn: () => getUserById(id),
    enabled: Boolean(id),
  });
}
```

```jsx
function UsersList() {
  const { data, isPending, isError } = useUsers();
  // ...
}
```

Теперь ключи живут в одном месте — меньше шансов опечататься.

## Типичные ошибки

- **Нет `QueryClientProvider`** — ошибка «No QueryClient set». Оберните приложение провайдером.
- **Старый синтаксис** `useQuery(["users"], getUsers)` из v3/v4 в v5 не работает: только объект `{ queryKey, queryFn }`.
- **`queryFn` не бросает ошибку.** `fetch` не бросает ошибку на статус 404 или 500 — проверяйте `res.ok` и делайте `throw` сами, иначе запрос будет «успешным» с неправильными данными.
- **Обращение к `data` до проверки загрузки** — `data.map` упадёт, пока `data` равно `undefined`.
- **Копирование ответа в `useState`** — лишнее: данные уже лежат в кэше, берите их из `data`.

Подробнее — в официальной документации [TanStack Query](https://tanstack.com/query/latest/docs/framework/react/overview).

## Практика

1. **Список постов.** Подключите TanStack Query и выведите заголовки постов с `https://jsonplaceholder.typicode.com/posts`. Покажите «Загрузка...» и текст ошибки. Ожидаемый результат: в DevTools виден запрос с ключом `["posts"]`.
2. **Кэш в действии.** Добавьте две страницы на React Router: список постов и «О проекте». Переключайтесь между ними и понаблюдайте во вкладке Network: при возврате список появляется мгновенно, а фоновый запрос уходит. Затем поставьте `staleTime: 60000` и убедитесь, что запросов стало меньше.
3. **Детальная страница.** Сделайте `/posts/:postId` с запросом `["posts", postId]` и выводом заголовка и текста поста.
4. **Зависимый запрос.** На детальной странице под постом выведите комментарии (`/comments?postId=...`) отдельным `useQuery`. Ожидаемый результат: пост и комментарии грузятся независимо, у каждого свой индикатор.
5. **Свои хуки.** Вынесите все запросы в `src/api/posts.js`, а хуки — в `src/hooks/usePosts.js`. Добавьте кнопку «Обновить» с `refetch` и значком на `isFetching`.

## Итоги

- TanStack Query управляет серверным состоянием: загрузка, ошибки, кэш, повторы и фоновое обновление.
- Приложение оборачивается в `QueryClientProvider` с одним `QueryClient`, созданным вне компонентов.
- `useQuery({ queryKey, queryFn })` возвращает `data`, `isPending`, `isError`, `error`, `isFetching`, `refetch`.
- В `queryKey` кладём всё, от чего зависит запрос; одинаковый ключ — общие данные.
- `staleTime` — сколько данные свежие, `gcTime` — сколько неиспользуемые данные живут в кэше.
- `enabled` позволяет отложить запрос, пока не готовы его параметры.
