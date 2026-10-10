Когда приложение растёт, одни и те же данные — пользователь, корзина, тема оформления — нужны сразу многим компонентам. Передавать их пропсами через пять уровней неудобно, и тут на помощь приходят **менеджеры состояния**. В этом уроке разберём, какие они бывают (Context, Redux Toolkit, Zustand, MobX, Jotai), напишем одну и ту же корзину на каждом и поймём, что выбрать для своего проекта.

## Что такое состояние и где оно живёт

**Состояние (state)** — это данные, которые меняются во время работы приложения и влияют на то, что видно на экране: текст в поле, открыт ли модал, список товаров в корзине.

### Локальное и глобальное состояние

- **Локальное** — нужно одному компоненту: открыт ли выпадающий список, значение поля ввода. Для него хватает `useState` (урок [useState и useEffect](lesson:usestate-i-useeffect)).
- **Глобальное** — нужно многим компонентам в разных частях дерева: авторизованный пользователь, корзина, язык интерфейса.

### Проблема prop drilling

Представим: корзину хранит `App`, а количество товаров показывает значок в `Header → Nav → CartIcon`.

```jsx
function App() {
  const [cart, setCart] = useState([]);
  return <Header cart={cart} />;
}

function Header({ cart }) {
  return <Nav cart={cart} />; // Header'у корзина не нужна, он просто передаёт
}

function Nav({ cart }) {
  return <CartIcon cart={cart} />; // Nav'у тоже не нужна
}

function CartIcon({ cart }) {
  return <span>🛒 {cart.length}</span>;
}
```

Это называется **prop drilling** («сверление пропсами»): данные протаскиваются через компоненты, которым они не нужны. Аналогия: чтобы передать записку соседу через три квартиры, вы стучитесь в каждую дверь по пути.

**Менеджер состояния** — это общее «хранилище» вне дерева компонентов. Любой компонент может напрямую взять из него данные или изменить их, без посредников.

### Клиентское и серверное состояние

Важно различать два вида данных:

| | Клиентское состояние | Серверное состояние |
| --- | --- | --- |
| Что это | Живёт только в браузере | Копия данных с сервера |
| Примеры | Тема, открыт ли модал, корзина до оформления | Список товаров, профиль, заказы |
| Чем управлять | Context, Zustand, Redux, Jotai | TanStack Query (уроки [React Query](lesson:react-query-get) и дальше) |

<aside class="callout" data-icon="📌" markdown="1">

Частая ошибка новичков — хранить в Redux или Zustand всё подряд, включая ответы сервера, и вручную писать загрузку, ошибки и обновление. Для серверных данных есть специальный инструмент — TanStack Query. Менеджеры состояния нужны в основном для **клиентских** данных.

</aside>

## Context API — встроенный в React

**Context** — механизм React, который позволяет «раздать» значение всем вложенным компонентам без пропсов. Ничего устанавливать не нужно.

### Корзина на Context

```jsx
// src/context/CartContext.jsx
import { createContext, useContext, useState } from "react";

const CartContext = createContext(null);

export function CartProvider({ children }) {
  const [items, setItems] = useState([]);

  const addItem = (product) => setItems((prev) => [...prev, product]);
  const removeItem = (id) =>
    setItems((prev) => prev.filter((item) => item.id !== id));

  return (
    <CartContext value={{ items, addItem, removeItem }}>
      {children}
    </CartContext>
  );
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart нужно использовать внутри CartProvider");
  return ctx;
}
```

Разбор:

- `createContext(null)` создаёт «канал» для передачи данных.
- `CartProvider` хранит состояние через обычный `useState` и раздаёт его всем детям.
- `<CartContext value={...}>` — провайдер. В React 19 контекст можно использовать как провайдер напрямую; в React 18 и старше пишут `<CartContext.Provider value={...}>`.
- `useCart` — свой хук, чтобы не писать `useContext(CartContext)` в каждом компоненте и сразу ловить ошибку, если провайдер забыли.

Подключаем и используем:

```jsx
// main.jsx
<CartProvider>
  <App />
</CartProvider>

// CartIcon.jsx — в любом месте дерева
function CartIcon() {
  const { items } = useCart();
  return <span>🛒 {items.length}</span>;
}
```

### Плюсы и минусы Context

- ✅ Встроен в React, прост для редко меняющихся данных: тема, язык, текущий пользователь.
- ❌ Когда значение меняется, **перерисовываются все** компоненты, которые используют этот контекст, даже если им нужна только часть данных.
- ❌ Много провайдеров превращаются в «пирамиду» из обёрток.

<aside class="callout" data-icon="💡" markdown="1">

Context — это скорее способ **доставки** данных, а не полноценный менеджер состояния. Для часто меняющихся данных и большого приложения лучше взять библиотеку.

