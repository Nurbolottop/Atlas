В интернет-магазине без входа в аккаунт не оформить заказ и не посмотреть историю покупок. В этом уроке соберём полную логику авторизации: разберёмся, что такое токены, безопасно сохраним их в **FlutterSecureStorage**, научим Dio автоматически подставлять токен через **интерцептор** и обновлять его, когда он истёк (**refresh**). Всё — в архитектуре из прошлых уроков.

## Как устроена авторизация по токену

Представьте фитнес-клуб. На ресепшене вы один раз показываете паспорт (логин и пароль) и получаете браслет (**токен**). Дальше проходите в зал по браслету. Браслет действует ограниченное время, потом его продлевают.

В приложении обычно два токена:

| Токен | Зачем | Срок жизни |
| --- | --- | --- |
| **Access token** | Прикладывается к каждому запросу в заголовке `Authorization: Bearer <token>` | Короткий: минуты или часы |
| **Refresh token** | Нужен только для получения нового access token | Длинный: дни или недели |

Зачем два? Access token летает в каждом запросе, и при перехвате вред ограничен его коротким сроком. Refresh token отправляется редко и только на один адрес.

Полный сценарий:

```text
1. Пользователь вводит логин/пароль → POST /auth/login
2. Сервер отвечает: accessToken + refreshToken
3. Приложение сохраняет оба токена в защищённое хранилище
4. Каждый запрос: заголовок Authorization: Bearer <accessToken>
5. Сервер ответил 401 (токен истёк) → POST /auth/refresh с refreshToken
6. Получили новые токены → сохранили → повторили исходный запрос
7. Refresh тоже не сработал → удаляем токены → экран входа
```

Будем использовать тестовый API `dummyjson.com`: `POST /auth/login` принимает `username`, `password` и `expiresInMins`, а `POST /auth/refresh` — `refreshToken`. Тестовый пользователь из документации сервиса — `emilys` / `emilyspass`.

## Где хранить токены

`SharedPreferences` — обычный файл: на взломанном телефоне или из резервной копии его читают как текст.

**FlutterSecureStorage** хранит данные в системных защищённых хранилищах:

-   **iOS** — Keychain, «связка ключей», где система хранит пароли;
-   **Android** — данные шифруются ключом из Android Keystore, к которому нет доступа у других приложений.

```bash
flutter pub add flutter_secure_storage
```

<aside class="callout" data-icon="🔐" markdown="1">

Храните в защищённом хранилище только токены. **Никогда не сохраняйте пароль пользователя** — для повторного входа достаточно refresh token. И не выводите токены в `print` и логи: логи видят другие разработчики и сервисы аналитики.

</aside>

### Прослойка TokenStorage

Как мы договорились в [уроке про прослойки](lesson:generics-enum-screenutil), не будем пускать пакет по всему проекту, а обернём его:

```dart
// lib/core/storage/token_storage.dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class TokenStorage {
  TokenStorage(this._storage);

  final FlutterSecureStorage _storage;

  static const _accessKey = 'access_token';
  static const _refreshKey = 'refresh_token';

  Future<String?> readAccessToken() => _storage.read(key: _accessKey);
  Future<String?> readRefreshToken() => _storage.read(key: _refreshKey);

  Future<void> saveTokens({required String access, required String refresh}) async {
    await _storage.write(key: _accessKey, value: access);
    await _storage.write(key: _refreshKey, value: refresh);
  }

  Future<void> clear() async {
    await _storage.delete(key: _accessKey);
    await _storage.delete(key: _refreshKey);
  }
}
```

-   `read` возвращает `null`, если значения нет, — так мы узнаём, что пользователь не входил.
-   Ключи — константы, чтобы не ошибиться в строке.

## Слои авторизации

### Data source и репозиторий

```dart
// lib/features/auth/data/datasources/auth_remote_data_source.dart
import 'package:dio/dio.dart';

class AuthRemoteDataSource {
  AuthRemoteDataSource(this._dio);
  final Dio _dio;

  Future<({String access, String refresh})> login(String username, String password) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/auth/login',
      data: {'username': username, 'password': password, 'expiresInMins': 30},
    );
    final json = response.data!;
    return (
      access: json['accessToken'] as String,
      refresh: json['refreshToken'] as String,
    );
  }
}
```

`({String access, String refresh})` — **record** из Dart 3: два значения без отдельного класса.

```dart
// lib/features/auth/data/repositories/auth_repository_impl.dart
class AuthRepositoryImpl extends BaseRepository implements AuthRepository {
  AuthRepositoryImpl(this._remote, this._tokens);

  final AuthRemoteDataSource _remote;
  final TokenStorage _tokens;

  @override
  Future<Result<void>> login(String username, String password) => safeCall(() async {
        final t = await _remote.login(username, password);
        await _tokens.saveTokens(access: t.access, refresh: t.refresh);
      });

  @override
  Future<bool> isLoggedIn() async => await _tokens.readAccessToken() != null;

  @override
  Future<void> logout() => _tokens.clear();
}
```

