В прошлом уроке все компоненты жили в одном файле и всегда показывали одно и то же. Теперь научимся раскладывать компоненты по отдельным файлам, импортировать и экспортировать их, а главное — передавать в них данные через **пропсы**. В конце подключим Ant Design — готовую библиотеку красивых компонентов, чтобы не верстать каждую кнопку с нуля.

## Компоненты в отдельных файлах

Когда компонентов становится десяток, держать их в `App.jsx` неудобно: файл разрастается, трудно найти нужное. Правило простое: **один компонент — один файл**, имя файла совпадает с именем компонента.

```text
src/
├── components/
│   ├── Header.jsx
│   ├── Footer.jsx
│   └── UserCard.jsx
├── App.jsx
└── main.jsx
```

Создадим `src/components/Header.jsx`:

```jsx
function Header() {
  return (
    <header className="header">
      <h1>Atlas Shop</h1>
    </header>
  );
}

export default Header;
```

И используем его в `App.jsx`:

```jsx
import Header from './components/Header.jsx';

function App() {
  return (
    <>
      <Header />
      <p>Добро пожаловать в магазин!</p>
    </>
  );
}

export default App;
```

## Import и export компонентов

Вы уже встречали модули в JavaScript. В React они используются постоянно. Есть два вида экспорта.

### Экспорт по умолчанию (default)

В файле может быть **только один** `export default`. При импорте имя можно выбрать любое, фигурные скобки не нужны.

```jsx
// Footer.jsx
export default function Footer() {
  return <footer>© 2026</footer>;
}
```

```jsx
// App.jsx
import Footer from './components/Footer.jsx';
import MyFooter from './components/Footer.jsx'; // тоже сработает — это тот же компонент
```

### Именованный экспорт (named)

Таких экспортов в файле может быть сколько угодно. Импортировать нужно **в фигурных скобках и точно по имени**.

```jsx
// components/Buttons.jsx
export function PrimaryButton() {
  return <button className="btn btn-primary">Купить</button>;
}

export function SecondaryButton() {
  return <button className="btn">Подробнее</button>;
}
```

```jsx
// App.jsx
import { PrimaryButton, SecondaryButton } from './components/Buttons.jsx';
import { PrimaryButton as BuyButton } from './components/Buttons.jsx'; // переименование через as
```

| | `export default` | `export` (именованный) |
| --- | --- | --- |
| Сколько в файле | Один | Сколько угодно |
| Импорт | `import Header from './Header'` | `import { Header } from './Header'` |
| Имя при импорте | Любое | Точно как при экспорте (или через `as`) |
| Когда удобно | Один главный компонент в файле | Несколько мелких компонентов или утилит |

<aside class="callout" data-icon="💡" markdown="1">

В проектах на Vite расширение `.jsx` при импорте можно не писать: `import Header from './components/Header'`. Главное — правильный относительный путь: `./` — текущая папка, `../` — на уровень выше.

</aside>

<aside class="callout" data-icon="⚠️" markdown="1">

Частая ошибка: экспортировали как `export default Header`, а импортируете `import { Header } from ...` — получите `undefined` и ошибку в консоли. И наоборот. Смотрите, как именно экспортирован компонент.

</aside>

## Пропсы: передаём данные в компонент

Представьте карточку пользователя. Если имя написано прямо внутри, каждая карточка будет одинаковой. Нам же нужна одна «форма» карточки, в которую подставляются разные данные. Для этого существуют **пропсы** (от англ. *properties* — свойства).

Аналогия: функция и её аргументы. Компонент — функция, пропсы — аргументы. Передаются пропсы как атрибуты тега:

```jsx
<UserCard name="Айгерим" age={21} city="Алматы" />
```

React соберёт все атрибуты в один объект и передаст его первым аргументом в функцию:

```jsx
// components/UserCard.jsx
function UserCard(props) {
  console.log(props); // { name: 'Айгерим', age: 21, city: 'Алматы' }

  return (
    <div className="user-card">
      <h3>{props.name}</h3>
      <p>Возраст: {props.age}</p>
      <p>Город: {props.city}</p>
    </div>
  );
}

export default UserCard;
```

```jsx
// App.jsx
import UserCard from './components/UserCard';

function App() {
  return (
    <div>
      <UserCard name="Айгерим" age={21} city="Алматы" />
      <UserCard name="Данияр" age={25} city="Астана" />
      <UserCard name="Мария" age={19} city="Шымкент" />
    </div>
  );
}

export default App;
```

Один компонент — три разные карточки.

### Деструктуризация пропсов

Писать `props.` каждый раз утомительно. Поэтому пропсы почти всегда **деструктурируют** прямо в параметрах (вспомните урок [Деструктуризация, spread, rest](lesson:destrukturizaciya-spread-rest)):

```jsx
function UserCard({ name, age, city }) {
  return (
    <div className="user-card">
      <h3>{name}</h3>
      <p>Возраст: {age}</p>
      <p>Город: {city}</p>
    </div>
  );
}
```

Это ровно то же самое, только короче и сразу видно, какие пропсы ожидает компонент.

### Значения по умолчанию

Если проп не передали, он будет `undefined`. Значение по умолчанию задаётся прямо в деструктуризации:

```jsx
function Button({ text = 'Нажми меня', color = 'blue' }) {
  return <button style={{ background: color, color: 'white' }}>{text}</button>;
}

// <Button />                       → «Нажми меня», синяя
// <Button text="Отправить" />       → «Отправить», синяя
// <Button text="Удалить" color="red" /> → «Удалить», красная
```

### Какие типы можно передавать

Строки передают в кавычках, всё остальное — в фигурных скобках:

```jsx
<Product
  title="Ноутбук"              // строка
  price={350000}               // число
  inStock={true}               // логическое значение
  isNew                        // то же, что isNew={true}
  tags={['новинка', 'хит']}    // массив
  onBuy={() => alert('Куплено!')} // функция
/>
```

<aside class="callout" data-icon="⚠️" markdown="1">

`price="350000"` — это строка, а `price={350000}` — число. Разница важна: `"350000" + 1` даст `"3500001"`. Числа и логические значения передавайте только в `{}`.

</aside>

Передачу объектов и массивов подробно разберём в уроке [Списки, ключи и CSS Modules](lesson:spiski-klyuchi-css-modules).

### Пропсы только для чтения

Компонент **не может менять** свои пропсы. Данные идут сверху вниз — от родителя к ребёнку, как вода по трубам. Если ребёнку нужно что-то изменить, это делает родитель (как именно — узнаем в уроке про `useState`).

```jsx
function Price({ value }) {
  value = value * 2; // ❌ так делать нельзя: пропсы — только для чтения
  return <span>{value}</span>;
}

function PriceWithTax({ value }) {
  const withTax = value * 1.12; // ✅ создаём новую переменную
  return <span>{withTax.toFixed(0)} ₸</span>;
}
```

### Специальный проп children

Иногда в компонент хочется передать не просто данные, а целый кусок разметки — как в обычный тег `<div>...</div>`. Всё, что вы пишете **между** открывающим и закрывающим тегом компонента, попадает в проп `children`.

```jsx
// components/Card.jsx
function Card({ title, children }) {
  return (
    <div style={{ border: '1px solid #ddd', borderRadius: 12, padding: 16 }}>
      <h3>{title}</h3>
      <div>{children}</div>
    </div>
  );
}

export default Card;
```

```jsx
<Card title="О нас">
  <p>Мы делаем лучшие сайты в городе.</p>
  <button>Связаться</button>
</Card>

<Card title="Контакты">
  <p>Телефон: +7 700 000 00 00</p>
</Card>
```

`Card` — это «рамка», а содержимое каждый раз своё. Так делают модальные окна, макеты страниц, секции.

### Композиция: компоненты внутри компонентов

