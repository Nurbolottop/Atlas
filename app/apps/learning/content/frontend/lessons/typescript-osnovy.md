TypeScript — это JavaScript с «подписями»: вы заранее указываете, какие данные лежат в переменной, что принимает функция и что она возвращает. Редактор и компилятор проверяют эти подписи и находят ошибки ещё до запуска программы. В этом уроке установим TypeScript, разберём базовые типы, `type`, `interface` и generics, а в конце научимся типизировать React-компоненты и их пропсы.

## Что такое TypeScript и зачем он нужен

JavaScript — язык с **динамической типизацией**: переменная может сегодня хранить число, а завтра строку, и никто вас не остановит. Ошибка всплывёт только тогда, когда пользователь нажмёт кнопку и увидит белый экран.

```js
function getTotal(price, count) {
  return price * count;
}

getTotal({}, 2); // NaN — ошибка тихо ушла дальше
```

TypeScript добавляет **статическую типизацию**: типы проверяются заранее, во время написания кода.

```ts
function getTotal(price: number, count: number): number {
  return price * count;
}

getTotal(100, 2);    // ✅ 200
getTotal("100", 2);  // ❌ Argument of type 'string' is not assignable to parameter of type 'number'
```

Аналогия: JavaScript — коробки без надписей, содержимое видно, только открыв их. TypeScript — коробки с наклейками «тут только книги»: положить туда кастрюлю не дадут.

Что даёт TypeScript на практике:

- **ошибки видны в редакторе** — красное подчёркивание до запуска;
- **автодополнение** — редактор знает, какие поля есть у объекта `user`, и подсказывает их;
- **безопасный рефакторинг** — переименовали поле, и TypeScript покажет все места, которые нужно поправить.

<aside class="callout" data-icon="📌" markdown="1">

Браузер не понимает TypeScript. Перед запуском код на TS превращается в обычный JavaScript, а все типы при этом просто удаляются. Типы — это помощь разработчику, а не часть работающей программы.

</aside>

## Установка TypeScript

### Вариант 1. Отдельно, чтобы поиграться

```bash
mkdir ts-practice && cd ts-practice
npm init -y
npm install -D typescript
npx tsc --init
```

- `npm install -D typescript` — ставим TypeScript как dev-зависимость (нужна только при разработке, подробнее — в уроке [npm и package.json](lesson:npm-i-package-json));
- `npx tsc --init` — создаёт файл настроек `tsconfig.json`;
- `tsc` — это **TypeScript Compiler**: он проверяет типы и превращает `.ts` в `.js`. Например, `npx tsc index.ts` создаст рядом `index.js`, который запускается через `node index.js`.

### Вариант 2. React-проект на Vite (как в реальной работе)

```bash
npm create vite@latest my-app -- --template react-ts
cd my-app
npm install
npm run dev
```

В шаблоне `react-ts` компоненты имеют расширение `.tsx` (TypeScript + JSX), обычные модули — `.ts`, а `tsconfig`-файлы уже настроены.

<aside class="callout" data-icon="⚠️" markdown="1">

Vite во время `npm run dev` **не проверяет типы** — он просто вырезает их, чтобы работать быстро. Ошибки типов вы видите в редакторе, а полная проверка запускается командой `npm run build` (в шаблоне она начинается с `tsc -b`). Можно проверить и отдельно, без сборки: `npx tsc -b`.

</aside>

Самая важная настройка в `tsconfig.json` — `"strict": true`: строгий режим, в котором TypeScript проверяет `null`/`undefined` и не пропускает неявный `any`. В шаблоне Vite он уже включён — не выключайте его, иначе большая часть ошибок пройдёт незамеченной.

## Базовые типы

### Примитивы

```ts
let userName: string = "Айгерим";
let age: number = 21;          // и целые, и дробные числа
let isAdmin: boolean = false;
```

### Вывод типов

Писать тип везде не обязательно. TypeScript умеет **выводить тип** сам — по значению:

```ts
let city = "Бишкек";   // TypeScript понял: string
city = 42;             // ❌ Type 'number' is not assignable to type 'string'
```

Правило: если значение понятно — тип не пишем. Явно указываем типы у параметров функций, пустых значений и сложных объектов.

### Массивы и кортежи

```ts
const scores: number[] = [5, 4, 5];
const tags: Array<string> = ["react", "ts"];  // то же самое, другая запись

// Кортеж (tuple) — массив фиксированной длины, где у каждой позиции свой тип
const point: [number, number] = [10, 20];
```

### Объекты

```ts
const user: { id: number; name: string; email?: string } = { id: 1, name: "Тимур" };
```

Знак `?` после имени поля означает **необязательное поле**: его может не быть, и тогда там `undefined`.

### Объединения и литеральные типы

**Union** (объединение) — «или то, или другое». Пишется через `|`:

```ts
let id: number | string;
id = 10;      // ✅
id = "abc";   // ✅
id = true;    // ❌

// Литеральный тип — разрешены только конкретные значения
let status: "loading" | "success" | "error" = "loading";
status = "success"; // ✅
status = "done";    // ❌ такого варианта нет
```

Литеральные типы удобны для статусов, размеров кнопок, ролей — опечатка сразу подсветится.

### any и unknown

- `any` — «что угодно, не проверяй». Это фактически отключение TypeScript, избегайте его.
- `unknown` — «что угодно, но сначала проверь». Подходит для данных неизвестного вида: ответ сервера, `error` в `catch`.

```ts
function parse(value: unknown) {
  if (typeof value === "string") {
    return value.toUpperCase(); // здесь TypeScript уже знает, что это string
  }
  return null;
}
```

Проверка `typeof value === "string"` называется **сужением типа** (narrowing): внутри `if` TypeScript «сужает» `unknown` до `string`.

## Типизация функций

```ts
// Параметры и возвращаемое значение
function add(a: number, b: number): number {
  return a + b;
}

// Стрелочная функция и необязательный параметр
const greet = (name: string, greeting?: string): string =>
  `${greeting ?? "Привет"}, ${name}!`;

// Функция, которая ничего не возвращает
function logMessage(message: string): void {
  console.log(message);
}
```

`void` означает «функция ничего не возвращает». Если функция асинхронная, её результат описывают как `Promise<тип>`, например `Promise<number>`.

## type и interface

Чтобы переиспользовать описание объекта, есть **псевдонимы типов** (`type`) и **интерфейсы** (`interface`).

### type

```ts
type User = {
  id: number;
  name: string;
  email?: string;
  role: "admin" | "user";
};

const admin: User = { id: 1, name: "Дана", role: "admin" };
```

`type` умеет давать имя чему угодно — не только объектам:

```ts
type ID = number | string;
type Status = "idle" | "loading" | "success" | "error";
type Point = [number, number];
```

### interface

```ts
interface Product {
  id: number;
  title: string;
  price: number;
  readonly createdAt: string; // readonly — поле нельзя менять после создания: phone.createdAt = "..." даст ошибку
}

const phone: Product = {
  id: 7,
  title: "Смартфон",
  price: 25000,
  createdAt: "2026-01-15",
};
```

### Расширение типов

Интерфейс расширяют через `extends`, а `type` — через пересечение `&`:

```ts
interface Animal {
  name: string;
}

interface Dog extends Animal {
  breed: string;
}

type Person = { name: string };
type Employee = Person & { position: string };

const dog: Dog = { name: "Рекс", breed: "овчарка" };
```

### Что выбрать

Главные отличия: `type` умеет описывать не только объекты, но и union, кортежи, примитивы, а `interface` можно расширять через `extends` и «дописывать», объявив второй раз с тем же именем.

<aside class="callout" data-icon="💡" markdown="1">

Для новичка простое правило: объекты и пропсы можно описывать любым способом, главное — **единообразно во всём проекте**. Многие команды используют `interface` для объектов и `type` для объединений и всего остального.