`BaseRepository.safeCall` и `Result` мы написали в [прошлом уроке](lesson:generics-enum-screenutil): ошибка сети или `400 Invalid credentials` превратится в `Failed(failure)`. Интерфейс `AuthRepository` в domain содержит те же три метода.

## Интерцептор: токен в каждом запросе

**Интерцептор (interceptor)** — «перехватчик», через который проходит каждый запрос и ответ Dio. Аналогия — охранник на проходной: он проверяет и дополняет всё, что входит и выходит.

Нам нужны два его метода: `onRequest` (перед отправкой) и `onError` (при ошибке).

### Уведомление о конце сессии

Когда refresh не удался, интерцептору нужно сообщить приложению: «выкидывай на экран входа». Сделаем маленький класс-сигнал:

```dart
// lib/core/auth/session_notifier.dart
import 'dart:async';

class SessionNotifier {
  final _controller = StreamController<void>.broadcast();

  Stream<void> get onExpired => _controller.stream;
  void expire() => _controller.add(null);
}
```

### AuthInterceptor с refresh

```dart
// lib/core/network/auth_interceptor.dart
import 'package:dio/dio.dart';
import '../auth/session_notifier.dart';
import '../storage/token_storage.dart';

class AuthInterceptor extends QueuedInterceptor {
  AuthInterceptor(this._tokens, this._session);

  final TokenStorage _tokens;
  final SessionNotifier _session;

  // Отдельный Dio без интерцепторов: для refresh и повтора запроса
  final _plainDio = Dio(BaseOptions(baseUrl: 'https://dummyjson.com'));

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _tokens.readAccessToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode != 401) {
      handler.next(err); // не наша ошибка — пропускаем дальше
      return;
    }

    final newToken = await _refreshToken(err.requestOptions);
    if (newToken == null) {
      await _tokens.clear();
      _session.expire();
      handler.next(err);
      return;
    }

    try {
      final options = err.requestOptions
        ..headers['Authorization'] = 'Bearer $newToken';
      handler.resolve(await _plainDio.fetch(options));
    } on DioException catch (e) {
      handler.next(e);
    }
  }

  Future<String?> _refreshToken(RequestOptions failed) async {
    final current = await _tokens.readAccessToken();
    final usedToken = failed.headers['Authorization'];
    // Пока этот запрос ждал в очереди, токен уже обновил другой запрос
    if (current != null && usedToken != 'Bearer $current') return current;

    final refresh = await _tokens.readRefreshToken();
    if (refresh == null) return null;

    try {
      final response = await _plainDio.post<Map<String, dynamic>>(
        '/auth/refresh',
        data: {'refreshToken': refresh, 'expiresInMins': 30},
      );
      final access = response.data!['accessToken'] as String;
      await _tokens.saveTokens(
        access: access,
        refresh: response.data!['refreshToken'] as String,
      );
      return access;
    } on DioException {
      return null;
    }
  }
}
```

Разберём по частям:

-   **`QueuedInterceptor`** вместо обычного `Interceptor`. Если пять запросов одновременно получили 401, обычный интерцептор запустил бы пять refresh. `QueuedInterceptor` обрабатывает их по очереди: первый обновляет токен, остальные видят, что токен уже новый.
-   **`onRequest`** читает токен и кладёт его в заголовок. `handler.next(options)` — «пропустить запрос дальше».
-   **Проверка `usedToken != 'Bearer $current'`** — это и есть защита от лишних refresh: запрос ушёл со старым токеном, а в хранилище уже новый — просто повторяем.
-   **`_plainDio`** — отдельный Dio без нашего интерцептора. Если refresh-запрос сам вернёт 401 через основной Dio, мы попадём в бесконечный цикл.
-   **`handler.resolve(response)`** — «подменить ошибку успешным ответом». Код, который делал запрос, получит данные, будто 401 и не было.
-   **Refresh не удался** — чистим токены и сигналим `_session.expire()`.

<aside class="callout" data-icon="⚠️" markdown="1">

Самая частая ошибка — делать refresh через тот же `Dio`, к которому подключён интерцептор. Получается вечный цикл «401 → refresh → 401 → refresh». Для refresh всегда используйте отдельный экземпляр Dio.

</aside>

## Состояние авторизации в приложении

Для статуса входа хватит enum и Cubit:

```dart
// lib/features/auth/presentation/cubit/auth_cubit.dart
import 'dart:async';
import 'package:flutter_bloc/flutter_bloc.dart';
// + импорты AuthRepository, Result, SessionNotifier

enum AuthStatus { unknown, authenticated, unauthenticated }

class AuthCubit extends Cubit<AuthStatus> {
  AuthCubit(this._repository, SessionNotifier session) : super(AuthStatus.unknown) {
    _sub = session.onExpired.listen((_) => emit(AuthStatus.unauthenticated));
  }

  final AuthRepository _repository;
  late final StreamSubscription<void> _sub;

  Future<void> checkAuth() async {
    final loggedIn = await _repository.isLoggedIn();
    emit(loggedIn ? AuthStatus.authenticated : AuthStatus.unauthenticated);
  }

  Future<Result<void>> login(String username, String password) async {
    final result = await _repository.login(username, password);
    if (result is Success) emit(AuthStatus.authenticated);
    return result;
  }

  Future<void> logout() async {
    await _repository.logout();
    emit(AuthStatus.unauthenticated);
  }

  @override
  Future<void> close() {
    _sub.cancel();
    return super.close();
  }
}
```

