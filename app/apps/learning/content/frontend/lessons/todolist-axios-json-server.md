Пора собрать всё изученное в настоящий мини-проект — список задач (ToDoList), который хранит данные на сервере. Мы поднимем учебный сервер **json-server** за одну минуту, проверим его в **Postman**, научимся делать запросы через библиотеку **axios** и сравним её с `fetch`. В конце у вас будет приложение, где задачи можно добавлять, отмечать, редактировать и удалять — и после перезагрузки страницы они никуда не исчезнут.

## План проекта

```text
Браузер (React, порт 5173)  ⇄  HTTP-запросы  ⇄  json-server (порт 3001)  ⇄  файл db.json
```

Что умеет приложение:

1.  Загружает список задач с сервера при открытии.
2.  Добавляет новую задачу.
3.  Отмечает задачу выполненной.
4.  Редактирует текст задачи.
5.  Удаляет задачу.
6.  Фильтрует: все / активные / выполненные.

Каждое действие — это HTTP-запрос. Вспомните таблицу методов из урока [REST API, PUT и DELETE](lesson:rest-api-put-delete):

| Действие | Метод | Адрес |
| --- | --- | --- |
| Получить все задачи | `GET` | `/todos` |
| Создать задачу | `POST` | `/todos` |
| Изменить часть полей | `PATCH` | `/todos/:id` |
| Удалить задачу | `DELETE` | `/todos/:id` |

## Шаг 1. Создаём проект

```bash
npm create vite@latest todo-app -- --template react
cd todo-app
npm install
npm install axios
npm install -D json-server
```

-   `axios` — библиотека для HTTP-запросов;
-   `json-server` ставим как dev-зависимость (`-D`): он нужен только для разработки.

Очистите `src/App.jsx` и `src/App.css` от стартового кода Vite.

## Шаг 2. Поднимаем json-server

**json-server** — это «ненастоящий» сервер для учёбы и прототипов. Вы даёте ему JSON-файл, а он сразу создаёт по нему полноценное REST API: можно получать, добавлять, менять и удалять данные. Все изменения записываются обратно в файл. Пока бэкенд-разработчик пишет настоящий сервер, фронтендер может работать с json-server.

Создайте в **корне проекта** (рядом с `package.json`, не в `src`) файл `db.json`:

```json
{
  "todos": [
    { "id": "1", "title": "Выучить JSX", "completed": true },
    { "id": "2", "title": "Разобраться с useState", "completed": true },
    { "id": "3", "title": "Сделать ToDoList на axios", "completed": false }
  ]
}
```

Ключ `todos` станет адресом `/todos`. Добавьте в `package.json` скрипт:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "server": "json-server db.json --port 3001"
  }
}
```

Запустите сервер **в отдельном терминале**:

```bash
npm run server
```

Откройте в браузере `http://localhost:3001/todos` — вы увидите массив задач в формате JSON. Сервер работает!

<aside class="callout" data-icon="💡" markdown="1">

Нам понадобятся **два терминала одновременно**: в одном `npm run server` (json-server на порту 3001), в другом `npm run dev` (React на порту 5173). Если закрыть терминал с сервером — приложение получит ошибку сети.

</aside>

<aside class="callout" data-icon="⚠️" markdown="1">

Новые версии json-server сами генерируют `id` новых записей в виде строки (например, `"a1b2"`), старые — числом. Поэтому мы и в `db.json` пишем `id` строками и нигде в коде не делаем с ними арифметику — просто передаём как есть.

</aside>

## Шаг 3. Проверяем API в Postman

**Postman** — программа для отправки HTTP-запросов без написания кода. Это как «пульт» для сервера: выбираете метод, вводите адрес, нажимаете Send и смотрите ответ. Бэкендеры и фронтендеры пользуются им каждый день, чтобы проверить, как работает API, ещё до того как писать интерфейс.

Скачайте Postman с официального сайта postman.com (есть и веб-версия, но для запросов на `localhost` удобнее установленное приложение) и выполните четыре запроса.

### GET — получить список

