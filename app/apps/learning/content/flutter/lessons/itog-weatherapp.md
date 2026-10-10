Этот урок — итог четвёртого месяца. Мы соберём всё пройденное в одно законченное приложение WeatherApp: вход через Firebase, поиск города, реальную погоду с Open-Meteo через Dio, модели на json_serializable, Bloc с состояниями загрузки и ошибки, светлую и тёмную тему, картинки с кэшем, push-уведомления и deep links. Внутри — структура проекта, план сборки, ключевой код, чек-лист и пример контрольной.

## Что должно уметь приложение

1. Вход, регистрация и выход по email и паролю (Firebase Auth); сессия сохраняется после перезапуска.
2. Главный экран: поле поиска города, карточка текущей погоды с фоном, иконкой, температурой и ветром.
3. Почасовой прогноз на ближайшие 24 часа списком.
4. Состояния: загрузка, ошибка с понятным текстом и кнопкой «Повторить», успех.
5. Переключатель светлой, тёмной и системной темы.
6. Push-уведомление со ссылкой открывает экран нужного города; ссылка `https://<ваш-домен>/city/<название>` тоже.

## Повторяем темы месяца

| Тема | Что используем в проекте | Урок |
| --- | --- | --- |
| ChangeNotifier, FutureBuilder, Builder | `Builder`, адаптер для роутера | [урок](lesson:changenotifier-futurebuilder) |
| Bloc, Cubit, BlocBuilder, BlocListener | `WeatherBloc`, `ThemeCubit`, `AuthCubit` | [урок](lesson:bloc-event-state) |
| JSON, Equatable, json_serializable, Dio GET | Модели прогноза и города | [урок](lesson:json-modeli-dio-get) |
| DioException, коды ответа, состояния | `ApiException`, Loading/Success/Error | [урок](lesson:dio-post-put-delete-sostoyaniya) |
| BlocProvider, темы | `MultiBlocProvider`, `AppTheme` | [урок](lesson:blocprovider-temy-weatherapp) |
| Firebase Auth, токен | `AuthRepository`, `AuthGate` | [урок](lesson:firebase-auth) |
| FCM, deep links | `PushService`, `go_router` | [урок](lesson:firebase-push-deeplinks) |
| Изображения | `CachedNetworkImage` для фона | [урок](lesson:networkimage) |

## Архитектура проекта

Разделяем код на слои. Каждый слой знает только о том, что ниже него:

```text
UI (виджеты)  →  Bloc / Cubit  →  Repository  →  Dio / Firebase
```

Структура папок:

```text
lib/
├── main.dart                 # инициализация Firebase, провайдеры, runApp
├── app.dart                  # MaterialApp.router, темы
├── core/
│   ├── api_exception.dart    # своё исключение
│   ├── dio_client.dart       # Dio с baseUrl, таймаутами, логами
│   ├── router.dart           # GoRouter и маршруты
│   └── theme/
│       ├── app_theme.dart
│       └── theme_cubit.dart
├── features/
│   ├── auth/
│   │   ├── auth_repository.dart
│   │   ├── auth_cubit.dart
│   │   └── login_page.dart
│   ├── weather/
│   │   ├── models/           # city.dart, forecast.dart (+ .g.dart)
│   │   ├── weather_repository.dart
│   │   ├── bloc/             # weather_bloc.dart, weather_event.dart, weather_state.dart
│   │   └── ui/               # weather_page.dart, weather_card.dart, hourly_list.dart
│   └── push/
│       └── push_service.dart
└── firebase_options.dart     # сгенерирован flutterfire configure
```

Деление «по фичам» держит всё про погоду в одной папке. В пятом месяце разовьём его до Clean Architecture ([GetIt и DI](lesson:getit-di-clean-1)).

## План сборки по шагам

Делайте по шагу и запускайте приложение после каждого.

1. **Проект и пакеты.**

```bash
flutter create weather_app && cd weather_app
flutter pub add flutter_bloc equatable dio json_annotation go_router cached_network_image
flutter pub add firebase_core firebase_auth firebase_messaging
flutter pub add dev:build_runner dev:json_serializable
flutterfire configure
```

