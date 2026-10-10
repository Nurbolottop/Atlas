Zustand — один из самых простых и популярных менеджеров состояния для React. Хранилище создаётся одной функцией, не нужен провайдер, а код получается коротким и понятным. В этом уроке разберём все основные моменты: как создать store, читать и менять данные, писать асинхронные действия, сохранять состояние в `localStorage` и не допускать лишних перерисовок.

## Что такое Zustand и зачем он нужен

В уроке [обзор менеджеров состояния](lesson:obzor-state-manager) мы увидели, что глобальное состояние избавляет от prop drilling. Zustand решает эту задачу с минимумом кода:

- **store** (хранилище) — обычный объект с данными и функциями, которые их меняют;
- **хук** — store превращается в хук `useXxxStore`, который можно вызвать в любом компоненте;
- **провайдер не нужен** — store живёт вне дерева React, как отдельный модуль.

Аналогия: store — это общая доска объявлений в офисе. Любой сотрудник (компонент) может подойти, прочитать нужное объявление или повесить новое. Не нужно передавать записки из рук в руки.

### Установка

```bash
npm create vite@latest zustand-demo -- --template react
cd zustand-demo
npm install
npm install zustand
```

## Первый store: счётчик

```js
// src/store/useCounterStore.js
import { create } from "zustand";

export const useCounterStore = create((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 })),
  decrement: () => set((state) => ({ count: state.count - 1 })),
  reset: () => set({ count: 0 }),
}));
```

Разбор по строкам:

- `create(...)` — создаёт store и возвращает хук. Название по договорённости начинается с `use` и заканчивается на `Store`.
- `(set) => ({ ... })` — функция, которая описывает store. Она получает `set` — функцию для изменения состояния — и возвращает начальный объект.
- `count: 0` — данные (state).
- `increment`, `decrement`, `reset` — **действия (actions)**: функции, которые меняют данные. Они лежат прямо в store рядом с данными.
- `set((state) => ({ count: state.count + 1 }))` — форма с функцией: получаем текущее состояние и возвращаем, что нужно изменить. Используйте её, когда новое значение зависит от старого.
- `set({ count: 0 })` — короткая форма: просто передаём новые значения.

<aside class="callout" data-icon="📌" markdown="1">

`set` **сливает** (merge) переданный объект с текущим состоянием. Если в store есть `count` и `title`, то `set({ count: 0 })` поменяет только `count`, а `title` останется. Но слияние неглубокое: вложенные объекты нужно копировать самостоятельно через spread.

</aside>

### Используем в компонентах

```jsx
// src/components/Counter.jsx
import { useCounterStore } from "../store/useCounterStore";

export function Counter() {
  const count = useCounterStore((state) => state.count);
  const increment = useCounterStore((state) => state.increment);
  const decrement = useCounterStore((state) => state.decrement);
  const reset = useCounterStore((state) => state.reset);

  return (
    <div>
      <h2>{count}</h2>
      <button onClick={decrement}>−</button>
      <button onClick={increment}>+</button>
      <button onClick={reset}>Сброс</button>
    </div>
  );
}
```

```jsx
// src/components/Header.jsx — совсем в другом месте дерева
import { useCounterStore } from "../store/useCounterStore";

export function Header() {
  const count = useCounterStore((state) => state.count);
  return <header>Текущее значение: {count}</header>;
}
```

Функция `(state) => state.count` называется **селектор**: она выбирает из store нужный кусочек. Компонент перерисуется **только тогда**, когда изменится то, что вернул селектор. Если `Header` читает только `count`, то изменения других полей его не затронут.

## Селекторы и лишние перерисовки

### Не берите весь store целиком

```jsx
// ❌ Плохо: компонент перерисуется при ЛЮБОМ изменении в store
const { count } = useCounterStore();

// ✅ Хорошо: только при изменении count
const count = useCounterStore((state) => state.count);
```

Вызов хука без селектора вернёт весь объект. Для маленького счётчика разницы нет, а в большом store это заметно замедлит приложение.

### Несколько полей сразу: useShallow

Хочется достать несколько значений одной строкой. Но если селектор каждый раз возвращает **новый** объект, Zustand посчитает, что данные изменились:

```jsx
// ❌ Каждый раз новый объект → бесконечные перерисовки / ошибка
const { count, increment } = useCounterStore((state) => ({
  count: state.count,
  increment: state.increment,
}));
```

Для этого есть `useShallow` — он сравнивает поля объекта по отдельности (поверхностно):

```jsx
import { useShallow } from "zustand/react/shallow";

const { count, increment } = useCounterStore(
  useShallow((state) => ({ count: state.count, increment: state.increment }))
);
```

