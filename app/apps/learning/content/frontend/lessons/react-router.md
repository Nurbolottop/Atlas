Пока всё наше приложение жило на одной странице. Но настоящему сайту нужны разделы: главная, каталог, карточка товара, профиль — и у каждого свой адрес в браузере. В этом уроке подключим **React Router** — стандартную библиотеку маршрутизации для React, научимся описывать страницы двумя способами (`BrowserRouter` + `Routes` и `createBrowserRouter`), читать параметры из адреса, переходить между страницами из кода, работать со строкой запроса и загружать страницы «лениво» через `lazy()`.

## Что такое SPA и маршрутизация

Обычный сайт при переходе по ссылке запрашивает у сервера **новую HTML-страницу**: экран мигает, всё грузится заново.

React-приложение — это **SPA** (Single Page Application, одностраничное приложение). HTML-страница одна (`index.html`), а «страницы» — это разные компоненты. При переходе браузер ничего не перезагружает: JavaScript меняет адрес в строке браузера и показывает другой компонент. Это быстро и плавно.

**Маршрутизация** (роутинг) — это правило «какой адрес → какой компонент»:

```text
/              →  <HomePage />
/products      →  <ProductsPage />
/products/42   →  <ProductPage />   (товар с id = 42)
/about         →  <AboutPage />
всё остальное  →  <NotFoundPage />  (404)
```

Аналогия: React Router — это навигатор в торговом центре. Вы называете ему номер павильона (адрес), и он ведёт к нужному магазину (компоненту), не выводя вас на улицу.

## Установка

```bash
npm install react-router
```

Актуальная версия React Router (v7) поставляется одним пакетом `react-router`. В старых проектах и туториалах вы встретите пакет `react-router-dom` и импорты из него — это то же самое API, просто раньше оно было разделено на два пакета.

Для примеров создадим страницы:

```jsx
// src/pages/HomePage.jsx
export default function HomePage() {
  return <h1>Главная</h1>;
}
```

```jsx
// src/pages/AboutPage.jsx
export default function AboutPage() {
  return <h1>О нас</h1>;
}
```

```jsx
// src/pages/NotFoundPage.jsx
import { Link } from 'react-router';

export default function NotFoundPage() {
  return (
    <div>
      <h1>404 — страница не найдена</h1>
      <Link to="/">Вернуться на главную</Link>
    </div>
  );
}
```

## Способ 1. BrowserRouter, Routes и Route

Это классический, «декларативный» способ: маршруты описываются JSX-компонентами.

```jsx
// src/main.jsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router';
import App from './App';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>
);
```

```jsx
// src/App.jsx
import { Routes, Route } from 'react-router';
import HomePage from './pages/HomePage';
import AboutPage from './pages/AboutPage';
import NotFoundPage from './pages/NotFoundPage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/about" element={<AboutPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

export default App;
```

Разбор:

-   `BrowserRouter` оборачивает всё приложение. Он следит за адресной строкой браузера и даёт доступ к роутингу всем компонентам внутри.
-   `Routes` — контейнер маршрутов: смотрит на текущий адрес и выбирает **один** подходящий `Route`.
-   `Route path="/about" element={<AboutPage />}` — «если адрес `/about`, покажи `AboutPage`». Обратите внимание: в `element` передаётся JSX-элемент `<AboutPage />`, а не имя компонента.
-   `path="*"` — «звёздочка» подходит под любой адрес. Это страница 404.

## Навигация: Link и NavLink

Обычная ссылка `<a href="/about">` перезагрузит всю страницу — всё состояние приложения пропадёт. Внутри приложения используйте компонент `Link`:

```jsx
import { Link } from 'react-router';

<Link to="/about">О нас</Link>
```

`Link` рисует обычный тег `<a>`, но перехватывает клик и меняет адрес без перезагрузки.

**NavLink** — та же ссылка, но она «знает», активна ли сейчас, и может подсветиться. Это нужно для меню:

