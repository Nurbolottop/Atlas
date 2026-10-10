Пока в проекте пять компонентов, неважно, где они лежат. Но когда файлов становится сотни, без порядка разработчик тратит больше времени на поиски, чем на работу. Архитектура проекта — это договорённость, как раскладывать код по папкам и кто кого может импортировать. В этом уроке разберём три популярных подхода — компонентный, модульный и Feature-Sliced Design (FSD), — их плюсы и минусы и научимся выбирать подходящий.

## Зачем нужна архитектура

Представьте квартиру, где вещи лежат где попало: носки на кухне, ложки в ванной. Жить можно, но каждый раз приходится вспоминать, где что. Архитектура — это шкафы с подписями: одежда здесь, посуда там.

Хорошая структура проекта решает несколько задач:

- **быстро найти код** — новичок в команде за минуту понимает, где лежит страница корзины;
- **менять код без страха** — правка в одном месте не ломает пять других;
- **работать командой** — два разработчика не правят одни и те же файлы;
- **удалять код** — фичу можно выкинуть целиком, удалив одну папку.

<aside class="callout" data-icon="📌" markdown="1">

Идеальной архитектуры не существует. Есть подходящая под размер проекта и команды. Для лендинга FSD — перебор, для большого интернет-магазина «всё в папке components» — боль.

</aside>

## Компонентная архитектура

### Как устроена

Самый простой подход: файлы раскладываются **по типу** — все компоненты в одну папку, все хуки в другую, все страницы в третью. Обычно именно так выглядят первые проекты на React:

```text
src/
├── components/
│   ├── Button.tsx
│   ├── Header.tsx
│   ├── ProductCard.tsx
│   ├── CartItem.tsx
│   └── LoginForm.tsx
├── pages/
│   ├── HomePage.tsx
│   ├── CartPage.tsx
│   └── LoginPage.tsx
├── hooks/
│   ├── useCart.ts
│   └── useAuth.ts
├── api/
│   └── index.ts
├── store/
│   └── cartStore.ts
├── App.tsx
└── main.tsx
```

Компонент — это кирпичик интерфейса (подробнее в уроке [Компоненты и пропсы](lesson:komponenty-i-propsy)). Страница собирается из кирпичиков:

```tsx
// src/pages/CartPage.tsx
import { Header } from "../components/Header";
import { CartItem } from "../components/CartItem";
import { useCart } from "../hooks/useCart";

export function CartPage() {
  const { items, total } = useCart();

  return (
    <>
      <Header />
      {items.map((item) => (
        <CartItem key={item.id} item={item} />
      ))}
      <p>Итого: {total} сом</p>
    </>
  );
}
```

### Плюсы и минусы

| Плюсы | Минусы |
| --- | --- |
| Понятна с первого дня | Папка `components` разрастается до сотни файлов |
| Не нужно ничего учить | Код одной фичи разбросан по 4–5 папкам |
| Идеальна для маленьких проектов | Непонятно, что от чего зависит |
| | Сложно удалить фичу: надо искать её куски везде |

Чтобы поменять корзину, придётся открыть `components/CartItem.tsx`, `hooks/useCart.ts`, `store/cartStore.ts`, `api/index.ts` и `pages/CartPage.tsx` — пять разных мест.

## Модульная архитектура

### Как устроена

Здесь код группируется **по смыслу** (по фичам, или модулям): всё, что относится к корзине, лежит в одной папке `cart`, всё про авторизацию — в `auth`. Внутри модуля уже можно делить по типам.

```text
src/
├── modules/
│   ├── auth/
│   │   ├── components/LoginForm.tsx
│   │   ├── hooks/useAuth.ts
│   │   ├── api.ts
│   │   └── index.ts
│   ├── cart/
│   │   ├── components/CartItem.tsx
│   │   ├── store.ts
│   │   ├── api.ts
│   │   └── index.ts
│   └── catalog/
│       ├── components/ProductCard.tsx
│       ├── api.ts
│       └── index.ts
├── shared/
│   ├── ui/Button.tsx
│   └── lib/formatPrice.ts
├── pages/
│   ├── HomePage.tsx
│   └── CartPage.tsx
└── App.tsx
```