</aside>

## Generics — типы-параметры

### Проблема

Напишем функцию, которая возвращает первый элемент массива:

```ts
function first(arr: any[]): any {
  return arr[0]; // работает с любым массивом, но результат — any, подсказки пропали
}
```

### Решение

**Generic** (дженерик) — это тип-параметр, «переменная для типа». Её пишут в угловых скобках, обычно буквой `T`:

```ts
function first<T>(arr: T[]): T | undefined {
  return arr[0];
}

const n = first([1, 2, 3]);       // T = number, тип n: number | undefined
const s = first(["a", "b"]);      // T = string
const u = first<string>([]);      // T можно указать явно
```

Аналогия: generic — форма для печенья: форма одна, тесто любое.

### Generic в интерфейсах

Частый пример — ответ сервера, у которого обёртка всегда одинаковая, а данные разные:

```ts
interface ApiResponse<T> {
  data: T;
  total: number;
  page: number;
}

type Todo = { id: number; title: string; completed: boolean };

const response: ApiResponse<Todo[]> = {
  data: [{ id: 1, title: "Выучить TS", completed: false }],
  total: 1,
  page: 1,
};
```

<aside class="callout" data-icon="⚠️" markdown="1">

Такой тип не проверяет, что сервер действительно прислал задачи — мы просто **обещаем** TypeScript, что так будет. Если бэкенд изменит формат, ошибка всплывёт во время работы. Как получать типы прямо из документации API, разберём в уроке [Swagger и генерация типов](lesson:swagger-generaciya-tipov).

</aside>

### Встроенные утилиты

TypeScript содержит готовые generic-типы, которые «переделывают» другие типы:

```ts
interface User {
  id: number;
  name: string;
  email: string;
}

type UserUpdate = Partial<User>;          // все поля стали необязательными
type UserPreview = Pick<User, "id" | "name">; // только id и name
type NewUser = Omit<User, "id">;          // всё, кроме id
type UsersById = Record<number, User>;    // объект: ключ — число, значение — User
```

`Omit<User, "id">` особенно полезен для форм создания: `id` ещё нет, его выдаст сервер.

## TypeScript в React

### Типизация пропсов

Пропсы описываем типом и указываем его у параметра компонента:

```tsx
type ButtonProps = {
  text: string;
  variant?: "primary" | "secondary";
  disabled?: boolean;
  onClick: () => void;
};

export function Button({ text, variant = "primary", disabled = false, onClick }: ButtonProps) {
  return (
    <button className={`btn btn-${variant}`} disabled={disabled} onClick={onClick}>
      {text}
    </button>
  );
}
```

Разбор:

- `variant?` и `disabled?` — необязательные, значения по умолчанию задаём при деструктуризации;
- `onClick: () => void` — функция без аргументов, которая ничего не возвращает.

Теперь при использовании редактор подскажет все пропсы и отругает за ошибки:

```tsx
<Button text="Сохранить" onClick={() => console.log("save")} />  // ✅
<Button text="Удалить" variant="danger" onClick={() => {}} />     // ❌ "danger" нет в списке
<Button onClick={() => {}} />                                      // ❌ не передан text
```

### children

Если компонент оборачивает другой JSX, используйте тип `React.ReactNode` — он принимает всё, что можно отрендерить: текст, числа, элементы, массивы, `null`.

```tsx
import type { ReactNode } from "react";

type CardProps = {
  title: string;
  children: ReactNode;
};

export function Card({ title, children }: CardProps) {
  return (
    <div className="card">
      <h3>{title}</h3>
      {children}
    </div>
  );
}
```

### useState

Обычно тип выводится из начального значения. Указывать его явно нужно, когда начальное значение «пустое»:

```tsx
const [count, setCount] = useState(0);                 // number — выведено
const [user, setUser] = useState<User | null>(null);   // пока null, потом User
const [todos, setTodos] = useState<Todo[]>([]);        // без <Todo[]> был бы never[]
```

