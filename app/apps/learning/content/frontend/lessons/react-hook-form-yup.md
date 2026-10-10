Формы есть почти в каждом приложении: регистрация, вход, оформление заказа, отзыв. В этом уроке посмотрим, как делать форму на чистом React и почему это быстро становится неудобно, затем перейдём на библиотеку **react-hook-form**, опишем правила проверки полей через **yup** и научимся показывать красивые всплывающие уведомления с помощью **react-toastify**.

## Форма на useState: в чём проблема

Вспомним управляемые поля из урока [useState и useEffect](lesson:usestate-i-useeffect) и сделаем форму входа с проверкой:

```jsx
import { useState } from 'react';

function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({});

  function handleSubmit(e) {
    e.preventDefault();
    const newErrors = {};
    if (!email) newErrors.email = 'Введите email';
    else if (!email.includes('@')) newErrors.email = 'Некорректный email';
    if (password.length < 8) newErrors.password = 'Минимум 8 символов';

    setErrors(newErrors);
    if (Object.keys(newErrors).length === 0) {
      console.log({ email, password });
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
      {errors.email && <p>{errors.email}</p>}
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      {errors.password && <p>{errors.password}</p>}
      <button type="submit">Войти</button>
    </form>
  );
}
```

Работает, но представьте форму регистрации на 8 полей: 8 состояний, 8 обработчиков `onChange`, длинная функция проверки, ручной сброс, флаг «отправляется»... К тому же каждое нажатие клавиши перерисовывает всю форму. Именно эти проблемы решает react-hook-form.

## Установка библиотек

Установим сразу всё, что понадобится в уроке:

```bash
npm install react-hook-form yup @hookform/resolvers react-toastify
```

| Пакет | Зачем |
| --- | --- |
| `react-hook-form` | Управляет формой: значения, ошибки, отправка, сброс |
| `yup` | Описывает правила проверки данных (схему) |
| `@hookform/resolvers` | «Переходник», который соединяет react-hook-form со схемой yup |
| `react-toastify` | Всплывающие уведомления (тосты) |

## react-hook-form: основы

Главный инструмент библиотеки — хук `useForm`. Он возвращает объект с функциями для работы с формой.

```jsx
import { useForm } from 'react-hook-form';

function LoginForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm();

  function onSubmit(data) {
    console.log(data); // { email: '...', password: '...' }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email', { required: 'Введите email' })} placeholder="Email" />
      {errors.email && <p className="error">{errors.email.message}</p>}

      <input
        type="password"
        {...register('password', {
          required: 'Введите пароль',
          minLength: { value: 8, message: 'Минимум 8 символов' },
        })}
        placeholder="Пароль"
      />
      {errors.password && <p className="error">{errors.password.message}</p>}

      <button type="submit">Войти</button>
    </form>
  );
}

export default LoginForm;
```

Разберём, что здесь происходит.

### register — регистрируем поле

`register('email')` «подключает» поле к форме под именем `email`. Функция возвращает объект со свойствами `name`, `onChange`, `onBlur` и `ref`, а `{...register('email')}` разворачивает их в атрибуты `<input>`. То есть одна строчка заменяет `value`, `onChange` и `useState`.

Вторым аргументом можно передать встроенные правила проверки:

| Правило | Пример | Что проверяет |
| --- | --- | --- |
| `required` | `required: 'Обязательное поле'` | Поле не пустое |
| `minLength` / `maxLength` | `minLength: { value: 8, message: '...' }` | Длина строки |
| `min` / `max` | `min: { value: 18, message: '...' }` | Числовое значение |
| `pattern` | `pattern: { value: /^\S+@\S+$/, message: '...' }` | Регулярное выражение |
| `validate` | `validate: checkName` | Своя функция: возвращает `true` или текст ошибки |

### handleSubmit — отправка

`handleSubmit(onSubmit)` создаёт обработчик для `<form onSubmit>`. Он сам вызывает `preventDefault`, проверяет все поля и:

-   если ошибок нет — вызывает вашу `onSubmit` с объектом **всех значений** формы;
-   если ошибки есть — `onSubmit` не вызывается, а ошибки попадают в `errors`.

### errors — ошибки

`formState.errors` — объект, где ключи — имена полей с ошибками. У каждой ошибки есть `message` — текст из правил. `errors.email?.message` — удобная запись с опциональной цепочкой.

<aside class="callout" data-icon="💡" markdown="1">

По умолчанию поля проверяются при отправке, а после первой отправки — при каждом изменении. Это можно поменять опцией `mode`: например, `useForm({ mode: 'onBlur' })` проверяет поле, когда пользователь уходит с него, а `mode: 'onTouched'` — после первого ухода с поля и далее при изменениях.

</aside>

### Что ещё умеет useForm

-   `defaultValues` (опция `useForm`) — начальные значения полей, важны для форм редактирования;
-   `reset()` — вернуть форму к начальным значениям, например после успешной отправки;
-   `watch('email')` — текущее значение поля «на лету» (для счётчика символов, силы пароля);
-   `formState.isSubmitting` — `true`, пока выполняется асинхронный `onSubmit`, удобно блокировать кнопку.

## Валидация с yup

Встроенные правила хороши для простых форм. Но когда правил много, их удобнее описать отдельно — **схемой**. Схема yup — это описание того, какими должны быть данные: «email — строка, обязательная, в формате email; возраст — число от 14 до 100».

### Пишем схему

```js
// schemas/registerSchema.js
import * as yup from 'yup';

export const registerSchema = yup.object({
  name: yup
    .string()
    .trim()
    .required('Введите имя')
    .min(2, 'Имя слишком короткое'),
  email: yup
    .string()
    .required('Введите email')
    .email('Некорректный email'),
  age: yup
    .number()
    .typeError('Введите число')
    .required('Укажите возраст')
    .min(14, 'Регистрация с 14 лет')
    .max(100, 'Проверьте возраст'),
  password: yup
    .string()
    .required('Введите пароль')
    .min(8, 'Минимум 8 символов')
    .matches(/[A-Z]/, 'Нужна хотя бы одна заглавная латинская буква')
    .matches(/\d/, 'Нужна хотя бы одна цифра'),
  confirmPassword: yup
    .string()
    .required('Повторите пароль')
    .oneOf([yup.ref('password')], 'Пароли не совпадают'),
  agree: yup
    .boolean()
    .oneOf([true], 'Нужно согласиться с правилами'),
});
```

Разбор методов:

-   `yup.object({...})` — схема объекта: каждое поле формы описано своим правилом.
-   `yup.string()`, `yup.number()`, `yup.boolean()` — тип значения.
-   `.required('текст')` — обязательное поле; в скобках сообщение об ошибке.
-   `.trim()` — убирает пробелы по краям перед проверкой.
-   `.email()` — проверка формата email.
-   `.min()` / `.max()` — для строк это длина, для чисел — значение.
-   `.typeError('Введите число')` — сообщение, если значение не превратилось в число (например, поле пустое или в нём буквы).
-   `.matches(/регулярка/, 'текст')` — проверка регулярным выражением (вспомните урок [Регулярные выражения](lesson:regulyarnye-vyrazheniya-rekursiya)).
-   `yup.ref('password')` — ссылка на значение другого поля; `.oneOf([...])` — значение должно совпасть с одним из списка. Так проверяется «повторите пароль».

### Подключаем схему к форме

```jsx
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import { registerSchema } from './schemas/registerSchema';

const { register, handleSubmit, formState: { errors } } = useForm({
  resolver: yupResolver(registerSchema),
});
```

Теперь правила в `register` писать не нужно — `register('email')` и всё. Проверкой занимается yup, а react-hook-form раскладывает его ошибки по полям.

<aside class="callout" data-icon="🔐" markdown="1">

Проверка в браузере нужна для удобства пользователя, но она **не защищает** сервер: любой может отправить запрос в обход формы. Сервер всегда должен проверять данные ещё раз сам.

</aside>