Аналогия — отделы в компании: бухгалтерия, склад, продажи. Каждый отдел хранит свои документы у себя.

### Публичный API модуля

Файл `index.ts` в корне модуля — это «окошко», через которое модуль общается с внешним миром. Наружу отдаём только то, что нужно другим:

```ts
// src/modules/cart/index.ts
export { CartItem } from "./components/CartItem";
export { useCartStore } from "./store";
// api.ts не экспортируем — это внутреннее дело модуля
```

Теперь страница импортирует из модуля, а не из его внутренностей:

```tsx
// ✅ хорошо — через публичный API
import { CartItem, useCartStore } from "../modules/cart";

// ❌ плохо — лезем внутрь чужого модуля
import { CartItem } from "../modules/cart/components/CartItem";
```

Если завтра внутри модуля переименуют папку `components` в `ui`, сломается только `index.ts` модуля, а не весь проект.

### Плюсы и минусы

| Плюсы | Минусы |
| --- | --- |
| Код фичи в одном месте | Нет строгих правил: каждый понимает «модуль» по-своему |
| Легко удалить или передать фичу | Модули начинают импортировать друг друга по кругу |
| Хорошо масштабируется на средних проектах | Непонятно, куда класть код, нужный двум модулям |

## Feature-Sliced Design (FSD)

### Что это

