Почти в каждом интернет-магазине есть поиск, фильтры по категории и цене, сортировка «сначала дешёвые» и постраничный вывод. В этом уроке научимся делать всё это на React: хранить фильтры в query-параметрах адреса, передавать их на сервер через TanStack Query и грамотно работать с кэшем — читать, обновлять и сбрасывать его.

## Где фильтровать: на клиенте или на сервере

Есть два подхода:

| | На клиенте | На сервере |
| --- | --- | --- |
| Как | Загрузили весь список, отфильтровали в JS (`filter`, `sort`) | Отправили параметры в запросе, сервер вернул готовый результат |
| Когда | Данных мало (до нескольких сотен записей) | Данных много, есть пагинация |
| Плюсы | Мгновенно, без запросов | Не грузим лишнее, работает на миллионах записей |

Обычно фильтрует сервер, но начнём с простого.

## Фильтрация и сортировка на клиенте

### Готовим данные

```js
// src/api/products.js
import axios from "axios";

export const api = axios.create({ baseURL: "http://localhost:3001" });

export async function getProducts(params) {
  const { data } = await api.get("/products", { params });
  return data;
}
```

Для практики поднимем локальный сервер на json-server (урок [ToDoList: axios, json-server](lesson:todolist-axios-json-server)). Файл `db.json`:

```json
{
  "products": [
    { "id": "1", "title": "iPhone 15", "category": "phones", "price": 900 },
    { "id": "2", "title": "Galaxy S24", "category": "phones", "price": 800 },
    { "id": "3", "title": "MacBook Air", "category": "laptops", "price": 1200 },
    { "id": "4", "title": "AirPods", "category": "audio", "price": 200 },
    { "id": "5", "title": "ThinkPad X1", "category": "laptops", "price": 1500 }
  ]
}
```

```bash
npx json-server db.json --port 3001
```

### Фильтр и сортировка через useMemo

```jsx
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getProducts } from "../api/products";

export function ProductsClient() {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("price-asc");

  const { data = [], isPending } = useQuery({
    queryKey: ["products"],
    queryFn: () => getProducts(),
  });

  const visible = useMemo(() => {
    const filtered = data.filter((p) =>
      p.title.toLowerCase().includes(search.toLowerCase())
    );
    return [...filtered].sort((a, b) =>
      sort === "price-asc" ? a.price - b.price : b.price - a.price
    );
  }, [data, search, sort]);

  if (isPending) return <p>Загрузка...</p>;

  return (
    <div>
      <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Поиск" />
      <select value={sort} onChange={(e) => setSort(e.target.value)}>
        <option value="price-asc">Сначала дешёвые</option>
        <option value="price-desc">Сначала дорогие</option>
      </select>
      <ul>
        {visible.map((p) => (
          <li key={p.id}>{p.title} — ${p.price}</li>
        ))}
      </ul>
    </div>
  );
}
```

Разбор:

- `data = []` — значение по умолчанию при деструктуризации, пока данных нет. Так `data.filter` не упадёт.
- `useMemo` (урок [useRef, useMemo, useCallback](lesson:useref-usememo-usecallback)) пересчитывает список только при изменении данных, поиска или сортировки.
- `[...filtered].sort(...)` — копируем массив перед сортировкой: `sort` меняет массив на месте, а данные из кэша менять нельзя.

<aside class="callout" data-icon="⚠️" markdown="1">

Никогда не сортируйте `data` из `useQuery` напрямую (`data.sort(...)`). Это мутирует кэш, и другие компоненты внезапно получат «перемешанные» данные. Сначала копия — потом `sort`.

</aside>

## Query-параметры: фильтры в адресе

Сейчас поиск хранится в `useState`. Обновили страницу — фильтры пропали, ссылкой с друзьями не поделишься. Решение — хранить фильтры в **query-параметрах** адреса: `/products?category=phones&sort=price&page=2`. Хук `useSearchParams` мы разбирали в уроке [SPA на React Router](lesson:spa-na-react-router).

### Хук для фильтров

```js
// src/hooks/useProductFilters.js
import { useSearchParams } from "react-router";

export function useProductFilters() {
  const [searchParams, setSearchParams] = useSearchParams();

  const filters = {
    category: searchParams.get("category") ?? "",
    sort: searchParams.get("sort") ?? "price",
    page: Number(searchParams.get("page") ?? 1),
  };

  function setFilter(key, value) {
    setSearchParams((prev) => {
      if (value === "" || value == null) {
        prev.delete(key);
      } else {
        prev.set(key, String(value));
      }
      if (key !== "page") prev.delete("page"); // сменили фильтр — на первую страницу
      return prev;
    });
  }

  return { filters, setFilter };
}
```

- `filters` — текущие фильтры из адреса со значениями по умолчанию; `Number(...)` — потому что из адреса приходят строки.
- `setFilter` меняет один параметр, не трогая остальные. Пустое значение удаляет параметр — адрес остаётся чистым.
- При смене категории или сортировки сбрасываем `page`, иначе можно оказаться на 5-й странице списка, где всего 2 страницы.

