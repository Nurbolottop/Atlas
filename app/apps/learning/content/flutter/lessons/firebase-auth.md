Почти каждому приложению нужен вход в аккаунт: чтобы сохранять избранные города, синхронизировать данные между устройствами и отправлять персональные уведомления. Писать свой сервер авторизации долго и рискованно, поэтому многие команды берут готовый сервис Firebase Authentication. В этом уроке подключим Firebase к Flutter-проекту через FlutterFire CLI, сделаем регистрацию и вход по email и паролю, выстроим логику «вошёл / не вошёл» на Bloc и разберёмся, что такое токен и как отправить его на свой сервер.

## Что такое Firebase

**Firebase** — набор облачных сервисов от Google для мобильных и веб-приложений: авторизация, базы данных, push-уведомления, хранилище файлов, аналитика. Вы не поднимаете свой сервер — подключаете SDK и пользуетесь готовым.

**Firebase Authentication** отвечает за пользователей: хранит их, проверяет пароли, выдаёт токены, отправляет письма для сброса пароля. Поддерживает вход по email, телефону, через Google, Apple и другие способы.

Аналогия: Firebase Auth — это охрана на входе в бизнес-центр. Она проверяет паспорт (пароль) и выдаёт пропуск (токен). Дальше вы показываете пропуск на каждом этаже, а не паспорт.

## Подключение через FlutterFire CLI

Раньше Firebase подключали вручную: скачивали `google-services.json` для Android, `GoogleService-Info.plist` для iOS и правили конфиги Gradle. Сейчас всё это делает **FlutterFire CLI** одной командой.

### Шаг 1. Проект в консоли Firebase

1. Откройте консоль Firebase (console.firebase.google.com) и войдите в Google-аккаунт.
2. Нажмите «Создать проект», введите название, например `weather-app`.

### Шаг 2. Инструменты

```bash
# Firebase CLI (нужен Node.js)
npm install -g firebase-tools
firebase login

# FlutterFire CLI
dart pub global activate flutterfire_cli
```

- `firebase login` откроет браузер для входа в Google-аккаунт.
- Если после установки команда `flutterfire` не находится, добавьте в `PATH` папку `$HOME/.pub-cache/bin` (терминал подскажет точный путь).

### Шаг 3. Конфигурация

В корне Flutter-проекта:

```bash
flutter pub add firebase_core firebase_auth
flutterfire configure
```

`flutterfire configure` спросит, какой Firebase-проект использовать и для каких платформ (Android, iOS, web), сам зарегистрирует приложения в консоли и создаст файл `lib/firebase_options.dart` с настройками.

<aside class="callout" data-icon="📌" markdown="1">

Запускайте `flutterfire configure` заново каждый раз, когда добавляете новую платформу или новый сервис Firebase (например, Crashlytics). Файл `firebase_options.dart` перезапишется с актуальными настройками.

</aside>

### Шаг 4. Инициализация в main

```dart
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'firebase_options.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  runApp(const App());
}
```

Разбор:

- `main` стал `async`, потому что инициализация Firebase асинхронная.
- `WidgetsFlutterBinding.ensureInitialized()` — обязательный вызов перед любой работой с платформой до `runApp`. Без него приложение упадёт на старте.
- `DefaultFirebaseOptions.currentPlatform` — настройки из сгенерированного файла для текущей платформы.

<aside class="callout" data-icon="🔐" markdown="1">

`apiKey` в `firebase_options.dart` — это не секрет, а идентификатор проекта: он всё равно попадает в сборку приложения. Защищают данные не им, а правилами безопасности (Security Rules) и App Check. Но сервисные ключи Admin SDK (JSON-файл сервисного аккаунта) в приложение и в Git класть нельзя никогда.

</aside>

### Шаг 5. Включаем способ входа

В консоли Firebase: **Authentication → Sign-in method → Email/Password → Включить**. Без этого любые попытки входа вернут ошибку `operation-not-allowed`.

## Основные методы FirebaseAuth

Всё начинается с `FirebaseAuth.instance` — единственного объекта авторизации в приложении.

| Метод / поле | Что делает |
| --- | --- |
| `createUserWithEmailAndPassword(email:, password:)` | Регистрация, сразу выполняет вход |
| `signInWithEmailAndPassword(email:, password:)` | Вход |
| `signOut()` | Выход |
| `sendPasswordResetEmail(email:)` | Письмо для сброса пароля |
| `currentUser` | Текущий пользователь или `null` |
| `authStateChanges()` | Поток: присылает `User?` при входе и выходе |
| `idTokenChanges()` | Поток: ещё и при обновлении токена |

Firebase **сам хранит сессию** на устройстве. Закрыли и открыли приложение — пользователь по-прежнему вошёл, ничего сохранять вручную не нужно.

## Репозиторий авторизации

Как и с сетью, не вызываем Firebase из виджетов напрямую. Делаем репозиторий, который прячет детали и переводит ошибки на человеческий язык:

