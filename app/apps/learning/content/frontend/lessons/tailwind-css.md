Tailwind CSS — это библиотека, в которой стили пишутся не в отдельном CSS-файле, а прямо в разметке — короткими готовыми классами вроде `p-4`, `text-center` или `bg-blue-500`. Такой подход ускоряет вёрстку и избавляет от вечного вопроса «как назвать этот класс». В этом уроке установим Tailwind в React-проект на Vite, разберём основные классы и сверстаем адаптивную страницу, которая хорошо выглядит и на телефоне, и на компьютере.

## Что такое Tailwind и чем он отличается от обычного CSS

### Подход utility-first

Вспомним, как мы верстали раньше (урок [CSS: подключение и свойства](lesson:css-podklyuchenie-i-svoystva)): придумываем класс, потом описываем его в CSS.

```html
<button class="primary-button">Купить</button>
```

```css
.primary-button {
  padding: 8px 16px;
  background-color: #2563eb;
  color: white;
  border-radius: 8px;
}
```

В Tailwind каждый класс отвечает **за одно свойство**, и вы собираете стиль из них, как из конструктора:

```html
<button class="px-4 py-2 bg-blue-600 text-white rounded-lg">Купить</button>
```

- `px-4` — padding слева и справа;
- `py-2` — padding сверху и снизу;
- `bg-blue-600` — цвет фона;
- `text-white` — цвет текста;
- `rounded-lg` — скругление углов.

Такие маленькие классы называются **утилитами** (utility — «полезная мелочь»), а подход — **utility-first**.

Аналогия: обычный CSS — это шить одежду на заказ под каждого человека. Tailwind — набор готовых деталей одного стандарта: пуговицы, карманы, воротники. Собирать быстрее, и всё сочетается между собой.

### Плюсы и минусы

| Плюсы | Минусы |
| --- | --- |
| Не нужно придумывать имена классов | Длинные строки классов в разметке |
| Не нужно переключаться между файлами | Нужно время, чтобы выучить названия |
| Единая система отступов, цветов и размеров | Разметка выглядит «шумно» для новичка |
| В итоговый CSS попадают только используемые классы | Без понимания самого CSS — сложно |

<aside class="callout" data-icon="📌" markdown="1">

Tailwind не заменяет знание CSS. `flex`, `justify-between`, `p-4` — это те же `display: flex`, `justify-content: space-between`, `padding`. Если не понимаете, что делает свойство в CSS, класс Tailwind тоже не поможет.

</aside>

## Установка в проект на Vite

Актуальная версия Tailwind (v4) подключается через официальный плагин для Vite. Создаём проект и ставим пакеты:

```bash
npm create vite@latest shop -- --template react-ts
cd shop
npm install
npm install tailwindcss @tailwindcss/vite
```

Подключаем плагин в `vite.config.ts`:

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
});
```

Заменяем всё содержимое `src/index.css` одной строкой:

```css
@import "tailwindcss";
```

Проверяем в `App.tsx`:

```tsx
export default function App() {
  return <h1 className="text-3xl font-bold text-blue-600">Tailwind работает!</h1>;
}
```

Запустите `npm run dev` — заголовок станет крупным, жирным и синим.

<aside class="callout" data-icon="⚠️" markdown="1">

В старых статьях встречается установка через `npx tailwindcss init` и файл `tailwind.config.js` с директивами `@tailwind base; @tailwind components;`. Это способ третьей версии. В четвёртой конфиг-файл не нужен — достаточно плагина и `@import "tailwindcss"`. Подробности — в [официальной документации](https://tailwindcss.com/docs/installation).

</aside>

<aside class="callout" data-icon="💡" markdown="1">

Установите в редактор расширение **Tailwind CSS IntelliSense**: оно подсказывает классы, показывает их CSS при наведении и подсвечивает опечатки.

</aside>

## Основные классы

### Размеры и отступы

В Tailwind есть общая шкала: **1 единица = 0.25rem = 4px**. Поэтому `p-4` — это `padding: 1rem` (16px), а `m-2` — `margin: 0.5rem` (8px).

| Класс | CSS |
| --- | --- |
| `p-4` | `padding: 1rem` |
| `px-6` / `py-2` | padding по горизонтали / вертикали |
| `pt-2`, `pr-2`, `pb-2`, `pl-2` | padding с одной стороны |
| `m-4`, `mx-auto` | margin; `mx-auto` центрирует блок |
| `w-full` | `width: 100%` |
| `w-64` | `width: 16rem` |
| `max-w-5xl` | ограничение ширины контейнера |
| `h-screen` | `height: 100vh` |

### Текст

```html
<p class="text-sm text-gray-500">Мелкий серый текст</p>
<h2 class="text-2xl font-semibold text-gray-900">Заголовок</h2>
<p class="text-center uppercase tracking-wide">По центру, заглавными</p>
```

- `text-xs … text-6xl` — размер шрифта;
- `font-normal`, `font-medium`, `font-bold` — жирность;
- `text-gray-500` — цвет; число от 50 (очень светлый) до 950 (почти чёрный).

### Цвета, фон, рамки, тени

```html
<div class="bg-white border border-gray-200 rounded-xl shadow-md p-6">
  Карточка
