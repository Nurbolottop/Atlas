Push-уведомления возвращают пользователя в приложение: «Завтра в Бишкеке гроза», «Ваш заказ доставлен». А deep links (глубокие ссылки) открывают не просто приложение, а нужный экран внутри него — например, погоду конкретного города. В этом уроке подключим Firebase Cloud Messaging, разберём, как обрабатывать уведомления в разных состояниях приложения, и настроим современные deep links через App Links и Universal Links — ведь старый сервис Firebase Dynamic Links больше не работает.

## Как работают push-уведомления

**FCM (Firebase Cloud Messaging)** — бесплатный сервис Google для доставки сообщений на Android, iOS и web. Схема:

```text
1. Приложение  → FCM:        «Дай мне адрес» → получает FCM-токен устройства
2. Приложение  → ваш сервер:  сохраняет токен у пользователя
3. Ваш сервер  → FCM:        «Отправь это сообщение на токен X»
4. FCM (через APNs на iOS) → устройство → уведомление
```

**FCM-токен** — это «почтовый адрес» конкретной установки приложения. Не путайте его с ID-токеном авторизации из урока [Firebase Auth](lesson:firebase-auth): тот подтверждает, *кто* пользователь, а FCM-токен — *куда* доставить сообщение.

Сообщения бывают двух видов:

| Вид | Что внутри | Поведение |
| --- | --- | --- |
| Notification | `title`, `body` | Система сама показывает уведомление, когда приложение свёрнуто |
| Data | Любые пары ключ-значение | Ничего не показывается автоматически, данные получает ваш код |

Чаще всего отправляют оба поля сразу: notification — для показа, data — например, ссылка на экран.

## Подключение FCM

```bash
flutter pub add firebase_messaging
flutterfire configure
```

Firebase уже должен быть инициализирован в `main` (см. урок про Auth).

**Android.** Дополнительной настройки почти не нужно. На Android 13+ требуется разрешение на уведомления — его запросит `requestPermission()`.

**iOS** (нужен платный аккаунт Apple Developer; проверять надёжнее на реальном устройстве):

1. В Xcode → Runner → Signing & Capabilities добавьте **Push Notifications** и **Background Modes** с галочкой *Remote notifications*.
2. В Apple Developer создайте APNs Authentication Key (файл `.p8`).
3. Загрузите его в консоль Firebase: Project settings → Cloud Messaging → Apple app configuration.

## Три состояния приложения

| Состояние | Что происходит | Как обработать |
| --- | --- | --- |
| **Foreground** (открыто) | Уведомление само не показывается | `FirebaseMessaging.onMessage` |
| **Background** (свёрнуто) | Система показывает уведомление | Нажатие — `onMessageOpenedApp` |
| **Terminated** (закрыто) | Система показывает уведомление | Нажатие — `getInitialMessage()` при запуске |

Для data-сообщений в фоне и в закрытом состоянии есть ещё `onBackgroundMessage` — отдельная функция, которая выполняется без UI.

## Код: сервис уведомлений

```dart
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'firebase_options.dart';

@pragma('vm:entry-point')
Future<void> firebaseBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  debugPrint('Фоновое сообщение: ${message.messageId}');
}

class PushService {
  PushService(this.onOpenLink);

  final void Function(String link) onOpenLink;
  final _fcm = FirebaseMessaging.instance;

  Future<void> init() async {
    final settings = await _fcm.requestPermission();
    if (settings.authorizationStatus == AuthorizationStatus.denied) return;

    await _fcm.setForegroundNotificationPresentationOptions(
      alert: true, badge: true, sound: true, // показывать в foreground на iOS
    );

    final token = await _fcm.getToken();
    debugPrint('FCM token: $token'); // отправьте его на свой сервер
    _fcm.onTokenRefresh.listen((t) {/* обновить токен на сервере */});

    FirebaseMessaging.onMessage.listen((m) {
      debugPrint('Пришло при открытом приложении: ${m.notification?.title}');
    });

    FirebaseMessaging.onMessageOpenedApp.listen(_handleTap);

    final initial = await _fcm.getInitialMessage();
    if (initial != null) _handleTap(initial);
  }

  void _handleTap(RemoteMessage message) {
    final link = message.data['link'] as String?;
    if (link != null) onOpenLink(link);
  }
}
```

Регистрация фонового обработчика — в `main`, до `runApp`:

```dart
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  FirebaseMessaging.onBackgroundMessage(firebaseBackgroundHandler);
  runApp(const App());
  await PushService((link) => router.go(Uri.parse(link).path)).init();
}
```

Разбор:

1. `firebaseBackgroundHandler` — **функция верхнего уровня** (не метод класса). Она запускается в отдельном изоляте, где нет вашего UI и состояния, поэтому Firebase в ней инициализируют заново.
2. `@pragma('vm:entry-point')` не даёт компилятору выбросить эту функцию в релизе: её вызывает нативный код, а не Dart.
3. `requestPermission()` показывает системный диалог. Если пользователь отказал — дальше нет смысла.
4. `getToken()` даёт адрес устройства, `onTokenRefresh` сообщает, когда он сменился (переустановка, очистка данных).
5. `getInitialMessage()` возвращает уведомление, по которому приложение запустили из закрытого состояния, или `null`.
6. `router` — это объект `GoRouter`, его настроим ниже в разделе про deep links.

<aside class="callout" data-icon="⚠️" markdown="1">

На Android уведомление в состоянии foreground **не появляется в шторке** автоматически — `onMessage` просто вызывает ваш код. Чтобы показать баннер, используют пакет `flutter_local_notifications` или показывают SnackBar внутри приложения.

</aside>

### Тестовая отправка

1. Запустите приложение и скопируйте FCM-токен из консоли.
2. Консоль Firebase → **Messaging** → создать кампанию → *Firebase Notification messages*.
3. Введите заголовок и текст, нажмите **Send test message**, вставьте токен.
4. В дополнительных параметрах добавьте пару `link` = `https://weather.example.com/city/Bishkek`.

Сверните приложение перед отправкой — так уведомление появится в шторке.

### Отправка с сервера

Сервер отправляет сообщения через **FCM HTTP v1 API** (старый legacy API отключён в 2024 году). Тело запроса:

```json
{
  "message": {
    "token": "DEVICE_FCM_TOKEN",
    "notification": { "title": "Гроза", "body": "Завтра в Бишкеке гроза, возьмите зонт" },
    "data": { "link": "https://weather.example.com/city/Bishkek" }
  }
}
```

Запрос идёт на `https://fcm.googleapis.com/v1/projects/YOUR_PROJECT_ID/messages:send` с OAuth-токеном сервисного аккаунта. Удобнее всего — через Firebase Admin SDK на бэкенде.

<aside class="callout" data-icon="🔐" markdown="1">

Ключ сервисного аккаунта даёт право рассылать уведомления всем вашим пользователям. Он живёт только на сервере — никогда в Flutter-приложении и в Git.

</aside>

## Deep links

### Что это

**Deep link** — ссылка, которая открывает конкретный экран приложения. Нажали в мессенджере на `https://weather.example.com/city/Bishkek` — открылась погода Бишкека в WeatherApp, а если приложения нет — сайт.

### Что случилось с Firebase Dynamic Links

Раньше для этого часто использовали **Firebase Dynamic Links**: умные ссылки, которые открывали приложение или магазин. Google объявил о закрытии сервиса, и **с 25 августа 2025 года он полностью отключён**: ссылки вида `*.page.link` перестали работать, а пакет `firebase_dynamic_links` больше не поддерживается. В старых туториалах вы его ещё встретите — не используйте.

Актуальный способ — встроенные механизмы самих платформ:

| Способ | Платформа | Как выглядит | Плюсы и минусы |
| --- | --- | --- | --- |
| **App Links** | Android | `https://ваш-домен/...` | Проверены доменом, открываются без вопросов «чем открыть» |
| **Universal Links** | iOS | `https://ваш-домен/...` | То же для iOS; если приложения нет — откроется сайт |
| Custom scheme | Обе | `weatherapp://city/Bishkek` | Просто настроить, но любое приложение может занять ту же схему, а без приложения ссылка не работает |

App Links и Universal Links — это обычные https-ссылки на **ваш домен**. Система проверяет, что домен действительно принадлежит вам, по специальному файлу на сайте.

### Android: App Links

В `android/app/src/main/AndroidManifest.xml` внутри `<activity android:name=".MainActivity">`:

```xml
<intent-filter android:autoVerify="true">
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="https" android:host="weather.example.com" />
</intent-filter>
```

На сайте по адресу `https://weather.example.com/.well-known/assetlinks.json`:

```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "com.example.weather_app",
    "sha256_cert_fingerprints": ["YOUR_SHA256_FINGERPRINT"]
  }
}]
```

Отпечаток SHA-256 вашего ключа подписи можно получить командой `./gradlew signingReport` в папке `android`. Для релиза из Google Play берите отпечаток из Play Console.

### iOS: Universal Links

1. В Xcode → Signing & Capabilities добавьте **Associated Domains** и запись `applinks:weather.example.com`.
2. На сайте по адресу `https://weather.example.com/.well-known/apple-app-site-association` (без расширения) положите:

```json
{
  "applinks": {
    "details": [
      {
        "appIDs": ["YOUR_TEAM_ID.com.example.weatherApp"],
        "components": [{ "/": "/city/*" }]
      }
    ]
  }
}
```

Оба файла должны отдаваться по HTTPS без редиректов.

### Flutter: вариант 1 — go_router

Начиная с Flutter 3.27 обработка deep links для роутера включена по умолчанию. Достаточно описать маршруты в `go_router` — входящая ссылка сама превратится в переход:

```bash
flutter pub add go_router
```

