В этом уроке разберём ещё три встроенных хука React. `useRef` даёт прямой доступ к DOM-элементу и позволяет хранить значение, которое не вызывает перерисовку. `useMemo` и `useCallback` помогают не делать лишнюю работу: запоминают результат тяжёлых вычислений и функции между рендерами. Важно не только понять, как они работают, но и когда они действительно нужны.

## Вспоминаем, как работает рендер

Чтобы понять эти хуки, держите в голове одну мысль: **при каждом рендере функция-компонент выполняется целиком заново**. Все переменные и функции внутри неё создаются с нуля.

```jsx
function App() {
  const [count, setCount] = useState(0);

  const user = { name: 'Айгерим' };      // новый объект на каждом рендере
  function handleClick() {}               // новая функция на каждом рендере
  const total = heavyCalculation();       // тяжёлый расчёт на каждом рендере

  return <button onClick={() => setCount(count + 1)}>{count}</button>;
}
```

Чаще всего это не проблема — JavaScript быстрый. Но бывает три ситуации, когда этого недостаточно:

1.  Нужно «дотянуться» до настоящего DOM-элемента или хранить значение без перерисовки → `useRef`.
2.  Тяжёлое вычисление тормозит каждый рендер → `useMemo`.
3.  Новая функция на каждом рендере заставляет перерисовываться дочерний компонент → `useCallback`.

## useRef

`useRef` создаёт «коробочку» с одним свойством `current`. Эта коробочка:

-   **живёт между рендерами** (как состояние);
-   **не вызывает перерисовку** при изменении (в отличие от состояния).

```jsx
import { useRef } from 'react';

const ref = useRef(начальноеЗначение);
console.log(ref.current); // начальноеЗначение
ref.current = 'новое';     // можно менять напрямую, React не перерисует компонент
```

У `useRef` два главных применения.

### Применение 1: доступ к DOM-элементу

Иногда нужно сделать с элементом то, что нельзя описать через состояние: поставить фокус в поле, прокрутить к блоку, запустить видео, измерить размер.

```jsx
import { useRef } from 'react';

function SearchBox() {
  const inputRef = useRef(null);

  function handleFocus() {
    inputRef.current.focus();
  }

  return (
    <div>
      <input ref={inputRef} placeholder="Поиск..." />
      <button onClick={handleFocus}>Перейти к поиску</button>
    </div>
  );
}
```

Разбор:

-   `useRef(null)` — пока элемента нет, в коробке `null`.
-   `ref={inputRef}` — специальный атрибут: после отрисовки React положит в `inputRef.current` настоящий DOM-элемент `<input>`.
-   `inputRef.current.focus()` — вызываем обычный метод DOM, как в уроке про DOM.

Это аналог `document.querySelector`, но «по-реактовски»: не нужно придумывать id, и ссылка всегда указывает именно на элемент этого компонента.

Автофокус при открытии страницы — `useRef` вместе с `useEffect`:

```jsx
import { useEffect, useRef } from 'react';

function LoginForm() {
  const emailRef = useRef(null);

  useEffect(() => {
    emailRef.current.focus(); // элемент уже есть на странице — эффект запускается после рендера
  }, []);

  return (
    <form>
      <input ref={emailRef} type="email" placeholder="Email" />
      <input type="password" placeholder="Пароль" />
    </form>
  );
}
```

<aside class="callout" data-icon="⚠️" markdown="1">

Не читайте и не меняйте `ref.current` прямо во время рендера (в теле компонента до `return`). На первом рендере там ещё `null`. Работайте с ref в обработчиках событий и в `useEffect`.

</aside>

### Передача ref в свой компонент

Если нужен ref на элемент внутри **вашего** компонента, в React 19 его можно передать как обычный проп:

```jsx
function MyInput({ label, ref }) {
  return (
    <label>
      {label}
      <input ref={ref} />
    </label>
  );
}

function Form() {
  const nameRef = useRef(null);
  return (
    <>
      <MyInput label="Имя" ref={nameRef} />
      <button onClick={() => nameRef.current.focus()}>Фокус</button>
    </>
  );
}
```

