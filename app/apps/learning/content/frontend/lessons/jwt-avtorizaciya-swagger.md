Почти любое приложение требует входа: личный кабинет, корзина, заказы. В этом уроке разберём JWT-авторизацию с access- и refresh-токенами, сделаем регистрацию и вход с валидацией, научимся подставлять токен в запросы через интерцепторы axios и закрывать страницы от гостей. А ещё научимся читать API в Swagger и писать запросы по нему вручную.

## Аутентификация и авторизация

- **Аутентификация** — «кто вы?»: проверка логина и пароля.
- **Авторизация** — «что вам можно?»: свои заказы — да, админка — нет.

HTTP не помнит прошлые запросы, поэтому после входа сервер выдаёт **токен** — пропуск, который фронтенд прикладывает к каждому запросу. Аналогия: на ресепшене проверили паспорт и выдали пропуск, дальше охрана смотрит только на пропуск.

## Что такое JWT

**JWT (JSON Web Token)** — популярный формат токена из трёх частей через точку:

```text
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI0MiIsInJvbGUiOiJ1c2VyIiwiZXhwIjoxNzYwMDAwMDAwfQ.k3Jf...подпись
     header                         payload                                   signature
```

- **header** — алгоритм подписи; **payload** — данные: id пользователя (`sub`), роль, срок действия (`exp`).
- **signature** — подпись секретным ключом сервера; без ключа токен не подделать.

<aside class="callout" data-icon="🔐" markdown="1">

Payload **не зашифрован**, а лишь закодирован (base64url) — прочитать его может любой. Поэтому в JWT не кладут секреты, а сам токен берегут как пароль: кто его украл, тот вошёл под вами.

</aside>

### Access и refresh токены

| | Access token | Refresh token |
| --- | --- | --- |
| Зачем | Доступ к API: прикладывается к каждому запросу | Получить новый access, когда старый истёк |
| Срок жизни | Короткий: 5–15 минут | Длинный: дни или недели |
| Куда отправляется | В заголовке `Authorization: Bearer <token>` | Только на `/auth/refresh` |

Зачем два? Украденный access скоро «протухнет», а refresh редко ходит по сети.

### Полный цикл

```text
1. POST /auth/register  { email, password }      → 201 Created
2. POST /auth/login     { email, password }      → { access, refresh }
3. GET  /auth/me        Authorization: Bearer access   → { id, email }
4. ...через 15 минут: GET /orders                → 401 Unauthorized (access истёк)
5. POST /auth/refresh   { refresh }              → { access }  (новый)
6. Повторяем GET /orders с новым access         → 200 OK
7. Выход: удаляем токены → /login
```

## Swagger: читаем документацию API

Какие адреса есть у бэкенда и что им отправлять? Бэкенд публикует документацию в формате **OpenAPI**, а **Swagger UI** показывает её интерактивной страницей — обычно по адресу вроде `/docs` или `/swagger` (точный подскажет бэкендер).

### Что смотреть в Swagger

- **Эндпоинты** сгруппированы по тегам (`auth`, `users`); у каждого метод и путь: `POST /auth/login`.
- **Request body** — поля, их типы и обязательность (`*`); **Example Value / Schema** — пример и описание.
- **Parameters** — параметры пути (`{id}`) и query-параметры (`?page=1`).
- **Responses** — коды ответов (`200`, `400`, `401`, `422`) и их формат.
- **Значок замка** — нужен токен. **Schemas** внизу — описания моделей (`User`, `TokenPair`).

### Try it out и Authorize

1. Откройте `POST /auth/login`, нажмите **Try it out**, заполните тело и **Execute** — придёт реальный ответ с токенами.
2. Нажмите **Authorize** вверху, вставьте access-токен (иногда с префиксом `Bearer ` — зависит от сервера). Теперь эндпоинты с замком работают прямо из Swagger.

### Пишем API-функции по Swagger вручную

В Swagger: `POST /auth/login`, тело `{ email, password }`, ответ `200: { access, refresh }`. Переносим в код:

```js
// src/api/auth.js
import { api } from "./client";

export const register = (body) => api.post("/auth/register", body).then((r) => r.data);
export const login = (body) => api.post("/auth/login", body).then((r) => r.data);
export const getMe = () => api.get("/auth/me").then((r) => r.data);
```

<aside class="callout" data-icon="💡" markdown="1">

Пути и названия полей (`access` или `access_token`, `email` или `username`) у каждого бэкенда свои — всегда сверяйтесь со Swagger, а не с этим уроком. Автоматическую генерацию кода и типов по Swagger разберём в уроке [Swagger и генерация типов](lesson:swagger-generaciya-tipov).

</aside>

## Где хранить токены

| Место | Переживёт перезагрузку | Доступно из JS | Главный риск |
| --- | --- | --- | --- |
| Память (переменная, Zustand без persist) | Нет | Да | Теряется при перезагрузке |
| `localStorage` | Да | Да | **XSS**: вредный скрипт на странице прочитает токен |
| `sessionStorage` | До закрытия вкладки | Да | Тот же XSS |
| Cookie с флагом `httpOnly` | Да | **Нет** | **CSRF**, защищается флагом `SameSite` и настройками сервера |