```jsx
import { NavLink } from 'react-router';
import styles from './Header.module.css';

function Header() {
  const getClass = ({ isActive }) => (isActive ? `${styles.link} ${styles.active}` : styles.link);

  return (
    <nav className={styles.nav}>
      <NavLink to="/" end className={getClass}>Главная</NavLink>
      <NavLink to="/products" className={getClass}>Каталог</NavLink>
      <NavLink to="/about" className={getClass}>О нас</NavLink>
    </nav>
  );
}

export default Header;
```

-   В `className` у `NavLink` можно передать функцию: она получает `{ isActive }` и возвращает класс.
-   `end` у ссылки на `/` означает «активна только при точном совпадении». Иначе главная подсвечивалась бы на любой странице, ведь все адреса начинаются с `/`.

## Вложенные маршруты, Layout и Outlet

На большинстве сайтов шапка и подвал одинаковы на всех страницах, меняется только середина. Чтобы не вставлять `<Header />` в каждую страницу, делают **макет** (layout) и **вложенные маршруты**.

```jsx
// src/layouts/MainLayout.jsx
import { Outlet } from 'react-router';
import Header from '../components/Header';

export default function MainLayout() {
  return (
    <>
      <Header />
      <main style={{ padding: 24 }}>
        <Outlet />
      </main>
      <footer>© 2026 Atlas Shop</footer>
    </>
  );
}
```

```jsx
// src/App.jsx
<Routes>
  <Route path="/" element={<MainLayout />}>
    <Route index element={<HomePage />} />
    <Route path="products" element={<ProductsPage />} />
    <Route path="products/:id" element={<ProductPage />} />
    <Route path="about" element={<AboutPage />} />
    <Route path="*" element={<NotFoundPage />} />
  </Route>
</Routes>
```

Разбор:

-   `Outlet` — «окошко», куда подставляется дочерняя страница. Шапка и подвал остаются на месте, меняется только содержимое `Outlet`.
-   Дочерние `path` пишутся **без** слеша в начале — они продолжают путь родителя: `products` внутри `/` даёт `/products`.
-   `index` — маршрут по умолчанию: что показать в `Outlet` по адресу ровно `/`.

## useParams: параметры из адреса

Сделать отдельный маршрут для каждого из 1000 товаров невозможно. Вместо этого в пути делают **параметр** — часть адреса с двоеточием: `products/:id`. Под него подходит `/products/1`, `/products/42`, `/products/abc`.

Достать значение параметра помогает хук `useParams`:

```jsx
// src/pages/ProductPage.jsx
import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router';

export default function ProductPage() {
  const { id } = useParams(); // для /products/42 → id = '42'
  const [product, setProduct] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let ignore = false;
    setProduct(null);
    setError(null);

    fetch(`https://dummyjson.com/products/${id}`)
      .then((res) => {
        if (!res.ok) throw new Error('Товар не найден');
        return res.json();
      })
      .then((data) => {
        if (!ignore) setProduct(data);
      })
      .catch((err) => {
        if (!ignore) setError(err.message);
      });

    return () => {
      ignore = true;
    };
  }, [id]);

  if (error) return <p>{error}</p>;
  if (!product) return <p>Загрузка...</p>;

  return (
    <article>
      <Link to="/products">← Назад в каталог</Link>
      <h1>{product.title}</h1>
      <img src={product.thumbnail} alt={product.title} width={240} />
      <p>{product.description}</p>
      <strong>${product.price}</strong>
    </article>
  );
}
```

-   Имя в `useParams` совпадает с именем в пути: `:id` → `id`. Для `users/:userId/posts/:postId` будет `{ userId, postId }`.
-   Параметр **всегда строка**. Нужно число — `Number(id)`.
-   `id` в зависимостях эффекта: при переходе с `/products/1` на `/products/2` компонент не пересоздаётся, но эффект перезапустится и загрузит новый товар.

А в каталоге сделаем ссылки на карточки:

```jsx
// src/pages/ProductsPage.jsx (упрощённо)
{products.map((p) => (
  <li key={p.id}>
    <Link to={`/products/${p.id}`}>{p.title}</Link>
  </li>
))}
```

## useNavigate: переход из кода

`Link` — для ссылок, по которым кликают. А если нужно перейти **после действия**: после входа в аккаунт, после отправки формы, по кнопке «Назад»? Для этого хук `useNavigate`:

```jsx
import { useNavigate } from 'react-router';