</div>
```

### Flexbox и Grid

Те же принципы, что в уроке [Flexbox и :hover](lesson:flexbox-i-hover), только короче:

```html
<header class="flex items-center justify-between gap-4 p-4">
  <a href="/" class="font-bold">Logo</a>
  <nav class="flex gap-6">
    <a href="/catalog">Каталог</a>
    <a href="/cart">Корзина</a>
  </nav>
</header>

<section class="grid grid-cols-3 gap-6">
  <div>1</div>
  <div>2</div>
  <div>3</div>
</section>
```

- `flex` — `display: flex`;
- `items-center` — `align-items: center`;
- `justify-between` — `justify-content: space-between`;
- `gap-4` — расстояние между элементами;
- `grid grid-cols-3` — сетка из трёх равных колонок.

### Состояния: hover, focus, disabled

Префикс перед классом означает «применить только в этом состоянии»:

```html
<button
  class="bg-blue-600 text-white px-4 py-2 rounded-lg
         hover:bg-blue-700
         focus-visible:outline-2 focus-visible:outline-blue-400
         disabled:opacity-50 disabled:cursor-not-allowed
         transition-colors"
>
  Отправить
</button>
```

`hover:bg-blue-700` в обычном CSS выглядел бы как `.btn:hover { background: ... }`.

### Произвольные значения

Если нужного значения нет в шкале, пишите его в квадратных скобках:

```html
<div class="w-[350px] bg-[#1da1f2] top-[117px]">...</div>
```

Пользуйтесь этим редко — иначе пропадает главная польза Tailwind, единая система размеров.

## Адаптивная вёрстка

### Mobile-first

Адаптивность в Tailwind строится по принципу **mobile-first**: класс без префикса работает на всех экранах, начиная с самых маленьких, а префиксы `sm:`, `md:`, `lg:` добавляют стили **начиная с** определённой ширины.

| Префикс | Минимальная ширина | Аналог в CSS |
| --- | --- | --- |
| `sm:` | 640px (40rem) | `@media (width >= 40rem)` |
| `md:` | 768px (48rem) | `@media (width >= 48rem)` |
| `lg:` | 1024px (64rem) | `@media (width >= 64rem)` |
| `xl:` | 1280px (80rem) | `@media (width >= 80rem)` |
| `2xl:` | 1536px (96rem) | `@media (width >= 96rem)` |

Это те же медиазапросы из урока [CSS-переменные и медиазапросы](lesson:css-peremennye-i-media), только записанные прямо в классе.

```html
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">...</div>
```

Читаем: на телефоне — одна колонка, от 640px — две, от 1024px — четыре.

<aside class="callout" data-icon="⚠️" markdown="1">

Частая ошибка: думать, что `sm:` означает «на маленьких экранах». Нет! `sm:` — это «от 640px и шире». Стили для телефона пишутся **без префикса**. Если нужно «только до 768px», есть варианты `max-md:`, `max-lg:`.

</aside>

### Пример: адаптивная карточка товара и каталог

Соберём компонент карточки на React:

```tsx
// src/components/ProductCard.tsx
type Product = {
  id: number;
  title: string;
  price: number;
  image: string;
};

