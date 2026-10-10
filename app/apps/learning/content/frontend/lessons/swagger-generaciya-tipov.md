Фронтенд и бэкенд общаются по договору: какие есть адреса, что туда отправлять и что придёт в ответ. Этот договор обычно описан в Swagger. В этом уроке научимся читать Swagger-документацию, разберёмся, что такое OpenAPI, и настроим автоматическую генерацию TypeScript-типов и даже готовых функций запросов — чтобы больше не переписывать интерфейсы руками и не ловить ошибки из-за переименованного поля.

## Swagger и OpenAPI: в чём разница

С документацией API вы уже встречались в уроке [JWT-авторизация и Swagger](lesson:jwt-avtorizaciya-swagger). Разберёмся в терминах:

- **OpenAPI** — стандарт (формат файла), в котором описывают REST API: адреса, методы, параметры, тела запросов и ответов. Файл называется спецификацией и пишется в JSON или YAML.
- **Swagger UI** — веб-страница, которая берёт этот файл и показывает его красиво: со списком эндпоинтов и кнопкой «попробовать».
- **Swagger** — так по привычке называют всё вместе.

Аналогия: OpenAPI-файл — это меню ресторана в виде таблицы для поваров, а Swagger UI — красиво свёрстанное меню для гостей. Информация одна и та же.

Бэкенд-фреймворки (Django REST Framework с drf-spectacular, FastAPI, NestJS, Spring) умеют генерировать спецификацию автоматически. Обычно она доступна по адресу вроде `/api/schema/`, `/openapi.json` или `/swagger.json` — точный путь подскажет бэкенд-разработчик.

### Как выглядит спецификация

Небольшой кусок OpenAPI-файла в формате YAML:

```yaml
openapi: 3.0.3
info:
  title: Shop API
  version: 1.0.0
paths:
  /products:
    get:
      operationId: listProducts
      tags: [products]
      parameters:
        - name: category
          in: query
          required: false
          schema:
            type: string
      responses:
        "200":
          description: Список товаров
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Product"
  /products/{id}:
    get:
      operationId: getProduct
      tags: [products]
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        "200":
          description: Один товар
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Product"
        "404":
          description: Не найден
components:
  schemas:
    Product:
      type: object
      required: [id, title, price]
      properties:
        id:
          type: integer
        title:
          type: string
        price:
          type: number
        description:
          type: string
          nullable: true
```

Как это читать:

- `paths` — список адресов; внутри каждого — методы (`get`, `post`…);
- `operationId` — уникальное имя операции, из него генераторы делают имена функций;
- `parameters` — параметры: `in: query` — после `?` в адресе, `in: path` — часть пути (`/products/5`);
- `responses` — что вернётся при каждом коде ответа;
- `components.schemas` — описания объектов, на них ссылаются через `$ref`;
- `required` — обязательные поля; всё остальное может отсутствовать.

## Как читать Swagger UI

Откройте Swagger UI вашего API. Что на странице:

1. **Группы эндпоинтов** (по `tags`) — например, `auth`, `products`, `orders`.
2. **Строка эндпоинта** — цветной метод (`GET` синий, `POST` зелёный, `PUT` оранжевый, `DELETE` красный) и путь. Клик раскрывает подробности.
3. **Parameters** — какие параметры принимает запрос и какие из них обязательные (`required`).
4. **Request body** — пример тела для `POST`/`PUT`/`PATCH`; рядом вкладка **Schema** с типами полей.
5. **Responses** — коды ответов и примеры JSON.
6. **Try it out → Execute** — отправить настоящий запрос прямо со страницы и увидеть ответ.
7. **Authorize** (замок сверху) — вставить токен, чтобы проверять защищённые эндпоинты.
8. **Schemas** внизу — все модели данных.

<aside class="callout" data-icon="💡" markdown="1">

Прежде чем писать запрос в коде, выполните его в Swagger через **Try it out**. Так вы сразу увидите, какой реальный ответ приходит, и отличите ошибку на фронте от ошибки на бэке.

</aside>

## Зачем генерировать типы

Без генерации тип для ответа приходится переписывать руками:

```ts
// написали вручную по Swagger
interface Product {
  id: number;
  title: string;
  price: number;
  description: string;
}
```

Проблемы:

- легко ошибиться: в спецификации `description` может быть `null`, а мы написали просто `string`;
- бэкенд переименовал `title` в `name` — TypeScript ничего не скажет, ведь наш тип не изменился, и ошибку увидит пользователь;
- на десятки эндпоинтов уходят часы ручной работы.

**Генерация типов** решает это: специальная программа читает OpenAPI-файл и сама пишет TypeScript-код. Обновили спецификацию → перезапустили генератор → TypeScript подсветил все места, которые сломались.