function LoginPage() {
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    // ... запрос на сервер для входа
    navigate('/profile'); // переход после успешного входа
  }

  return (
    <form onSubmit={handleSubmit}>
      <input placeholder="Email" />
      <button type="submit">Войти</button>
      <button type="button" onClick={() => navigate(-1)}>Назад</button>
    </form>
  );
}
```

| Вызов | Что делает |
| --- | --- |
| `navigate('/profile')` | Переход на `/profile` |
| `navigate(-1)` | Назад по истории (как кнопка «Назад» в браузере) |
| `navigate(1)` | Вперёд по истории |
| `navigate('/login', { replace: true })` | Переход с заменой текущей записи в истории — «Назад» не вернёт на эту страницу |
| `` navigate(`/products/${id}`) `` | Переход на динамический адрес |

<aside class="callout" data-icon="⚠️" markdown="1">

Не вызывайте `navigate()` прямо в теле компонента во время рендера — только в обработчиках событий или в `useEffect`. Для перенаправления во время рендера есть компонент `<Navigate to="/login" replace />`.

</aside>

## useSearchParams: строка запроса

Помните адреса вида `/products?category=phones&sort=price`? Часть после `?` — это **строка запроса** (query string, search params). В ней удобно хранить фильтры, поиск, номер страницы: таким адресом можно поделиться, и у другого человека откроются те же фильтры.

`useSearchParams` работает похоже на `useState`, только значения хранятся в адресе:

```jsx
import { useSearchParams } from 'react-router';

const allProducts = [
  { id: 1, title: 'iPhone', category: 'phones' },
  { id: 2, title: 'Galaxy', category: 'phones' },
  { id: 3, title: 'MacBook', category: 'laptops' },
];

export default function ProductsPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  const query = searchParams.get('q') ?? '';
  const category = searchParams.get('category') ?? 'all';

  function updateParam(key, value) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value && value !== 'all') next.set(key, value);
      else next.delete(key);
      return next;
    });
  }

  const visible = allProducts.filter(
    (p) =>
      p.title.toLowerCase().includes(query.toLowerCase()) &&
      (category === 'all' || p.category === category)
  );

  return (
    <div>
      <input value={query} onChange={(e) => updateParam('q', e.target.value)} placeholder="Поиск" />
      <select value={category} onChange={(e) => updateParam('category', e.target.value)}>
        <option value="all">Все</option>
        <option value="phones">Телефоны</option>
        <option value="laptops">Ноутбуки</option>
      </select>

      <ul>
        {visible.map((p) => (
          <li key={p.id}>{p.title}</li>
        ))}
      </ul>
    </div>
  );
}
```

Разбор:

-   `searchParams` — объект `URLSearchParams`. `get('q')` возвращает строку или `null`, если параметра нет; `?? ''` подставляет значение по умолчанию.
-   `setSearchParams` меняет строку запроса — адрес становится, например, `/products?q=mac&category=laptops`, и компонент перерисовывается.
-   Передаём в `setSearchParams` функцию и копируем старые параметры, чтобы при изменении поиска не потерять выбранную категорию.
-   Пустые значения удаляем (`next.delete`), чтобы адрес оставался чистым.
-   Обновите страницу или отправьте ссылку другу — фильтры сохранятся.

| | `useParams` | `useSearchParams` |
| --- | --- | --- |
| Часть адреса | Путь: `/products/42` | После `?`: `?q=mac&page=2` |
| Описывается в маршруте | Да, `:id` | Нет |
| Обязательность | Без него маршрут не совпадёт | Необязательные |
| Для чего | Какой объект открыть | Фильтры, поиск, сортировка, пагинация |

## lazy(): ленивая загрузка страниц

По умолчанию сборщик кладёт **все** страницы в один большой JavaScript-файл. Пользователь открыл главную — а скачал ещё и админку, и профиль, и корзину. Функция `lazy` из React позволяет загружать код страницы **только когда она нужна**:

```jsx
import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router';
import MainLayout from './layouts/MainLayout';
import HomePage from './pages/HomePage';