Большой интерфейс собирают из маленьких частей, передавая данные вниз по дереву:

```jsx
function Avatar({ src, size = 64 }) {
  return <img src={src} width={size} height={size} style={{ borderRadius: '50%' }} alt="" />;
}

function UserInfo({ name, role }) {
  return (
    <div>
      <strong>{name}</strong>
      <p>{role}</p>
    </div>
  );
}

function Comment({ author, avatar, role, text }) {
  return (
    <div style={{ display: 'flex', gap: 12 }}>
      <Avatar src={avatar} size={48} />
      <div>
        <UserInfo name={author} role={role} />
        <p>{text}</p>
      </div>
    </div>
  );
}
```

`Comment` получает все данные и раздаёт нужные части детям: `Avatar` получает только картинку, `UserInfo` — имя и роль. Каждый маленький компонент легко переиспользовать в другом месте.

## Ant Design: готовые компоненты

Верстать с нуля кнопки, модальные окна, таблицы, выпадающие списки — долго. Поэтому существуют **UI-библиотеки** — наборы готовых красивых компонентов. Одна из самых популярных — [Ant Design](https://ant.design/) (сокращённо antd). Она особенно хороша для админок и личных кабинетов: таблицы, формы, меню, уведомления.

### Установка

```bash
npm install antd
```

Стили antd подключаются автоматически — отдельно импортировать CSS не нужно. Для иконок есть отдельный пакет:

```bash
npm install @ant-design/icons
```

<aside class="callout" data-icon="💡" markdown="1">

Если в консоли браузера появилось предупреждение о совместимости antd с вашей версией React, откройте раздел документации Ant Design про React 19 — там описано, что делать для вашей версии antd. Обычно хватает обновить antd до последней версии.

</aside>

### Первые компоненты

```jsx
import { Button, Space } from 'antd';
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons';

function App() {
  return (
    <Space>
      <Button type="primary" icon={<PlusOutlined />}>
        Добавить
      </Button>
      <Button>Обычная</Button>
      <Button type="dashed">Пунктирная</Button>
      <Button danger icon={<DeleteOutlined />}>
        Удалить
      </Button>
      <Button type="primary" loading>
        Загрузка
      </Button>
    </Space>
  );
}

export default App;
```

Разбор:

-   `import { Button, Space } from 'antd'` — компоненты antd импортируются именованным импортом.
-   `type="primary"` — проп, который меняет вид кнопки. Видите? Компоненты antd настраиваются **теми же пропсами**, что мы только что изучили.
-   `icon={<PlusOutlined />}` — в проп можно передать даже JSX-элемент.
-   `danger`, `loading` — логические пропсы без значения (то же, что `danger={true}`).
-   `Space` — обёртка, которая ставит одинаковые отступы между детьми.

### Карточка товара на antd

Соберём собственный компонент на основе компонентов antd:

```jsx
// components/ProductCard.jsx
import { Card, Button, Tag, Typography } from 'antd';
import { ShoppingCartOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

function ProductCard({ title, price, image, isNew = false }) {
  return (
    <Card
      hoverable
      style={{ width: 260 }}
      cover={<img src={image} alt={title} />}
    >
      {isNew && <Tag color="green">Новинка</Tag>}
      <Title level={4}>{title}</Title>
      <Text strong>{price.toLocaleString('ru-RU')} ₸</Text>
      <div style={{ marginTop: 12 }}>
        <Button type="primary" icon={<ShoppingCartOutlined />} block>
          В корзину
        </Button>
      </div>
    </Card>
  );
}

export default ProductCard;
```

```jsx
// App.jsx
import { Flex } from 'antd';
import ProductCard from './components/ProductCard';

function App() {
  return (
    <Flex gap={16} wrap style={{ padding: 24 }}>
      <ProductCard title="Наушники" price={45000} image="https://placehold.co/260x180" isNew />
      <ProductCard title="Клавиатура" price={32000} image="https://placehold.co/260x180" />
      <ProductCard title="Мышь" price={12000} image="https://placehold.co/260x180" />
    </Flex>
  );
}

export default App;
```

Что нового:

-   `Card` с пропом `cover` — картинка сверху, `hoverable` — тень при наведении.
-   `Typography` — набор компонентов для текста; `Title level={4}` — это `h4`.
-   `price.toLocaleString('ru-RU')` превратит `45000` в `45 000` с пробелами.
-   `block` растягивает кнопку на всю ширину.
-   `Flex` — компонент-обёртка на основе flexbox: `gap` — отступ, `wrap` — перенос.

### Своя тема через ConfigProvider

Хотите поменять основной цвет во всём приложении? Оберните приложение в `ConfigProvider`:

```jsx
// main.jsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { ConfigProvider } from 'antd';
import ruRU from 'antd/locale/ru_RU';
import App from './App';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ConfigProvider
      locale={ruRU}
      theme={{ token: { colorPrimary: '#7c3aed', borderRadius: 10 } }}
    >
      <App />
    </ConfigProvider>
  </StrictMode>
);
```

-   `theme.token.colorPrimary` — главный цвет: все `primary`-кнопки станут фиолетовыми.
-   `locale={ruRU}` — русские надписи во встроенных компонентах (например, в календаре или пагинации).

Все компоненты и их пропсы описаны в документации на ant.design — там у каждого компонента есть живые примеры, которые можно скопировать.

## Типичные ошибки

-   **Путают default и named импорт** — компонент оказывается `undefined`, React падает с ошибкой «Element type is invalid».
-   **Передают число строкой** — `age="21"` вместо `age={21}`.
-   **Опечатка в имени пропса** — передали `titel`, а читаете `title`. Ошибки не будет, просто ничего не выведется. Проверяйте через `console.log(props)`.
-   **Пытаются изменить проп** внутри компонента. Пропсы — только для чтения.
-   **Забывают импортировать** компонент antd или иконку — ошибка «Button is not defined».

## Практика

1.  **Разложить по файлам.** Вынесите `Header`, `Footer` и `Main` из прошлого урока в папку `src/components`, каждый в свой файл с `export default`. Ожидаемый результат: `App.jsx` содержит только импорты и сборку страницы.
2.  **Карточка пользователя.** Сделайте компонент `UserCard` с пропсами `name`, `age`, `email` и `avatar` (по умолчанию — картинка-заглушка). Выведите в `App` три разные карточки. Ожидаемый результат: одна функция — три разных пользователя.
3.  **Обёртка `Section`.** Создайте компонент `Section` с пропом `title` и `children`. Оберните им блоки «О нас», «Услуги», «Контакты». Ожидаемый результат: одинаковое оформление секций с разным содержимым.
4.  **Именованный экспорт.** Создайте файл `Badges.jsx` с компонентами `SuccessBadge`, `ErrorBadge`, `InfoBadge` (каждый принимает `text`). Импортируйте все три одной строкой.
5.  **Ant Design.** Установите `antd` и `@ant-design/icons`. Сделайте страницу «Каталог» из 4–6 `ProductCard` на компонентах `Card`, `Tag`, `Button`, `Typography`. Поменяйте основной цвет через `ConfigProvider`. Ожидаемый результат: сетка аккуратных карточек в цветах вашей темы.

## Итоги

-   Один компонент — один файл; папка `components` для переиспользуемых частей.
-   `export default` — один на файл, импорт без скобок; именованный `export` — много на файл, импорт в `{}` точно по имени.
-   Пропсы — данные от родителя к ребёнку, передаются как атрибуты и приходят одним объектом.
-   Пропсы деструктурируют в параметрах, можно задавать значения по умолчанию; менять их нельзя.
-   `children` — всё, что лежит между тегами компонента.
-   Ant Design даёт готовые компоненты (`Button`, `Card`, `Space`, `Flex`, `Typography`), которые настраиваются пропсами, а тема задаётся через `ConfigProvider`.