export function ProductCard({ product }: { product: Product }) {
  return (
    <article className="flex flex-col overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm transition hover:shadow-lg">
      <img
        src={product.image}
        alt={product.title}
        className="aspect-square w-full object-cover"
      />
      <div className="flex flex-1 flex-col gap-2 p-4">
        <h3 className="line-clamp-2 text-base font-medium text-gray-900 md:text-lg">
          {product.title}
        </h3>
        <p className="mt-auto text-xl font-bold text-gray-900">{product.price} сом</p>
        <button className="rounded-lg bg-blue-600 py-2 text-white hover:bg-blue-700">
          В корзину
        </button>
      </div>
    </article>
  );
}
```

Разбор по частям:

- `flex flex-col` — содержимое карточки идёт сверху вниз;
- `overflow-hidden rounded-2xl` — картинка не вылезает за скруглённые углы;
- `transition hover:shadow-lg` — при наведении плавно появляется тень;
- `aspect-square object-cover` — картинка всегда квадратная и не искажается;
- `flex-1` и `mt-auto` — цена и кнопка прижимаются к низу, даже если название короткое;
- `line-clamp-2` — длинное название обрезается до двух строк с многоточием;
- `text-base md:text-lg` — на компьютере текст чуть крупнее.

Теперь страница каталога с адаптивной шапкой:

```tsx
// src/App.tsx
import { useState } from "react";
import { ProductCard } from "./components/ProductCard";

const products = [
  { id: 1, title: "Беспроводные наушники", price: 3500, image: "https://placehold.co/400" },
  { id: 2, title: "Смарт-часы", price: 7200, image: "https://placehold.co/400" },
  { id: 3, title: "Портативная колонка", price: 4100, image: "https://placehold.co/400" },
  { id: 4, title: "Внешний аккумулятор", price: 1900, image: "https://placehold.co/400" },
];

export default function App() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <span className="text-xl font-bold">Shop</span>

          <button className="md:hidden" onClick={() => setMenuOpen(!menuOpen)}>
            ☰
          </button>

          <nav className="hidden gap-6 md:flex">
            <a href="#" className="hover:text-blue-600">Каталог</a>
            <a href="#" className="hover:text-blue-600">Доставка</a>
            <a href="#" className="hover:text-blue-600">Контакты</a>
          </nav>
        </div>

        {menuOpen && (
          <nav className="flex flex-col gap-2 border-t border-gray-200 px-4 py-3 md:hidden">
            <a href="#">Каталог</a>
            <a href="#">Доставка</a>
            <a href="#">Контакты</a>
          </nav>
        )}
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6 md:py-10">
        <h1 className="mb-6 text-2xl font-bold md:text-4xl">Каталог</h1>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 lg:gap-6">
          {products.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      </main>
    </div>
  );
}
```

Что происходит на разных экранах:

- **Телефон:** видна кнопка ☰ (`md:hidden` прячет её только от 768px), навигация скрыта (`hidden`), товары в одну колонку.
- **Планшет (от 640px):** товары в две колонки.
- **От 768px:** кнопка ☰ исчезает, навигация появляется (`md:flex`), заголовок крупнее.
- **Компьютер (от 1024px):** четыре колонки и увеличенные отступы между ними.

`mx-auto max-w-6xl px-4` — классический «контейнер»: контент не растягивается на огромных мониторах, стоит по центру и не прилипает к краям на телефоне.

<aside class="callout" data-icon="💡" markdown="1">

Проверяйте адаптивность в DevTools: кнопка «Toggle device toolbar» (`Ctrl+Shift+M`, на Mac — `Cmd+Shift+M`) позволяет менять ширину экрана и выбирать модели телефонов.

</aside>

## Настройка темы и тёмный режим

### Свои цвета и шрифты

В Tailwind v4 тема настраивается прямо в CSS через блок `@theme`:

```css
@import "tailwindcss";