1.  Нажмите «New» → «HTTP» (или `+` для новой вкладки).
2.  Метод `GET`, адрес `http://localhost:3001/todos`.
3.  Нажмите **Send**. Внизу появится ответ со статусом `200 OK` и массивом задач.

Одну задачу можно получить по адресу `http://localhost:3001/todos/1`.

### POST — создать задачу

1.  Метод `POST`, адрес `http://localhost:3001/todos`.
2.  Вкладка **Body** → **raw** → в выпадающем списке справа выберите **JSON**.
3.  Тело запроса:

```json
{
  "title": "Задача из Postman",
  "completed": false
}
```

4.  **Send**. Статус `201 Created`, в ответе — новая задача с `id`, который выдал сервер. Загляните в `db.json` — запись появилась в файле.

### PATCH — изменить поле

Метод `PATCH`, адрес `http://localhost:3001/todos/3`, Body → raw → JSON:

```json
{ "completed": true }
```

Сервер изменит только поле `completed`, остальные поля останутся. (`PUT` заменил бы задачу целиком — нужно было бы прислать все поля.)

### DELETE — удалить

Метод `DELETE`, адрес `http://localhost:3001/todos/3`, тело не нужно. После запроса задача исчезнет из `db.json`.

<aside class="callout" data-icon="💡" markdown="1">

Сохраняйте запросы в **коллекцию** (кнопка Save → New Collection «ToDo API»). Так у вас будет готовый набор запросов к проекту, который можно отправить коллегам.

</aside>

## Шаг 4. Знакомимся с axios

С `fetch` вы уже работали в уроке [fetch, async/await и GET](lesson:fetch-async-await-get). **axios** делает то же самое, но удобнее. Сравним одинаковый POST-запрос:

```js
// fetch
const response = await fetch('http://localhost:3001/todos', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ title: 'Новая задача', completed: false }),
});
if (!response.ok) throw new Error(`Ошибка ${response.status}`);
const todo = await response.json();
```

```js
// axios
const { data: todo } = await axios.post('http://localhost:3001/todos', {
  title: 'Новая задача',
  completed: false,
});
```

| | `fetch` | `axios` |
| --- | --- | --- |
| Установка | Встроен в браузер | `npm install axios` |
| Превратить объект в JSON | Вручную `JSON.stringify` + заголовок | Автоматически |
| Получить данные ответа | `await response.json()` | Сразу в `response.data` |
| Ошибки 404, 500 | Не выбрасывает ошибку, нужно проверять `response.ok` | Выбрасывает ошибку сама |
| Общие настройки (адрес, заголовки) | Писать обёртку самому | `axios.create({ baseURL })` |

Оба инструмента рабочие, и знать нужно оба. В этом проекте используем axios.

### Экземпляр axios с базовым адресом

Чтобы не повторять `http://localhost:3001` в каждом запросе, создадим **экземпляр** axios с настройками. Адрес вынесем в переменную окружения — так его легко поменять, когда появится настоящий сервер.

Создайте в корне проекта файл `.env`:

```bash
VITE_API_URL=http://localhost:3001
```

В Vite в код попадают только переменные, которые начинаются с `VITE_`, а читаются они через `import.meta.env`. После изменения `.env` перезапустите `npm run dev`.

```js
// src/api/client.js
import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 5000, // если сервер молчит 5 секунд — ошибка
});
```

<aside class="callout" data-icon="🔐" markdown="1">

Всё, что начинается с `VITE_`, попадает в собранный JavaScript и видно любому пользователю в браузере. Адрес API хранить так можно, а секретные ключи и пароли — никогда.

</aside>

## Шаг 5. Слой API

Хорошая практика — не писать запросы прямо в компонентах, а собрать их в отдельный файл. Компоненты будут вызывать понятные функции вроде `createTodo(title)` и не думать об адресах и методах.

```js
// src/api/todos.js
import { api } from './client';

export async function getTodos() {
  const { data } = await api.get('/todos');
  return data;
}

export async function createTodo(title) {
  const { data } = await api.post('/todos', { title, completed: false });
  return data; // сервер вернёт задачу вместе с новым id
}

export async function updateTodo(id, changes) {
  const { data } = await api.patch(`/todos/${id}`, changes);
  return data;
}

export async function deleteTodo(id) {
  await api.delete(`/todos/${id}`);
}
```