## React-toastify: уведомления

**Тост** — маленькое всплывающее сообщение в углу экрана: «Сохранено», «Ошибка сети». Оно само исчезает через несколько секунд и не мешает работе, в отличие от `alert`.

### Подключение

`ToastContainer` — «место», где будут появляться уведомления. Его добавляют **один раз** в корне приложения:

```jsx
// App.jsx
import { ToastContainer } from 'react-toastify';
import RegisterForm from './components/RegisterForm';

function App() {
  return (
    <>
      <RegisterForm />
      <ToastContainer position="top-right" autoClose={3000} />
    </>
  );
}

export default App;
```

В актуальной версии react-toastify стили подключаются автоматически. Если вы работаете со старым проектом и тосты выглядят «голыми», добавьте импорт `import 'react-toastify/dist/ReactToastify.css'`.

### Показ уведомлений

Функцию `toast` можно вызвать из любого компонента:

```jsx
import { toast } from 'react-toastify';

toast('Обычное сообщение');
toast.success('Профиль сохранён!');
toast.error('Не удалось отправить форму');
toast.info('Новая версия доступна');
toast.warning('Сессия скоро истечёт');

// с настройками для конкретного тоста
toast.success('Готово', { position: 'bottom-center', autoClose: 1500 });
```

Особенно удобен `toast.promise` — он сам показывает «загрузка», «успех» или «ошибка» в зависимости от результата Promise:

```jsx
toast.promise(saveProfile(data), {
  pending: 'Сохраняем...',
  success: 'Сохранено!',
  error: 'Ошибка сохранения',
});
```

## Собираем полную форму регистрации

Объединим всё: react-hook-form + yup + toastify + асинхронная отправка.

```jsx
// components/RegisterForm.jsx
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import { toast } from 'react-toastify';
import { registerSchema } from '../schemas/registerSchema';
import styles from './RegisterForm.module.css';

// имитация запроса на сервер
function fakeRegister(data) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (data.email === 'taken@example.com') {
        reject(new Error('Этот email уже зарегистрирован'));
      } else {
        resolve({ id: Date.now(), ...data });
      }
    }, 1500);
  });
}

function RegisterForm() {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: yupResolver(registerSchema),
    mode: 'onTouched',
    defaultValues: {
      name: '',
      email: '',
      password: '',
      confirmPassword: '',
      agree: false,
    },
  });

  async function onSubmit(data) {
    try {
      const user = await fakeRegister(data);
      toast.success(`Добро пожаловать, ${user.name}!`);
      reset();
    } catch (error) {
      toast.error(error.message);
    }
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit(onSubmit)} noValidate>
      <h2>Регистрация</h2>

      <label className={styles.field}>
        Имя
        <input {...register('name')} />
        {errors.name && <span className={styles.error}>{errors.name.message}</span>}
      </label>

      <label className={styles.field}>
        Email
        <input type="email" {...register('email')} />
        {errors.email && <span className={styles.error}>{errors.email.message}</span>}
      </label>

      <label className={styles.field}>
        Возраст
        <input type="number" {...register('age')} />
        {errors.age && <span className={styles.error}>{errors.age.message}</span>}
      </label>

      <label className={styles.field}>
        Пароль
        <input type="password" {...register('password')} />
        {errors.password && <span className={styles.error}>{errors.password.message}</span>}
      </label>

      <label className={styles.field}>
        Повторите пароль
        <input type="password" {...register('confirmPassword')} />
        {errors.confirmPassword && (
          <span className={styles.error}>{errors.confirmPassword.message}</span>
        )}
      </label>

      <label className={styles.checkbox}>
        <input type="checkbox" {...register('agree')} />
        Я согласен с правилами
      </label>
      {errors.agree && <span className={styles.error}>{errors.agree.message}</span>}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Отправляем...' : 'Зарегистрироваться'}
      </button>
    </form>
  );
}

export default RegisterForm;
```

