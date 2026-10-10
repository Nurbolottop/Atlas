В реальной работе фронтендер почти никогда не придумывает интерфейс сам: дизайнер рисует макет в Figma, а разработчик превращает его в код. В этом уроке научимся читать макет — находить размеры, отступы, цвета и шрифты, — разберём, что такое UI-kit и дизайн-система, и соберём собственную библиотеку компонентов в Storybook, где каждую кнопку и поле можно посмотреть и потрогать отдельно от приложения.

## Figma: как читать макет

### Что такое Figma

**Figma** — онлайн-редактор интерфейсов, в котором работает большинство дизайнеров. Обычно вам присылают ссылку на файл с правом просмотра. Ставить ничего не нужно: Figma открывается в браузере, есть и приложение для компьютера.

Из чего состоит макет:

| Понятие в Figma | Что это | Аналог в коде |
| --- | --- | --- |
| **Page** | Страница файла (вкладки слева сверху) | Раздел проекта |
| **Frame** | Рамка-экран, например «Главная — Desktop 1440» | Страница или блок |
| **Layer** | Любой элемент: текст, прямоугольник, иконка | HTML-элемент |
| **Group** | Просто сгруппированные слои | Обёртка без стилей |
| **Auto Layout** | Рамка, которая сама раскладывает детей в ряд или колонку | `display: flex` |
| **Component** | Повторяющийся элемент (кнопка, карточка) | React-компонент |
| **Variant** | Вариант компонента: primary/secondary, S/M/L | Пропсы компонента |
| **Variables / Styles** | Сохранённые цвета, шрифты, отступы | CSS-переменные, токены |

### Режим разработчика и инспектор

Справа в Figma находится панель свойств. Когда вы кликаете по элементу, там видны его размеры, цвета, шрифт и скругления. В **Dev Mode** (переключатель `</>` на верхней панели; доступность зависит от тарифа команды) панель показывает свойства сразу в виде CSS.

<aside class="callout" data-icon="⚠️" markdown="1">

Не копируйте CSS из Figma целиком. Там будут абсолютные координаты, лишние `position: absolute`, точные `width` в пикселях. Берите **значения** (цвет, размер шрифта, отступ), а саму вёрстку пишите своими руками — через flex, grid и относительные размеры.

</aside>

### Как узнать отступы

Самый полезный приём: выделите элемент и, удерживая `Alt` (на Mac — `Option`), наведите мышь на соседний элемент. Figma покажет красные линии с расстоянием в пикселях.

Если элемент лежит внутри **Auto Layout**, отступы видны прямо в панели свойств:

```text
Auto Layout в Figma            →  CSS
Direction: horizontal          →  display: flex; flex-direction: row;
Gap between items: 16          →  gap: 16px;
Padding: 12 24                 →  padding: 12px 24px;
Alignment: center              →  align-items: center;
Width: Fill container          →  flex: 1  (или width: 100%)
Width: Hug contents            →  ширина по содержимому (по умолчанию)
Width: Fixed 320               →  width: 320px
```

### Типографика и цвета

Кликните по тексту — увидите шрифт, размер, жирность, межстрочный интервал (line height) и межбуквенный интервал (letter spacing):

```text
Inter · Semi Bold · 24 / 32 · -0.5%
```

Это читается так: шрифт Inter, жирность 600, размер 24px, высота строки 32px, letter-spacing −0.5%.

```css
.title {
  font-family: "Inter", sans-serif;
  font-weight: 600;
  font-size: 24px;
  line-height: 32px;
  letter-spacing: -0.005em;
}
```

Если в макете есть **сохранённые стили или переменные** (например, `Primary/500` или `Heading/H2`), переносите их в CSS-переменные — это и есть **дизайн-токены**: именованные значения, которые используются везде.

```css
:root {
  --color-primary-500: #2563eb;
  --color-gray-900: #111827;
  --radius-md: 8px;
  --space-4: 16px;
}
```

### Картинки и иконки

Чтобы скачать иконку или картинку, выделите её и в самом низу панели свойств найдите блок **Export**: выберите формат (SVG для иконок, PNG/WebP для фото, `2x` — для чётких экранов) и нажмите Export. Как подключать картинки, разбирали в уроке [Шрифты и картинки](lesson:shrifty-i-kartinki).

### Чек-лист перед вёрсткой макета

1. Посмотрите все фреймы: какие есть экраны и **брейкпоинты** (Desktop 1440, Tablet 768, Mobile 375).
2. Найдите страницу с UI-kit или компонентами — обычно дизайнер собирает кнопки, поля и цвета отдельно.
3. Выпишите цвета, шрифты, отступы — вынесите их в CSS-переменные.
4. Найдите повторяющиеся элементы — это будущие компоненты.
5. Непонятные состояния (hover, ошибка поля, пустой список, загрузка) уточните у дизайнера **до** начала работы.

## UI-kit и дизайн-система

**UI-kit** — набор базовых компонентов интерфейса в едином стиле: кнопки, поля ввода, чекбоксы, модальные окна, бейджи. **Дизайн-система** — это UI-kit плюс правила: токены, принципы, документация «когда какую кнопку использовать».