- **XSS** (межсайтовый скриптинг) — злоумышленник запускает свой JavaScript на вашей странице (через уязвимость или заражённую библиотеку) и забирает всё из `localStorage`.
- **httpOnly cookie** ставит сервер, и JavaScript (даже вредный) не может её прочитать.

<aside class="callout" data-icon="🔐" markdown="1">

Самый безопасный вариант: refresh-токен — в `httpOnly`-cookie (это настраивает бэкенд), access — только в памяти. Во многих учебных и небольших проектах бэкенд отдаёт оба токена в JSON, и их кладут в `localStorage` — так сделаем и мы, но помните о риске XSS: не вставляйте чужой HTML через `dangerouslySetInnerHTML` и не подключайте сомнительные библиотеки.

</aside>

## Хранилище авторизации на Zustand

```js
// src/store/useAuthStore.js
import { create } from "zustand";
import { persist } from "zustand/middleware";

export const useAuthStore = create(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      setTokens: ({ access, refresh }) =>
        set((state) => ({
          accessToken: access,
          refreshToken: refresh ?? state.refreshToken,
        })),
      logout: () => set({ accessToken: null, refreshToken: null }),
    }),
    { name: "auth" }
  )
);
```

`persist` (урок [Zustand](lesson:zustand)) сохраняет токены в `localStorage`. `refresh ?? state.refreshToken` — если сервер вернул только access, старый refresh остаётся.

## axios-интерцепторы

**Интерцептор** (перехватчик) — функция, через которую axios пропускает каждый запрос или ответ, как таможня посылки.

```js
// src/api/client.js
import axios from "axios";
import { useAuthStore } from "../store/useAuthStore";

const BASE_URL = "https://api.example.com";

export const api = axios.create({ baseURL: BASE_URL });

// 1. Перед каждым запросом — подставляем access
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// 2. После ответа — ловим 401 и обновляем токен
let refreshPromise = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const isRefreshUrl = original?.url?.includes("/auth/refresh");

    if (error.response?.status !== 401 || original._retry || isRefreshUrl) {
      return Promise.reject(error);
    }
    original._retry = true;

    try {
      const { refreshToken, setTokens } = useAuthStore.getState();
      if (!refreshToken) throw error;

      refreshPromise ??= axios
        .post(`${BASE_URL}/auth/refresh`, { refresh: refreshToken })
        .then((res) => res.data)
        .finally(() => { refreshPromise = null; });

      const tokens = await refreshPromise;
      setTokens(tokens);

      original.headers.Authorization = `Bearer ${tokens.access}`;
      return api(original);
    } catch (refreshError) {
      useAuthStore.getState().logout();
      window.location.href = "/login";
      return Promise.reject(refreshError);
    }
  }
);
```

Разбор:

- **Request-интерцептор** берёт токен через `getState()` (вне компонента хук вызвать нельзя) и добавляет заголовок `Authorization`.
- **Response-интерцептор**: первый аргумент — для успешных ответов, второй — для ошибок.
- Не `401`, запрос уже повторяли (`_retry`) или упал сам refresh — отдаём ошибку дальше, иначе будет бесконечный цикл.
- `refreshPromise ??= ...` — если пять запросов разом получили `401`, токен обновится **один раз**.
- Refresh идёт через «чистый» `axios`, а не через `api`, чтобы не попасть в свои же интерцепторы.
- Новые токены получены — повторяем исходный запрос `api(original)`, пользователь ничего не заметит. Refresh не удался — выходим на `/login`.

## Регистрация с валидацией

```bash
npm install react-hook-form yup @hookform/resolvers
```

```jsx
// src/pages/RegisterPage.jsx
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import * as yup from "yup";
import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { register as registerUser } from "../api/auth";

const schema = yup.object({
  email: yup.string().required("Введите email").email("Неверный email"),
  password: yup
    .string()
    .required("Введите пароль")
    .min(8, "Минимум 8 символов")
    .matches(/\d/, "Нужна хотя бы одна цифра"),
  confirmPassword: yup
    .string()
    .required("Повторите пароль")
    .oneOf([yup.ref("password")], "Пароли не совпадают"),
});

export default function RegisterPage() {
  const navigate = useNavigate();
  const { register, handleSubmit, setError, formState: { errors } } = useForm({
    resolver: yupResolver(schema),
  });

  const mutation = useMutation({
    mutationFn: registerUser,
    onSuccess: () => navigate("/login", { state: { message: "Аккаунт создан, войдите" } }),
    onError: (error) => {
      if (error.response?.status === 400) {
        setError("email", { message: "Такой email уже зарегистрирован" });
      }
    },
  });

  const onSubmit = ({ email, password }) => mutation.mutate({ email, password });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input placeholder="Email" {...register("email")} />
      <p>{errors.email?.message}</p>

      <input type="password" placeholder="Пароль" {...register("password")} />
      <p>{errors.password?.message}</p>

      <input type="password" placeholder="Повторите пароль" {...register("confirmPassword")} />
      <p>{errors.confirmPassword?.message}</p>

      <button disabled={mutation.isPending}>Зарегистрироваться</button>
    </form>
  );
}
```