```css
/* components/RegisterForm.module.css */
.form { max-width: 360px; margin: 40px auto; display: flex; flex-direction: column; gap: 14px; }
.field { display: flex; flex-direction: column; gap: 4px; }
.field input { padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 8px; }
.checkbox { display: flex; gap: 8px; align-items: center; }
.error { color: #dc2626; font-size: 13px; }
```

Разбор ключевых мест:

-   `resolver: yupResolver(registerSchema)` — вся проверка по схеме yup.
-   `mode: 'onTouched'` — ошибка появится, когда пользователь ушёл с поля, а не сразу при открытии формы.
-   `defaultValues` — начальные значения полей; `reset()` из `useForm` возвращает форму к ним. Поле `age` без начального значения: пустое поле не превратится в число, и yup покажет «Введите число».
-   `noValidate` на `<form>` отключает встроенные браузерные подсказки, чтобы показывались наши сообщения.
-   `onSubmit` — `async`: пока Promise не завершился, `formState.isSubmitting` равен `true`, кнопка заблокирована, и пользователь не отправит форму дважды.
-   `try/catch` — успех показываем `toast.success`, ошибку сервера — `toast.error` (повторите урок [try, catch, finally](lesson:try-catch-finally)).
-   Попробуйте зарегистрировать `taken@example.com` — увидите красный тост.

Вместо `fakeRegister` в реальном проекте будет запрос на сервер через `fetch` или axios — это сделаем в следующем уроке.

## Типичные ошибки

-   **`register` без spread.** `<input register('email') />` — ошибка синтаксиса. Нужно `{...register('email')}`.
-   **`onSubmit={onSubmit}`** вместо `onSubmit={handleSubmit(onSubmit)}` — проверка не сработает, страница перезагрузится.
-   **Имя в схеме и в `register` не совпадает** — `confirmPassword` в одном месте и `passwordConfirm` в другом. Ошибка не покажется.
-   **Забыли `ToastContainer`** — `toast.success` ничего не покажет.
-   **Два `ToastContainer`** в разных компонентах — тосты будут дублироваться.
-   **Числовое поле без `typeError`** — пользователь увидит непонятное английское сообщение yup о типе.

## Практика

1.  **Форма входа на react-hook-form.** Поля email и пароль со встроенными правилами (`required`, `pattern`, `minLength`). Ожидаемый результат: ошибки под полями, при успехе данные в консоли.
2.  **Схема yup.** Перепишите форму входа на `yupResolver`. Добавьте чекбокс «Запомнить меня» с `defaultValues: { remember: true }`.
3.  **Тосты.** При успешном входе показывайте `toast.success`, а если email равен `blocked@example.com` — `toast.error('Аккаунт заблокирован')`. Кнопка блокируется на время «запроса» (`setTimeout` на 1 секунду).
4.  **Обратная связь.** Форма «Связаться с нами»: имя (2–50 символов), телефон (регулярка для формата `+7XXXXXXXXXX`), тема (`select` с 3 вариантами, обязателен), сообщение (от 10 символов). Под полем сообщения — счётчик символов через `watch`. После отправки — `reset()` и тост.
5.  **Полная регистрация.** Повторите `RegisterForm` из урока и добавьте поле «Дата рождения» (`yup.date()` с проверкой, что пользователю есть 14 лет) и отображение силы пароля (слабый/средний/сильный) через `watch('password')`.

## Итоги

-   Формы на `useState` быстро разрастаются; react-hook-form берёт на себя значения, ошибки, отправку и сброс.
-   `useForm()` → `register` (подключить поле), `handleSubmit` (отправка с проверкой), `formState.errors` (ошибки), `reset`, `watch`, `isSubmitting`.
-   Правила удобно описывать схемой yup: `yup.object({ поле: yup.string().required() })` и подключать через `yupResolver`.
-   Полезные методы yup: `required`, `email`, `min`/`max`, `matches`, `typeError`, `oneOf([yup.ref('password')])`.
-   react-toastify: один `ToastContainer` в корне, затем `toast.success/error/info/promise` из любого места.
-   Проверка на клиенте — для удобства; сервер обязан проверять данные сам.
