Получать данные с сервера через `useQuery` мы научились. Теперь пора их **изменять**: создавать, обновлять и удалять. В TanStack Query для этого есть хук `useMutation`. В этом уроке разберём методы POST, PUT и PATCH, научимся обновлять кэш после изменений, сделаем «оптимистичное» обновление интерфейса, а перед этим проверим запросы в Postman — главном инструменте для тестирования API.

## Запрос на чтение и запрос на изменение

| | `useQuery` | `useMutation` |
| --- | --- | --- |
| Задача | Получить данные | Изменить данные на сервере |
| HTTP-методы | GET | POST, PUT, PATCH, DELETE |
| Когда выполняется | Автоматически при монтировании компонента | Только когда вы вызовете `mutate` |
| Кэшируется | Да, по `queryKey` | Нет |

**Мутация** (от слова «изменение») — любой запрос, который меняет данные на сервере.

### Напоминание: POST, PUT, PATCH

Мы знакомились с ними в уроках [формы и POST](lesson:formy-i-post) и [REST API, PUT и DELETE](lesson:rest-api-put-delete):

| Метод | Что делает | Пример | Тело запроса |
| --- | --- | --- | --- |
| `POST` | Создаёт новую запись | `POST /todos` | Вся новая запись (без `id`) |
| `PUT` | **Заменяет** запись целиком | `PUT /todos/3` | Все поля записи |
| `PATCH` | **Частично** изменяет запись | `PATCH /todos/3` | Только изменённые поля |
| `DELETE` | Удаляет запись | `DELETE /todos/3` | Обычно нет |

Аналогия: PUT — переклеить всю этикетку на банке, PATCH — исправить на этикетке одну цифру. Если в PUT забыть какое-то поле, сервер может его стереть.

## Работа с Postman

**Postman** — программа для отправки HTTP-запросов без написания кода. Прежде чем писать запрос в React, удобно проверить в Postman: работает ли API, какое тело нужно, что приходит в ответ.

### Подготовка: локальный API

```json
{
  "todos": [
    { "id": "1", "title": "Выучить useQuery", "completed": true },
    { "id": "2", "title": "Выучить useMutation", "completed": false }
  ]
}
```

```bash
npx json-server db.json --port 3001
```

### Первый запрос

1. Установите Postman с официального сайта и откройте его (можно без регистрации или через бесплатный аккаунт).
2. Нажмите **New → HTTP** (или «+» на панели вкладок).
3. Слева от адресной строки выберите метод `GET`, введите `http://localhost:3001/todos` и нажмите **Send**.
4. Внизу появится ответ: статус `200 OK`, время и JSON со списком задач.

### POST с телом запроса

1. Смените метод на `POST`, адрес тот же.
2. Откройте вкладку **Body → raw** и справа выберите тип **JSON**.
3. Введите тело:

```json
{
  "title": "Проверить API в Postman",
  "completed": false
}
```

4. Нажмите **Send**. Ответ — статус `201 Created` и созданная задача, уже с `id`.

Так же проверьте `PATCH http://localhost:3001/todos/2` с телом `{ "completed": true }` и `PUT` с полным объектом.

### Полезные возможности

- **Collections** — папки для сохранения запросов. Сохраните все запросы проекта в одну коллекцию, чтобы не набирать заново.
- **Environments и переменные.** Создайте переменную `baseUrl = http://localhost:3001` и пишите адреса как `{{baseUrl}}/todos`. При переезде на боевой сервер меняете переменную в одном месте.
- **Headers** — заголовки запроса. Postman сам ставит `Content-Type: application/json` для raw JSON.
- **Authorization** — вкладка для токенов: выбираете **Bearer Token** и вставляете токен. Пригодится в уроке [JWT-авторизация](lesson:jwt-avtorizaciya-swagger).

<aside class="callout" data-icon="💡" markdown="1">

Если запрос не работает в React, сначала повторите его в Postman. Работает в Postman, но не в браузере — ищите ошибку во фронтенде (адрес, тело, заголовки, CORS). Не работает и в Postman — проблема в API или в запросе.

</aside>

## Первая мутация: создаём задачу

### Функции API

```js
// src/api/todos.js
import axios from "axios";

const api = axios.create({ baseURL: "http://localhost:3001" });

export const getTodos = async () => (await api.get("/todos")).data;

export const createTodo = async (todo) => (await api.post("/todos", todo)).data;

export const updateTodo = async ({ id, ...todo }) =>
  (await api.put(`/todos/${id}`, todo)).data;

export const patchTodo = async ({ id, ...changes }) =>
  (await api.patch(`/todos/${id}`, changes)).data;

export const deleteTodo = async (id) => api.delete(`/todos/${id}`);
```

`({ id, ...changes })` — деструктуризация с rest (урок [деструктуризация, spread, rest](lesson:destrukturizaciya-spread-rest)): `id` идёт в адрес, остальные поля — в тело.

