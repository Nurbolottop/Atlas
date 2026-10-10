Почти любой сайт показывает списки: товары, комментарии, сообщения, задачи. В этом уроке научимся выводить массивы данных через `map`, разберёмся, зачем React нужны ключи `key`, начнём стилизовать компоненты через CSS Modules, передавать в пропсы объекты и массивы и, наконец, реагировать на действия пользователя — клики, ввод текста, отправку формы.

## Списки: выводим массив через map

В прошлом уроке мы копировали `<ProductCard />` вручную три раза. В реальности данные приходят с сервера массивом, и мы не знаем заранее, сколько там элементов. Решение — метод `map`, который вы знаете из урока [Методы перебора массива](lesson:metody-perebora-massiva).

`map` превращает каждый элемент массива в новый. А React умеет показывать **массив JSX-элементов**. Значит, можно превратить массив данных в массив разметки:

```jsx
const fruits = ['Яблоко', 'Банан', 'Апельсин'];

function FruitList() {
  return (
    <ul>
      {fruits.map((fruit) => (
        <li key={fruit}>{fruit}</li>
      ))}
    </ul>
  );
}
```

Результат в браузере:

```html
<ul>
  <li>Яблоко</li>
  <li>Банан</li>
  <li>Апельсин</li>
</ul>
```

Разбор:

-   `{fruits.map(...)}` — фигурные скобки, потому что внутри JavaScript.
-   `(fruit) => (<li>...</li>)` — стрелочная функция с круглыми скобками сразу возвращает JSX.
-   `key={fruit}` — уникальный ключ для каждого элемента списка. Про него — ниже.

### Список объектов

Чаще всего в массиве лежат объекты:

```jsx
const users = [
  { id: 1, name: 'Айгерим', role: 'Дизайнер' },
  { id: 2, name: 'Данияр', role: 'Frontend-разработчик' },
  { id: 3, name: 'Мария', role: 'Тестировщик' },
];

function Team() {
  return (
    <div>
      <h2>Наша команда</h2>
      {users.map((user) => (
        <div key={user.id} className="member">
          <h3>{user.name}</h3>
          <p>{user.role}</p>
        </div>
      ))}
    </div>
  );
}
```

### filter + map

Методы можно соединять в цепочку. Например, показать только товары в наличии:

```jsx
const products = [
  { id: 1, title: 'Ноутбук', price: 350000, inStock: true },
  { id: 2, title: 'Планшет', price: 180000, inStock: false },
  { id: 3, title: 'Телефон', price: 220000, inStock: true },
];

function AvailableProducts() {
  const available = products.filter((p) => p.inStock);

  if (available.length === 0) {
    return <p>Товаров нет в наличии</p>;
  }

  return (
    <ul>
      {available.map((p) => (
        <li key={p.id}>
          {p.title} — {p.price.toLocaleString('ru-RU')} ₸
        </li>
      ))}
    </ul>
  );
}
```

Обратите внимание на проверку пустого списка — хороший интерфейс всегда показывает понятное сообщение, а не пустоту.

## Ключи (key): зачем они нужны

Если убрать `key`, в консоли появится предупреждение: *Each child in a list should have a unique "key" prop*. Зачем React это нужно?

Представьте гардероб в театре. Пальто вешают на крючки с номерками. Если гость уйдёт, гардеробщик по номерку точно знает, какое пальто снять — и не перевешивает все остальные. **key — это номерок** для элемента списка. Когда список меняется (элемент добавили, удалили, переставили), React по ключам понимает, какой элемент какой, и обновляет только нужное.

### Правила ключей

1.  Ключ **уникален среди соседей** в одном списке (в разных списках ключи могут повторяться).
2.  Ключ **стабилен** — у одного и того же элемента он не меняется между рендерами.
3.  Ключ ставится на **внешний** элемент, который возвращает `map`, а не внутри него.
4.  Лучший ключ — `id` из данных (из базы данных, с сервера).

### Почему индекс — плохой ключ

Возникает соблазн написать так:

```jsx
{todos.map((todo, index) => (
  <li key={index}>{todo.text}</li> // ⚠️ плохо, если список меняется
))}
```