<aside class="callout" data-icon="⚠️" markdown="1">

В Zustand v5 селектор, возвращающий новый объект или массив без `useShallow`, приводит к ошибке «Maximum update depth exceeded». Если видите её — оберните селектор в `useShallow` или выбирайте поля по одному.

</aside>

## get: чтение состояния внутри действий

Кроме `set`, функция store получает второй аргумент — `get`. Он возвращает текущее состояние. Пригодится, когда действию нужно прочитать данные без их изменения.

```js
// src/store/useCartStore.js
import { create } from "zustand";

export const useCartStore = create((set, get) => ({
  items: [],

  addItem: (product) => {
    const exists = get().items.find((item) => item.id === product.id);
    if (exists) {
      set({
        items: get().items.map((item) =>
          item.id === product.id ? { ...item, qty: item.qty + 1 } : item
        ),
      });
    } else {
      set({ items: [...get().items, { ...product, qty: 1 }] });
    }
  },

  removeItem: (id) =>
    set((state) => ({ items: state.items.filter((item) => item.id !== id) })),

  clear: () => set({ items: [] }),

  totalPrice: () =>
    get().items.reduce((sum, item) => sum + item.price * item.qty, 0),
}));
```

Разбор:

- `addItem` сначала через `get()` проверяет, есть ли товар в корзине. Если есть — увеличивает `qty` (количество), создавая **новый** массив через `map` и новый объект через spread. Если нет — добавляет товар с `qty: 1`.
- `totalPrice` — функция, которая считает сумму. В компоненте её вызывают так: `useCartStore((s) => s.totalPrice())`.

```jsx
function CartSummary() {
  const items = useCartStore((s) => s.items);
  const total = useCartStore((s) => s.totalPrice());
  const clear = useCartStore((s) => s.clear);

  return (
    <div>
      <p>Товаров: {items.length}</p>
      <p>Сумма: {total} сом</p>
      <button onClick={clear}>Очистить</button>
    </div>
  );
}
```

<aside class="callout" data-icon="⚠️" markdown="1">

Не мутируйте состояние: `get().items.push(product)` изменит массив «на месте», и React **не увидит** изменений — интерфейс не обновится. Всегда создавайте новый массив или объект.

</aside>

## Асинхронные действия

Действие может быть `async`: загрузить данные с сервера и записать их в store. Zustand не требует ничего особенного — просто вызываем `set`, когда данные пришли.

```js
// src/store/useUsersStore.js
import { create } from "zustand";

export const useUsersStore = create((set) => ({
  users: [],
  isLoading: false,
  error: null,

  fetchUsers: async () => {
    set({ isLoading: true, error: null });
    try {
      const res = await fetch("https://jsonplaceholder.typicode.com/users");
      if (!res.ok) throw new Error("Ошибка загрузки");
      const data = await res.json();
      set({ users: data, isLoading: false });
    } catch (err) {
      set({ error: err.message, isLoading: false });
    }
  },
}));
```

```jsx
import { useEffect } from "react";
import { useUsersStore } from "../store/useUsersStore";

export function UsersList() {
  const users = useUsersStore((s) => s.users);
  const isLoading = useUsersStore((s) => s.isLoading);
  const error = useUsersStore((s) => s.error);
  const fetchUsers = useUsersStore((s) => s.fetchUsers);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  if (isLoading) return <p>Загрузка...</p>;
  if (error) return <p>Ошибка: {error}</p>;

  return (
    <ul>
      {users.map((u) => (
        <li key={u.id}>{u.name}</li>
      ))}
    </ul>
  );
}
```

- Перед запросом ставим `isLoading: true` и сбрасываем прошлую ошибку.
- `try/catch` (урок [try, catch, finally](lesson:try-catch-finally)) ловит сетевые ошибки и наш `throw`.
- Функции в store не пересоздаются, поэтому `fetchUsers` в зависимостях `useEffect` безопасен.

<aside class="callout" data-icon="💡" markdown="1">

Так можно, но для серверных данных удобнее TanStack Query: он сам хранит загрузку, ошибки и кэш. Мы перейдём на него в уроке [React Query: GET](lesson:react-query-get). А в Zustand оставим клиентские данные: корзину, настройки, токен.

</aside>

## Сохранение в localStorage: persist

По умолчанию store живёт в памяти и обнуляется после перезагрузки страницы. Middleware **persist** (промежуточный слой) автоматически сохраняет состояние в `localStorage` и восстанавливает его при запуске.

