Картинку на страницу можно поставить двумя способами: тегом `<img>` в HTML или свойством `background-image` в CSS. Снаружи результат похож, но смысл и возможности у них разные, и выбор неправильного способа — частая ошибка новичков. В этом уроке разберём оба способа подробно, научимся управлять фоном и обрезкой картинок, а затем соберём страницу, где используем все стили, пройденные за месяц.

## Два способа показать картинку

```html
<!-- Способ 1: картинка — часть содержимого -->
<img src="images/cat.jpg" alt="Рыжий кот спит на диване">

<!-- Способ 2: картинка — оформление блока -->
<div class="banner"></div>
```

```css
.banner {
  height: 300px;
  background-image: url("../images/pattern.jpg");
}
```

Главный вопрос, который нужно себе задать: **если картинку убрать, потеряет ли пользователь информацию?**

-   Да (фото товара, портрет автора, схема в статье) — это **контент**, используйте `<img>`.
-   Нет (декоративный узор, фоновая фотография под заголовком, текстура) — это **оформление**, используйте `background-image`.

Аналогия: `<img>` — это фотография в рамке, которую вы повесили на стену, она важна сама по себе. `background-image` — это обои: они делают комнату красивее, но смысла не несут.

## Тег img: возможности

С тегом `<img>` вы уже знакомы. Вспомним главное и добавим новое.

```html
<img
    class="product-photo"
    src="images/sneakers.jpg"
    alt="Белые кроссовки, вид сбоку"
    width="600"
    height="600"
    loading="lazy"
>
```

-   `alt` описывает картинку для поисковиков и незрячих пользователей;
-   `width`/`height` задают пропорции, чтобы страница не прыгала при загрузке;
-   `loading="lazy"` откладывает загрузку картинок ниже первого экрана.

### object-fit: как картинка заполняет рамку

Допустим, у всех карточек товаров место под фото 300×200px, а сами фото разных пропорций: одни квадратные, другие вытянутые. Если просто задать размеры, картинки **сплющатся**:

```css
.product-photo {
  width: 300px;
  height: 200px;
  object-fit: cover;
  object-position: center;
}
```

| Значение `object-fit` | Что происходит |
| --- | --- |
| `fill` | Растянуть под размер, пропорции ломаются (по умолчанию) |
| `contain` | Вписать целиком, могут остаться пустые поля |
| `cover` | Заполнить рамку целиком, лишнее обрезается по краям |
| `none` | Показать в исходном размере, лишнее обрезать |

`object-position` говорит, какую часть оставить при обрезке: `center`, `top`, `left bottom` и т. д. Для портретов часто ставят `top`, чтобы не обрезать голову.

## background-image: возможности

### Подключение

```css
.hero {
  background-image: url("../images/hero.jpg");
}
```

Путь в `url()` считается **от CSS-файла**, как и у шрифтов. Если стиль лежит в `css/style.css`, а картинка в `images/`, нужен `../`.

<aside class="callout" data-icon="⚠️" markdown="1">

У блока с фоном должен быть размер. Пустой `div` имеет высоту 0, и фон просто не видно. Задайте `height`/`min-height` или положите внутрь содержимое с отступами.

</aside>

### background-size: размер фона

```css
.hero {
  background-image: url("../images/hero.jpg");
  background-size: cover;
}
```

| Значение | Что делает |
| --- | --- |
| `auto` | Исходный размер картинки (по умолчанию) |
| `cover` | Покрыть весь блок, лишнее обрежется |
| `contain` | Вписать целиком, могут остаться пустые места |
| `200px 100px` | Точная ширина и высота |
| `50%` | Ширина фона — половина ширины блока |

`cover` и `contain` работают так же, как у `object-fit`.

### background-position: где стоит фон

```css
.hero {
  background-position: center;        /* по центру */
  background-position: right bottom;  /* в правом нижнем углу */
  background-position: 20px 50%;      /* 20px слева, по центру по вертикали */
}
```

### background-repeat: повторение

По умолчанию маленькая картинка **повторяется плиткой** на весь блок. Это удобно для узоров, но обычно не нужно для фотографий:

```css
.pattern  { background-repeat: repeat; }     /* плитка во все стороны */
.stripe   { background-repeat: repeat-x; }   /* только по горизонтали */
.photo    { background-repeat: no-repeat; }  /* один раз */
```

### Сокращённая запись

```css
.hero {
  background: #1a202c url("../images/hero.jpg") center / cover no-repeat;
}
```

