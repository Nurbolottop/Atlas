Этот урок подводит итоги пятого месяца. Мы коротко повторим всё, что изучили: SPA на React Router, менеджеры состояния и Zustand, запросы через TanStack Query, фильтры и кэш, мутации и JWT-авторизацию. В конце — чек-лист «что нужно уметь», пример итоговой контрольной работы и советы, как к ней подготовиться.

## Как пользоваться этим уроком

Читайте раздел, затем попробуйте без подсказок ответить на вопросы для самопроверки. Если не получается — вернитесь к уроку по ссылке и повторите тему. Цель не выучить наизусть, а понять, **какой инструмент для какой задачи**.

| Задача | Инструмент |
| --- | --- |
| Несколько страниц без перезагрузки | React Router: `createBrowserRouter`, `Link`, `Outlet` |
| Данные до показа страницы | `loader` + `useLoaderData` |
| Фильтры и поиск в адресе | `useSearchParams` |
| Общие клиентские данные (корзина, тема, токен) | Zustand (или Context для редких изменений) |
| Получить данные с сервера | `useQuery` |
| Создать, изменить, удалить | `useMutation` + обновление кэша |
| Вход и закрытые страницы | JWT, axios-интерцепторы, `ProtectedRoute` |

## Повторение: React Router и SPA

Тема: [SPA на React Router](lesson:spa-na-react-router).

- **SPA** загружает одну страницу и меняет содержимое без перезагрузки; **MPA** грузит новый HTML на каждый переход.
- Маршруты описываются массивом в `createBrowserRouter` и подключаются через `RouterProvider`.
- Общий каркас — layout-компонент с `<Outlet />`; вложенные маршруты — в `children`.
- Передача данных: путь (`/users/:id` + `useParams`), query-параметры (`useSearchParams`), `state` навигации (`navigate(to, { state })` + `useLocation`).

```jsx
const router = createBrowserRouter([
  {
    path: "/",
    element: <RootLayout />,
    errorElement: <ErrorPage />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "posts/:postId", element: <PostPage />, loader: postLoader },
    ],
  },
]);

async function postLoader({ params }) {
  const res = await fetch(`https://jsonplaceholder.typicode.com/posts/${params.postId}`);
  if (!res.ok) throw new Response("Пост не найден", { status: res.status });
  return res.json();
}
```

**Вопросы для самопроверки:**

1. Почему для внутренних переходов нельзя использовать `<a href>`?
2. Чем `useParams` отличается от `useSearchParams`? Приведите пример адреса для каждого.
3. Что произойдёт, если loader выбросит ошибку?
4. Почему `searchParams.get("page") + 1` даёт неожиданный результат?

## Повторение: менеджеры состояния и Zustand

Темы: [обзор менеджеров состояния](lesson:obzor-state-manager), [Zustand](lesson:zustand).

- **Prop drilling** — передача пропсов через компоненты, которым они не нужны. Решается глобальным состоянием.
- **Context** — встроен в React, подходит для редко меняющихся данных, но перерисовывает всех подписчиков.
- **Redux Toolkit** — `createSlice`, `configureStore`, `useSelector`, `useDispatch`; строгий, популярен в крупных командах.
- **Zustand** — `create((set, get) => ({...}))`, без провайдера, минимум кода.
- **MobX** — реактивные классы и `observer`; **Jotai** — маленькие атомы.

```js
import { create } from "zustand";
import { persist } from "zustand/middleware";

export const useCartStore = create(
  persist(
    (set, get) => ({
      items: [],
      add: (product) => set({ items: [...get().items, product] }),
      remove: (id) => set({ items: get().items.filter((i) => i.id !== id) }),
      total: () => get().items.reduce((sum, i) => sum + i.price, 0),
    }),
    { name: "cart" }
  )
);

