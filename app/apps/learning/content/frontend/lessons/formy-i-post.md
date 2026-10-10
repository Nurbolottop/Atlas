Формы — это главный способ, которым пользователь передаёт сайту данные: регистрация, вход, комментарий, заказ. В этом уроке разберём HTML-теги для форм (`form`, `input`, `label`, `select`, `textarea`, `button`), научимся получать и проверять введённые значения в JavaScript и отправлять их на сервер **методом POST**.

## Из чего состоит форма

### Тег form

`<form>` — контейнер для всех полей формы. Он объединяет поля в одну группу и умеет «отправляться» — по кнопке или по нажатию Enter.

```html
<form id="signup-form">
  <!-- поля формы -->
  <button type="submit">Зарегистрироваться</button>
</form>
```

### Тег input

`<input>` — поле ввода. Это одиночный тег (без закрывающего). Его вид и поведение задаёт атрибут `type`:

| `type` | Для чего | Особенность |
| --- | --- | --- |
| `text` | обычный текст | значение по умолчанию |
| `email` | email | браузер проверяет наличие `@` |
| `password` | пароль | символы скрыты точками |
| `number` | число | стрелки, `min`, `max`, `step` |
| `tel` | телефон | на телефоне открывается цифровая клавиатура |
| `checkbox` | галочка «да/нет» | значение в `checked` |
| `radio` | один вариант из нескольких | у группы одинаковый `name` |
| `date` | дата | встроенный календарь |
| `file` | загрузка файла | выбор файла с компьютера |

Важные атрибуты:

-   `name` — имя поля. По нему мы потом достаём значение. **Без `name` поле не попадёт в данные формы.**
-   `id` — уникальный идентификатор, нужен для связи с `label`.
-   `placeholder` — серая подсказка внутри пустого поля.
-   `value` — значение по умолчанию.
-   `required` — поле обязательно.
-   `minlength`, `maxlength` — ограничения длины текста.
-   `min`, `max` — ограничения для чисел и дат.
-   `pattern` — регулярное выражение для проверки (вспомните урок [про регулярные выражения](lesson:regulyarnye-vyrazheniya-rekursiya)).

### Тег label

`<label>` — подпись к полю. Его связывают с полем через атрибут `for`, равный `id` поля:

```html
<label for="email">Email</label>
<input id="email" name="email" type="email" placeholder="you@mail.com" required>
```

Зачем это нужно:

-   клик по подписи ставит курсор в поле (для чекбокса — переключает галочку);
-   программы чтения с экрана для незрячих людей озвучивают, к чему относится поле.

Можно и просто вложить поле внутрь `label` — тогда `for` не нужен:

```html
<label>
  <input type="checkbox" name="agree" required>
  Согласен с правилами
</label>
```

<aside class="callout" data-icon="⚠️" markdown="1">

`placeholder` не заменяет `label`. Подсказка исчезает, как только пользователь начинает печатать, и он может забыть, что это было за поле. У каждого поля должна быть подпись.

</aside>

### Остальные элементы

```html
<!-- Выпадающий список -->
<label for="city">Город</label>
<select id="city" name="city">
  <option value="">Выберите город</option>
  <option value="bishkek">Бишкек</option>
  <option value="osh">Ош</option>
</select>

<!-- Многострочный текст -->
<label for="about">О себе</label>
<textarea id="about" name="about" rows="4"></textarea>

<!-- Переключатели: одинаковый name — выбрать можно только один -->
<p>Уровень:</p>
<label><input type="radio" name="level" value="junior" checked> Junior</label>
<label><input type="radio" name="level" value="middle"> Middle</label>
```

-   У `<option>` атрибут `value` — то, что уйдёт в данные, а текст между тегами — то, что видит пользователь.
-   `<textarea>` — парный тег, значение пишется между тегами, а не в `value`.

### Кнопки

`<button>` внутри формы по умолчанию имеет `type="submit"` — то есть **отправляет форму**. Если нужна обычная кнопка (например, «Показать пароль»), указывайте `type="button"`:

```html
<button type="submit">Отправить</button>   <!-- отправляет форму -->
<button type="button">Показать пароль</button> <!-- просто кнопка -->
<button type="reset">Очистить</button>     <!-- сбрасывает поля -->
```

## Работа с формой в JavaScript

### Событие submit и preventDefault

Когда форма отправляется, браузер по умолчанию **перезагружает страницу** — так было принято в старых сайтах. Нам это не нужно: мы хотим обработать данные сами. Поэтому слушаем событие `submit` на форме и отменяем стандартное поведение:

```js
const form = document.querySelector("#signup-form");

form.addEventListener("submit", (event) => {
  event.preventDefault(); // не перезагружать страницу
  console.log("Форма отправлена!");
});
```

<aside class="callout" data-icon="💡" markdown="1">

Слушайте событие `submit` на форме, а не `click` на кнопке. Тогда отправка сработает и по клику, и по нажатию Enter в любом поле, и встроенная проверка `required` тоже выполнится.

</aside>

### Получаем значения полей