## Фильтрация на сервере через TanStack Query

### Параметры в запросе и в ключе

```jsx
// src/pages/ProductsPage.jsx
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { getProducts } from "../api/products";
import { useProductFilters } from "../hooks/useProductFilters";

const PER_PAGE = 2;

export function ProductsPage() {
  const { filters, setFilter } = useProductFilters();

  const params = {
    category: filters.category || undefined,
    _sort: filters.sort,
    _page: filters.page,
    _per_page: PER_PAGE,
  };

  const { data, isPending, isError, isFetching, isPlaceholderData } = useQuery({
    queryKey: ["products", "list", filters],
    queryFn: () => getProducts(params),
    placeholderData: keepPreviousData,
  });

  if (isPending) return <p>Загрузка...</p>;
  if (isError) return <p>Не удалось загрузить товары</p>;

  return (
    <div style={{ opacity: isFetching ? 0.6 : 1 }}>
      <select value={filters.category} onChange={(e) => setFilter("category", e.target.value)}>
        <option value="">Все категории</option>
        <option value="phones">Телефоны</option>
        <option value="laptops">Ноутбуки</option>
        <option value="audio">Аудио</option>
      </select>

      <select value={filters.sort} onChange={(e) => setFilter("sort", e.target.value)}>
        <option value="price">Сначала дешёвые</option>
        <option value="-price">Сначала дорогие</option>
        <option value="title">По названию</option>
      </select>

      <ul>
        {data.data.map((p) => (
          <li key={p.id}>{p.title} — ${p.price}</li>
        ))}
      </ul>

      <button disabled={!data.prev} onClick={() => setFilter("page", filters.page - 1)}>
        Назад
      </button>
      <span> Страница {filters.page} из {data.pages} </span>
      <button
        disabled={isPlaceholderData || !data.next}
        onClick={() => setFilter("page", filters.page + 1)}
      >
        Вперёд
      </button>
    </div>
  );
}
```

Разберём главное:

- **Параметры запроса.** `axios` превращает объект `params` в строку: `/products?category=phones&_sort=-price&_page=1&_per_page=2`. Поля со значением `undefined` он пропускает — поэтому «все категории» передаём как `undefined`.
- **Синтаксис json-server v1:** `_sort=price` — по возрастанию, `_sort=-price` — по убыванию, `_page` и `_per_page` — пагинация. С пагинацией сервер отвечает объектом `{ first, prev, next, last, pages, items, data }`, где `data` — товары текущей страницы. У вашего бэкенда названия параметров могут быть другими (`ordering`, `limit`, `offset`…) — их смотрят в документации API, например в Swagger.
- **`queryKey: ["products", "list", filters]`** — каждая комбинация фильтров кэшируется отдельно: вернулись к «Телефонам» — результат из кэша мгновенно.
- **`placeholderData: keepPreviousData`** — пока грузится новая страница, показываем предыдущую, а не «Загрузка...» (в v4 — `keepPreviousData: true`).
- **`isPlaceholderData`** — `true`, пока на экране старые данные; блокируем «Вперёд». **`isFetching`** — делаем список полупрозрачным.

<aside class="callout" data-icon="📌" markdown="1">

TanStack Query сравнивает ключи по содержимому, а не по ссылке. `["products", { page: 1 }]` и `["products", { page: 1 }]` — один и тот же ключ, даже если объекты созданы заново. А порядок полей внутри объекта не важен.

</aside>

### Поиск с задержкой (debounce)

Если отправлять запрос на каждую букву, при вводе «iphone» уйдёт 6 запросов. **Debounce** («подавление дребезга») — ждём, пока пользователь перестанет печатать, и только потом ищем.

```js
// src/hooks/useDebounce.js
import { useEffect, useState } from "react";

export function useDebounce(value, delay = 400) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}
```

```jsx
const [search, setSearch] = useState("");
const debouncedSearch = useDebounce(search);

const { data } = useQuery({
  queryKey: ["products", "search", debouncedSearch],
  // параметр поиска зависит от вашего API (search, q, title__icontains...)
  queryFn: () => getProducts({ search: debouncedSearch || undefined }),
});
```

Каждое нажатие перезапускает таймер (`clearTimeout` отменяет предыдущий), поэтому `debouncedSearch`, а с ним ключ и запрос, меняются только после 400 мс тишины.

## Работа с кэшем

Кэш — это хранилище «ключ → данные». С ним работают через `queryClient` из хука `useQueryClient`.

### Иерархия ключей

Ключи удобно строить «от общего к частному»:

```text
["products"]                             — всё про товары
["products", "list", { category: "phones", page: 1 }]  — конкретный список
["products", "detail", "3"]              — один товар
```

Многие методы работают по **префиксу**: операция с ключом `["products"]` затронет все ключи, которые с него начинаются. Чтобы не ошибаться в ключах, их собирают в одном объекте — **фабрике ключей**:

```js
// src/api/productKeys.js
export const productKeys = {
  all: ["products"],
  lists: () => [...productKeys.all, "list"],
  list: (filters) => [...productKeys.lists(), filters],
  detail: (id) => [...productKeys.all, "detail", id],
};
```