// в компоненте — только нужная часть
const count = useCartStore((s) => s.items.length);
```

**Вопросы для самопроверки:**

1. Чем клиентское состояние отличается от серверного? Чем управлять каждым?
2. Почему `useCartStore()` без селектора — плохая идея в большом приложении?
3. Зачем нужен `useShallow`?
4. Почему `get().items.push(product)` не обновит интерфейс?

## Повторение: TanStack Query — GET, фильтры, кэш

Темы: [React Query: GET](lesson:react-query-get), [фильтрация, сортировка и кэш](lesson:filtraciya-sortirovka-kesh).

- Приложение оборачивается в `QueryClientProvider`; `QueryClient` создаётся один раз вне компонентов.
- `useQuery({ queryKey, queryFn })` возвращает `data`, `isPending`, `isError`, `error`, `isFetching`, `refetch`.
- В `queryKey` — всё, от чего зависит запрос: `["products", "list", filters]`.
- `staleTime` — сколько данные свежие; `gcTime` — сколько неиспользуемые данные хранятся в кэше.
- `enabled` откладывает запрос; `placeholderData: keepPreviousData` убирает мигание при пагинации.
- `queryClient`: `getQueryData`, `setQueryData`, `invalidateQueries`, `removeQueries`, `prefetchQuery`.

```jsx
function Products() {
  const [searchParams, setSearchParams] = useSearchParams();
  const category = searchParams.get("category") ?? "";

  const { data, isPending, isError } = useQuery({
    queryKey: ["products", { category }],
    queryFn: () =>
      api.get("/products", { params: { category: category || undefined } }).then((r) => r.data),
    placeholderData: keepPreviousData,
  });

  if (isPending) return <p>Загрузка...</p>;
  if (isError) return <p>Ошибка</p>;

  return (
    <>
      <select value={category} onChange={(e) => setSearchParams(e.target.value ? { category: e.target.value } : {})}>
        <option value="">Все</option>
        <option value="phones">Телефоны</option>
      </select>
      <ul>{data.map((p) => <li key={p.id}>{p.title}</li>)}</ul>
    </>
  );
}
```

**Вопросы для самопроверки:**

1. Чем `isPending` отличается от `isFetching`?
2. Что будет, если не добавить `category` в `queryKey`?
3. Почему нельзя писать `data.sort(...)` для данных из `useQuery`?
4. Когда использовать `invalidateQueries`, а когда `setQueryData`?
5. Зачем нужен debounce при поиске?

## Повторение: useMutation и Postman

Тема: [useMutation: POST, PUT и PATCH](lesson:usemutation).

- `POST` создаёт, `PUT` заменяет целиком, `PATCH` меняет часть полей, `DELETE` удаляет.
- `useMutation({ mutationFn, onSuccess, onError, onSettled })`; запуск — `mutate(variables)` или `await mutateAsync(variables)`.
- После успеха обновляем кэш; на время запроса блокируем кнопку через `isPending`.
- Оптимистичное обновление: `onMutate` (снимок + изменение кэша), `onError` (откат), `onSettled` (инвалидация).
- **Postman** — проверка API без кода: метод, адрес, Body → raw → JSON, коллекции, переменные `{{baseUrl}}`, Bearer Token.

```jsx
const queryClient = useQueryClient();

const addTodo = useMutation({
  mutationFn: (todo) => api.post("/todos", todo).then((r) => r.data),
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ["todos"] }),
});

<button disabled={addTodo.isPending} onClick={() => addTodo.mutate({ title, completed: false })}>
  Добавить