## openapi-typescript: только типы

### Установка и генерация

[openapi-typescript](https://openapi-ts.dev/) превращает спецификацию в один файл с типами. Никакого кода запросов он не создаёт — только типы.

```bash
npm install -D openapi-typescript typescript
```

Добавим скрипт в `package.json`:

```json
{
  "scripts": {
    "api:types": "openapi-typescript ./openapi.yaml -o ./src/shared/api/schema.d.ts"
  }
}
```

Вместо локального файла можно указать URL спецификации, например `https://api.example.com/openapi.json`. Запускаем:

```bash
npm run api:types
```

В `src/shared/api/schema.d.ts` появятся типы `paths` (все адреса) и `components` (все схемы). Фрагмент того, что сгенерируется:

```ts
export interface components {
  schemas: {
    Product: {
      id: number;
      title: string;
      price: number;
      description?: string | null;
    };
  };
}
```

Обратите внимание: генератор сам учёл, что `description` необязательное и может быть `null`. Руками мы об этом забыли.

### Используем типы с axios

Достаём нужную схему и даём ей короткое имя:

```ts
// src/shared/api/types.ts
import type { components } from "./schema";

export type Product = components["schemas"]["Product"];
```

```ts
// src/entities/product/api.ts
import axios from "axios";
import type { Product } from "@/shared/api/types";

const http = axios.create({ baseURL: import.meta.env.VITE_API_URL });

export async function getProduct(id: number): Promise<Product> {
  const { data } = await http.get<Product>(`/products/${id}`);
  return data;
}
```

Теперь, если бэкенд переименует поле, после повторной генерации TypeScript подсветит все компоненты, где использовалось старое имя.

### openapi-fetch: типизированный клиент

У того же автора есть крошечный клиент **openapi-fetch**. Он знает все адреса из `paths` и проверяет параметры прямо при вызове:

```bash
npm install openapi-fetch
```

```ts
// src/shared/api/client.ts
import createClient from "openapi-fetch";
import type { paths } from "./schema";

export const api = createClient<paths>({ baseUrl: import.meta.env.VITE_API_URL });
```

```ts
import { api } from "@/shared/api/client";

async function showProduct(id: number) {
  const { data, error } = await api.GET("/products/{id}", {
    params: { path: { id } },
  });

  if (error || !data) {
    console.error("Товар не найден");
    return;
  }

  console.log(data.title); // data имеет тип Product
}
```

Разбор:

- `api.GET("/products/{id}", ...)` — редактор подсказывает только существующие адреса; опечатка в пути — ошибка компиляции;
- `params.path.id` обязателен и должен быть числом — так написано в спецификации;
- после проверки `if (error || !data)` TypeScript знает, что дальше `data` точно есть;
- `data` и `error` типизированы по разделу `responses`.

## Orval: типы, функции и хуки React Query

### Что умеет

[Orval](https://orval.dev/) идёт дальше: по спецификации он генерирует не только типы, но и **готовые функции запросов**, а по желанию — **хуки TanStack Query** (урок [Запросы через React Query](lesson:react-query-get)). Вы больше не пишете `useQuery` руками для каждого эндпоинта.

```bash
npm install -D orval
npm install axios @tanstack/react-query
```

### Конфигурация

Создайте в корне проекта `orval.config.ts`:

```ts
import { defineConfig } from "orval";

export default defineConfig({
  shop: {
    input: "./openapi.yaml",
    output: {
      mode: "tags-split",
      target: "./src/shared/api/generated",
      schemas: "./src/shared/api/generated/model",
      client: "react-query",
      httpClient: "axios",
    },
  },
});
```

- `input` — путь или URL спецификации;
- `mode: "tags-split"` — отдельная папка на каждый тег (`products`, `orders`), чтобы не было одного огромного файла;
- `target` — куда положить функции и хуки, `schemas` — куда положить типы;
- `client: "react-query"` — генерировать хуки TanStack Query;
- `httpClient: "axios"` — запросы внутри хуков делать через axios.

Скрипт в `package.json` и запуск:

```json
{
  "scripts": {
    "api:generate": "orval"
  }
}
```

```bash
npm run api:generate
```

### Используем сгенерированные хуки

Имена функций и хуков Orval берёт из `operationId`. Для `listProducts` и `getProduct` получатся, например, `useListProducts` и `useGetProduct`:

```tsx
// src/pages/ProductPage.tsx
import { useParams } from "react-router";
import { useGetProduct } from "@/shared/api/generated/products/products";

export function ProductPage() {
  const { id } = useParams();
  const { data, isPending, isError } = useGetProduct(Number(id));

  if (isPending) return <p>Загрузка…</p>;
  if (isError) return <p>Товар не найден</p>;

  return (
    <article>
      <h1>{data.data.title}</h1>
      <p>{data.data.price} сом</p>
      {data.data.description && <p>{data.data.description}</p>}
    </article>
  );
}
```

Почему `data.data`? Хук возвращает весь ответ axios, а сами данные лежат в поле `data` этого ответа. Чтобы хуки сразу отдавали полезные данные и использовали ваш собственный экземпляр axios (с `baseURL` и токеном из урока про JWT), в Orval есть настройка `override.mutator` — она подключает свою функцию запроса. Подробности — в документации Orval, раздел про custom axios instance.

<aside class="callout" data-icon="⚠️" markdown="1">

Не редактируйте сгенерированные файлы руками: при следующем запуске генератора все правки сотрутся. Если что-то сгенерировалось неправильно, чините спецификацию (попросите бэкенд) или настройки генератора.

</aside>

<aside class="callout" data-icon="🔐" markdown="1">

Не вписывайте в конфиг генератора реальные токены, даже если спецификация закрыта авторизацией. Используйте переменные окружения и плейсхолдеры вроде `YOUR_API_TOKEN`, а `.env` держите в `.gitignore`.

</aside>

## openapi-typescript или Orval

| | openapi-typescript (+ openapi-fetch) | Orval |
| --- | --- | --- |
| Что генерирует | Только типы | Типы, функции запросов, хуки |
| Объём кода | Один файл `.d.ts` | Много файлов |
| HTTP-клиент | Любой (axios, fetch, openapi-fetch) | axios или fetch, внутри функций |
| React Query | Пишете хуки сами | Хуки готовы |
| Когда брать | Хотите контроль и минимум «магии» | Много эндпоинтов, хотите скорость |

Оба подхода нормальные. Главное — чтобы типы рождались из спецификации, а не из памяти разработчика.

## Как встроить генерацию в работу

1. Договоритесь с бэкендом, где лежит актуальная спецификация.
2. Добавьте скрипт генерации в `package.json`.
3. После каждого изменения API запускайте генерацию и затем `npm run build` — TypeScript покажет, что сломалось.
4. Решите в команде, хранить ли сгенерированные файлы в Git. Частый вариант — хранить: так ревьюер видит, как поменялось API.

## Типичные ошибки

- **Писать типы руками, когда есть спецификация.** Рано или поздно они разойдутся с реальностью.
- **Забывать перегенерировать** после изменений на бэкенде — типы устаревают так же, как ручные.
- **Плохая спецификация на бэке.** Без `required` все поля станут необязательными, а без `operationId` имена функций получатся неудобными. Попросите бэкенд это поправить.
- **Путать пути** `/products/{id}` и `/products/5`: в openapi-fetch пишется шаблон с `{id}`, а значение передаётся в `params.path`.
- **Править сгенерированный код** вместо конфига.

## Практика

1. **Чтение Swagger.** Откройте Swagger вашего учебного API и выпишите для трёх эндпоинтов: метод, путь, обязательные параметры, коды ответов. Ожидаемый результат: таблица на три строки.
2. **Своя спецификация.** Скопируйте YAML из урока в `openapi.yaml` и добавьте эндпоинт `POST /products` с телом `ProductCreate` (title, price). Ожидаемый результат: файл без ошибок открывается в любом онлайн-просмотрщике OpenAPI или в Swagger UI.
3. **Генерация типов.** Сгенерируйте `schema.d.ts` через openapi-typescript и выведите тип `Product`. Ожидаемый результат: `description` имеет тип `string | null | undefined`.
4. **openapi-fetch.** Напишите функцию `loadProduct(id)` через `api.GET`. Ожидаемый результат: вызов `api.GET("/product/{id}")` с опечаткой подсвечивается ошибкой.
5. **Orval + React Query.** Настройте Orval для своего проекта и замените один ручной `useQuery` на сгенерированный хук. Ожидаемый результат: страница работает как раньше, а ручного кода запроса больше нет.

## Итоги

- OpenAPI — стандарт описания API, Swagger UI — страница, которая его показывает; файл бывает в JSON или YAML.
- В Swagger UI смотрим эндпоинты, параметры, тело запроса, ответы, а через Try it out проверяем запросы вживую.
- Типы, написанные вручную, расходятся с API; генерация из спецификации решает эту проблему.
- openapi-typescript создаёт только типы (`paths`, `components`), openapi-fetch — типизированный клиент по ним.
- Orval генерирует типы, функции запросов и хуки React Query, имена берутся из `operationId`.
- Сгенерированный код не правим руками — меняем спецификацию или конфиг и перегенерируем.