-   `unknown` — состояние на старте, пока мы читаем хранилище. В это время показываем сплэш.
-   Cubit подписан на `onExpired`: интерцептор сообщил о конце сессии — статус сам меняется на `unauthenticated`.
-   В `close()` отменяем подписку, иначе будет утечка памяти.

### Регистрация в GetIt

Регистрация `Dio` здесь заменяет прежнюю — теперь у него есть интерцептор:

```dart
sl.registerLazySingleton(() => const FlutterSecureStorage());
sl.registerLazySingleton(() => TokenStorage(sl()));
sl.registerLazySingleton(() => SessionNotifier());

sl.registerLazySingleton<Dio>(() {
  final dio = Dio(BaseOptions(baseUrl: 'https://dummyjson.com'));
  dio.interceptors.add(AuthInterceptor(sl(), sl()));
  return dio;
});

sl.registerLazySingleton(() => AuthRemoteDataSource(sl()));
sl.registerLazySingleton<AuthRepository>(() => AuthRepositoryImpl(sl(), sl()));
sl.registerLazySingleton(() => AuthCubit(sl(), sl()));
```

`AuthCubit` — исключение из правила «Bloc через фабрику»: статус входа нужен всему приложению всё время его жизни, поэтому он синглтон.

### Выбор экрана по статусу

```dart
class ShopApp extends StatelessWidget {
  const ShopApp({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider.value(
      value: sl<AuthCubit>(), // checkAuth() вызван в main()
      child: MaterialApp(
        home: BlocBuilder<AuthCubit, AuthStatus>(
          builder: (context, status) => switch (status) {
            AuthStatus.unknown => const SplashPage(),
            AuthStatus.authenticated => const ProductsPage(),
            AuthStatus.unauthenticated => const LoginPage(),
          },
        ),
      ),
    );
  }
}
```

`BlocProvider.value` используется для уже созданного объекта: он не закроет синглтон при уничтожении виджета. Проверку входа запускаем один раз в `main()` после `initDependencies()`: `sl<AuthCubit>().checkAuth();`.

Кнопка входа на `LoginPage`:

```dart
Future<void> _submit() async {
  final result = await context.read<AuthCubit>().login(
        _usernameController.text.trim(),
        _passwordController.text,
      );
  if (!mounted) return;
  if (result case Failed(:final failure)) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(failure.message)));
  }
}
```

После успешного входа экран сменится сам: `BlocBuilder` увидит `authenticated`. Кнопка «Выйти» в профиле — просто `context.read<AuthCubit>().logout()`.

## Типичные ошибки

-   **Токен в `SharedPreferences`.** Работает, но небезопасно. Для секретов — только `FlutterSecureStorage`.
-   **Refresh через основной Dio.** Бесконечный цикл 401. Используйте отдельный экземпляр.
-   **Обычный `Interceptor` вместо `QueuedInterceptor`.** Параллельные запросы запускают несколько refresh, и сервер может отозвать токены.
-   **Забыли `handler.next()` или `handler.resolve()`.** Запрос «зависнет» навсегда: каждый метод интерцептора обязан вызвать один из методов handler.

## Практика

1.  Создайте `TokenStorage` и проверьте его: сохраните пару токенов, перезапустите приложение и выведите в консоль, есть ли сохранённый access token (`true`/`false`, не сам токен).
2.  Сделайте экран входа с полями логина и пароля и `AuthCubit`. Ожидаемый результат: с `emilys` / `emilyspass` открывается каталог, с неверным паролем — SnackBar с ошибкой.
3.  Добавьте `AuthInterceptor` и экран профиля, который делает `GET /auth/me`. Убедитесь, что запрос проходит без ручного добавления заголовка.
4.  Проверьте refresh: войдите с `expiresInMins: 1`, подождите минуту и откройте профиль. Профиль должен загрузиться, а в логах Dio — появиться запрос `/auth/refresh`.
5.  Добавьте кнопку «Выйти». После выхода и перезапуска приложения должен открываться экран входа, а не каталог.

## Итоги

-   Access token прикладывается к каждому запросу и живёт недолго, refresh token нужен для его обновления.
-   Токены храним в `FlutterSecureStorage` через прослойку `TokenStorage`; пароль не храним никогда.
-   Интерцептор Dio добавляет заголовок `Authorization` и обрабатывает 401.
-   `QueuedInterceptor` и отдельный Dio для refresh защищают от гонок и бесконечных циклов.
-   `AuthCubit` со статусами `unknown` / `authenticated` / `unauthenticated` решает, какой экран показать.
-   Конец сессии интерцептор сообщает через `SessionNotifier`, а Cubit переводит пользователя на вход.
