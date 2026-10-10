Приложение опубликовано — но как узнать, что с ним происходит у тысяч пользователей? Какие экраны открывают, где бросают покупку, почему у кого-то оно падает? В этом уроке подключим Firebase Analytics для событий, Crashlytics для отчётов о падениях и TalkerFlutter для удобного логирования прямо в приложении.

## Аналитика, краш-репорты и логи — в чём разница

| Инструмент | Отвечает на вопрос | Пример |
| --- | --- | --- |
| Аналитика (Firebase Analytics) | Что делают пользователи? | 40% доходят до корзины, 10% оплачивают |
| Краш-репорты (Crashlytics) | Где и почему приложение падает? | `Null check operator` в `CartPage` у 2% пользователей Android 12 |
| Логи (Talker) | Что происходило шаг за шагом? | Запрос → ответ 500 → показали ошибку |

Аналогия: аналитика — камера над входом в магазин (сколько вошло, куда пошли), Crashlytics — сигнализация (что-то сломалось), логи — подробный журнал смены.

## Firebase Analytics

### Подключение

Firebase у вас уже настроен (урок [Firebase: подключение и авторизация](lesson:firebase-auth)). Добавляем пакет:

```bash
flutter pub add firebase_analytics
```

Сразу после подключения Analytics сам собирает базовые события: первый запуск (`first_open`), сессии (`session_start`), версию ОС, страну, модель устройства. Ваша задача — добавить **свои** события, важные для бизнеса.

### Свои события

```dart
import 'package:firebase_analytics/firebase_analytics.dart';

final analytics = FirebaseAnalytics.instance;

Future<void> onAddToCart(Product product) async {
  await analytics.logEvent(
    name: 'add_to_cart_click',
    parameters: {
      'product_id': product.id,
      'category': product.category,
      'price': product.price,
    },
  );
}
```

- `name` — имя события: латиница, цифры и `_`, до 40 символов, начинается с буквы.
- `parameters` — детали события. Значения — `String` или `num`.
- Для типовых действий есть готовые методы с правильными именами: `logLogin`, `logSignUp`, `logSearch`, `logAddToCart`, `logPurchase`. Их Firebase понимает «из коробки» и строит по ним готовые отчёты.

```dart
await analytics.logLogin(loginMethod: 'email');
await analytics.logSearch(searchTerm: 'кроссовки');
```

### Свойства пользователя и экраны

```dart
// после входа
await analytics.setUserId(id: user.uid);
await analytics.setUserProperty(name: 'plan', value: 'premium');
```

- `setUserId` — связывает события с пользователем (только внутренний id, не email и не телефон).
- `setUserProperty` — постоянные характеристики: тариф, язык, тема. По ним удобно делить пользователей на группы в отчётах.

Чтобы автоматически отслеживать открытие экранов, добавьте наблюдатель навигации:

```dart
MaterialApp(
  navigatorObservers: [
    FirebaseAnalyticsObserver(analytics: FirebaseAnalytics.instance),
  ],
);
```

Наблюдатель логирует `screen_view` при каждом переходе с именем маршрута, поэтому давайте маршрутам понятные имена (`RouteSettings(name: '/cart')` или имена роутов в go_router). Вручную экран отмечается через `analytics.logScreenView(screenName: 'Cart')`.

<aside class="callout" data-icon="🔐" markdown="1">

Не отправляйте в аналитику персональные данные: email, телефон, имя, адрес, текст сообщений. Это нарушает правила Google и законы о защите данных. И не забудьте указать сбор аналитики в анкетах магазинов (Data safety / App Privacy) — см. урок [о публикации](lesson:publikaciya-v-store).

</aside>

### Проверка: DebugView

Обычные отчёты обновляются с задержкой до суток. Для разработки есть **DebugView** в консоли Firebase (Analytics → DebugView) — события видны почти сразу.

```bash
# Android: включить режим отладки для приложения
adb shell setprop debug.firebase.analytics.app com.example.shop.dev
# выключить
adb shell setprop debug.firebase.analytics.app .none.
```

Для iOS в Xcode: **Product → Scheme → Edit Scheme → Run → Arguments** и добавьте аргумент `-FIRDebugEnabled`.

### Обёртка для аналитики

Вызывать `FirebaseAnalytics.instance` из виджетов — плохая идея: код привязан к Firebase, а в тестах он будет мешать. Сделаем абстракцию, как в [Clean Architecture](lesson:getit-di-clean-1):