Порядок: цвет, картинка, позиция `/` размер, повтор. Размер пишется **только через слеш после позиции**. Цвет показывается, пока картинка грузится или если она не загрузилась — указывайте его всегда, чтобы белый текст не оказался на белом фоне.

### Затемнение фона градиентом

На яркой фотографии текст читается плохо. Решение — положить поверх полупрозрачный градиент. Фонов можно указать несколько через запятую, **первый рисуется сверху**:

```css
.hero {
  background-image:
    linear-gradient(rgb(0 0 0 / 60%), rgb(0 0 0 / 30%)),
    url("../images/hero.jpg");
  background-size: cover;
  background-position: center;
}
```

`linear-gradient` — плавный переход цветов. Здесь от чёрного с 60% непрозрачности сверху к 30% снизу. Сам по себе градиент тоже может быть фоном: `background-image: linear-gradient(to right, #3182ce, #805ad5);`.

## Сравнение img и background-image

| | `<img>` | `background-image` |
| --- | --- | --- |
| Где задаётся | В HTML | В CSS |
| Смысл | Контент | Оформление |
| Альтернативный текст `alt` | Есть | Нет |
| Видят поисковики | Да | Нет |
| Ленивая загрузка `loading="lazy"` | Есть | Нет |
| Текст поверх картинки | Нужно позиционирование | Просто пишем текст внутри блока |
| Несколько слоёв и градиенты | Нет | Да |
| Сохранить правой кнопкой «Сохранить картинку как» | Да | Нет |
| Обрезка под рамку | `object-fit` | `background-size` |
| Меняется в медиазапросах | Только через `<picture>` | Легко, одной строкой в CSS |

<aside class="callout" data-icon="📌" markdown="1">

Правило выбора: контент — `<img>` с `alt`; оформление, под которым лежит текст, — `background-image`. Если сомневаетесь, выбирайте `<img>`: так картинка доступнее и лучше индексируется.

</aside>

## Собираем страницу из всего пройденного

Сверстаем небольшую страницу магазина: hero с фоновой фотографией, сетка карточек товаров с `<img>` и подвал. Здесь будут все темы месяца: семантические теги, подключение CSS и шрифтов, каскад, блочная модель, `position`, Flexbox, `:hover`, оба способа вставки картинок.

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sneaker Shop</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <section class="hero">
        <h1 class="hero-title">Новая коллекция</h1>
        <p class="hero-text">Лёгкие кроссовки на каждый день</p>
        <a class="btn" href="#catalog">Смотреть</a>
    </section>

    <main class="container" id="catalog">
        <h2 class="section-title">Каталог</h2>
        <div class="cards">
            <article class="card">
                <span class="card-badge">NEW</span>
                <img class="card-image" src="images/sneakers-1.jpg" alt="Белые кроссовки" width="600" height="600">
                <h3 class="card-title">Air Light</h3>
                <p class="card-price">5 900 сом</p>
            </article>
            <article class="card">
                <img class="card-image" src="images/sneakers-2.jpg" alt="Чёрные беговые кроссовки" width="600" height="400">
                <h3 class="card-title">Runner Pro</h3>
                <p class="card-price">7 200 сом</p>
            </article>
            <article class="card">
                <img class="card-image" src="images/sneakers-3.jpg" alt="Синие кеды" width="400" height="600">
                <h3 class="card-title">City Blue</h3>
                <p class="card-price">4 500 сом</p>
            </article>
        </div>
    </main>

    <footer class="footer">
        <p>&copy; 2026 Sneaker Shop</p>
    </footer>
</body>
</html>
```

```css
/* Сброс и база */
*,
*::before,
*::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: "Inter", Arial, sans-serif;
  color: #1a202c;
  background-color: #f7fafc;
}

img {
  max-width: 100%;
  display: block;
}