В старых проектах (React 18 и ниже) для этого использовали обёртку `forwardRef` — если встретите её в чужом коде, знайте: это тот же механизм.

### Применение 2: значение, которое не влияет на отображение

Иногда нужно что-то запомнить между рендерами, но показывать это не нужно: id таймера, количество кликов для аналитики, предыдущее значение. Хранить такое в `useState` расточительно — каждое изменение вызывало бы лишний рендер.

Секундомер:

```jsx
import { useRef, useState } from 'react';

function Stopwatch() {
  const [time, setTime] = useState(0);
  const intervalRef = useRef(null);

  function start() {
    if (intervalRef.current) return; // уже запущен
    intervalRef.current = setInterval(() => {
      setTime((prev) => prev + 10);
    }, 10);
  }

  function stop() {
    clearInterval(intervalRef.current);
    intervalRef.current = null;
  }

  function reset() {
    stop();
    setTime(0);
  }

  return (
    <div>
      <h2>{(time / 1000).toFixed(2)} с</h2>
      <button onClick={start}>Старт</button>
      <button onClick={stop}>Стоп</button>
      <button onClick={reset}>Сброс</button>
    </div>
  );
}
```

Почему id интервала в `useRef`, а не в обычной переменной `let intervalId`? Обычная переменная обнулялась бы при каждом рендере (а рендер происходит каждые 10 мс), и функция `stop` не нашла бы, что останавливать.

| | `useState` | `useRef` | Обычная переменная |
| --- | --- | --- | --- |
| Сохраняется между рендерами | Да | Да | Нет |
| Изменение вызывает рендер | Да | Нет | Нет |
| Как менять | `setValue(...)` | `ref.current = ...` | `x = ...` |
| Для чего | То, что видно на экране | DOM-элементы, таймеры, служебные данные | Временные вычисления внутри рендера |

## useMemo

`useMemo` **запоминает результат вычисления** и пересчитывает его, только когда изменились зависимости.

```jsx
const result = useMemo(() => вычисление(), [зависимости]);
```

Аналогия: вы решили сложную задачу по математике и записали ответ на стикер. Пока условие не поменялось, вы просто смотрите на стикер, а не решаете заново.

### Пример: фильтрация большого списка

```jsx
import { useMemo, useState } from 'react';

// создаём 20 000 тестовых товаров
const allProducts = Array.from({ length: 20000 }, (_, i) => ({
  id: i + 1,
  title: `Товар ${i + 1}`,
  price: Math.round(Math.random() * 100000),
}));

function Catalog() {
  const [search, setSearch] = useState('');
  const [sortAsc, setSortAsc] = useState(true);
  const [theme, setTheme] = useState('light');

  const visibleProducts = useMemo(() => {
    console.log('Пересчитываю список...');
    const filtered = allProducts.filter((p) =>
      p.title.toLowerCase().includes(search.toLowerCase())
    );
    return filtered.toSorted((a, b) => (sortAsc ? a.price - b.price : b.price - a.price));
  }, [search, sortAsc]);

  return (
    <div style={{ background: theme === 'light' ? '#fff' : '#222', color: theme === 'light' ? '#000' : '#fff' }}>
      <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>Сменить тему</button>
      <button onClick={() => setSortAsc(!sortAsc)}>Цена {sortAsc ? '↑' : '↓'}</button>
      <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Поиск" />
      <p>Найдено: {visibleProducts.length}</p>
      <ul>
        {visibleProducts.slice(0, 50).map((p) => (
          <li key={p.id}>{p.title} — {p.price} ₸</li>
        ))}
      </ul>
    </div>
  );
}
```

Разбор:

-   Фильтрация и сортировка 20 000 элементов — заметная работа.
-   С `useMemo` список пересчитывается **только** при изменении `search` или `sortAsc`.
-   Нажмите «Сменить тему» — в консоли не появится «Пересчитываю список...»: тема не входит в зависимости, React вернул запомненный результат.
-   Без `useMemo` смена темы каждый раз заново перебирала бы весь массив.

<aside class="callout" data-icon="⚠️" markdown="1">

`useMemo` — это оптимизация, а не обязательный инструмент. Запоминание само тоже стоит ресурсов. Для простых вычислений (сложить два числа, отфильтровать 20 элементов) он не нужен. Сначала пишите без него, а добавляйте, когда видите реальные тормоза.

</aside>

## React.memo и useCallback

### Проблема: лишние перерисовки детей

Когда родитель перерисовывается, по умолчанию перерисовываются **все** его дети — даже если их пропсы не изменились. Обернуть компонент в `memo` значит сказать React: «перерисовывай этот компонент, только если изменились его пропсы».

```jsx
import { memo, useState } from 'react';

const ExpensiveList = memo(function ExpensiveList({ items, onRemove }) {
  console.log('ExpensiveList отрисовался');
  return (
    <ul>
      {items.map((item) => (
        <li key={item.id}>
          {item.title} <button onClick={() => onRemove(item.id)}>✕</button>
        </li>
      ))}
    </ul>
  );
});
```

Теперь используем его в родителе:

```jsx
function App() {
  const [count, setCount] = useState(0);
  const [items, setItems] = useState([
    { id: 1, title: 'React' },
    { id: 2, title: 'Vite' },
  ]);

  function handleRemove(id) {
    setItems((prev) => prev.filter((item) => item.id !== id));
  }

  return (
    <>
      <button onClick={() => setCount(count + 1)}>Счётчик: {count}</button>
      <ExpensiveList items={items} onRemove={handleRemove} />
    </>
  );
}
```

Нажимаем на счётчик — и в консоли всё равно «ExpensiveList отрисовался»! Почему? `items` не менялся, но `handleRemove` — **новая функция** на каждом рендере `App`. Для React две разные функции — разные пропсы, даже если код у них одинаковый (как два одинаковых на вид, но разных объекта: `{} === {}` даёт `false`).

### useCallback: запоминаем функцию

`useCallback` возвращает **одну и ту же функцию** между рендерами, пока не изменятся зависимости:

```jsx
const memoizedFn = useCallback(функция, [зависимости]);
```

Исправим `App`:

```jsx
import { useCallback, useState } from 'react';

function App() {
  const [count, setCount] = useState(0);
  const [items, setItems] = useState([
    { id: 1, title: 'React' },
    { id: 2, title: 'Vite' },
  ]);

  const handleRemove = useCallback((id) => {
    setItems((prev) => prev.filter((item) => item.id !== id));
  }, []); // зависимостей нет: используем функциональную форму setItems

  return (
    <>
      <button onClick={() => setCount(count + 1)}>Счётчик: {count}</button>
      <ExpensiveList items={items} onRemove={handleRemove} />
    </>
  );
}
```

Теперь клик по счётчику не перерисовывает `ExpensiveList`: `items` тот же, `handleRemove` та же. А при удалении элемента `items` меняется — и список, как и положено, обновляется.

Обратите внимание на приём: благодаря `setItems((prev) => ...)` функции не нужно знать текущий `items`, поэтому массив зависимостей пустой. Если бы мы писали `setItems(items.filter(...))`, пришлось бы добавить `items` в зависимости.

<aside class="callout" data-icon="📌" markdown="1">

`useCallback` почти всегда работает **в паре** с `memo` у дочернего компонента (или когда функция попадает в зависимости `useEffect`). Сам по себе, без `memo`, он ничего не ускоряет: ребёнок без `memo` всё равно перерисуется вместе с родителем.

</aside>

### useMemo и useCallback — в чём разница

По сути `useCallback(fn, deps)` — это то же самое, что `useMemo(() => fn, deps)`.