</aside>

## Redux Toolkit — индустриальный стандарт

**Redux** — самый известный менеджер состояния. Вся информация хранится в одном объекте — **store** (хранилище). Изменить его можно только отправив **action** (действие) — объект с описанием «что произошло». **Reducer** — функция, которая по action вычисляет новое состояние.

**Redux Toolkit (RTK)** — официальный современный способ писать на Redux: меньше кода и меньше ошибок.

```bash
npm install @reduxjs/toolkit react-redux
```

### Корзина на Redux Toolkit

```js
// src/store/cartSlice.js
import { createSlice } from "@reduxjs/toolkit";

const cartSlice = createSlice({
  name: "cart",
  initialState: { items: [] },
  reducers: {
    addItem(state, action) {
      state.items.push(action.payload);
    },
    removeItem(state, action) {
      state.items = state.items.filter((item) => item.id !== action.payload);
    },
  },
});

export const { addItem, removeItem } = cartSlice.actions;
export default cartSlice.reducer;
```

```js
// src/store/index.js
import { configureStore } from "@reduxjs/toolkit";
import cartReducer from "./cartSlice";

export const store = configureStore({
  reducer: { cart: cartReducer },
});
```

```jsx
// main.jsx
import { Provider } from "react-redux";
import { store } from "./store";

<Provider store={store}>
  <App />
</Provider>
```

```jsx
// Компоненты
import { useDispatch, useSelector } from "react-redux";
import { addItem } from "./store/cartSlice";

function CartIcon() {
  const count = useSelector((state) => state.cart.items.length);
  return <span>🛒 {count}</span>;
}

function ProductCard({ product }) {
  const dispatch = useDispatch();
  return <button onClick={() => dispatch(addItem(product))}>В корзину</button>;
}
```

Разбор:

- `createSlice` — создаёт «кусочек» хранилища: начальное состояние + функции изменения. Внутри можно «мутировать» `state.items.push(...)` — RTK под капотом (через библиотеку Immer) превратит это в безопасное создание нового объекта.
- `cartSlice.actions` — готовые функции-создатели action: `addItem(product)` вернёт `{ type: "cart/addItem", payload: product }`.
- `useSelector` — достаёт из store нужную часть. Компонент перерисуется, только если **эта часть** изменилась.
- `useDispatch` — даёт функцию `dispatch`, чтобы отправить action.

### Когда Redux

- ✅ Большие команды и проекты: строгая структура, отличные DevTools (видно каждое действие и «перемотку времени»).
- ✅ Много вакансий его требуют — знать основы полезно.
- ❌ Больше шаблонного кода и понятий, чем в альтернативах.

## Zustand — просто и быстро

**Zustand** (по-немецки «состояние») — маленькая библиотека: хранилище создаётся одной функцией, провайдер не нужен.

```bash
npm install zustand
```

```js
// src/store/useCartStore.js
import { create } from "zustand";

export const useCartStore = create((set) => ({
  items: [],
  addItem: (product) => set((state) => ({ items: [...state.items, product] })),
  removeItem: (id) =>
    set((state) => ({ items: state.items.filter((item) => item.id !== id) })),
}));
```

```jsx
function CartIcon() {
  const count = useCartStore((state) => state.items.length);
  return <span>🛒 {count}</span>;
}
```

Сравните с Redux: тот же результат в несколько раз меньшим кодом. Подробно разберём Zustand в следующем уроке — [Знакомство с Zustand](lesson:zustand).

## MobX — реактивные объекты

**MobX** работает по другому принципу: вы описываете обычный класс, а MobX «следит» за его полями. Изменили поле — все компоненты, которые его читают, перерисовались сами. Похоже на таблицу Excel: поменяли ячейку — пересчитались все формулы, которые от неё зависят.

```bash
npm install mobx mobx-react-lite
```

```js
// src/store/cartStore.js
import { makeAutoObservable } from "mobx";

class CartStore {
  items = [];

  constructor() {
    makeAutoObservable(this);
  }

  addItem(product) {
    this.items.push(product);
  }

  get count() {
    return this.items.length;
  }
}

export const cartStore = new CartStore();
```

```jsx
import { observer } from "mobx-react-lite";
import { cartStore } from "./store/cartStore";

const CartIcon = observer(() => <span>🛒 {cartStore.count}</span>);
```

- `makeAutoObservable(this)` делает поля «наблюдаемыми», методы — действиями, а геттеры (`get count`) — вычисляемыми значениями.
- `observer` оборачивает компонент, чтобы он перерисовывался при изменении данных.

✅ Мало кода, привычный ООП-стиль. ❌ «Магия»: сложнее понять, почему компонент перерисовался; забыли `observer` — ничего не обновляется.