Пока список не меняется, всё работает. Но если удалить первый элемент, у всех остальных индексы сдвинутся: бывший второй станет «нулевым». React решит, что удалили *последний* элемент, а у остальных просто поменялся текст. Если внутри элементов есть поля ввода или чекбоксы, введённые данные «перепрыгнут» на соседние строки.

<aside class="callout" data-icon="⚠️" markdown="1">

Индекс в качестве ключа допустим только для статичных списков, которые никогда не сортируются, не фильтруются и из которых ничего не удаляется. Во всех остальных случаях используйте `id`. Не генерируйте ключ через `Math.random()` прямо в `map` — ключ будет новым при каждом рендере, и React будет пересоздавать все элементы.

</aside>

### Ключ на компоненте

Если элемент списка — ваш компонент, ключ ставится на сам компонент:

```jsx
{users.map((user) => (
  <UserCard key={user.id} name={user.name} role={user.role} />
))}
```

`key` — служебный атрибут для React, внутрь компонента он **не передаётся**. Если `id` нужен внутри, передайте его отдельным пропсом: `id={user.id}`.

## Передача объектных типов через пропсы

### Объект целиком

Вместо того чтобы передавать каждое поле отдельно, можно передать весь объект одним пропсом:

```jsx
function UserCard({ user }) {
  return (
    <div className="card">
      <img src={user.avatar} alt={user.name} width={64} />
      <h3>{user.name}</h3>
      <p>{user.email}</p>
      <p>Город: {user.address.city}</p>
    </div>
  );
}

const user = {
  id: 1,
  name: 'Айгерим',
  email: 'aigerim@example.com',
  avatar: 'https://placehold.co/64',
  address: { city: 'Алматы', street: 'Абая, 10' },
};

// использование
<UserCard user={user} />
```

### Разворачивание объекта через spread

Если поля объекта совпадают с названиями пропсов, объект можно «развернуть» оператором `...`:

```jsx
function ProductCard({ title, price, inStock }) {
  return (
    <div>
      <h3>{title}</h3>
      <p>{price} ₸</p>
      <p>{inStock ? 'В наличии' : 'Нет в наличии'}</p>
    </div>
  );
}

{products.map((product) => (
  <ProductCard key={product.id} {...product} />
))}
```

`{...product}` — то же самое, что `title={product.title} price={product.price} inStock={product.inStock} id={product.id}`.

| Способ | Пример | Плюсы | Минусы |
| --- | --- | --- | --- |
| Отдельные пропсы | `title={p.title} price={p.price}` | Явно видно, что передаём | Много кода |
| Объект целиком | `product={p}` | Коротко, удобно для вложенных данных | Не видно, какие поля используются |
| Spread | `{...p}` | Очень коротко | Можно случайно передать лишнее |

### Массив через пропсы

Массив передаётся так же, как объект — в фигурных скобках. Внутри компонента его можно перебрать через `map`:

```jsx
function TagList({ tags }) {
  return (
    <div className="tags">
      {tags.map((tag) => (
        <span key={tag} className="tag">#{tag}</span>
      ))}
    </div>
  );
}

<TagList tags={['react', 'javascript', 'frontend']} />
```

<aside class="callout" data-icon="⚠️" markdown="1">

Если данные приходят с сервера, поле может отсутствовать. Код `user.address.city` упадёт, если `address` нет. Используйте опциональную цепочку `user.address?.city` и значения по умолчанию: `function TagList({ tags = [] })`.

</aside>

## CSS Modules

### Проблема обычного CSS

Обычный CSS-файл действует на всю страницу. Если в `Header.css` и `Card.css` есть класс `.title`, стили перемешаются, и какой победит — зависит от порядка подключения. В большом проекте это постоянная головная боль.

**CSS Modules** решают проблему: классы из такого файла действуют **только на тот компонент**, который его импортировал. Vite поддерживает их из коробки — ничего устанавливать не нужно.

### Как пользоваться

1.  Назовите файл с суффиксом `.module.css`, например `Card.module.css`.
2.  Импортируйте его как объект: `import styles from './Card.module.css'`.
3.  Используйте классы как свойства объекта: `className={styles.card}`.