Аналогия: UI-kit — это детали конструктора одной серии, а дизайн-система — ещё и инструкция, как их правильно соединять.

Зачем свой UI-kit, если есть готовые библиотеки вроде Ant Design (урок [Компоненты, пропсы и Ant Design](lesson:komponenty-i-propsy))? Потому что у продукта свой дизайн. Компоненты из Figma нужно один раз аккуратно сверстать и потом переиспользовать по всему проекту — в FSD они живут в слое `shared/ui` (урок [Архитектура проектов](lesson:arhitektura-proektov-fsd)).

### Компонент Button из макета

Допустим, в Figma у кнопки есть варианты: `variant` = primary / secondary / danger, `size` = sm / md, состояние disabled. Переводим это в пропсы:

```tsx
// src/shared/ui/Button/Button.tsx
import type { ComponentProps } from "react";
import styles from "./Button.module.css";

export type ButtonProps = ComponentProps<"button"> & {
  variant?: "primary" | "secondary" | "danger";
  size?: "sm" | "md";
};

export function Button({
  variant = "primary",
  size = "md",
  className = "",
  ...rest
}: ButtonProps) {
  return (
    <button
      className={`${styles.button} ${styles[variant]} ${styles[size]} ${className}`}
      {...rest}
    />
  );
}
```

```css
/* src/shared/ui/Button/Button.module.css */
.button {
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s;
}
.button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sm { padding: 6px 12px; font-size: 14px; }
.md { padding: 10px 20px; font-size: 16px; }

.primary { background: var(--color-primary-500); color: #fff; }
.primary:hover:not(:disabled) { background: #1d4ed8; }

.secondary { background: #fff; color: var(--color-gray-900); border-color: #d1d5db; }
.secondary:hover:not(:disabled) { background: #f3f4f6; }

.danger { background: #dc2626; color: #fff; }
.danger:hover:not(:disabled) { background: #b91c1c; }
```

Разбор:

- `ComponentProps<"button">` — наша кнопка принимает все обычные атрибуты `<button>`: `onClick`, `type`, `disabled`, `aria-label`;
- `variant` и `size` — ровно те варианты, что нарисованы в Figma; литеральные типы не дадут передать несуществующий `variant="green"`;
- `...rest` передаёт остальные пропсы настоящему `<button>`, а `children` попадает туда же;
- стили описаны через CSS Modules (урок [Списки, ключи и CSS Modules](lesson:spiski-klyuchi-css-modules)), но то же самое можно сделать и на Tailwind.

## Storybook: витрина компонентов

### Что это и зачем

**Storybook** — инструмент, который запускает ваши компоненты **отдельно от приложения** на специальной странице-витрине. Для каждого компонента вы пишете **истории** (stories) — примеры состояний: «основная кнопка», «отключённая», «маленькая».

Зачем это нужно:

- видно все состояния компонента сразу, не нужно кликать по приложению, чтобы дойти до ошибки в форме;
- дизайнер и тестировщик могут проверить компоненты без запуска бэкенда;
- автоматически генерируется документация;
- новый разработчик за минуту видит, какие компоненты уже есть.

Аналогия: приложение — это ресторан, а Storybook — витрина с образцами блюд. Каждое блюдо видно отдельно, его можно рассмотреть со всех сторон.

### Установка

В корне React-проекта на Vite выполните:

```bash
npm create storybook@latest
```

Мастер установки сам определит React и Vite, поставит пакеты, создаст папку `.storybook` с настройками и примеры историй в `src/stories`. После установки запуск:

```bash
npm run storybook
```

Витрина откроется по адресу `http://localhost:6006`. Примеры из `src/stories` можно удалить, когда разберётесь.

<aside class="callout" data-icon="💡" markdown="1">

Если в проекте есть глобальные стили или CSS-переменные (`index.css`), импортируйте их в файл `.storybook/preview.ts` — иначе компоненты в Storybook будут выглядеть без ваших токенов: `import "../src/index.css";`.

</aside>

### Первая история

Рядом с компонентом создаём файл `Button.stories.tsx`:

```tsx
// src/shared/ui/Button/Button.stories.tsx
import type { Meta, StoryObj } from "@storybook/react-vite";
import { fn } from "storybook/test";
import { Button } from "./Button";

const meta = {
  title: "UI/Button",
  component: Button,
  tags: ["autodocs"],
  args: {
    children: "Кнопка",
    onClick: fn(),
  },
  argTypes: {
    variant: { control: "select", options: ["primary", "secondary", "danger"] },
    size: { control: "radio", options: ["sm", "md"] },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: { variant: "primary" },
};

export const Secondary: Story = {
  args: { variant: "secondary" },
};

export const Danger: Story = {
  args: { variant: "danger", children: "Удалить" },
};

export const Small: Story = {
  args: { size: "sm" },
};

export const Disabled: Story = {
  args: { disabled: true },
};
```

Разбираем по частям:

- `meta` — общая информация о компоненте. `title: "UI/Button"` задаёт место в меню Storybook (папка UI, пункт Button);
- `component: Button` — какой компонент показываем;
- `tags: ["autodocs"]` — Storybook сам сгенерирует страницу документации со всеми пропсами и их типами;
- `args` — пропсы по умолчанию для всех историй. `fn()` создаёт «шпиона»: при клике в панели **Actions** будет видно, что `onClick` сработал;
- `argTypes` — какие элементы управления показать: выпадающий список для `variant`, радиокнопки для `size`;
- `satisfies Meta<typeof Button>` — проверка TypeScript: объект должен соответствовать формату Storybook, а пропсы — компоненту;
- каждый `export const` — отдельная история со своими `args`.

В витрине внизу есть панель **Controls**: там можно менять пропсы на лету — переключать `variant`, вводить текст `children`, ставить `disabled` — и сразу видеть результат.

<aside class="callout" data-icon="📌" markdown="1">

Названия пакетов Storybook менялись между версиями. В актуальных версиях типы для React + Vite импортируются из `@storybook/react-vite`, а `fn` — из `storybook/test`. Если в старой статье видите `@storybook/react` или `@storybook/test`, сверяйтесь с [официальной документацией](https://storybook.js.org/docs).

</aside>

### История для поля ввода

```tsx
// src/shared/ui/Input/Input.tsx
import type { ComponentProps } from "react";
import styles from "./Input.module.css";

type InputProps = ComponentProps<"input"> & {
  label: string;
  error?: string;
};

export function Input({ label, error, id, ...rest }: InputProps) {
  const inputId = id ?? label;
  return (
    <div className={styles.field}>
      <label htmlFor={inputId}>{label}</label>
      <input id={inputId} className={error ? styles.invalid : ""} {...rest} />
      {error && <span className={styles.error}>{error}</span>}
    </div>
  );
}
```

```tsx
// src/shared/ui/Input/Input.stories.tsx
import type { Meta, StoryObj } from "@storybook/react-vite";
import { Input } from "./Input";

const meta = {
  title: "UI/Input",
  component: Input,
  tags: ["autodocs"],
  args: { label: "Email", placeholder: "you@example.com" },
} satisfies Meta<typeof Input>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const WithError: Story = {
  args: { value: "abc", error: "Некорректный email", readOnly: true },
};
```

История `WithError` показывает состояние ошибки, до которого в приложении пришлось бы добираться, заполняя форму. Стили `Input.module.css` (классы `field`, `invalid`, `error`) напишите сами по макету.

## Типичные ошибки

- **Пиксель-в-пиксель через `position: absolute`.** Макет надо повторить визуально, но вёрстка должна оставаться гибкой.
- **Цвета «на глаз».** Всегда берите HEX/RGB из инспектора и выносите в переменные.
- **Компонент «под одну страницу».** Кнопка из UI-kit не должна знать про корзину или пользователя — только внешний вид и пропсы.
- **Истории только для «красивого» состояния.** Самое полезное в Storybook — ошибки, загрузка, длинный текст, отключённое состояние.
- **Забыли подключить глобальные стили** в `.storybook/preview.ts` — компоненты выглядят «голыми».

## Практика

1. **Разбор макета.** Откройте любой бесплатный макет из сообщества Figma (Community) и выпишите: брейкпоинты, 5 цветов, 3 стиля текста, отступы карточки. Ожидаемый результат: список токенов в виде CSS-переменных `:root { ... }`.
2. **Кнопка.** Сверстайте `Button` из урока с тремя вариантами и двумя размерами. Ожидаемый результат: TypeScript ругается на `variant="green"`.
3. **Storybook.** Установите Storybook и напишите истории для `Button`. Ожидаемый результат: на `localhost:6006` видны 5 историй, а в Controls можно переключать варианты и видеть клики в Actions.
4. **Поле ввода и бейдж.** Добавьте компоненты `Input` (с состоянием ошибки) и `Badge` (цвета success / warning / error) с историями. Ожидаемый результат: страница autodocs показывает все пропсы.
5. **Мини UI-kit.** Соберите в `shared/ui` 5–6 компонентов (Button, Input, Badge, Card, Modal, Spinner) по одному макету и используйте их на странице своего проекта. Ожидаемый результат: в приложении нет «самодельных» кнопок и полей мимо UI-kit.

## Итоги

- Макет в Figma состоит из фреймов, слоёв и компонентов; Auto Layout — это flex.
- Отступы смотрим с зажатым `Alt`/`Option`, свойства — в панели справа или в Dev Mode; берём значения, а не готовый CSS.
- Цвета, шрифты и отступы выносим в CSS-переменные — дизайн-токены.
- UI-kit — набор базовых компонентов в едином стиле; варианты из Figma становятся пропсами.
- Storybook показывает компоненты отдельно от приложения; устанавливается через `npm create storybook@latest`.
- История — это компонент с конкретными `args`; `autodocs`, Controls и Actions дают документацию и интерактив бесплатно.