**FSD** — это методология (набор правил) для фронтенд-проектов, популярная в русскоязычном сообществе. Она берёт идею модулей и добавляет строгие правила: на какие **слои** делить код и кто кого может импортировать. Официальный сайт — [feature-sliced.design](https://feature-sliced.design/).

### Слои

Слои идут сверху вниз — от самого «общего» к самому «базовому»:

| Слой | Что лежит | Пример |
| --- | --- | --- |
| `app` | Запуск приложения: провайдеры, роутер, глобальные стили | `App.tsx`, `router.tsx`, `QueryClientProvider` |
| `pages` | Страницы целиком | `CatalogPage`, `CartPage` |
| `widgets` | Крупные самостоятельные блоки страницы | `Header`, `ProductList`, `Sidebar` |
| `features` | Действия пользователя, которые приносят пользу | `AddToCart`, `LoginByEmail`, `SearchProducts` |
| `entities` | Бизнес-сущности — «существительные» проекта | `product`, `user`, `order` |
| `shared` | Переиспользуемый код без бизнес-логики | `Button`, `Input`, настройки axios, `formatPrice` |

Простой способ запомнить: **entities — существительные** («товар», «пользователь»), **features — глаголы** («добавить в корзину», «войти»).

<aside class="callout" data-icon="📌" markdown="1">

Главное правило FSD: **слой может импортировать только из слоёв ниже себя**. `pages` может брать из `widgets`, `features`, `entities`, `shared`. А `entities` не может импортировать из `features` — сущность ничего не знает о действиях над ней. `shared` вообще ни от кого не зависит.

</aside>

### Слайсы и сегменты

Слои (кроме `app` и `shared`) делятся на **слайсы** — папки по бизнес-смыслу: `entities/product`, `entities/user`, `features/add-to-cart`.

Слайсы делятся на **сегменты** — папки по назначению кода:

| Сегмент | Что внутри |
| --- | --- |
| `ui` | Компоненты |
| `model` | Состояние, хранилища, бизнес-логика, типы |
| `api` | Запросы к серверу |
| `lib` | Вспомогательные функции |
| `config` | Константы и настройки |

Второе правило: **слайсы одного слоя не импортируют друг друга**. `features/add-to-cart` не должен лезть в `features/login`. Если двум фичам нужен общий код, его опускают ниже — в `entities` или `shared`.

### Пример структуры интернет-магазина

```text
src/
├── app/
│   ├── providers/QueryProvider.tsx
│   ├── router.tsx
│   └── styles/index.css
├── pages/
│   ├── catalog/
│   │   ├── ui/CatalogPage.tsx
│   │   └── index.ts
│   └── cart/
│       ├── ui/CartPage.tsx
│       └── index.ts
├── widgets/
│   └── product-list/
│       ├── ui/ProductList.tsx
│       └── index.ts
├── features/
│   └── add-to-cart/
│       ├── ui/AddToCartButton.tsx
│       ├── model/cartStore.ts
│       └── index.ts
├── entities/
│   └── product/
│       ├── ui/ProductCard.tsx
│       ├── api/getProducts.ts
│       ├── model/types.ts
│       └── index.ts
└── shared/
    ├── ui/Button.tsx
    ├── api/http.ts
    └── lib/formatPrice.ts
```

### Как слои работают вместе

Пройдём снизу вверх. Сначала `shared` — общий HTTP-клиент:

```ts
// src/shared/api/http.ts
import axios from "axios";

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});
```

Сущность `product` — тип, запрос и карточка:

```ts
// src/entities/product/model/types.ts
export interface Product {
  id: number;
  title: string;
  price: number;
}
```

```ts
// src/entities/product/api/getProducts.ts
import { http } from "@/shared/api/http";
import type { Product } from "../model/types";

export async function getProducts(): Promise<Product[]> {
  const { data } = await http.get<Product[]>("/products");
  return data;
}
```

```tsx
// src/entities/product/ui/ProductCard.tsx
import type { ReactNode } from "react";
import { formatPrice } from "@/shared/lib/formatPrice";
import type { Product } from "../model/types";

type Props = { product: Product; actions?: ReactNode };

export function ProductCard({ product, actions }: Props) {
  return (
    <article>
      <h3>{product.title}</h3>
      <p>{formatPrice(product.price)}</p>
      {actions}
    </article>
  );
}
```

```ts
// src/entities/product/index.ts — публичный API сущности
export { ProductCard } from "./ui/ProductCard";
export { getProducts } from "./api/getProducts";
export type { Product } from "./model/types";
```

Обратите внимание на проп `actions`. Карточка товара — это сущность, она не знает о кнопке «В корзину» (кнопка — это фича, слой выше). Поэтому кнопку в карточку **вставляет виджет**, который знает и о сущности, и о фиче:

```tsx
// src/widgets/product-list/ui/ProductList.tsx
import { useQuery } from "@tanstack/react-query";
import { ProductCard, getProducts } from "@/entities/product";
import { AddToCartButton } from "@/features/add-to-cart";

export function ProductList() {
  const { data, isPending, isError } = useQuery({
    queryKey: ["products"],
    queryFn: getProducts,
  });

  if (isPending) return <p>Загрузка…</p>;
  if (isError) return <p>Не удалось загрузить товары</p>;

  return (
    <div className="grid">
      {data.map((product) => (
        <ProductCard
          key={product.id}
          product={product}
          actions={<AddToCartButton productId={product.id} />}
        />
      ))}
    </div>
  );
}
```

А страница `pages/catalog/ui/CatalogPage.tsx` просто выводит заголовок и `<ProductList />`, импортированный из `@/widgets/product-list`.

Разбор цепочки: `pages` → `widgets` → `features` и `entities` → `shared`. Все стрелки направлены только вниз, поэтому зависимости понятны и нет циклов.

### Плюсы и минусы

| Плюсы | Минусы |
| --- | --- |
| Строгие правила: все в команде раскладывают код одинаково | Высокий порог входа: надо выучить слои и правила |
| Понятно, что от чего зависит | Много папок и `index.ts` даже для мелочей |
| Легко найти, изменить и удалить фичу | Споры «это feature или entity?» |
| Хорошо подходит для больших проектов и команд | Для маленьких проектов — избыточно |

## Алиасы путей: `@/` вместо `../../../`

В примерах выше мы писали `@/shared/api/http`. Это **алиас** — короткое имя для папки `src`. Без него импорты выглядят так: `../../../shared/api/http`, и при переносе файла всё ломается.

Настраивается алиас в двух местах. В Vite — чтобы сборка понимала путь:

```ts
// vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
});
```

И в TypeScript — чтобы редактор не подчёркивал импорт красным:

```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

Этот блок добавляют в `tsconfig.app.json` (в проекте Vite с шаблоном `react-ts`) к уже существующим настройкам. Если редактор подчёркивает `node:url` в `vite.config.ts`, установите типы Node: `npm install -D @types/node`.

## Сравнение и выбор

| | Компонентная | Модульная | FSD |
| --- | --- | --- | --- |
| Группировка | По типу файла | По фичам | По слоям и фичам |
| Порог входа | Нулевой | Низкий | Средний/высокий |
| Правила импорта | Нет | Публичный API модуля | Строгие: только вниз |
| Размер проекта | Маленький | Средний | Средний и большой |
| Пример | Лендинг, пет-проект | Админка, сервис на 10–20 экранов | Маркетплейс, банк, большая команда |

<aside class="callout" data-icon="💡" markdown="1">

Не нужно сразу строить идеальную архитектуру. Начните с компонентной, а когда почувствуете боль («где лежит этот хук?», «почему правка корзины сломала профиль?») — переходите к модулям или FSD. На собеседовании часто спрашивают именно про плюсы и минусы, а не про «единственно правильный» вариант.

</aside>

## Типичные ошибки

- **Импорт снизу вверх в FSD.** `entities/product` импортирует `features/add-to-cart` — нарушение. Передайте кнопку через проп или `children`, как в примере с `actions`.
- **Обход публичного API.** Импорт `@/entities/product/ui/ProductCard` вместо `@/entities/product` привязывает вас к внутренней структуре слайса.
- **Всё в `shared`.** `shared` — только для кода без бизнес-смысла. Компонент `UserAvatar` с логикой пользователя — это `entities/user`, а не `shared`.
- **FSD для лендинга из трёх блоков.** Двадцать папок ради трёх компонентов только мешают.
- **Смешивание подходов.** Половина проекта в `components`, половина в `features` — хуже, чем любой подход по отдельности.

## Практика

1. **Разбор своего проекта.** Возьмите свой проект из прошлых месяцев и нарисуйте (в `text`-блоке или на бумаге) его текущую структуру. Ожидаемый результат: список мест, где код одной фичи разбросан по разным папкам.
2. **Классификация.** Разложите по слоям FSD: `LoginForm`, `Button`, `user`, `Header`, `formatDate`, `ProfilePage`, `LikePost`, `post`. Ожидаемый результат: таблица «элемент → слой», например `LikePost → features`.
3. **Алиас.** Настройте `@/` в Vite-проекте на TypeScript (`vite.config.ts` + `tsconfig.app.json`). Ожидаемый результат: импорт `import { Button } from "@/shared/ui/Button"` работает и не подчёркивается.
4. **Переезд на модули.** Переведите ToDoList из урока [ToDoList: axios и json-server](lesson:todolist-axios-json-server) на модульную структуру с `index.ts` у каждого модуля. Ожидаемый результат: страницы импортируют только из `modules/<имя>`.
5. **Мини-FSD.** Соберите каталог товаров по примеру из урока: `shared/api`, `entities/product`, `features/add-to-cart`, `widgets/product-list`, `pages/catalog`. Ожидаемый результат: ни один файл не импортирует из слоя выше себя.

## Итоги

- Архитектура — это договорённость, где лежит код и кто кого импортирует.
- Компонентная: файлы по типам (`components`, `hooks`, `pages`); проста, но плохо растёт.
- Модульная: код по фичам с публичным API (`index.ts`); хорошо для средних проектов.
- FSD: слои `app → pages → widgets → features → entities → shared`, слайсы и сегменты (`ui`, `model`, `api`, `lib`, `config`).
- Главные правила FSD: импорт только из слоёв ниже и через публичный API; слайсы одного слоя не знают друг о друге.
- Алиас `@/` убирает длинные относительные пути — настраивается в `vite.config.ts` и `tsconfig`.
- Выбирайте архитектуру под размер проекта и команды, а не «по моде».