```dart
abstract interface class AnalyticsService {
  Future<void> logEvent(String name, [Map<String, Object>? params]);
  Future<void> setUserId(String? id);
}

class FirebaseAnalyticsService implements AnalyticsService {
  FirebaseAnalyticsService(this._analytics);
  final FirebaseAnalytics _analytics;

  @override
  Future<void> logEvent(String name, [Map<String, Object>? params]) =>
      _analytics.logEvent(name: name, parameters: params);

  @override
  Future<void> setUserId(String? id) => _analytics.setUserId(id: id);
}

// регистрация в GetIt
getIt.registerLazySingleton<AnalyticsService>(
  () => FirebaseAnalyticsService(FirebaseAnalytics.instance),
);
```

В тестах подставляете фейковую реализацию, а захотите добавить вторую систему аналитики — поменяете одну реализацию. Имена событий держите в одном месте (класс с константами), чтобы не было `add_to_cart` и `addToCart` одновременно.

## Firebase Crashlytics

**Crashlytics** собирает отчёты о падениях и ошибках: стек вызовов, модель устройства, версию ОС и приложения, сколько пользователей затронуто.

```bash
flutter pub add firebase_crashlytics
flutterfire configure
```

Повторный `flutterfire configure` добавит в Android-проект Gradle-плагин Crashlytics. Затем перехватываем все ошибки в `main`:

```dart
import 'dart:ui';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'firebase_options.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);

  // в debug не засоряем отчёты
  await FirebaseCrashlytics.instance
      .setCrashlyticsCollectionEnabled(!kDebugMode);

  // 1. Ошибки фреймворка Flutter (build, layout, paint)
  FlutterError.onError = FirebaseCrashlytics.instance.recordFlutterFatalError;

  // 2. Все остальные асинхронные ошибки, не пойманные в try/catch
  PlatformDispatcher.instance.onError = (error, stack) {
    FirebaseCrashlytics.instance.recordError(error, stack, fatal: true);
    return true;
  };

  runApp(const App());
}
```

- `FlutterError.onError` ловит ошибки внутри фреймворка — например, исключение в `build`.
- `PlatformDispatcher.instance.onError` ловит всё остальное: необработанные ошибки в `Future`, колбэках, таймерах. `return true` означает «ошибка обработана».
- `fatal: true` — помечаем как падение, такие ошибки в консоли идут отдельным списком.

### Нефатальные ошибки и контекст

Не каждая ошибка роняет приложение. Например, сервер вернул некорректный JSON — вы показали «Что-то пошло не так», но знать об этом нужно:

```dart
try {
  final products = await repository.getProducts();
} catch (e, st) {
  await FirebaseCrashlytics.instance.recordError(
    e,
    st,
    reason: 'Ошибка загрузки каталога',
  );
  emit(state.copyWith(status: Status.failure));
}
```

Добавьте контекст, чтобы по отчёту было понятно, что происходило:

```dart
final crashlytics = FirebaseCrashlytics.instance;
await crashlytics.setUserIdentifier(user.uid);       // чей отчёт
await crashlytics.setCustomKey('flavor', 'prod');    // любые пары ключ-значение
await crashlytics.log('Открыт экран оплаты');        // «хлебные крошки» перед падением
```

### Проверяем, что всё работает

Добавьте временную кнопку и нажмите её в **release**-сборке:

```dart
TextButton(
  onPressed: () => FirebaseCrashlytics.instance.crash(),
  child: const Text('Тестовый краш'),
);
```

Отчёт отправится при **следующем запуске** приложения и появится в консоли (Crashlytics) через несколько минут.

<aside class="callout" data-icon="⚠️" markdown="1">

Если вы собираете с `--obfuscate --split-debug-info=build/symbols` (урок [про сборки](lesson:build-types-jit-aot)), стек в Crashlytics будет из бессмысленных имён. Загрузите символы для каждой версии: `firebase crashlytics:symbols:upload --app=YOUR_FIREBASE_APP_ID build/symbols`. Без этого отчёты почти бесполезны.

</aside>

## TalkerFlutter: логирование