```js
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export const useSettingsStore = create(
  persist(
    (set) => ({
      theme: "light",
      language: "ru",
      toggleTheme: () =>
        set((state) => ({ theme: state.theme === "light" ? "dark" : "light" })),
      setLanguage: (language) => set({ language }),
    }),
    {
      name: "settings-storage",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ theme: state.theme, language: state.language }),
    }
  )
);
```

- `persist(описание store, настройки)` — оборачиваем нашу функцию.
- `name` — ключ, под которым данные лежат в `localStorage`. Откройте DevTools → Application → Local Storage и увидите его (урок [JSON, localStorage и DevTools](lesson:json-storage-devtools)).
- `storage` — где хранить. `localStorage` — по умолчанию; можно `sessionStorage`.
- `partialize` — что именно сохранять. Функции сохранять не нужно, поэтому выбираем только данные.

## DevTools: смотрим, что происходит в store

Middleware `devtools` подключает store к расширению браузера **Redux DevTools**: вы увидите каждое изменение и состояние до и после.

```js
import { create } from "zustand";
import { devtools } from "zustand/middleware";

export const useCounterStore = create(
  devtools(
    (set) => ({
      count: 0,
      increment: () =>
        set((state) => ({ count: state.count + 1 }), undefined, "counter/increment"),
    }),
    { name: "CounterStore" }
  )
);
```

Третий аргумент `set` — имя действия, которое отобразится в DevTools. Middleware можно комбинировать: `create(devtools(persist((set) => ({...}), {...})))`.

## Работа со store вне компонентов

Хук из `create` — ещё и объект с методами. Это полезно в обычных JS-функциях, например в axios-интерцепторе (урок [JWT-авторизация](lesson:jwt-avtorizaciya-swagger)):

```js
// прочитать текущее состояние
const count = useCounterStore.getState().count;

// вызвать действие
useCounterStore.getState().increment();

// изменить напрямую
useCounterStore.setState({ count: 10 });

// подписаться на изменения
const unsubscribe = useCounterStore.subscribe((state) => {
  console.log("Новое значение:", state.count);
});
```

<aside class="callout" data-icon="⚠️" markdown="1">

`getState()` внутри компонента **не подписывает** его на изменения: значение прочитается один раз и не обновится. В компонентах всегда используйте хук с селектором.

</aside>

## Как организовать stores

- Делайте **несколько небольших stores** по смыслу: `useCartStore`, `useAuthStore`, `useSettingsStore`. Их проще читать и тестировать.
- Храните stores в папке `src/store/` (или `src/stores/`), по одному файлу на store.
- Добавляйте действие `reset`, чтобы вернуть начальное состояние (например, при выходе из аккаунта):

```js
const initialState = { items: [] };

export const useCartStore = create((set) => ({
  ...initialState,
  addItem: (p) => set((s) => ({ items: [...s.items, p] })),
  reset: () => set(initialState),
}));
```

Подробнее — в официальной документации [Zustand](https://zustand.docs.pmnd.rs/).

## Практика

1. **Счётчик.** Создайте `useCounterStore` с действиями `increment`, `decrement`, `reset` и `incrementBy(n)`. Выведите значение в двух разных компонентах. Ожидаемый результат: оба компонента синхронно показывают одно число.
2. **Список дел.** Сделайте `useTodoStore` с полем `todos` и действиями `addTodo(text)`, `toggleTodo(id)`, `removeTodo(id)`. Форма добавления и список — отдельные компоненты без общих пропсов.
3. **Сохранение.** Подключите `persist` к списку дел. Ожидаемый результат: после перезагрузки страницы задачи остаются, в Local Storage виден ваш ключ.
4. **Корзина.** Реализуйте корзину с `qty`, `totalPrice()`, кнопками «+» и «−» у каждого товара (при `qty` = 0 товар удаляется). Используйте `useShallow` хотя бы в одном компоненте.
5. **Загрузка с сервера.** Сделайте `usePostsStore` с асинхронным `fetchPosts`, полями `isLoading` и `error`. Подключите `devtools` и проверьте в Redux DevTools, что видны все изменения.

## Итоги

- `create((set, get) => ({...}))` создаёт store и возвращает хук; провайдер не нужен.
- Данные и действия лежат вместе; `set` сливает изменения с текущим состоянием, `get` читает его.
- Читайте данные через селекторы, для нескольких полей — `useShallow`.
- Состояние нельзя мутировать: всегда новый массив или объект.
- `persist` сохраняет store в `localStorage`, `devtools` показывает изменения в Redux DevTools.
- `getState()`/`setState()` позволяют работать со store вне компонентов.