@theme {
  --color-brand: #7c3aed;
  --color-brand-dark: #5b21b6;
  --font-display: "Montserrat", sans-serif;
}
```

После этого появляются классы `bg-brand`, `text-brand-dark`, `font-display`.

### Тёмная тема

Префикс `dark:` применяет стиль, когда у пользователя в системе включена тёмная тема:

```html
<div class="bg-white text-gray-900 dark:bg-gray-900 dark:text-gray-100">
  Текст читается в обеих темах
</div>
```

## Условные классы в React

Часто класс зависит от состояния. Не склеивайте строки вручную со множеством тернарников — используйте маленькую библиотеку `clsx`:

```bash
npm install clsx
```

```tsx
import clsx from "clsx";

type Props = { active: boolean; label: string };

export function Tab({ active, label }: Props) {
  return (
    <button
      className={clsx(
        "rounded-md px-3 py-1.5 text-sm",
        active ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-100"
      )}
    >
      {label}
    </button>
  );
}
```

<aside class="callout" data-icon="⚠️" markdown="1">

Не собирайте имена классов из кусочков: `` `bg-${color}-500` ``. Tailwind ищет классы в коде как обычный текст и не увидит `bg-red-500`, если он нигде не написан целиком — стиль просто не появится. Пишите полные имена: `color === "red" ? "bg-red-500" : "bg-green-500"`.

</aside>

## Типичные ошибки

- **Ставить `sm:` для мобильной версии.** Мобильные стили — без префикса, префиксы — для экранов шире.
- **Динамические имена классов** (`` `text-${size}` ``) — Tailwind их не найдёт.
- **Писать `class` в React.** В JSX — только `className`.
- **Злоупотреблять `[...]`.** Если везде `w-[347px]`, вы теряете единую систему.
- **Установка по старым инструкциям v3** — не нужны `tailwind.config.js` и `@tailwind base`.

## Практика

1. **Кнопки.** Сделайте три кнопки — основную, второстепенную (белая с рамкой) и опасную (красная) — с `hover:` и `disabled:`. Ожидаемый результат: при наведении цвет темнеет, отключённая кнопка полупрозрачная.
2. **Адаптивная сетка.** Выведите 8 карточек: 1 колонка на телефоне, 2 от 640px, 3 от 768px, 4 от 1280px. Ожидаемый результат: в DevTools при изменении ширины число колонок меняется.
3. **Шапка с бургер-меню.** Повторите шапку из урока, добавив закрытие меню по клику на ссылку. Ожидаемый результат: на телефоне меню открывается и закрывается, на компьютере видна обычная навигация.
4. **Своя тема.** Добавьте через `@theme` фирменный цвет и шрифт и используйте их в заголовках и кнопках. Ожидаемый результат: классы `bg-brand` и `font-display` работают.
5. **Перевёрстка проекта.** Переведите одну страницу своего проекта с CSS Modules на Tailwind. Ожидаемый результат: страница выглядит так же или лучше на ширине 375px, 768px и 1440px.

## Итоги

- Tailwind — utility-first библиотека: стили собираются из маленьких классов прямо в разметке.
- Установка v4: `tailwindcss` + `@tailwindcss/vite`, плагин в `vite.config.ts` и `@import "tailwindcss"` в CSS.
- Шкала отступов: 1 единица = 4px (`p-4` = 16px); состояния — через префиксы `hover:`, `focus-visible:`, `disabled:`.
- Адаптивность — mobile-first: класс без префикса для телефона, `sm:` `md:` `lg:` `xl:` — от заданной ширины и шире.
- Тема настраивается в CSS через `@theme`, тёмный режим — префиксом `dark:`.
- Условные классы удобно собирать через `clsx`, но имена классов всегда пишутся целиком.