```dart
import 'package:go_router/go_router.dart';

final router = GoRouter(
  routes: [
    GoRoute(path: '/', builder: (context, state) => const WeatherPage()),
    GoRoute(
      path: '/city/:name',
      builder: (context, state) => CityWeatherPage(city: state.pathParameters['name']!),
    ),
  ],
);

class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp.router(routerConfig: router);
}
```

`/city/:name` — шаблон: часть после `/city/` попадёт в `state.pathParameters['name']`. Ссылка `https://weather.example.com/city/Bishkek` откроет `CityWeatherPage(city: 'Bishkek')`.

### Flutter: вариант 2 — пакет app_links

Если нужен полный контроль (например, сначала проверить авторизацию), ссылки ловят пакетом `app_links`:

```bash
flutter pub add app_links
```

```dart
import 'dart:async';
import 'package:app_links/app_links.dart';

class DeepLinkService {
  final _appLinks = AppLinks();
  StreamSubscription<Uri>? _sub;

  void start(void Function(Uri uri) onLink) {
    _sub = _appLinks.uriLinkStream.listen(onLink); // включая ссылку запуска
  }

  void dispose() => _sub?.cancel();
}

// где-то при старте приложения:
DeepLinkService().start((uri) {
  if (uri.pathSegments.length == 2 && uri.pathSegments.first == 'city') {
    router.go('/city/${uri.pathSegments[1]}');
  }
});
```

<aside class="callout" data-icon="⚠️" markdown="1">

Если обрабатываете ссылки сами через `app_links`, отключите встроенную обработку Flutter, иначе ссылка обработается дважды: в `AndroidManifest.xml` добавьте `<meta-data android:name="flutter_deeplinking_enabled" android:value="false" />`, а в `ios/Runner/Info.plist` — ключ `FlutterDeepLinkingEnabled` со значением `NO`.

</aside>

### Как проверить

```bash
# Android (эмулятор или устройство)
adb shell am start -a android.intent.action.VIEW \
  -c android.intent.category.BROWSABLE \
  -d "https://weather.example.com/city/Bishkek" com.example.weather_app

# iOS-симулятор
xcrun simctl openurl booted "https://weather.example.com/city/Bishkek"
```

Подробнее — в руководстве по deep linking на docs.flutter.dev ([документация](https://docs.flutter.dev/ui/navigation/deep-linking)).

## Push + deep link вместе

Связка из этого урока: сервер кладёт ссылку в `data.link`, пользователь нажимает на уведомление, `PushService` передаёт ссылку в `router.go(...)`, и открывается нужный экран. Один формат ссылок работает и из мессенджера, и из уведомления.

## Типичные ошибки

- Фоновый обработчик объявлен методом класса или без `@pragma('vm:entry-point')` — в релизе он не вызывается.
- Ждут баннер в foreground на Android — его нет без `flutter_local_notifications`.
- Не обработан `getInitialMessage()` — нажатие на уведомление при закрытом приложении просто открывает главный экран.
- `assetlinks.json` с отпечатком debug-ключа — в релизной сборке App Links не проходят проверку.
- Используют `firebase_dynamic_links` из старых статей — сервис отключён.

## Практика

1. **Токен.** Подключите `firebase_messaging`, запросите разрешение и выведите FCM-токен в консоль. Ожидаемый результат: в консоли длинная строка, на Android 13+ появился системный диалог.
2. **Тестовое уведомление.** Отправьте сообщение из консоли Firebase при свёрнутом приложении и при открытом. Ожидаемый результат: в первом случае — уведомление в шторке, во втором — строка из `onMessage` в логах.
3. **go_router.** Переведите WeatherApp на `go_router` с маршрутами `/` и `/city/:name`. Ожидаемый результат: `router.go('/city/Osh')` открывает погоду Оша.
4. **Deep link.** Настройте intent-filter (для учёбы можно custom scheme: `<data android:scheme="weatherapp" android:host="app" />` и ссылка `weatherapp://app/city/Osh`) и проверьте командой `adb`. Ожидаемый результат: приложение открывается сразу на экране города.
5. **Связка.** Добавьте в тестовое уведомление `link` и обработайте нажатие во всех трёх состояниях приложения. Ожидаемый результат: в каждом случае открывается экран нужного города.

## Итоги

- FCM доставляет сообщения по FCM-токену устройства; токен нужно отправить на свой сервер и обновлять по `onTokenRefresh`.
- Foreground — `onMessage`, нажатие в фоне — `onMessageOpenedApp`, запуск из уведомления — `getInitialMessage()`.
- Фоновый обработчик — функция верхнего уровня с `@pragma('vm:entry-point')`.
- Firebase Dynamic Links отключён с августа 2025 года — используйте App Links (Android) и Universal Links (iOS).
- Домен подтверждается файлами `assetlinks.json` и `apple-app-site-association` в `/.well-known/`.
- Во Flutter ссылки обрабатывает `go_router` из коробки или пакет `app_links` для ручного контроля.