2. **Тема.** `AppTheme` и `ThemeCubit`, `MaterialApp` с `theme`, `darkTheme`, `themeMode`. Проверка: переключатель меняет тему.
3. **Модели.** `City` и `Forecast` с `@JsonSerializable`, запуск `build_runner`. Проверка: тест `fromJson` на примере ответа.
4. **Dio и репозиторий.** `dio_client.dart`, `WeatherRepository` с методами `searchCity` и `getForecast`, перевод `DioException` в `ApiException`. Проверка: `print` результата из `main`.
5. **WeatherBloc.** События `WeatherCityRequested`, `WeatherRefreshed`; состояния Initial, Loading, Success, Failure. Проверка: экран показывает все состояния.
6. **UI погоды.** Поиск, карточка с `CachedNetworkImage`, почасовой список. Проверка: обе темы, авиарежим, несуществующий город.
7. **Auth.** `AuthRepository`, `AuthCubit`, `LoginPage`. Проверка: регистрация, вход, выход, перезапуск.
8. **Роутер.** `go_router` с маршрутами `/login`, `/`, `/city/:name` и `redirect` по состоянию входа.
9. **Push и deep links.** `PushService`, intent-filter и Associated Domains. Проверка: `adb`-команда и тестовое уведомление.
10. **Полировка.** Иконка, пустые состояния, README.

## Ключевые фрагменты кода

### Модель прогноза

```dart
import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';

part 'forecast.g.dart';

@JsonSerializable(explicitToJson: true)
class Forecast extends Equatable {
  const Forecast({required this.current, required this.hourly});
  final CurrentWeather current;
  final HourlyWeather hourly;

  factory Forecast.fromJson(Map<String, dynamic> json) => _$ForecastFromJson(json);
  Map<String, dynamic> toJson() => _$ForecastToJson(this);

  @override
  List<Object?> get props => [current, hourly];
}

@JsonSerializable()
class CurrentWeather extends Equatable {
  const CurrentWeather({required this.temperature, required this.windSpeed, required this.weatherCode});
  @JsonKey(name: 'temperature_2m')
  final double temperature;
  @JsonKey(name: 'wind_speed_10m')
  final double windSpeed;
  @JsonKey(name: 'weather_code')
  final int weatherCode;

  factory CurrentWeather.fromJson(Map<String, dynamic> json) => _$CurrentWeatherFromJson(json);
  Map<String, dynamic> toJson() => _$CurrentWeatherToJson(this);

  @override
  List<Object?> get props => [temperature, windSpeed, weatherCode];
}

@JsonSerializable()
class HourlyWeather extends Equatable {
  const HourlyWeather({required this.time, required this.temperatures});
  final List<String> time;
  @JsonKey(name: 'temperature_2m')
  final List<double> temperatures;

  factory HourlyWeather.fromJson(Map<String, dynamic> json) => _$HourlyWeatherFromJson(json);
  Map<String, dynamic> toJson() => _$HourlyWeatherToJson(this);

  @override
  List<Object?> get props => [time, temperatures];
}
```

Ключи с цифрами (`temperature_2m`) задаём явно через `@JsonKey(name:)`: `FieldRename.snake` ставит `_` только перед заглавными буквами и с цифрами не справится. `explicitToJson: true` превращает вложенные модели в словари при `toJson`.

### Репозиторий

```dart
class WeatherRepository {
  WeatherRepository(this._dio);
  final Dio _dio;

  Future<Forecast> getForecast(City city) async {
    try {
      final res = await _dio.get<Map<String, dynamic>>(
        'https://api.open-meteo.com/v1/forecast',
        queryParameters: {
          'latitude': city.latitude,
          'longitude': city.longitude,
          'current': 'temperature_2m,wind_speed_10m,weather_code',
          'hourly': 'temperature_2m',
          'forecast_hours': 24,
          'timezone': 'auto',
        },
      );
      return Forecast.fromJson(res.data!);
    } on DioException catch (e) {
      throw ApiException(describeError(e), statusCode: e.response?.statusCode);
    }
  }
}
```

`describeError` — из урока про `DioException`. `searchCity` устроен так же и бросает `ApiException('Город не найден')` при пустом `results`.