</button>
```

**Вопросы для самопроверки:**

1. Почему мутация не выполняется сама, как `useQuery`?
2. Что случится, если отправить в PUT только одно поле?
3. Какие три колбэка нужны для оптимистичного обновления и что делает каждый?

## Повторение: JWT, валидация и Swagger

Тема: [JWT-авторизация и Swagger](lesson:jwt-avtorizaciya-swagger).

- JWT = header.payload.signature; payload читается кем угодно — секретов в нём нет.
- **Access** — короткий, идёт в `Authorization: Bearer <token>`; **refresh** — длинный, только для обновления access.
- Хранение: безопаснее всего refresh в `httpOnly`-cookie, access в памяти; `localStorage` уязвим для XSS.
- Request-интерцептор подставляет токен; response-интерцептор на `401` обновляет его и повторяет запрос.
- `ProtectedRoute` с `Navigate` и `Outlet` закрывает страницы; при выходе — очистка токенов и `queryClient.clear()`.
- Валидация формы — `yup` + `yupResolver`; серверные ошибки — через `setError`.
- **Swagger** — эндпоинты, тела, ответы, Try it out и Authorize.

**Вопросы для самопроверки:**

1. Зачем нужны два токена, а не один?
2. Почему refresh-запрос отправляют не через тот же экземпляр `api`?
3. Защищает ли `ProtectedRoute` данные на сервере?
4. Как проверить в yup, что два пароля совпадают?

## Чек-лист: что нужно уметь

Пройдитесь по каждому пункту. Если пункт вызывает сомнения — потренируйтесь ещё раз.

- Создать проект на Vite и настроить `createBrowserRouter` с layout, вложенными маршрутами и страницей ошибки.
- Загрузить данные через `loader` и получить их через `useLoaderData`.
- Хранить фильтры, сортировку и номер страницы в query-параметрах.
- Передать данные между страницами через путь, query-параметры и `state`.
- Объяснить разницу между Context, Redux Toolkit, Zustand, MobX и Jotai.
- Создать store на Zustand с действиями, селекторами и `persist`.
- Подключить TanStack Query и сделать GET-запросы со списком и детальной страницей.
- Правильно составлять `queryKey` и настраивать `staleTime`.
- Сделать серверную пагинацию и поиск с debounce.
- Создавать, изменять и удалять данные через `useMutation` и обновлять кэш.
- Проверить любой эндпоинт в Postman и прочитать его описание в Swagger.
- Реализовать регистрацию и вход с валидацией, интерцепторы и защищённые маршруты.

## Пример итоговой контрольной работы

Ниже — примерный формат. Точные задания, сроки и критерии оценки объявит ментор.

### Часть 1. Теория (устно или письменно)

1. Чем SPA отличается от MPA? Назовите плюсы и минусы каждого подхода.
2. Перечислите три способа передать данные между страницами в React Router.
3. Когда стоит выбрать Zustand, а когда хватит Context?
4. Что такое `queryKey` и почему в нём должны быть все параметры запроса?
5. Чем отличаются POST, PUT и PATCH?
6. Где можно хранить JWT-токены и какие риски у каждого варианта?

### Часть 2. Практика: «Мини-магазин»

Используйте json-server как бэкенд:

```json
{
  "products": [
    { "id": "1", "title": "Наушники", "category": "audio", "price": 50 },
    { "id": "2", "title": "Клавиатура", "category": "pc", "price": 80 },
    { "id": "3", "title": "Мышь", "category": "pc", "price": 30 }
  ],
  "reviews": []
}
```

**Обязательные требования:**

1. Маршруты: `/` (каталог), `/products/:id` (товар), `/cart` (корзина), страница 404. Общая шапка с `NavLink`.
2. Каталог загружается через `useQuery`; фильтр по категории и сортировка по цене хранятся в query-параметрах.
3. Страница товара — отдельный запрос с ключом `["products", id]`.
4. Корзина — Zustand-store с `persist`: добавление, удаление, изменение количества, итоговая сумма. Значок в шапке показывает количество товаров.
5. На странице товара — форма отзыва (react-hook-form + yup: имя обязательно, текст от 10 символов), отправка через `useMutation` (POST `/reviews`), после чего список отзывов обновляется.
6. Состояния загрузки и ошибок обработаны на всех страницах.

**Дополнительно (на повышенную оценку):**

- Оптимистичное удаление отзыва с откатом при ошибке.
- Предзагрузка товара при наведении на карточку.
- Страница `/admin`, закрытая `ProtectedRoute` (токен можно имитировать кнопкой «Войти», которая кладёт строку `"FAKE_TOKEN"` в store).

### Как обычно проверяют работу

- Приложение запускается командами `npm install` и `npm run dev` без ошибок в консоли.
- Все обязательные пункты работают; после перезагрузки фильтры и корзина сохраняются.
- Код разбит на понятные файлы: `api/`, `store/`, `hooks/`, `pages/`, `components/`.
- Вы можете объяснить любую строку своего кода.

<aside class="callout" data-icon="⚠️" markdown="1">

Самая частая причина потерянных баллов — не баги, а то, что студент не может объяснить свой код. Если что-то взяли из документации или подсказки ИИ, разберитесь, как это работает, до сдачи.

</aside>

## Советы по подготовке

- **Повторяйте руками, а не глазами.** Перечитать урок — мало. Закройте его и напишите пример с нуля.
- **Соберите шпаргалку**: структура `createBrowserRouter`, шаблон store на Zustand, шаблон `useQuery` и `useMutation`. Она пригодится и на работе.
- **Начинайте с API.** Перед кодом проверьте эндпоинты в Postman — это экономит время на поиск ошибок.
- **Открывайте DevTools.** Вкладка Network показывает запросы и ответы, React Query Devtools — кэш, Application → Local Storage — сохранённые данные.
- **Делайте коммиты** после каждого готового пункта (урок [Git и основы JS](lesson:git-i-osnovy-js)), чтобы можно было откатиться.
- **Читайте ошибки целиком.** Текст ошибки в консоли почти всегда подсказывает, где проблема.

<aside class="callout" data-icon="💡" markdown="1">

Если застряли больше чем на 30 минут — сформулируйте вопрос: что делаю, что ожидаю, что получаю, какой текст ошибки. Часто во время формулировки ответ находится сам, а если нет — с таким вопросом ментору будет легко помочь.

</aside>

## Практика

1. **Самопроверка.** Ответьте письменно на все вопросы для самопроверки из этого урока. Ожидаемый результат: по каждому вопросу 2–3 предложения своими словами.
2. **Шпаргалка.** Составьте файл-шпаргалку с шаблонами: роутер с layout и loader, store на Zustand с `persist`, `useQuery` с параметрами, `useMutation` с инвалидацией, axios-интерцептор.
3. **Пробная контрольная.** Выполните обязательную часть «Мини-магазина» за 3–4 часа, засекая время.
4. **Повышенный уровень.** Добавьте в «Мини-магазин» все дополнительные пункты.
5. **Код-ревью.** Обменяйтесь проектами с одногруппником и найдите друг у друга по три замечания: ошибки, неудобный код, необработанные состояния.

## Итоги

- React Router отвечает за страницы, `loader` — за данные до показа, `useSearchParams` — за состояние в адресе.
- Zustand и другие менеджеры состояния хранят клиентские данные; серверные — в TanStack Query.
- `useQuery` получает данные с кэшированием, `useMutation` изменяет их, `queryClient` управляет кэшем.
- JWT-авторизация: два токена, интерцепторы, защищённые маршруты и внимание к безопасности.
- Swagger и Postman помогают понять и проверить API до написания кода.
- Готовьтесь практикой: пишите код с нуля и умейте объяснить каждую строку.