Пока `user` может быть `null`, TypeScript не даст обратиться к `user.name` без проверки — пишите `user?.name ?? "Гость"`.

### События

```tsx
import { useState, type ChangeEvent, type FormEvent } from "react";

export function SearchForm({ onSearch }: { onSearch: (query: string) => void }) {
  const [query, setQuery] = useState("");

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
  };

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    onSearch(query);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input value={query} onChange={handleChange} />
      <button type="submit">Найти</button>
    </form>
  );
}
```

- `ChangeEvent<HTMLInputElement>` — событие изменения именно у `<input>`, поэтому `e.target.value` известен;
- `FormEvent<HTMLFormElement>` — событие отправки формы.

<aside class="callout" data-icon="💡" markdown="1">

Не помните тип события? Напишите `onChange={(e) => ...}` прямо в JSX и наведите мышку на `e` — редактор покажет точный тип.

</aside>

### useRef

Для ссылки на DOM-элемент указываем его тип и начальное `null`: `const inputRef = useRef<HTMLInputElement>(null)`. Обращаемся через `inputRef.current?.focus()` — пока элемент не отрисован, `current` равен `null`.

## Типичные ошибки

- **Ставить `any`, чтобы «ошибка ушла».** Ошибка не уходит — вы просто перестаёте её видеть. Используйте `unknown` и проверки.
- **Обращаться к полю, которое может быть `undefined`.** Ошибка `Object is possibly 'undefined'` — это подсказка: добавьте проверку или `?.`.
- **Пустой массив без типа:** `useState([])` даёт `never[]`, и в него ничего нельзя положить. Пишите `useState<Todo[]>([])`.
- **Путать `as` с проверкой.** `data as User` — это не проверка, а «поверь мне». Используйте его осторожно.

Официальная документация с примерами: [typescriptlang.org/docs](https://www.typescriptlang.org/docs/) и раздел про TypeScript на [react.dev](https://react.dev/learn/typescript).

## Практика

1. **Типы для магазина.** Опишите `interface Product` (id, title, price, необязательное поле discount) и `type Category = "phones" | "laptops" | "audio"`. Создайте массив из трёх товаров. Ожидаемый результат: товар без `price` или с категорией `"tv"` подсвечивается ошибкой.
2. **Generic.** Напишите `function last<T>(arr: T[]): T | undefined` и `function groupBy<T>(items: T[], getKey: (item: T) => string): Record<string, T[]>`. Ожидаемый результат: `last(["a", "b"])` имеет тип `string | undefined`.
3. **React-компонент.** Создайте проект `react-ts` на Vite и компонент `ProductCard` с пропсами `product: Product` и `onBuy: (id: number) => void`. Ожидаемый результат: без переданного `onBuy` проект не собирается командой `npm run build`.
4. **Перевод проекта.** Возьмите свой ToDoList из урока [ToDoList: axios и json-server](lesson:todolist-axios-json-server) и переведите на TypeScript: тип `Todo`, типизированный `useState`, обработчики событий. Ожидаемый результат: `npx tsc -b` проходит без ошибок, `any` в коде нет.

## Итоги

- TypeScript — это JavaScript с типами; типы проверяются до запуска и удаляются при сборке.
- React-проект на TS создаётся командой `npm create vite@latest my-app -- --template react-ts`.
- Базовые типы: `string`, `number`, `boolean`, массивы, кортежи, union `|`, литеральные типы; вместо `any` — `unknown`.
- `type` и `interface` дают имя форме данных; `interface` расширяется через `extends`, `type` — через `&`.
- Generics (`<T>`) позволяют писать одну функцию или тип для разных данных без потери подсказок.
- В React типизируем пропсы, `children: ReactNode`, `useState<T>`, события (`ChangeEvent`, `FormEvent`) и `useRef<HTMLElement>(null)`.