-   `api.get('/todos')` — axios склеит `baseURL` и путь: `http://localhost:3001/todos`.
-   `{ data }` — деструктуризация: из ответа axios сразу берём тело.
-   `updateTodo(id, changes)` — универсальная функция: `changes` может быть `{ completed: true }` или `{ title: 'Новый текст' }`.

## Шаг 6. Компоненты

Структура:

```text
src/
├── api/
│   ├── client.js
│   └── todos.js
├── components/
│   ├── TodoForm.jsx
│   ├── TodoItem.jsx
│   └── TodoItem.module.css
├── App.jsx
├── App.module.css
└── main.jsx
```

### TodoForm — добавление задачи

```jsx
// src/components/TodoForm.jsx
import { useState } from 'react';

function TodoForm({ onAdd }) {
  const [title, setTitle] = useState('');
  const [isSending, setIsSending] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    const text = title.trim();
    if (!text) return;

    setIsSending(true);
    try {
      await onAdd(text);
      setTitle(''); // очищаем поле только при успехе
    } finally {
      setIsSending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8 }}>
      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Что нужно сделать?"
        style={{ flex: 1, padding: 8 }}
      />
      <button type="submit" disabled={isSending || !title.trim()}>
        {isSending ? 'Добавляем...' : 'Добавить'}
      </button>
    </form>
  );
}

export default TodoForm;
```

Форма ничего не знает о сервере: она просто вызывает `onAdd(text)` из пропсов и ждёт результат. Кнопка заблокирована, пока поле пустое или идёт отправка.

### TodoItem — одна задача с редактированием

```jsx
// src/components/TodoItem.jsx
import { useState } from 'react';
import styles from './TodoItem.module.css';

function TodoItem({ todo, onToggle, onDelete, onRename }) {
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState(todo.title);

  function startEdit() {
    setDraft(todo.title);
    setIsEditing(true);
  }

  async function saveEdit() {
    const text = draft.trim();
    if (text && text !== todo.title) {
      await onRename(todo.id, text);
    }
    setIsEditing(false);
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') saveEdit();
    if (e.key === 'Escape') setIsEditing(false);
  }

  return (
    <li className={styles.item}>
      <input
        type="checkbox"
        checked={todo.completed}
        onChange={() => onToggle(todo.id, !todo.completed)}
      />

      {isEditing ? (
        <input
          className={styles.edit}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={saveEdit}
          autoFocus
        />
      ) : (
        <span
          className={`${styles.title} ${todo.completed ? styles.done : ''}`}
          onDoubleClick={startEdit}
        >
          {todo.title}
        </span>
      )}

      <button onClick={startEdit} disabled={isEditing}>✏️</button>
      <button onClick={() => onDelete(todo.id)}>🗑️</button>
    </li>
  );
}

export default TodoItem;
```

```css
/* src/components/TodoItem.module.css */
.item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
  border-bottom: 1px solid #e5e7eb;
}

.title {
  flex: 1;
  cursor: pointer;
}

.done {
  text-decoration: line-through;
  color: #9ca3af;
}

.edit {
  flex: 1;
  padding: 4px 6px;
}
```

Разбор:

-   `isEditing` — локальное состояние задачи: показываем текст или поле ввода. Другим задачам и `App` это знать не нужно, поэтому состояние живёт здесь.
-   `draft` — черновик текста. Пока пользователь печатает, мы не дёргаем сервер; запрос уходит только при сохранении.
-   Сохранение — по Enter или при уходе с поля (`onBlur`); Escape — отмена.
-   `autoFocus` ставит курсор в поле редактирования сразу при появлении.
-   Двойной клик по тексту тоже включает редактирование.

### App — состояние и запросы