const AboutPage = lazy(() => import('./pages/AboutPage'));
const ProductsPage = lazy(() => import('./pages/ProductsPage'));
const ProductPage = lazy(() => import('./pages/ProductPage'));

function App() {
  return (
    <Suspense fallback={<p>Загрузка страницы...</p>}>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<HomePage />} />
          <Route path="products" element={<ProductsPage />} />
          <Route path="products/:id" element={<ProductPage />} />
          <Route path="about" element={<AboutPage />} />
        </Route>
      </Routes>
    </Suspense>
  );
}

export default App;
```

-   `lazy(() => import('./pages/AboutPage'))` — динамический `import()`: Vite вынесет страницу в отдельный файл и загрузит его при первом переходе на `/about`.
-   Страница для `lazy` должна быть экспортирована через `export default`.
-   `Suspense` показывает `fallback`, пока код страницы скачивается.
-   Главную обычно импортируют обычным способом — она нужна сразу.

Проверьте: `npm run build` — в папке `dist/assets` появятся отдельные JS-файлы для ленивых страниц. А во вкладке Network видно, как файл страницы скачивается при первом переходе.

<aside class="callout" data-icon="💡" markdown="1">

Можно поставить `Suspense` внутри `MainLayout` вокруг `<Outlet />` — тогда при загрузке страницы шапка и подвал останутся на экране, а «Загрузка...» появится только в середине.

</aside>

## Способ 2. createBrowserRouter и RouterProvider

Начиная с версии 6.4 у React Router есть **data router** — маршруты описываются обычным массивом объектов, а не JSX. Это рекомендуемый способ для новых приложений: он даёт дополнительные возможности — загрузку данных до открытия страницы (loaders), обработку ошибок маршрута, формы (actions).

```jsx
// src/router.jsx
import { createBrowserRouter } from 'react-router';
import MainLayout from './layouts/MainLayout';
import HomePage from './pages/HomePage';
import ProductsPage from './pages/ProductsPage';
import ProductPage from './pages/ProductPage';
import AboutPage from './pages/AboutPage';
import NotFoundPage from './pages/NotFoundPage';
import ErrorPage from './pages/ErrorPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    errorElement: <ErrorPage />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'products', element: <ProductsPage /> },
      { path: 'products/:id', element: <ProductPage /> },
      { path: 'about', element: <AboutPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]);
```

```jsx
// src/main.jsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { RouterProvider } from 'react-router';
import { router } from './router';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>
);
```

Сравните с первым способом — структура та же:

-   `{ path, element }` ↔ `<Route path element />`;
-   `children: [...]` ↔ вложенные `<Route>`;
-   `index: true` ↔ `<Route index />`;
-   `RouterProvider` заменяет и `BrowserRouter`, и `Routes` — `App` с `Routes` больше не нужен.

`Link`, `NavLink`, `Outlet`, `useParams`, `useNavigate`, `useSearchParams` работают **одинаково** в обоих способах.

### errorElement

Если в компоненте страницы произошла ошибка, вместо белого экрана покажется `errorElement`. Узнать, что случилось, помогает хук `useRouteError`:

```jsx
// src/pages/ErrorPage.jsx
import { useRouteError, Link } from 'react-router';