**Способ 1 — по одному полю через `value`:**

```js
const emailInput = document.querySelector("#email");
console.log(emailInput.value);          // строка из поля

const agree = document.querySelector('[name="agree"]');
console.log(agree.checked);             // true / false для чекбокса
```

`value` у `input` **всегда строка**, даже у `type="number"`. Чтобы получить число, используйте `Number(input.value)` или `input.valueAsNumber`.

**Способ 2 — все поля сразу через FormData:**

```js
form.addEventListener("submit", (event) => {
  event.preventDefault();

  const formData = new FormData(form);
  const data = Object.fromEntries(formData);

  console.log(data);
  // { email: "anna@mail.com", city: "bishkek", about: "...", level: "junior", agree: "on" }
});
```

-   `new FormData(form)` собирает все поля, у которых есть `name`.
-   `Object.fromEntries(...)` превращает их в обычный объект.
-   Отмеченный чекбокс даёт значение `"on"`, а неотмеченный вообще не попадает в данные.

### События полей: input и change

-   `input` срабатывает **при каждом изменении** — на каждую нажатую букву. Подходит для живого поиска и счётчика символов.
-   `change` срабатывает, когда изменение **завершено**: поле потеряло фокус, выбран вариант в `select`, переключён чекбокс.

Пусть под полем «О себе» из примера выше стоит элемент для счётчика:

```html
<small id="counter">0 / 200</small>
```

```js
const about = document.querySelector("#about");
const counter = document.querySelector("#counter");

about.addEventListener("input", () => {
  counter.textContent = `${about.value.length} / 200`;
});
```

## Проверка данных (валидация)

### Встроенная проверка браузера

Атрибуты `required`, `type="email"`, `minlength`, `pattern` браузер проверяет сам: если что-то не так, он не даст отправить форму и покажет подсказку. Это бесплатно и работает без JavaScript.

```html
<input name="phone" type="tel" placeholder="+996700123456"
       pattern="\+996\d{9}" required>
```

### Своя проверка на JavaScript

Встроенных сообщений часто недостаточно: нужно проверить, совпадают ли пароли, и показать ошибку красиво. Сделаем свою проверку:

```js
function validate(data) {
  const errors = {};

  if (data.name.trim().length < 2) {
    errors.name = "Имя должно быть не короче 2 символов";
  }
  if (!/^[\w.-]+@[\w-]+\.[a-z]{2,}$/i.test(data.email)) {
    errors.email = "Введите корректный email";
  }
  if (data.password.length < 8) {
    errors.password = "Пароль — минимум 8 символов";
  }
  if (data.password !== data.confirm) {
    errors.confirm = "Пароли не совпадают";
  }

  return errors; // пустой объект — ошибок нет
}
```

Функция возвращает объект, где ключ — имя поля, а значение — текст ошибки. Если объект пустой, всё в порядке: `Object.keys(errors).length === 0`.

<aside class="callout" data-icon="🔐" markdown="1">

Проверка в браузере — для удобства пользователя. Злоумышленник может отправить запрос напрямую, минуя вашу форму. Сервер всегда должен проверять данные заново. И никогда не храните пароли в `localStorage`.

</aside>

## Метод POST

### Чем POST отличается от GET

В уроке [про fetch и GET](lesson:fetch-async-await-get) мы **получали** данные. Чтобы **создать** что-то новое на сервере (зарегистрировать пользователя, добавить комментарий), используют метод **POST**.

| | GET | POST |
| --- | --- | --- |
| Назначение | получить данные | создать новые данные |
| Где данные | в URL (query-параметры) | в теле запроса (body) |
| Видны в адресной строке | да | нет |
| Типичный ответ | `200 OK` | `201 Created` |

### POST-запрос через fetch

Для POST в `fetch` передают второй аргумент — объект настроек:

```js
async function createPost(post) {
  const response = await fetch("https://jsonplaceholder.typicode.com/posts", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(post),
  });

  if (!response.ok) {
    throw new Error(`Ошибка ${response.status}`);
  }

  return response.json();
}

createPost({ title: "Мой первый пост", body: "Привет, мир!", userId: 1 })
  .then((created) => console.log(created));
// { title: "Мой первый пост", body: "Привет, мир!", userId: 1, id: 101 }
```

Разбор настроек:

-   `method: "POST"` — указываем метод (по умолчанию был бы GET).
-   `headers` — заголовок `Content-Type: application/json` говорит серверу: «в теле лежит JSON».
-   `body: JSON.stringify(post)` — тело запроса. Отправить можно только **строку** (или FormData), поэтому объект превращаем в JSON.
-   Сервер отвечает созданной записью с новым `id` и статусом `201`.

<aside class="callout" data-icon="📌" markdown="1">

JSONPlaceholder — тестовый сервер: он честно отвечает так, будто запись создана, но на самом деле ничего не сохраняет. Если потом запросить `/posts/101`, вы получите 404. Для учёбы этого достаточно.

</aside>

## Собираем всё вместе: форма отзыва

HTML:

```html
<form id="review-form" novalidate>
  <label for="name">Имя</label>
  <input id="name" name="name" type="text">
  <small class="error" data-error-for="name"></small>

  <label for="email">Email</label>
  <input id="email" name="email" type="email">
  <small class="error" data-error-for="email"></small>

  <label for="text">Отзыв</label>
  <textarea id="text" name="text" rows="4"></textarea>
  <small class="error" data-error-for="text"></small>

  <button type="submit">Отправить</button>
  <p id="status"></p>
</form>
```

Атрибут `novalidate` отключает встроенные подсказки браузера, потому что ошибки мы покажем сами.

JavaScript:

```js
const form = document.querySelector("#review-form");
const statusText = document.querySelector("#status");
const submitBtn = form.querySelector('button[type="submit"]');

function validateReview(data) {
  const errors = {};
  if (data.name.trim().length < 2) errors.name = "Укажите имя";
  if (!data.email.includes("@")) errors.email = "Неверный email";
  if (data.text.trim().length < 10) errors.text = "Отзыв — минимум 10 символов";
  return errors;
}

function showErrors(errors) {
  form.querySelectorAll(".error").forEach((el) => {
    el.textContent = errors[el.dataset.errorFor] ?? "";
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const data = Object.fromEntries(new FormData(form));
  const errors = validateReview(data);
  showErrors(errors);

  if (Object.keys(errors).length > 0) return; // есть ошибки — не отправляем

  submitBtn.disabled = true;
  statusText.textContent = "Отправляем...";

  try {
    const response = await fetch("https://jsonplaceholder.typicode.com/comments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...data, postId: 1 }),
    });

    if (!response.ok) throw new Error(`Ошибка ${response.status}`);

    const saved = await response.json();
    statusText.textContent = `Спасибо! Отзыв №${saved.id} отправлен.`;
    form.reset(); // очищаем поля
  } catch (error) {
    statusText.textContent = "Не удалось отправить. Попробуйте ещё раз.";
    console.error(error);
  } finally {
    submitBtn.disabled = false;
  }
});
```

Как это работает по шагам:

1.  Отменяем перезагрузку страницы через `preventDefault`.
2.  Собираем данные через `FormData` в объект.
3.  Проверяем данные; `showErrors` находит все элементы `.error` и по атрибуту `data-error-for` подставляет текст ошибки нужного поля (или очищает его).
4.  Если ошибок нет — блокируем кнопку, чтобы пользователь не отправил отзыв дважды.
5.  Отправляем POST. Через spread `{ ...data, postId: 1 }` добавляем к данным формы ещё одно поле.
6.  При успехе показываем сообщение и очищаем форму методом `form.reset()`; при ошибке — понятный текст.
7.  В `finally` разблокируем кнопку в любом случае.

## Типичные ошибки

-   **Нет `event.preventDefault()`** — страница перезагружается, данные пропадают, а запрос может не успеть уйти.
-   **У поля нет `name`** — `FormData` его не видит.
-   **Отправили объект без `JSON.stringify`** — на сервер уйдёт строка `"[object Object]"`.
-   **Забыли заголовок `Content-Type`** — сервер может не понять, что в теле JSON.
-   **Кнопка без `type` внутри формы** — неожиданно отправляет форму. Для вспомогательных кнопок пишите `type="button"`.

Справка: [MDN: элемент form](https://developer.mozilla.org/ru/docs/Web/HTML/Element/form), [MDN: FormData](https://developer.mozilla.org/ru/docs/Web/API/FormData).

## Практика

1.  **Форма входа.** Сверстайте форму с полями email и пароль, у каждого поля — `label`. При отправке без перезагрузки страницы выведите объект с данными в консоль.
2.  **Счётчик символов.** Добавьте `textarea` с ограничением 200 символов и живым счётчиком «N / 200». Когда символов больше 180, счётчик становится красным.
3.  **Регистрация с проверкой.** Форма: имя, email, пароль, повтор пароля, чекбокс согласия. Показывайте ошибки под полями и не отправляйте форму, пока они есть.
4.  **POST.** Подключите отправку формы из задания 3 на `https://jsonplaceholder.typicode.com/users` методом POST. После успеха выведите «Пользователь создан, id: …» и очистите форму. Пароль в теле запроса не отправляйте — это тестовый сервер.
5.  **Мини-блог.** Форма «заголовок + текст» отправляет POST на `/posts`, а ответ сервера сразу добавляется карточкой в начало списка постов на странице.

## Итоги

-   `form` объединяет поля, `input` с разными `type` — поля ввода, `label` — подписи, связанные через `for` и `id`.
-   У каждого поля должен быть `name` — по нему собираются данные.
-   Событие `submit` слушаем на форме и отменяем перезагрузку через `event.preventDefault()`.
-   `new FormData(form)` + `Object.fromEntries` — самый быстрый способ получить все значения.
-   Валидация в браузере удобна, но сервер обязан проверять данные сам.
-   POST создаёт данные: `method: "POST"`, заголовок `Content-Type: application/json` и `body: JSON.stringify(...)`.