### Bloc с повтором

```dart
class WeatherBloc extends Bloc<WeatherEvent, WeatherState> {
  WeatherBloc(this._repo) : super(const WeatherInitial()) {
    on<WeatherCityRequested>(_onCity);
    on<WeatherRefreshed>((event, emit) async {
      final city = _lastCity;
      if (city != null) await _onCity(WeatherCityRequested(city), emit);
    });
  }

  final WeatherRepository _repo;
  String? _lastCity;

  Future<void> _onCity(WeatherCityRequested event, Emitter<WeatherState> emit) async {
    _lastCity = event.name;
    emit(const WeatherLoading());
    try {
      final city = await _repo.searchCity(event.name);
      final forecast = await _repo.getForecast(city);
      emit(WeatherSuccess(city: city, forecast: forecast));
    } on ApiException catch (e) {
      emit(WeatherFailure(e.message, canRetry: e.statusCode == null || e.statusCode! >= 500));
    }
  }
}
```

`canRetry` — кнопка «Повторить» только при сбое сети или сервера (при 4xx повтор бесполезен).

### Роутер с защитой экранов

```dart
GoRouter createRouter(AuthCubit auth) => GoRouter(
      refreshListenable: GoRouterRefreshStream(auth.stream),
      redirect: (context, state) {
        final loggedIn = auth.state is AuthAuthenticated;
        final onLogin = state.matchedLocation == '/login';
        if (!loggedIn && !onLogin) return '/login';
        if (loggedIn && onLogin) return '/';
        return null; // остаёмся, где были
      },
      routes: [
        GoRoute(path: '/login', builder: (_, __) => const LoginPage()),
        GoRoute(path: '/', builder: (_, __) => const WeatherPage()),
        GoRoute(
          path: '/city/:name',
          builder: (_, state) => WeatherPage(initialCity: state.pathParameters['name']),
        ),
      ],
    );
```

`redirect` вызывается при каждом переходе и отправляет гостя на `/login`. `refreshListenable` пересчитывает `redirect` при смене состояния `AuthCubit`. Адаптер потока пишем сами:

```dart
class GoRouterRefreshStream extends ChangeNotifier {
  GoRouterRefreshStream(Stream<dynamic> stream) {
    _sub = stream.listen((_) => notifyListeners());
  }
  late final StreamSubscription<dynamic> _sub;

  @override
  void dispose() {
    _sub.cancel();
    super.dispose();
  }
}
```

### main.dart

```dart
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  FirebaseMessaging.onBackgroundMessage(firebaseBackgroundHandler);

  final authRepo = AuthRepository();
  final authCubit = AuthCubit(authRepo);
  final router = createRouter(authCubit);

  runApp(
    MultiRepositoryProvider(
      providers: [
        RepositoryProvider.value(value: authRepo),
        RepositoryProvider(create: (_) => WeatherRepository(createDio())),
      ],
      child: MultiBlocProvider(
        providers: [
          BlocProvider.value(value: authCubit),
          BlocProvider(create: (_) => ThemeCubit()),
          BlocProvider(create: (context) => WeatherBloc(context.read<WeatherRepository>())),
        ],
        child: App(router: router),
      ),
    ),
  );

  await PushService((link) => router.go(Uri.parse(link).path)).init();
}
```

`authCubit` создаём до `runApp`: он нужен и роутеру, и дереву виджетов, поэтому в дерево он попадает через `BlocProvider.value`. Закрывать его не нужно — он живёт всё время работы приложения; экранные Bloc всегда создавайте через `create`.

## Чек-лист готовности проекта

- Приложение запускается на Android и iOS без ошибок и предупреждений анализатора (`flutter analyze`).
- Вход, регистрация, выход работают; после перезапуска пользователь остаётся в аккаунте.
- Ошибки входа показаны по-русски, кнопка блокируется на время запроса.
- Поиск существующего города показывает погоду; несуществующего — понятное сообщение.
- В авиарежиме — ошибка сети и кнопка «Повторить».
- Все экраны читаемы в светлой и тёмной теме, цвета взяты из `colorScheme`.
- Картинки имеют размер, заглушку при загрузке и при ошибке, кэшируются.
- Модели сгенерированы `build_runner`, `.g.dart` актуальны.
- Ни одного запроса в виджетах — только через репозитории.
- Уведомление со ссылкой открывает нужный город из закрытого и свёрнутого приложения.
- В репозитории нет секретов (ключей сервисного аккаунта, паролей, токенов).
- README: описание, скриншоты, как запустить.