```jsx
// src/App.jsx
import { useEffect, useState } from 'react';
import { getTodos, createTodo, updateTodo, deleteTodo } from './api/todos';
import TodoForm from './components/TodoForm';
import TodoItem from './components/TodoItem';
import styles from './App.module.css';

const FILTERS = {
  all: () => true,
  active: (todo) => !todo.completed,
  done: (todo) => todo.completed,
};

function App() {
  const [todos, setTodos] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');

  // 1. Загрузка списка при открытии
  useEffect(() => {
    getTodos()
      .then((data) => setTodos(data))
      .catch(() => setError('Не удалось загрузить задачи. Запущен ли json-server?'))
      .finally(() => setIsLoading(false));
  }, []);

  // 2. Добавление
  async function handleAdd(title) {
    try {
      const newTodo = await createTodo(title);
      setTodos((prev) => [...prev, newTodo]);
    } catch {
      setError('Не удалось добавить задачу');
    }
  }

  // 3. Отметка выполнения
  async function handleToggle(id, completed) {
    try {
      const updated = await updateTodo(id, { completed });
      setTodos((prev) => prev.map((t) => (t.id === id ? updated : t)));
    } catch {
      setError('Не удалось обновить задачу');
    }
  }

  // 4. Переименование
  async function handleRename(id, title) {
    try {
      const updated = await updateTodo(id, { title });
      setTodos((prev) => prev.map((t) => (t.id === id ? updated : t)));
    } catch {
      setError('Не удалось переименовать задачу');
    }
  }

  // 5. Удаление
  async function handleDelete(id) {
    if (!confirm('Удалить задачу?')) return;
    try {
      await deleteTodo(id);
      setTodos((prev) => prev.filter((t) => t.id !== id));
    } catch {
      setError('Не удалось удалить задачу');
    }
  }

  const visibleTodos = todos.filter(FILTERS[filter]);
  const activeCount = todos.filter((t) => !t.completed).length;

  return (
    <div className={styles.app}>
      <h1>Мои задачи</h1>

      <TodoForm onAdd={handleAdd} />

      {error && (
        <p className={styles.error}>
          {error} <button onClick={() => setError(null)}>✕</button>
        </p>
      )}

      <div className={styles.filters}>
        <button className={filter === 'all' ? styles.active : ''} onClick={() => setFilter('all')}>Все</button>
        <button className={filter === 'active' ? styles.active : ''} onClick={() => setFilter('active')}>Активные</button>
        <button className={filter === 'done' ? styles.active : ''} onClick={() => setFilter('done')}>Выполненные</button>
      </div>

      {isLoading ? (
        <p>Загрузка...</p>
      ) : visibleTodos.length === 0 ? (
        <p>Здесь пока пусто</p>
      ) : (
        <ul className={styles.list}>
          {visibleTodos.map((todo) => (
            <TodoItem
              key={todo.id}
              todo={todo}
              onToggle={handleToggle}
              onDelete={handleDelete}
              onRename={handleRename}
            />
          ))}
        </ul>
      )}

      <p className={styles.counter}>Осталось задач: {activeCount}</p>
    </div>
  );
}

export default App;
```

```css
/* src/App.module.css */
.app { max-width: 520px; margin: 40px auto; padding: 0 16px; font-family: system-ui, sans-serif; }
.list { list-style: none; padding: 0; }
.filters { display: flex; gap: 8px; margin: 16px 0; }
.active { background: #2563eb; color: white; }
.error { color: #dc2626; }
.counter { color: #6b7280; }
```

### Разбор App

-   **Состояние.** `todos` — данные с сервера; `isLoading` и `error` — для интерфейса загрузки и ошибок; `filter` — выбранная вкладка.
-   **Загрузка.** `useEffect` с пустым массивом запускает `getTodos()` один раз. Здесь показан вариант с `.then/.catch/.finally` — он тоже рабочий и короче для простого случая.
-   **Сначала сервер, потом экран.** В каждом обработчике мы ждём ответа сервера и только потом обновляем `todos`. Если сервер вернул ошибку — состояние не меняется, и пользователь видит сообщение. Экран всегда совпадает с тем, что лежит в базе.
-   **Ответ сервера — источник правды.** После `PATCH` мы заменяем задачу тем объектом, который вернул сервер (`updated`), а при создании — берём `newTodo` с `id` от сервера.
-   **Неизменяемые обновления.** `[...prev, newTodo]`, `map`, `filter` — как в уроке про `useState`.
-   **Фильтр вычисляется**, а не хранится: `visibleTodos` и `activeCount` считаются из `todos` при каждом рендере.
-   **Вложенный тернарник** выбирает одно из трёх состояний: загрузка, пусто, список.