export default function ErrorPage() {
  const error = useRouteError();
  console.error(error);

  return (
    <div style={{ padding: 24 }}>
      <h1>Что-то пошло не так</h1>
      <p>{error?.statusText || error?.message}</p>
      <Link to="/">На главную</Link>
    </div>
  );
}
```

### Ленивые маршруты в data router

В `createBrowserRouter` у маршрута есть собственное свойство `lazy` — роутер сам загрузит код перед переходом, без `Suspense`. Модуль страницы для этого экспортирует компонент под именем `Component`:

```jsx
// src/pages/AboutPage.jsx — добавляем именованный экспорт
export function Component() {
  return <h1>О нас</h1>;
}
```

```jsx
// в router.jsx
{ path: 'about', lazy: () => import('./pages/AboutPage') },
```

Привычный `React.lazy` + `Suspense` в `element` тоже работает и в data router.

### Какой способ выбрать

| | `BrowserRouter` + `Routes` | `createBrowserRouter` |
| --- | --- | --- |
| Как описываются маршруты | JSX внутри компонентов | Массив объектов в отдельном файле |
| Загрузка данных (loader), actions | Нет | Да |
| `errorElement` | Нет | Да |
| Где встречается | Много существующих проектов | Рекомендуется для новых |

Загрузку данных через `loader` и хук `useLoaderData` подробно разберём в уроке [SPA на React Router](lesson:spa-na-react-router).

## Типичные ошибки

-   **Хуки роутера вне роутера.** `useNavigate` в компоненте, который не лежит внутри `BrowserRouter`/`RouterProvider`, — ошибка «useNavigate() may be used only in the context of a <Router> component».
-   **`<a href>` вместо `<Link to>`** — страница полностью перезагружается, состояние теряется.
-   **`element={AboutPage}`** вместо `element={<AboutPage />}`.
-   **Слеш у дочернего пути** (`/products` внутри родителя) — путь станет абсолютным и может не совпасть с ожидаемым.
-   **Забыли `<Outlet />`** в макете — вложенные страницы не отображаются.
-   **Ждут число из `useParams`** — там всегда строка.
-   **404 после деплоя при обновлении страницы.** Dev-сервер Vite сам отдаёт `index.html` на любой адрес, а обычный хостинг — нет. На хостинге нужно настроить, чтобы все адреса отдавали `index.html`.

## Практика

1.  **Три страницы.** Подключите React Router через `BrowserRouter`: главная, «О нас», «Контакты» и страница 404. Ожидаемый результат: переходы по меню без перезагрузки, на неизвестном адресе — 404.
2.  **Макет и меню.** Вынесите шапку с `NavLink` и подвал в `MainLayout` с `Outlet`. Активный пункт меню подсвечивается.
3.  **Каталог и карточка.** Страница `/products` загружает список с `https://dummyjson.com/products?limit=20`, каждая позиция — `Link` на `/products/:id`. Страница товара берёт `id` из `useParams` и загружает товар. Добавьте кнопку «Назад» через `navigate(-1)`.
4.  **Фильтры в адресе.** Добавьте на страницу каталога поиск `?q=` и сортировку `?sort=price-asc|price-desc` через `useSearchParams`. Ожидаемый результат: после обновления страницы фильтры сохраняются.
5.  **Переезд на data router.** Перепишите маршруты на `createBrowserRouter` + `RouterProvider`, добавьте `errorElement` и сделайте страницы «О нас» и «Контакты» ленивыми. Проверьте через `npm run build`, что они вынесены в отдельные файлы.

## Итоги

-   SPA — одна HTML-страница, «страницы» — компоненты; React Router связывает адреса с компонентами без перезагрузки.
-   Способ 1: `BrowserRouter` → `Routes` → `Route path element`; способ 2: `createBrowserRouter([...])` + `RouterProvider` с `children` и `errorElement`.
-   Для переходов — `Link` и `NavLink` (подсветка активного пункта), для общего каркаса — макет с `Outlet`.
-   `useParams` читает параметры пути (`/products/:id`), значения всегда строки.
-   `useNavigate` переходит из кода: `navigate('/path')`, `navigate(-1)`, `{ replace: true }`.
-   `useSearchParams` хранит фильтры и поиск в строке запроса, которой можно поделиться.
-   `lazy(() => import(...))` + `Suspense` загружают код страниц по требованию; в data router есть свойство маршрута `lazy`.