## Что нужно уметь к концу месяца

- Выбирать между `setState`, `ChangeNotifier`, `ValueNotifier` и Bloc.
- Написать Cubit и Bloc с `sealed`-состояниями и отрисовать их через `switch`.
- Различать `BlocBuilder` и `BlocListener`, `create` и `.value`, `read` и `watch`.
- Описать модель с `fromJson`/`toJson`, Equatable и json_serializable.
- Делать GET, POST, PUT, DELETE через Dio и обрабатывать `DioException` и коды 4xx/5xx.
- Подключить Firebase через FlutterFire CLI, сделать вход и получить ID-токен.
- Получить FCM-токен, обработать уведомление в трёх состояниях, настроить App Links / Universal Links.
- Показать картинку из сети с загрузкой, ошибкой и кэшем.

## Пример контрольной работы

Ниже — пример заданий для самопроверки (ориентир — около 3 часов с документацией). Реальный формат, время и критерии оценки уточните у ментора.

1. **Модель (15 баллов).** Опишите модель `DailyForecast` для параметра `daily=temperature_2m_max,temperature_2m_min` Open-Meteo с json_serializable и Equatable.
2. **Репозиторий (20 баллов).** Метод `getDaily(City)` с обработкой `DioException`: таймаут, нет сети, 400, 500 — разные сообщения.
3. **Bloc (25 баллов).** `DailyCubit` с состояниями Loading, Success, Error и методом `load`.
4. **UI (20 баллов).** Экран «Прогноз на 7 дней»: список с min/max, `BlocBuilder` для данных, `BlocListener` для SnackBar ошибки, корректный вид в обеих темах.
5. **Навигация (10 баллов).** Маршрут `/city/:name/daily` и переход на него из карточки погоды.
6. **Вопросы (10 баллов).** Почему `FutureBuilder` нельзя давать Future, созданный в `build`? Чем `BlocProvider.value` отличается от `create`? Что заменило Firebase Dynamic Links?

## Советы по подготовке

- Соберите проект с нуля ещё раз, не подглядывая в старый код.
- Пройдите чек-лист честно: авиарежим, абракадабра в поиске, обе темы.
- Держите открытыми документацию [flutter_bloc](https://pub.dev/packages/flutter_bloc), [dio](https://pub.dev/packages/dio) и [FlutterFire](https://firebase.google.com/docs/flutter/setup).
- Коммитьте после каждого шага плана.

## Практика

1. **Каркас.** Создайте структуру папок, тему и `ThemeCubit`. Ожидаемый результат: пустое приложение с переключением темы.
2. **Погода без входа.** Выполните шаги 3–6 плана. Ожидаемый результат: поиск города, карточка с фоном и почасовой список, все состояния работают.
3. **Авторизация и роутер.** Добавьте шаги 7–8. Ожидаемый результат: без входа нельзя попасть на главный экран, выход возвращает на `/login`.
4. **Уведомления и ссылки.** Выполните шаг 9. Ожидаемый результат: уведомление и `adb`-ссылка открывают экран выбранного города.
5. **Контрольная.** Решите пример контрольной работы. Ожидаемый результат: экран прогноза на 7 дней, доступный по deep link.

## Итоги

- WeatherApp объединяет все темы месяца: Bloc, Dio, модели, темы, Firebase Auth, FCM, deep links и картинки.
- Слои: UI → Bloc → Repository → Dio/Firebase; виджеты не делают запросов.
- Собирайте по шагам и проверяйте приложение после каждого.
- `go_router` с `redirect` и `refreshListenable` защищает экраны от неавторизованных пользователей.
- Чек-лист — ваш критерий готовности: ошибки, тёмная тема, авиарежим, отсутствие секретов.
- В следующем месяце этот же проект превратится в Clean Architecture с DI.