## Шаг 7. Запуск и проверка

```bash
# терминал 1
npm run server

# терминал 2
npm run dev
```

Проверьте:

1.  Открылся список из `db.json`.
2.  Добавьте задачу — она появилась в списке и в файле `db.json`.
3.  Отметьте, переименуйте (двойной клик), удалите — обновите страницу, изменения сохранились.
4.  Откройте DevTools → вкладка **Network** → фильтр **Fetch/XHR**. Каждое действие — отдельный запрос с методом, статусом и телом (повторите урок [JSON и DevTools](lesson:json-storage-devtools)).
5.  Остановите json-server и обновите страницу — должно появиться понятное сообщение об ошибке, а не белый экран.

## Типичные ошибки

| Симптом | Причина | Решение |
| --- | --- | --- |
| `Network Error` / `ERR_CONNECTION_REFUSED` | json-server не запущен или другой порт | Запустить `npm run server`, сверить порт в `.env` |
| `import.meta.env.VITE_API_URL` равен `undefined` | Нет префикса `VITE_` или не перезапущен dev-сервер | Проверить имя, перезапустить `npm run dev` |
| `404 Not Found` | Опечатка в пути (`/todo` вместо `/todos`) | Сверить с ключом в `db.json` |
| Страница перезагружается при добавлении | Нет `e.preventDefault()` | Добавить в `handleSubmit` |
| Изменения пропадают после перезагрузки | Состояние меняется, а запрос не отправляется | Сначала вызывать функцию API |
| `db.json` лежит в `src` и Vite перезагружает страницу | Vite следит за файлами в проекте | Хранить `db.json` в корне проекта |

## Практика

1.  **Postman.** Создайте коллекцию «ToDo API» с запросами GET (все), GET (одна задача), POST, PATCH, DELETE. Ожидаемый результат: все запросы отрабатывают, изменения видны в `db.json`.
2.  **Базовый проект.** Повторите ToDoList по шагам этого урока. Ожидаемый результат: все 5 действий работают и сохраняются после перезагрузки.
3.  **Кнопка «Удалить выполненные».** Удаляет все задачи с `completed: true`. Подсказка: `Promise.all` по массиву запросов `deleteTodo` (вспомните урок [Event Loop и Promise](lesson:event-loop-i-promise)).
4.  **Тосты.** Подключите react-toastify из урока [Формы и react-toastify](lesson:react-hook-form-yup): вместо блока `error` показывайте `toast.error`, а при добавлении и удалении — `toast.success`.
5.  **Дата и приоритет.** Добавьте в задачу поля `createdAt` (дата создания, `new Date().toISOString()`) и `priority` (`low`/`medium`/`high`, выбор через `select` в форме). Выводите дату в формате `toLocaleDateString('ru-RU')` и цветную метку приоритета. Добавьте сортировку по приоритету.

## Итоги

-   json-server за минуту превращает `db.json` в REST API: `GET`, `POST`, `PATCH`, `DELETE` по адресу `/todos`.
-   Postman позволяет проверить API без кода: метод, адрес, тело в Body → raw → JSON, Send.
-   axios сам превращает данные в JSON, кладёт ответ в `response.data` и выбрасывает ошибку на статусах 4xx/5xx.
-   `axios.create({ baseURL })` + адрес в `.env` (`VITE_API_URL`) избавляют от повторов.
-   Запросы выносят в слой `api/`, компоненты вызывают понятные функции.
-   Сначала дожидаемся ответа сервера, потом обновляем состояние неизменяемыми методами, а ошибки показываем пользователю.