```dart
import 'package:firebase_auth/firebase_auth.dart';

class AuthFailure implements Exception {
  AuthFailure(this.message);
  final String message;
  @override
  String toString() => message;
}

class AuthRepository {
  AuthRepository({FirebaseAuth? auth}) : _auth = auth ?? FirebaseAuth.instance;

  final FirebaseAuth _auth;

  Stream<User?> get user => _auth.authStateChanges();

  User? get currentUser => _auth.currentUser;

  Future<void> signUp(String email, String password) =>
      _guard(() => _auth.createUserWithEmailAndPassword(email: email, password: password));

  Future<void> signIn(String email, String password) =>
      _guard(() => _auth.signInWithEmailAndPassword(email: email, password: password));

  Future<void> signOut() => _auth.signOut();

  Future<void> _guard(Future<Object?> Function() action) async {
    try {
      await action();
    } on FirebaseAuthException catch (e) {
      throw AuthFailure(_message(e.code));
    }
  }

  String _message(String code) => switch (code) {
        'invalid-email' => 'Неверный формат email.',
        'email-already-in-use' => 'Этот email уже зарегистрирован.',
        'weak-password' => 'Слишком простой пароль (минимум 6 символов).',
        'invalid-credential' || 'wrong-password' || 'user-not-found' =>
          'Неверный email или пароль.',
        'user-disabled' => 'Аккаунт заблокирован.',
        'too-many-requests' => 'Слишком много попыток. Подождите немного.',
        'network-request-failed' => 'Нет подключения к интернету.',
        _ => 'Ошибка авторизации ($code).',
      };
}
```

Разбор:

- `FirebaseAuth? auth` в конструкторе — можно подставить подделку в тестах, а по умолчанию берётся настоящий `FirebaseAuth.instance`.
- `_guard` — общая обёртка: выполняет действие и ловит `FirebaseAuthException`. Так не нужно дублировать `try/catch` в каждом методе.
- `e.code` — короткий код ошибки. По нему выбираем понятное сообщение.

<aside class="callout" data-icon="💡" markdown="1">

В новых проектах Firebase по умолчанию включена защита от перебора email (email enumeration protection). Поэтому при неверном пароле или несуществующем пользователе чаще приходит один общий код `invalid-credential`, а не `wrong-password` и `user-not-found`. Это нормально и даже безопаснее: злоумышленник не узнает, зарегистрирован ли email.

</aside>

## Логика авторизации на Bloc

### Состояние

Приложению важно знать одно: вошёл пользователь или нет. Плюс есть короткий момент при запуске, когда это ещё неизвестно.

```dart
import 'package:equatable/equatable.dart';
import 'package:firebase_auth/firebase_auth.dart';

sealed class AuthState extends Equatable {
  const AuthState();
  @override
  List<Object?> get props => [];
}

final class AuthUnknown extends AuthState {
  const AuthUnknown();
}

final class AuthAuthenticated extends AuthState {
  const AuthAuthenticated(this.user);
  final User user;
  @override
  List<Object?> get props => [user.uid];
}

final class AuthUnauthenticated extends AuthState {
  const AuthUnauthenticated();
}
```

### Cubit, подписанный на поток

```dart
import 'dart:async';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

class AuthCubit extends Cubit<AuthState> {
  AuthCubit(this._repo) : super(const AuthUnknown()) {
    _sub = _repo.user.listen((user) {
      emit(user == null ? const AuthUnauthenticated() : AuthAuthenticated(user));
    });
  }

  final AuthRepository _repo;
  late final StreamSubscription<User?> _sub;

  Future<void> signOut() => _repo.signOut();

  @override
  Future<void> close() {
    _sub.cancel();
    return super.close();
  }
}
```

Главная идея: Cubit не решает сам «вошёл или нет» — он **слушает** Firebase. Вошли через форму, вышли кнопкой, сессия истекла — `authStateChanges()` пришлёт новое значение, и состояние обновится само. В `close()` обязательно отменяем подписку.

### Форма входа — отдельный Cubit

Ошибки и загрузка формы не должны смешиваться с глобальным состоянием «вошёл / не вошёл». Сделаем маленький Cubit для формы:

```dart
enum FormStatus { idle, loading, error }

class LoginState extends Equatable {
  const LoginState({this.status = FormStatus.idle, this.error});
  final FormStatus status;
  final String? error;
  @override
  List<Object?> get props => [status, error];
}

class LoginCubit extends Cubit<LoginState> {
  LoginCubit(this._repo) : super(const LoginState());
  final AuthRepository _repo;

  Future<void> submit(String email, String password, {bool register = false}) async {
    emit(const LoginState(status: FormStatus.loading));
    try {
      register
          ? await _repo.signUp(email.trim(), password)
          : await _repo.signIn(email.trim(), password);
      emit(const LoginState());
    } on AuthFailure catch (e) {
      emit(LoginState(status: FormStatus.error, error: e.message));
    }
  }
}
```

После успешного входа `LoginCubit` ничего не делает с навигацией — `AuthCubit` сам получит пользователя из потока.

### Переключение экранов