- Схема `yup` (урок [react-hook-form и yup](lesson:react-hook-form-yup)) проверяет поля **до** отправки; `yup.ref("password")` ссылается на другое поле — так сверяем пароли.
- `register as registerUser` — чтобы не путать с `register` из react-hook-form. `confirmPassword` на сервер не отправляем.
- **Серверная валидация**: сервер может отказать (email занят) — `setError` покажет ошибку под полем. Код и формат ошибки смотрите в Swagger.

<aside class="callout" data-icon="🔐" markdown="1">

Валидация на фронтенде — только для удобства пользователя. Её легко обойти, отправив запрос из Postman, поэтому настоящая проверка всегда происходит на сервере.

</aside>

### Вход

```jsx
const setTokens = useAuthStore((s) => s.setTokens);

const loginMutation = useMutation({
  mutationFn: login,
  onSuccess: (tokens) => {
    setTokens(tokens);
    navigate(location.state?.from ?? "/profile", { replace: true });
  },
  onError: () => setError("root", { message: "Неверный email или пароль" }),
});
```

Ошибку `root` выводят над кнопкой: `{errors.root?.message}`. Не уточняйте, что неверно — email или пароль: это подсказка взломщику.

## Защищённые маршруты

```jsx
// src/components/ProtectedRoute.jsx
import { Navigate, Outlet, useLocation } from "react-router";
import { useAuthStore } from "../store/useAuthStore";

export function ProtectedRoute() {
  const token = useAuthStore((s) => s.accessToken);
  const location = useLocation();

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}
```

```jsx
// src/router.jsx
createBrowserRouter([
  {
    path: "/",
    element: <RootLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "login", element: <LoginPage /> },
      { path: "register", element: <RegisterPage /> },
      {
        element: <ProtectedRoute />,
        children: [
          { path: "profile", element: <ProfilePage /> },
          { path: "orders", element: <OrdersPage /> },
        ],
      },
    ],
  },
]);
```

- `ProtectedRoute` — маршрут-обёртка без `path`: есть токен — показывает детей через `<Outlet />`, нет — отправляет на `/login`.
- `state={{ from: ... }}` запоминает, куда шёл пользователь; `replace` не даёт «Назад» вернуть на закрытую страницу.

<aside class="callout" data-icon="🔐" markdown="1">

Защищённый маршрут лишь **прячет интерфейс**. Настоящая защита — на сервере: без валидного токена API не отдаёт данные.

</aside>

### Выход

```jsx
const queryClient = useQueryClient();
const logout = useAuthStore((s) => s.logout);

function handleLogout() {
  logout();
  queryClient.clear(); // удаляем кэш с данными прошлого пользователя
  navigate("/login");
}
```

## Типичные ошибки

- **`Bearer` без пробела** или токен без префикса — сервер вернёт `401`.
- **Бесконечный цикл refresh** — нет флага `_retry` или refresh идёт через тот же `api`.
- **Не очистили кэш при выходе** — следующий пользователь видит чужие данные.
- **Токены в `console.log`** или в адресе — попадают в логи и историю.
- **Доверие к payload.** Роль из токена годится, чтобы спрятать кнопку, но не как защита.

## Практика

1. **Swagger.** Откройте Swagger учебного API (его даст ментор). Выпишите для регистрации и входа метод, путь, тело и коды ответов. Войдите через **Try it out** и **Authorize**.
2. **Регистрация.** Сделайте форму регистрации с валидацией yup: email, пароль от 8 символов с цифрой, совпадение паролей. Ожидаемый результат: ошибки под полями, запрос не уходит, пока форма невалидна.
3. **Вход и интерцептор.** Реализуйте вход, сохранение токенов в Zustand и request-интерцептор. Во вкладке Network убедитесь, что запрос `/auth/me` идёт с заголовком `Authorization`.
4. **Защищённые страницы.** Добавьте `ProtectedRoute` для `/profile` и возврат на исходную страницу после входа. Кнопка «Выйти» очищает токены и кэш.
5. **Refresh.** Добавьте response-интерцептор с обновлением токена. Испортите access-токен в Local Storage: запрос должен получить `401`, обновить токен и повториться.

## Итоги

- JWT состоит из header, payload и signature; payload читается кем угодно, поэтому секретов в нём нет.
- Access-токен короткоживущий и идёт в `Authorization: Bearer`, refresh — для получения нового access.
- Swagger показывает эндпоинты, тела запросов и ответы; по нему вручную пишем функции API и тестируем запросы через Try it out.
- Самое безопасное хранение — refresh в `httpOnly`-cookie, access в памяти; `localStorage` уязвим для XSS.
- Интерцепторы axios подставляют токен и прозрачно обновляют его при `401`.
- `ProtectedRoute` с `Navigate` и `Outlet` закрывает страницы, но настоящая защита — на сервере.