/* Hero с фоновой картинкой */
.hero {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 70vh;
  padding: 2rem 1rem;
  text-align: center;
  color: white;
  background-color: #1a202c;
  background-image:
    linear-gradient(rgb(0 0 0 / 55%), rgb(0 0 0 / 55%)),
    url("../images/hero.jpg");
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

.hero-title {
  font-size: 3rem;
  margin: 0 0 1rem;
}

.hero-text {
  font-size: 1.25rem;
  margin: 0 0 2rem;
}

/* Кнопка */
.btn {
  display: inline-block;
  padding: 0.875rem 2rem;
  border-radius: 999px;
  background-color: #3182ce;
  color: white;
  font-weight: 600;
  text-decoration: none;
  transition: background-color 0.2s ease;
}

.btn:hover {
  background-color: #2b6cb0;
}

/* Каталог */
.container {
  max-width: 1140px;
  margin: 0 auto;
  padding: 4rem 1rem;
}

.section-title {
  font-size: 2rem;
  margin: 0 0 2rem;
}

.cards {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
}

.card {
  position: relative;
  flex: 1 1 280px;
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  background-color: white;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgb(0 0 0 / 10%);
}

.card-image {
  width: 100%;
  height: 240px;
  object-fit: cover;
  border-radius: 12px;
}

.card-badge {
  position: absolute;
  top: 1.5rem;
  left: 1.5rem;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  background-color: tomato;
  color: white;
  font-size: 0.75rem;
  font-weight: 700;
}

.card-title {
  margin: 1rem 0 0.25rem;
  font-size: 1.25rem;
}

.card-price {
  margin: 0;
  font-weight: 700;
  color: #3182ce;
}

/* Подвал */
.footer {
  padding: 2rem 1rem;
  text-align: center;
  color: #a0aec0;
  background-color: #1a202c;
}
```

### Разбор ключевых мест

-   **Hero** — фоновая фотография через `background-image`: это оформление, а смысл несут заголовок и текст поверх. Градиент затемняет фото, `background-color` подстрахует, если картинка не загрузится. Flexbox с `flex-direction: column` и `align-items: center` ставит содержимое по центру.
-   **Фото товаров** — через `<img>`: это контент, у каждой картинки свой `alt`. Пропорции у фото разные, но `object-fit: cover` с фиксированной высотой 240px делает все карточки ровными.
-   **Бейдж** — `position: absolute` внутри `.card` с `position: relative`. Отступ `1.5rem` = padding карточки (`1rem`) + небольшой отступ внутри картинки.
-   **Карточки** — `flex: 1 1 280px` и `flex-wrap: wrap`: на широком экране три в ряд, на узком переносятся.
-   **Каскад** — общие стили заданы `body` и наследуются, а у `.hero` свой `color: white`, потому что правило по классу сильнее унаследованного значения.

## Типичные ошибки

-   Фон не виден — у блока нет высоты или неверный путь в `url()` (считается от CSS-файла).
-   Фон повторяется плиткой — забыли `background-repeat: no-repeat`.
-   Фото товаров сплющены — нет `object-fit: cover` при заданных `width` и `height`.
-   Важная картинка (фото товара, схема) вставлена фоном — поисковики и незрячие пользователи её «не увидят».
-   Белый текст на светлом фото — добавьте затемняющий градиент и `background-color`.

Справочник: [MDN: background](https://developer.mozilla.org/ru/docs/Web/CSS/background) и [MDN: object-fit](https://developer.mozilla.org/ru/docs/Web/CSS/object-fit).

## Практика

1.  **Сравнение.** Выведите одну и ту же фотографию двумя способами: `<img>` и `div` с `background-image` одинакового размера 400×250px. Попробуйте `object-fit: cover` и `background-size: cover`. Результат: обе картинки выглядят одинаково, но только первую можно «Сохранить как».
2.  **Узор.** Сделайте блок с маленькой картинкой-узором, повторяющейся плиткой, и второй блок с той же картинкой, повторяющейся только по горизонтали. Результат: видна разница `repeat` и `repeat-x`.
3.  **Hero с затемнением.** Сделайте первый экран на `min-height: 100vh` с фоновой фотографией, градиентом и центрированным текстом. Результат: текст хорошо читается на любом участке фото.
4.  **Магазин.** Повторите страницу из урока, добавив ещё три карточки и `:hover` у заголовка карточки. Результат: шесть ровных карточек с фото разных пропорций, бейдж держится в углу своей карточки.
5.  **Своя страница.** Придумайте тему (кафе, портфолио, путешествия) и сверстайте страницу из 4 секций с использованием всех пройденных тем. Для каждой картинки осознанно выберите `<img>` или фон. Результат: страница и короткое объяснение выбора для каждой картинки.

## Итоги

-   `<img>` — для контента, `background-image` — для оформления.
-   `object-fit: cover` обрезает `<img>` под рамку без искажений.
-   `background-size`, `background-position`, `background-repeat` управляют фоном; сокращение — `background`.
-   Несколько фонов перечисляют через запятую, первый — сверху; градиент затемняет фото под текстом.
-   Блоку с фоном нужен размер, а путь в `url()` считается от CSS-файла.
-   Реальная страница — это комбинация семантики, блочной модели, Flexbox, позиционирования и картинок.