### Компонент с useMutation

```jsx
// src/components/AddTodo.jsx
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createTodo } from "../api/todos";

export function AddTodo() {
  const [title, setTitle] = useState("");
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: createTodo,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      setTitle("");
    },
    onError: (error) => {
      alert(`Не удалось создать задачу: ${error.message}`);
    },
  });

  function handleSubmit(e) {
    e.preventDefault();
    if (!title.trim()) return;
    mutation.mutate({ title, completed: false });
  }

  return (
    <form onSubmit={handleSubmit}>
      <input value={title} onChange={(e) => setTitle(e.target.value)} />
      <button disabled={mutation.isPending}>
        {mutation.isPending ? "Сохраняю..." : "Добавить"}
      </button>
      {mutation.isError && <p>Ошибка: {mutation.error.message}</p>}
    </form>
  );
}
```

Разбор:

- `mutationFn: createTodo` — функция, которая выполняет запрос. Она получает то, что вы передадите в `mutate`.
- `mutation.mutate({ title, completed: false })` — **запускает** мутацию. Сама по себе мутация не выполняется.
- `onSuccess` — вызывается после успешного ответа. Здесь мы **инвалидируем** кэш `["todos"]`: список задач помечается устаревшим и перезапрашивается, новая задача сразу появляется в списке.
- `onError` — вызывается при ошибке (сеть, статус 4xx/5xx).
- `mutation.isPending` — идёт запрос. Блокируем кнопку, чтобы пользователь не создал задачу дважды двойным кликом.

### Что возвращает useMutation

| Поле | Значение |
| --- | --- |
| `mutate(variables, { onSuccess, onError })` | Запустить мутацию |
| `mutateAsync(variables)` | То же, но возвращает Promise — можно `await` |
| `isPending` / `isSuccess` / `isError` | Состояние последнего запуска |
| `data` | Ответ сервера |
| `error` | Ошибка |
| `variables` | Данные, с которыми вызвали `mutate` |
| `reset()` | Сбросить состояние (например, убрать сообщение об ошибке) |

### Колбэки: onSuccess, onError, onSettled

```jsx
useMutation({
  mutationFn: createTodo,
  onSuccess: (data, variables) => {
    console.log("Сервер вернул:", data);       // созданная задача с id
    console.log("Мы отправили:", variables);  // { title, completed }
  },
  onError: (error) => console.error(error),
  onSettled: () => {
    // вызывается всегда — и после успеха, и после ошибки (как finally)
  },
});
```

<aside class="callout" data-icon="📌" markdown="1">

`mutate` возвращает `undefined`, а ошибки обрабатывает через `onError`. Если нужно дождаться результата через `await`, используйте `mutateAsync` — но тогда оборачивайте вызов в `try/catch`, иначе ошибка «вылетит» необработанной.

</aside>

```jsx
async function handleSubmit(values) {
  try {
    const created = await mutation.mutateAsync(values);
    navigate(`/todos/${created.id}`);
  } catch (error) {
    // ошибку уже видно в mutation.error
  }
}
```

## PATCH и PUT: обновляем задачу

### Переключение статуса через PATCH

```jsx
// src/components/TodoItem.jsx
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { patchTodo, deleteTodo } from "../api/todos";

export function TodoItem({ todo }) {
  const queryClient = useQueryClient();

  const toggle = useMutation({
    mutationFn: patchTodo,
    onSuccess: (updated) => {
      queryClient.setQueryData(["todos"], (old) =>
        old?.map((t) => (t.id === updated.id ? updated : t))
      );
    },
  });

  const remove = useMutation({
    mutationFn: deleteTodo,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["todos"] }),
  });

  return (
    <li>
      <input
        type="checkbox"
        checked={todo.completed}
        disabled={toggle.isPending}
        onChange={() => toggle.mutate({ id: todo.id, completed: !todo.completed })}
      />
      {todo.title}
      <button onClick={() => remove.mutate(todo.id)} disabled={remove.isPending}>
        Удалить
      </button>
    </li>
  );
}
```

Здесь показаны два способа обновить экран после мутации:

- **`invalidateQueries`** — «сходи на сервер ещё раз». Просто и надёжно, но это лишний запрос.
- **`setQueryData`** — «вот новые данные, запиши в кэш». Сервер вернул обновлённую задачу — подменяем её в списке без нового запроса. Не забываем создавать новый массив через `map`.

### Редактирование через PUT

PUT отправляет **все** поля записи:

```jsx
const edit = useMutation({
  mutationFn: updateTodo,
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ["todos"] }),
});

// отправляем весь объект целиком
edit.mutate({ id: todo.id, title: newTitle, completed: todo.completed });
```

<aside class="callout" data-icon="⚠️" markdown="1">