```css
/* components/Card.module.css */
.card {
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
}

.title {
  margin: 0 0 8px;
  font-size: 20px;
}

.price {
  color: #16a34a;
  font-weight: 700;
}
```

```jsx
// components/Card.jsx
import styles from './Card.module.css';

function Card({ title, price }) {
  return (
    <div className={styles.card}>
      <h3 className={styles.title}>{title}</h3>
      <p className={styles.price}>{price} ₸</p>
    </div>
  );
}

export default Card;
```

Откройте DevTools — у элемента будет класс вроде `_card_1x2ab_1`. Vite добавил к имени уникальный «хвост», поэтому класс `.title` из другого модуля с ним никогда не пересечётся.

### Несколько классов и условные классы

`className` — просто строка, поэтому классы склеивают шаблонной строкой:

```jsx
import styles from './Button.module.css';

function Button({ text, variant = 'primary', disabled = false }) {
  const className = `${styles.button} ${styles[variant]} ${disabled ? styles.disabled : ''}`;

  return <button className={className} disabled={disabled}>{text}</button>;
}
```

```css
/* Button.module.css */
.button { padding: 8px 16px; border: none; border-radius: 8px; cursor: pointer; }
.primary { background: #2563eb; color: white; }
.danger { background: #dc2626; color: white; }
.disabled { opacity: 0.5; cursor: not-allowed; }
```

-   `styles[variant]` — доступ через квадратные скобки: если `variant = 'danger'`, получим `styles.danger`. Так же обращаются к классам с дефисом: `styles['card-title']` (поэтому классы удобнее называть в camelCase).
-   Тернарник добавляет класс `disabled` только когда нужно.

Глобальные стили (сброс отступов, шрифт для `body`) по-прежнему держите в обычном `index.css`, подключённом в `main.jsx`.

## Обработчики событий

### Как подписаться на событие

В DOM мы писали `addEventListener`. В React обработчик передаётся прямо в JSX атрибутом в camelCase: `onClick`, `onChange`, `onSubmit`, `onMouseEnter`, `onKeyDown`.

```jsx
function AlertButton() {
  function handleClick() {
    alert('Вы нажали на кнопку!');
  }

  return <button onClick={handleClick}>Нажми</button>;
}
```

Обработчики принято называть `handleЧтоТо`: `handleClick`, `handleSubmit`, `handleDelete`.

<aside class="callout" data-icon="⚠️" markdown="1">

Самая частая ошибка: `onClick={handleClick()}`. Скобки **вызывают** функцию сразу при рендере, а в `onClick` попадает её результат (`undefined`). Нужно передать саму функцию: `onClick={handleClick}`.

</aside>

### Передача аргумента в обработчик

Если нужно передать данные (например, `id` товара), оберните вызов в стрелочную функцию:

```jsx
function ProductList({ products }) {
  function handleBuy(title) {
    alert(`Товар «${title}» добавлен в корзину`);
  }

  return (
    <ul>
      {products.map((p) => (
        <li key={p.id}>
          {p.title}
          <button onClick={() => handleBuy(p.title)}>Купить</button>
        </li>
      ))}
    </ul>
  );
}
```

`() => handleBuy(p.title)` — новая функция, которая вызовет `handleBuy` только при клике.

### Объект события

React передаёт в обработчик объект события `event` (часто пишут `e`) — почти такой же, как в обычном DOM:

```jsx
function SearchInput() {
  function handleChange(e) {
    console.log('Введено:', e.target.value);
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') {
      console.log('Нажат Enter');
    }
  }

  return <input onChange={handleChange} onKeyDown={handleKeyDown} placeholder="Поиск..." />;
}
```

-   `e.target` — элемент, на котором произошло событие; `e.target.value` — текст в поле.
-   В React `onChange` срабатывает **на каждый введённый символ** (в обычном DOM событие `change` — только при потере фокуса).

### Отправка формы

При отправке формы браузер по умолчанию перезагружает страницу. Отменяем это через `e.preventDefault()`:

```jsx
function SubscribeForm() {
  function handleSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const email = formData.get('email');
    alert(`Подписка оформлена на ${email}`);
  }

  return (
    <form onSubmit={handleSubmit}>
      <input name="email" type="email" required placeholder="Email" />
      <button type="submit">Подписаться</button>
    </form>
  );
}
```

`onSubmit` вешается на `<form>`, а не на кнопку — так форма отправится и по клику, и по Enter.

### Обработчик как проп

Функцию можно передать в дочерний компонент через пропсы. Так ребёнок «сообщает» родителю о событии:

```jsx
function TodoItem({ todo, onDelete }) {
  return (
    <li>
      {todo.text}
      <button onClick={() => onDelete(todo.id)}>Удалить</button>
    </li>
  );
}

function TodoList() {
  const todos = [
    { id: 1, text: 'Выучить JSX' },
    { id: 2, text: 'Разобраться с пропсами' },
  ];

  function handleDelete(id) {
    console.log('Удалить задачу с id', id);
  }

  return (
    <ul>
      {todos.map((todo) => (
        <TodoItem key={todo.id} todo={todo} onDelete={handleDelete} />
      ))}
    </ul>
  );
}
```

Разбор цепочки:

1.  Родитель `TodoList` описывает, *что делать* при удалении, — `handleDelete`.
2.  Передаёт функцию ребёнку пропсом `onDelete` (пропсы-события принято называть `onЧтоТо`).
3.  Ребёнок `TodoItem` вызывает её при клике и передаёт свой `id`.

Пока задача только выводится в консоль: чтобы она действительно исчезала со страницы, нужно **состояние** — это тема урока [useState и useEffect](lesson:usestate-i-useeffect).

## Типичные ошибки

-   Нет `key` в списке или `key` стоит не на внешнем элементе `map`.
-   `key={index}` в списке, который меняется, или `key={Math.random()}`.
-   `map` с фигурными скобками без `return`: `items.map((i) => { <li>{i}</li> })` вернёт массив `undefined`. Используйте `() => (...)` или явный `return`.
-   Импорт `import './Card.module.css'` без имени — классы не применятся. Нужно `import styles from ...`.
-   `onClick={handleClick()}` вместо `onClick={handleClick}`.
-   Забыли `e.preventDefault()` в `onSubmit` — страница перезагружается.

## Практика

1.  **Список городов.** Выведите массив из 6 городов списком `<ul>`. Ожидаемый результат: список без предупреждений о ключах в консоли.
2.  **Каталог.** Создайте массив из 6 товаров (`id`, `title`, `price`, `category`, `inStock`). Выведите их компонентом `ProductCard`, передавая объект через spread. Товары не в наличии показывайте с серой надписью «Нет в наличии».
3.  **CSS Modules.** Оформите `ProductCard` через `ProductCard.module.css`. Добавьте карточкам, у которых `inStock = false`, дополнительный класс `outOfStock` с прозрачностью 0.5.
4.  **События.** Добавьте в карточку кнопку «В корзину», которая через проп `onAddToCart` сообщает родителю `id` товара; родитель выводит в консоль `Добавлен товар: <название>`. Ожидаемый результат: в консоли название нажатого товара.
5.  **Форма поиска.** Сделайте форму с полем и кнопкой «Найти». При отправке (без перезагрузки страницы) выводите в консоль все товары, в названии которых есть введённый текст (без учёта регистра).

## Итоги

-   Списки выводятся через `array.map(item => <Component />)`, можно комбинировать с `filter`.
-   Каждому элементу списка нужен уникальный и стабильный `key`, лучше всего `id`; индекс — только для статичных списков.
-   В пропсы можно передавать объекты (`user={user}`), массивы и разворачивать объект через `{...obj}`.
-   CSS Modules (`*.module.css`) изолируют классы внутри компонента: `className={styles.card}`.
-   Обработчики пишутся в camelCase (`onClick`), передаётся сама функция, а для аргументов — стрелка `() => fn(id)`.
-   Функцию-обработчик можно передать ребёнку пропсом `onЧтоТо`, чтобы он сообщал родителю о событиях.