### Основные методы queryClient

```jsx
import { useQueryClient } from "@tanstack/react-query";

function CacheDemo() {
  const queryClient = useQueryClient();

  // 1. Прочитать данные из кэша (без запроса)
  const cached = queryClient.getQueryData(productKeys.detail("3"));

  // 2. Пометить устаревшими и перезапросить активные
  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: productKeys.all });

  // 3. Положить данные в кэш вручную
  const rename = () =>
    queryClient.setQueryData(productKeys.detail("3"), (old) =>
      old ? { ...old, title: "MacBook Air M3" } : old
    );

  // 4. Удалить данные из кэша
  const clear = () => queryClient.removeQueries({ queryKey: productKeys.all });

  return (
    <div>
      <p>В кэше: {cached?.title ?? "ничего"}</p>
      <button onClick={refresh}>Обновить все товары</button>
      <button onClick={rename}>Переименовать в кэше</button>
      <button onClick={clear}>Очистить кэш товаров</button>
    </div>
  );
}
```

| Метод | Что делает | Когда нужен |
| --- | --- | --- |
| `getQueryData(key)` | Возвращает данные из кэша или `undefined` | Взять уже загруженное без запроса |
| `invalidateQueries({ queryKey })` | Помечает данные устаревшими; активные запросы сразу перезапрашиваются | После изменения данных на сервере |
| `setQueryData(key, updater)` | Записывает данные в кэш | Обновить интерфейс сразу, не дожидаясь сервера |
| `removeQueries({ queryKey })` | Удаляет данные из кэша | При выходе из аккаунта |
| `prefetchQuery({ queryKey, queryFn })` | Загружает данные заранее | Наведение мыши на ссылку |

<aside class="callout" data-icon="💡" markdown="1">

`invalidateQueries` — самый частый метод. После того как вы добавили или изменили товар на сервере, просто «инвалидируйте» `["products"]` — все списки обновятся сами. Подробно используем это в уроке [useMutation](lesson:usemutation).

</aside>

### Предзагрузка при наведении

```jsx
import { Link } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "../api/products";
import { productKeys } from "../api/productKeys";

function ProductLink({ id, title }) {
  const queryClient = useQueryClient();

  const prefetch = () =>
    queryClient.prefetchQuery({
      queryKey: productKeys.detail(id),
      queryFn: () => api.get(`/products/${id}`).then((res) => res.data),
      staleTime: 1000 * 30,
    });

  return (
    <Link to={`/products/${id}`} onMouseEnter={prefetch}>
      {title}
    </Link>
  );
}
```

Пока пользователь ведёт мышь и кликает, данные уже грузятся, и страница товара с тем же ключом откроется без «Загрузка...».

## Типичные ошибки

- **Фильтры не в `queryKey`.** Поменяли категорию, а список прежний — библиотека думает, что это тот же запрос.
- **Мутация кэша** через `data.sort()` или `old.title = ...`. Всегда возвращайте новый объект.
- **Строка вместо числа.** `page + 1`, где `page` = `"1"`, даст `"11"`. Превращайте параметры адреса в числа.
- **Не сбросили страницу** при смене фильтра — пустой список на «несуществующей» странице.
- **Запрос на каждую букву** — используйте debounce.

## Практика

1. **Клиентская сортировка.** Выведите товары из `db.json` и добавьте сортировку по цене и по названию через `useMemo`. Ожидаемый результат: исходные данные в кэше не меняются (проверьте в DevTools).
2. **Фильтры в адресе.** Перенесите категорию и сортировку в query-параметры. Ожидаемый результат: после обновления страницы и при открытии ссылки в новой вкладке фильтры сохраняются.
3. **Серверная пагинация.** Подключите `_page` и `_per_page` для json-server, кнопки «Назад»/«Вперёд» и `keepPreviousData`. Список не должен «мигать» при переключении страниц.
4. **Поиск с debounce.** Добавьте поле поиска по названию с задержкой 400 мс. Во вкладке Network убедитесь, что при быстром вводе уходит один запрос.
5. **Кэш.** Создайте фабрику ключей, сделайте предзагрузку товара при наведении на ссылку и кнопку «Обновить всё», которая вызывает `invalidateQueries` для `["products"]`.

## Итоги

- Маленькие списки можно фильтровать на клиенте (`filter` + копия перед `sort`), большие — на сервере через параметры запроса.
- Фильтры, сортировку и страницу удобно хранить в query-параметрах через `useSearchParams`.
- Всё, от чего зависит запрос, кладём в `queryKey`; `axios` собирает строку запроса из `params`.
- `placeholderData: keepPreviousData` убирает «мигание» при пагинации, debounce — лишние запросы при поиске.
- `queryClient` умеет читать (`getQueryData`), обновлять (`setQueryData`), инвалидировать (`invalidateQueries`), удалять и предзагружать данные кэша.
- Фабрика ключей помогает не путаться в ключах и инвалидировать данные по префиксу.