Частая ошибка: отправить в PUT только изменённое поле — `{ id, title }`. Сервер заменит запись целиком, и поле `completed` пропадёт. Меняете одно поле — используйте PATCH.

</aside>

## Оптимистичное обновление

Обычно интерфейс ждёт ответа сервера. **Оптимистичное обновление** — меняем интерфейс **сразу**, будто сервер уже ответил «ок», а если пришла ошибка — откатываем назад. Так работают лайки в соцсетях: сердечко краснеет мгновенно.

```jsx
const toggle = useMutation({
  mutationFn: patchTodo,

  onMutate: async (changes) => {
    await queryClient.cancelQueries({ queryKey: ["todos"] });
    const previous = queryClient.getQueryData(["todos"]);

    queryClient.setQueryData(["todos"], (old) =>
      old?.map((t) => (t.id === changes.id ? { ...t, ...changes } : t))
    );

    return { previous };
  },

  onError: (error, changes, context) => {
    queryClient.setQueryData(["todos"], context.previous);
  },

  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ["todos"] });
  },
});
```

По шагам:

1. **`onMutate`** вызывается до запроса. `cancelQueries` отменяет текущие загрузки списка, чтобы они не перезаписали наше изменение старыми данными.
2. Сохраняем снимок кэша `previous` — на случай отката.
3. Сразу меняем задачу в кэше — галочка ставится мгновенно.
4. Возвращаем `{ previous }` — этот объект придёт третьим аргументом в `onError`.
5. **`onError`** — что-то пошло не так, возвращаем снимок.
6. **`onSettled`** — в любом случае сверяемся с сервером.

<aside class="callout" data-icon="💡" markdown="1">

Оптимистичные обновления делают интерфейс «быстрым», но добавляют сложности. Используйте их для частых мелких действий (лайк, галочка, перетаскивание). Для создания заказа или оплаты лучше честно показать «Сохраняю...».

</aside>

## Мутация и форма

С react-hook-form (урок [react-hook-form и yup](lesson:react-hook-form-yup)) мутация подключается так:

```jsx
import { useForm } from "react-hook-form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createTodo } from "../api/todos";

function TodoForm() {
  const { register, handleSubmit, reset } = useForm();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: createTodo,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      reset();
    },
  });

  return (
    <form onSubmit={handleSubmit((values) => mutation.mutate({ ...values, completed: false }))}>
      <input {...register("title", { required: true })} />
      <button disabled={mutation.isPending}>Добавить</button>
    </form>
  );
}
```

## Типичные ошибки

- **Ждут, что мутация выполнится сама.** В отличие от `useQuery`, нужно вызвать `mutate`.
- **Забыли обновить кэш.** Задача создана на сервере, но список прежний — добавьте `invalidateQueries` или `setQueryData` в `onSuccess`.
- **PUT вместо PATCH** с неполными данными — поля стираются.
- **Нет блокировки кнопки** на `isPending` — двойной клик создаёт две записи.
- **`mutateAsync` без `try/catch`** — необработанная ошибка в консоли.

Подробнее — в документации [TanStack Query: Mutations](https://tanstack.com/query/latest/docs/framework/react/guides/mutations).

## Практика

1. **Postman.** Создайте коллекцию «Todos» с переменной `{{baseUrl}}` и пятью запросами: GET, POST, PUT, PATCH, DELETE. Ожидаемый результат: все запросы возвращают правильные статусы (`200`, `201`).
2. **Создание.** Сделайте форму добавления задачи на `useMutation` с блокировкой кнопки и сообщением об ошибке. Остановите json-server и проверьте, что ошибка показывается.
3. **Обновление и удаление.** Добавьте чекбокс (PATCH) и кнопку «Удалить». После PATCH обновляйте кэш через `setQueryData`, после удаления — через `invalidateQueries`.
4. **Редактирование.** Сделайте режим редактирования названия с сохранением через PUT. Проверьте в Postman, что поле `completed` не пропало.
5. **Оптимистичный чекбокс.** Переделайте переключение статуса на оптимистичное обновление с откатом. Для проверки временно поменяйте адрес на несуществующий: галочка должна поставиться и вернуться обратно.

## Итоги

- `useMutation({ mutationFn })` — хук для POST, PUT, PATCH и DELETE; запускается вызовом `mutate` или `mutateAsync`.
- POST создаёт, PUT заменяет целиком, PATCH меняет часть полей.
- После успешной мутации обновляем кэш: `invalidateQueries` (перезапрос) или `setQueryData` (подмена данных).
- `isPending` помогает блокировать кнопки, `onError` — показать ошибку, `onSettled` — выполнить код в любом случае.
- Оптимистичное обновление: `onMutate` меняет кэш сразу, `onError` откатывает, `onSettled` сверяет с сервером.
- Postman помогает проверить API до написания кода: методы, тело, заголовки, токены и коллекции.