`print` в продакшене — плохая практика: логи нельзя отфильтровать, они пропадают, а пользователь не может их показать. [Talker](https://pub.dev/packages/talker_flutter) — библиотека логирования для Flutter: цветные логи по уровням, история в памяти, готовый экран просмотра логов внутри приложения и интеграции с Dio и Bloc.

```bash
flutter pub add talker_flutter talker_dio_logger talker_bloc_logger
```

### Создание и уровни логов

```dart
import 'package:talker_flutter/talker_flutter.dart';

final talker = TalkerFlutter.init();

void example() {
  talker.debug('Подробности для разработчика');
  talker.info('Пользователь открыл каталог');
  talker.warning('Кэш устарел, грузим заново');
  talker.error('Не удалось сохранить корзину');

  try {
    throw const FormatException('Плохой JSON');
  } catch (e, st) {
    talker.handle(e, st, 'Ошибка парсинга товаров'); // исключение + стек
  }
}
```

| Метод | Когда использовать |
| --- | --- |
| `debug` / `verbose` | Детали, нужные только при отладке |
| `info` | Обычные события: вход, открытие экрана |
| `warning` | Что-то странное, но приложение работает |
| `error` / `handle` | Ошибки; `handle` принимает исключение и стек |
| `critical` | Всё сломалось |

Зарегистрируйте `talker` в GetIt как синглтон, чтобы один и тот же объект был доступен везде.

### Логи Dio и Bloc

```dart
import 'package:talker_bloc_logger/talker_bloc_logger.dart';
import 'package:talker_dio_logger/talker_dio_logger.dart';

final dio = Dio()
  ..interceptors.add(
    TalkerDioLogger(
      talker: talker,
      settings: const TalkerDioLoggerSettings(
        printRequestHeaders: false, // не светим токены в логах
        printResponseData: true,
      ),
    ),
  );

Bloc.observer = TalkerBlocObserver(talker: talker);
```

- `TalkerDioLogger` — перехватчик Dio (вы знаете их по урокам про Dio): логирует каждый запрос, ответ и ошибку.
- `TalkerBlocObserver` — логирует события и смены состояний всех Bloc. Видно, какое событие привело к какому состоянию.

### Экран логов внутри приложения

```dart
ElevatedButton(
  onPressed: () => Navigator.of(context).push(
    MaterialPageRoute(builder: (_) => TalkerScreen(talker: talker)),
  ),
  child: const Text('Логи'),
);
```

`TalkerScreen` показывает всю историю логов с фильтрами и поиском и позволяет поделиться ими. Тестировщик нашёл баг — открыл экран логов, отправил вам файл. Покажите кнопку только в dev-сборке: `if (appFlavor == 'dev')`. А `TalkerRouteObserver(talker)` в `navigatorObservers` добавит в логи переходы между экранами.

### Связываем Talker и Crashlytics

Чтобы каждая ошибка, залогированная через Talker, автоматически уходила в Crashlytics, напишите наблюдатель:

```dart
class CrashlyticsTalkerObserver extends TalkerObserver {
  @override
  void onError(TalkerError err) {
    FirebaseCrashlytics.instance.recordError(err.error, err.stackTrace, reason: err.message);
  }

  @override
  void onException(TalkerException err) {
    FirebaseCrashlytics.instance.recordError(err.exception, err.stackTrace, reason: err.message);
  }
}

final talker = TalkerFlutter.init(observer: CrashlyticsTalkerObserver());
```

Теперь в коде достаточно одного вызова `talker.handle(e, st)` — ошибка попадёт и в локальный лог, и в Crashlytics.

## Типичные ошибки

- **События не видны в отчётах** — обычные отчёты обновляются с задержкой, смотрите DebugView.
- **Personal data в параметрах** — email и телефоны в аналитике.
- **Crashlytics молчит** — краш вызывали в debug с выключенным сбором или не перезапустили приложение.
- **Нечитаемый стек** — не загружены символы после `--obfuscate`.
- **Токены в логах** — включён вывод заголовков запросов в продакшене.

## Практика

1. Подключите Firebase Analytics и отправьте события `add_to_cart_click` и `logLogin`. Ожидаемый результат: события видны в DebugView с параметрами.
2. Создайте `AnalyticsService` с реализацией на Firebase и фейковой реализацией, которая пишет события в список. Ожидаемый результат: в unit-тесте проверяете, что нажатие на кнопку отправляет нужное событие.
3. Настройте Crashlytics и вызовите тестовый краш в release-сборке. Ожидаемый результат: отчёт с вашим `setCustomKey('flavor', ...)` в консоли Firebase.
4. Подключите Talker с `TalkerDioLogger` и `TalkerBlocObserver` и добавьте кнопку «Логи» в dev-сборке. Ожидаемый результат: на `TalkerScreen` видны запросы к API и смены состояний Bloc.
5. Добавьте `CrashlyticsTalkerObserver`. Ожидаемый результат: ошибка, переданная в `talker.handle`, появляется в Crashlytics как нефатальная.

## Итоги

- Аналитика показывает, что делают пользователи; Crashlytics — где падает; логи — что происходило по шагам.
- Свои события — через `logEvent` или готовые методы вроде `logLogin`; проверяются в DebugView.
- Аналитику прячут за интерфейсом `AnalyticsService` и не отправляют персональные данные.
- Crashlytics перехватывает ошибки через `FlutterError.onError` и `PlatformDispatcher.instance.onError`.
- После обфускации обязательно загружают символы.
- Talker заменяет `print`: уровни логов, экран логов, интеграции с Dio, Bloc и Crashlytics.