| Хук | Что запоминает | Пример |
| --- | --- | --- |
| `useMemo` | **Результат** вызова функции | Отфильтрованный массив, сумма, объект настроек |
| `useCallback` | **Саму функцию** | Обработчик, передаваемый в `memo`-компонент |
| `memo` | **Компонент** (пропускает рендер при тех же пропсах) | Тяжёлый список, график |

`useMemo` также пригодится, когда в `memo`-компонент передаётся объект: `const options = useMemo(() => ({ color, size }), [color, size])` — без него объект будет новым на каждом рендере.

### А как же React Compiler

В новых версиях React есть **React Compiler** — инструмент, который подключается к сборке и автоматически добавляет запоминание там, где оно полезно. В проектах с включённым компилятором `useMemo`, `useCallback` и `memo` вручную пишут гораздо реже. Но понимать эти хуки всё равно нужно: они встречаются почти во всех существующих проектах и часто спрашиваются на собеседованиях. Подробности — в документации на react.dev.

## Когда что использовать

-   Нужен доступ к DOM (фокус, скролл, размеры, видео) → `useRef`.
-   Значение должно жить между рендерами, но не отображается → `useRef`.
-   Медленное вычисление, которое зависит от немногих данных → `useMemo`.
-   Функция передаётся в компонент, обёрнутый в `memo`, или используется в зависимостях эффекта → `useCallback`.
-   Всё остальное → пишите обычный код без оптимизаций.

## Типичные ошибки

-   **Хранение отображаемых данных в `useRef`.** Изменили `ref.current`, а на экране ничего не поменялось — потому что ref не вызывает рендер. Для отображаемого используйте `useState`.
-   **Обращение к `ref.current` до отрисовки** — получите `null`.
-   **Неполные зависимости** в `useMemo`/`useCallback` — хук вернёт устаревшее значение. Добавляйте все используемые переменные.
-   **`useCallback` без `memo`** у ребёнка — бессмысленная оптимизация.
-   **Мемоизация всего подряд** — код становится сложнее, а быстрее не становится.

## Практика

1.  **Автофокус.** Форма входа, в которой при открытии страницы курсор сразу стоит в поле email, а кнопка «Очистить» очищает оба поля и возвращает фокус в email. Ожидаемый результат: можно сразу печатать, не кликая по полю.
2.  **Секундомер.** Повторите `Stopwatch` и добавьте кнопку «Круг», которая сохраняет текущее время в список кругов (список — в `useState`). Повторные нажатия «Старт» не должны ускорять секундомер.
3.  **Счётчик рендеров.** Сделайте компонент, который через `useRef` считает, сколько раз он отрисовался, и выводит это число в консоль в `useEffect`. Объясните, почему число не показывается на экране сразу при изменении.
4.  **Тяжёлый каталог.** Повторите пример с 20 000 товаров. Добавьте фильтр «Цена до» (`input type="number"`). Убедитесь по консоли, что смена темы не вызывает пересчёт, а смена фильтра — вызывает.
5.  **memo + useCallback.** Сделайте список из 5 контактов с кнопкой «Избранное» в каждом (`ContactItem` в `memo`, лог рендера внутри) и отдельный счётчик в родителе. Добейтесь, чтобы при клике по счётчику ни один `ContactItem` не перерисовывался, а при клике «Избранное» перерисовывался только изменённый контакт.

## Итоги

-   `useRef` хранит значение в `ref.current` между рендерами и не вызывает перерисовку.
-   Через атрибут `ref` получают DOM-элемент: фокус, скролл, размеры; работают с ним в обработчиках и эффектах.
-   `useMemo(() => расчёт, [deps])` запоминает результат вычисления до изменения зависимостей.
-   `memo(Component)` пропускает рендер, если пропсы не изменились.
-   `useCallback(fn, [deps])` запоминает функцию — нужен в паре с `memo` или в зависимостях эффектов.
-   Оптимизации добавляют только при реальной необходимости; React Compiler умеет делать многое из этого автоматически.