## Jotai — состояние из маленьких атомов

**Jotai** (по-японски «состояние») хранит данные не в одном большом store, а в маленьких независимых кусочках — **атомах**. Работает почти как `useState`, только общий для всего приложения.

```bash
npm install jotai
```

```jsx
import { atom, useAtom, useAtomValue } from "jotai";

const cartAtom = atom([]);
const cartCountAtom = atom((get) => get(cartAtom).length); // производный атом

function ProductCard({ product }) {
  const [cart, setCart] = useAtom(cartAtom);
  return <button onClick={() => setCart([...cart, product])}>В корзину</button>;
}

function CartIcon() {
  const count = useAtomValue(cartCountAtom);
  return <span>🛒 {count}</span>;
}
```

- `atom([])` — создаёт атом с начальным значением.
- `atom((get) => ...)` — производный атом: вычисляется из других и пересчитывается сам.
- `useAtom` возвращает `[значение, сеттер]`, как `useState`; `useAtomValue` — только значение.

## Сравнение и выбор

| Инструмент | Установка | Объём кода | Провайдер | Когда выбрать |
| --- | --- | --- | --- | --- |
| Context | Встроен | Средний | Нужен | Тема, язык, редкие изменения |
| Redux Toolkit | `@reduxjs/toolkit react-redux` | Больше всех | Нужен | Крупный проект, большая команда |
| Zustand | `zustand` | Минимальный | Не нужен | Большинство небольших и средних проектов |
| MobX | `mobx mobx-react-lite` | Мало | Не обязателен | Любите классы и реактивность |
| Jotai | `jotai` | Мало | Не обязателен | Много мелких независимых кусочков состояния |

Есть и другие: **Valtio** (похож на MobX, от авторов Zustand), **Recoil** (больше не развивается), **Effector** (популярен в русскоязычном сообществе). Принципы у всех похожи.

### Простой алгоритм выбора

1. Данные нужны одному компоненту? → `useState`.
2. Это данные с сервера? → TanStack Query.
3. Глобальные, редко меняются (тема, язык)? → Context.
4. Глобальные и часто меняются? → Zustand (или Redux Toolkit, если так принято в команде).

<aside class="callout" data-icon="⚠️" markdown="1">

Не тащите менеджер состояния в проект «на всякий случай». Если всё помещается в `useState` и пару пропсов — так и оставьте. Библиотеку добавляют, когда появилась реальная проблема: prop drilling или лишние перерисовки.

</aside>

## Типичные ошибки

- **Компонент вне провайдера.** Для Context и Redux: вызвали `useCart()`/`useSelector` в компоненте, который не обёрнут провайдером, — ошибка или `null`.
- **Мутация состояния в Context/useState/Zustand.** `items.push(x)` без создания нового массива — React не заметит изменений. «Мутировать» можно только внутри `createSlice` (Immer) и в MobX.
- **Выбор всего store целиком.** `useSelector((state) => state)` перерисует компонент при любом изменении. Выбирайте только нужное.
- **Один огромный контекст на всё приложение** — каждое изменение перерисовывает всё. Делите контексты по смыслу.

## Практика

1. **Тема через Context.** Сделайте `ThemeContext` со значением `"light" | "dark"` и кнопкой переключения в шапке. Ожидаемый результат: карточки в глубине дерева меняют фон без передачи пропсов.
2. **Счётчик на трёх библиотеках.** Реализуйте счётчик с кнопками «+», «−» и «Сброс» на Redux Toolkit, Zustand и Jotai. Сравните, сколько строк кода понадобилось в каждом случае.
3. **Корзина на Redux Toolkit.** Выведите список из 5 товаров (массив в коде), кнопку «В корзину» у каждого и значок с количеством товаров в шапке. Добавьте action `clearCart`.
4. **Корзина на Zustand.** Повторите задание 3 на Zustand и добавьте подсчёт общей суммы. Ожидаемый результат: одинаковое поведение, заметно меньше кода.
5. **Аргументированный выбор.** Опишите в 5–7 предложениях, какой менеджер состояния вы бы выбрали для интернет-магазина, админки и блога, и почему.

## Итоги

- Глобальное состояние нужно, когда данные используют многие компоненты; без него появляется prop drilling.
- Context встроен в React и подходит для редко меняющихся данных, но перерисовывает всех подписчиков.
- Redux Toolkit — строгий и популярный в крупных командах: `createSlice`, `configureStore`, `useSelector`, `useDispatch`.
- Zustand — минимум кода и без провайдера, хороший выбор по умолчанию.
- MobX делает объекты реактивными, Jotai строит состояние из атомов.
- Серверные данные лучше хранить не в менеджере состояния, а в TanStack Query.