```dart
class AuthGate extends StatelessWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AuthCubit, AuthState>(
      builder: (context, state) => switch (state) {
        AuthUnknown() => const Scaffold(body: Center(child: CircularProgressIndicator())),
        AuthAuthenticated() => const WeatherPage(),
        AuthUnauthenticated() => BlocProvider(
            create: (context) => LoginCubit(context.read<AuthRepository>()),
            child: const LoginPage(),
          ),
      },
    );
  }
}
```

`AuthGate` ставится в `home` у `MaterialApp`, а `AuthRepository` и `AuthCubit` — в провайдеры над ним (как в уроке [BlocProvider и темы](lesson:blocprovider-temy-weatherapp)). Выход — это просто `context.read<AuthCubit>().signOut()`: экран сменится автоматически.

## Токен

### Что это

После входа Firebase выдаёт **ID-токен** — длинную строку в формате JWT (JSON Web Token). Внутри зашифрованы `uid` пользователя, email, время выдачи и срок действия, а также подпись Google, которую нельзя подделать.

Зачем он нужен: если у вас есть собственный сервер (например, на Django), приложение отправляет токен в заголовке каждого запроса, а сервер проверяет подпись через Firebase Admin SDK и узнаёт, кто это. Пароль на ваш сервер не попадает никогда.

### Как получить

```dart
final user = FirebaseAuth.instance.currentUser;
final token = await user?.getIdToken();
```

- Токен живёт **около часа**. SDK сам обновляет его в фоне, а `getIdToken()` всегда возвращает действующий.
- `getIdToken(true)` принудительно получает новый токен — нужно, например, после смены прав пользователя на сервере.
- `getIdTokenResult()` возвращает токен вместе с деталями: `expirationTime`, `claims` (дополнительные метки вроде роли `admin`).

### Отправка токена через Dio

Свяжем с перехватчиком из урока [про Dio POST и ошибки](lesson:dio-post-put-delete-sostoyaniya):

```dart
import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart';

class AuthInterceptor extends Interceptor {
  @override
  Future<void> onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final token = await FirebaseAuth.instance.currentUser?.getIdToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }
}

final api = Dio(BaseOptions(baseUrl: 'https://api.example.com'))
  ..interceptors.add(AuthInterceptor());
```

Теперь к каждому запросу автоматически добавляется свежий токен. Если сервер всё же ответил `401`, можно в `onError` запросить `getIdToken(true)` и повторить запрос один раз.

<aside class="callout" data-icon="🔐" markdown="1">

Не печатайте токен в консоль в релизе и не сохраняйте его в `SharedPreferences` — Firebase сам хранит сессию безопасно. Если же ваш собственный сервер выдаёт свои токены (access/refresh), храните их в `flutter_secure_storage` — подробно в уроке [Авторизация и FlutterSecureStorage](lesson:avtorizaciya-secure-storage).

</aside>

## Типичные ошибки

- `[core/no-app] No Firebase App '[DEFAULT]' has been created` — забыли `await Firebase.initializeApp(...)` или вызвали Firebase до него.
- `Binding has not yet been initialized` — нет `WidgetsFlutterBinding.ensureInitialized()`.
- `operation-not-allowed` — способ входа не включён в консоли.
- Навигация «вручную» после входа (`Navigator.push`) вместе с `AuthGate` — экраны дублируются. Доверьте переключение потоку `authStateChanges()`.

## Практика

1. **Подключение.** Создайте Firebase-проект, выполните `flutterfire configure` и инициализацию в `main`. Ожидаемый результат: приложение запускается без ошибок, в консоли Firebase видны зарегистрированные приложения.
2. **Регистрация и вход.** Сделайте `LoginPage` с полями email и пароль и двумя кнопками: «Войти» и «Зарегистрироваться». Ожидаемый результат: новый пользователь появляется во вкладке Authentication → Users.
3. **AuthGate.** Подключите `AuthCubit` и `AuthGate`, добавьте кнопку выхода в `AppBar` WeatherApp. Ожидаемый результат: после перезапуска приложения вы остаётесь в аккаунте, после выхода — видите форму входа.
4. **Ошибки.** Проверьте неверный пароль, занятый email, пароль из трёх символов и авиарежим. Ожидаемый результат: под формой понятные сообщения на русском, кнопка блокируется на время загрузки.
5. **Токен.** Выведите в консоль (только в debug) первые 20 символов токена и `expirationTime` из `getIdTokenResult()`. Подключите `AuthInterceptor` к Dio. Ожидаемый результат: в логах `LogInterceptor` виден заголовок `Authorization: Bearer ...`.

## Итоги

- Firebase подключается командой `flutterfire configure`, которая создаёт `firebase_options.dart`.
- В `main`: `WidgetsFlutterBinding.ensureInitialized()` и `await Firebase.initializeApp(...)`.
- Основные методы: `createUserWithEmailAndPassword`, `signInWithEmailAndPassword`, `signOut`; ошибки — `FirebaseAuthException` с полем `code`.
- Логика «вошёл / не вошёл» строится на потоке `authStateChanges()` и `AuthCubit`.
- ID-токен (JWT) живёт около часа, обновляется сам и отправляется на сервер в заголовке `Authorization: Bearer`.
- Firebase хранит сессию сам; собственные токены сервера — в `flutter_secure_storage`.
