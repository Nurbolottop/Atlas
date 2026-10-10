До сих пор вы запускали приложение кнопкой Run, и всё «просто работало». Но в реальном проекте одно и то же приложение собирают по-разному: для разработки, для тестировщиков, для магазина — с разными серверами, названиями и иконками. В этом уроке разберём режимы сборки Flutter, узнаем, что такое JIT и AOT и почему release-версия работает быстрее, а затем настроим build types и flavors для Android и iOS.

## Как Dart превращается в приложение: JIT и AOT

Телефон не понимает Dart напрямую — он понимает только машинный код процессора (обычно ARM). Перевести Dart в машинный код можно двумя способами.

**JIT (Just-In-Time, «точно в срок»)** — код переводится прямо во время работы программы. Аналогия: синхронный переводчик на встрече — переводит фразу за фразой, и если вы поменяли текст, он сразу переведёт новый вариант.

**AOT (Ahead-Of-Time, «заранее»)** — весь код переводится в машинный **до** запуска, при сборке. Аналогия: книга, переведённая и напечатанная заранее, — читается быстро, но чтобы что-то изменить, нужно переиздание.

| | JIT | AOT |
| --- | --- | --- |
| Когда компилируется | Во время работы | При сборке |
| Скорость запуска | Медленнее | Быстрая |
| Производительность | Ниже, бывают подтормаживания | Максимальная, плавная анимация |
| Hot reload | Есть | Нет |
| Размер | Больше (внутри компилятор и отладка) | Меньше |
| Где во Flutter | Debug-режим | Profile и Release |

Именно благодаря JIT работает **hot reload**: Dart VM подгружает изменённый код в уже запущенное приложение, не теряя состояние. А пользователь в магазине получает AOT-версию — быструю и компактную.

<aside class="callout" data-icon="⚠️" markdown="1">

Никогда не оценивайте скорость приложения в debug-режиме. Подтормаживания в debug — это нормально: там JIT, проверки `assert` и инструменты отладки. Плавность и производительность проверяйте только в profile-режиме на реальном устройстве (см. урок [Flutter DevTools](lesson:flutter-devtools)).

</aside>

## Три режима сборки Flutter

| Режим | Команда | Компиляция | Для чего |
| --- | --- | --- | --- |
| Debug | `flutter run` | JIT | Разработка, hot reload, `assert` работают |
| Profile | `flutter run --profile` | AOT | Замер производительности в DevTools |
| Release | `flutter run --release` | AOT | То, что получит пользователь |

Profile почти как release, но оставляет минимум инструментов для замеров. Profile-режим на эмуляторах и симуляторах отключён: их скорость не похожа на настоящий телефон, поэтому замеры делают только на реальном устройстве.

В коде режим можно узнать через константы:

```dart
import 'package:flutter/foundation.dart';

void setupLogging() {
  if (kDebugMode) {
    debugPrint('Debug: подробные логи включены');
  }
  if (kReleaseMode) {
    // в релизе отправляем ошибки в Crashlytics, а не в консоль
  }
}

void transfer(int amount) {
  assert(amount > 0, 'Сумма должна быть положительной'); // только в debug
}
```

- `kDebugMode`, `kProfileMode`, `kReleaseMode` — константы времени компиляции. В release код внутри `if (kDebugMode)` компилятор вообще выбрасывает.
- `assert` проверяется только в debug. Не кладите в него важную логику — в release её не будет.

## Сборка для Android и iOS

```bash
# Android
flutter build apk --release              # один APK для всех процессоров
flutter build apk --split-per-abi        # отдельный APK под каждую архитектуру — меньше размер
flutter build appbundle                  # AAB — формат для Google Play

# iOS (только на macOS с Xcode)
flutter build ios --release              # сборка без архива
flutter build ipa                        # архив .ipa для App Store / TestFlight
```

Готовые файлы лежат в `build/app/outputs/flutter-apk/`, `build/app/outputs/bundle/release/` и `build/ios/ipa/`.

| Формат | Что это | Куда |
| --- | --- | --- |
| APK | Готовый установочный файл | Отправить тестировщику, установить вручную |
| AAB | Набор, из которого Google Play сам соберёт APK под каждое устройство | Google Play |
| IPA | Архив iOS-приложения | App Store Connect, TestFlight |

Подпись, иконки и загрузку в магазины разберём в уроке [Публикация в App Store и Google Play](lesson:publikaciya-v-store).

## Build types в Android

**Build type** — это «как собрать»: с отладкой или без, со сжатием кода или без, какой ключ подписи. В Android по умолчанию есть `debug` и `release`. Они описаны в `android/app/build.gradle.kts` (в новых проектах Flutter файлы Gradle пишутся на Kotlin DSL):

```text
android {
    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("debug") // заменим на свой ключ при публикации
            isMinifyEnabled = true      // удаляет неиспользуемый нативный код
            isShrinkResources = true    // удаляет неиспользуемые ресурсы
        }
    }
}
```

Flutter сам сопоставляет свои режимы с build types: `flutter run` → `debug`, `flutter build apk` → `release`. Свой Dart-код Flutter при этом компилирует AOT в любом случае, если режим не debug.

## Flavors: dev, stage, prod

**Flavor** (вариант, «вкус») — это «что собрать»: разные версии одного приложения. Типичный набор:

- **dev** — для разработчиков: тестовый сервер, отладочные логи;
- **stage** — для тестировщиков: копия боевого сервера с тестовыми данными;
- **prod** — для пользователей: боевой сервер.

Зачем это нужно? Чтобы на одном телефоне стояли **одновременно** dev- и prod-версии (у них разный `applicationId`), чтобы тестировщик видел по названию «Shop Dev», с какой версией работает, и чтобы случайно не отправить тестовые заказы на боевой сервер.

Build type и flavor комбинируются: `devDebug`, `devRelease`, `prodDebug`, `prodRelease`.

### Шаг 1. Flavors в Android

```text
android {
    // ...
    flavorDimensions += "env"

    productFlavors {
        create("dev") {
            dimension = "env"
            applicationIdSuffix = ".dev"
            versionNameSuffix = "-dev"
            resValue("string", "app_name", "Shop Dev")
        }
        create("prod") {
            dimension = "env"
            resValue("string", "app_name", "Shop")
        }
    }
}
```

- `flavorDimensions` — «ось» вариантов. Нам хватит одной — окружение (`env`).
- `applicationIdSuffix = ".dev"` — dev-версия получит id `com.example.shop.dev` и установится рядом с prod.
- `resValue` создаёт строковый ресурс `app_name`. Чтобы он стал названием приложения, в `android/app/src/main/AndroidManifest.xml` укажите `android:label="@string/app_name"`.
- Файлы для конкретного flavor кладут в `android/app/src/dev/` и `android/app/src/prod/` — например, разные `google-services.json` или иконки.

### Шаг 2. Flavors в iOS

В iOS нет `productFlavors` — их роль играют **Build Configurations** и **Schemes** в Xcode:

1. Откройте `ios/Runner.xcworkspace` в Xcode.
2. **Runner (проект) → Info → Configurations**: продублируйте `Debug`, `Release`, `Profile` и назовите копии `Debug-dev`, `Release-dev`, `Profile-dev`, `Debug-prod`, `Release-prod`, `Profile-prod`.
3. **Product → Scheme → Manage Schemes**: создайте схемы `dev` и `prod`. Имя схемы должно **совпадать** с именем flavor. В настройках схемы выберите для Run/Archive конфигурации с нужным суффиксом.
4. **Runner (target) → Build Settings**: для каждой конфигурации задайте свой `PRODUCT_BUNDLE_IDENTIFIER` (например, `com.example.shop.dev`) и добавьте пользовательскую настройку `APP_DISPLAY_NAME`.
5. В `ios/Runner/Info.plist` используйте её как название: ключ `CFBundleDisplayName` со значением `$(APP_DISPLAY_NAME)`.

Подробная инструкция с актуальными экранами Xcode — в [документации Flutter про flavors](https://docs.flutter.dev/deployment/flavors-ios).

### Шаг 3. Запуск с flavor

```bash
flutter run --flavor dev
flutter run --flavor prod --release
flutter build appbundle --flavor prod
flutter build ipa --flavor prod
```

Во Flutter-коде текущий flavor доступен через константу `appFlavor`:

```dart
import 'package:flutter/services.dart';

final isDev = appFlavor == 'dev';
```

## Настройки окружения в Dart

Нативная часть знает про flavor, а Dart-коду нужен свой адрес API и флаги. Удобный способ — файлы с переменными и `--dart-define-from-file`.

```json
{
  "API_URL": "https://dev-api.example.com",
  "ENABLE_LOGS": true
}
```

Это файл `config/dev.json`, рядом — `config/prod.json` с боевыми значениями. Читаем их в коде:

```dart
class AppConfig {
  static const apiUrl = String.fromEnvironment('API_URL');
  static const enableLogs = bool.fromEnvironment('ENABLE_LOGS');
}

final dio = Dio(BaseOptions(baseUrl: AppConfig.apiUrl));
```

```bash
flutter run --flavor dev --dart-define-from-file=config/dev.json
flutter build appbundle --flavor prod --dart-define-from-file=config/prod.json
```

- `String.fromEnvironment` работает только с `const` — значения «вшиваются» при компиляции.
- Если переменную забыли передать, придёт пустая строка. Добавьте проверку при старте: `assert(AppConfig.apiUrl.isNotEmpty)`.

Альтернатива — отдельные точки входа `lib/main_dev.dart` и `lib/main_prod.dart`, которые вызывают общий `bootstrap(config)`, и запуск через `-t lib/main_dev.dart`.

<aside class="callout" data-icon="🔐" markdown="1">

Всё, что попало в приложение — `--dart-define`, `.env`, строки в коде, — можно достать из APK/IPA. Адрес API — нормально, а секретные ключи платёжных систем или админские токены в мобильном приложении хранить нельзя никак. Такие операции делает только бэкенд.

</aside>

### Firebase для разных flavors

Хорошая практика — отдельный Firebase-проект для dev и prod, чтобы тестовые данные не смешивались с боевыми. FlutterFire CLI умеет генерировать конфиги под каждый flavor:

```bash
flutterfire configure \
  --project=shop-dev \
  --out=lib/firebase_options_dev.dart \
  --android-package-name=com.example.shop.dev \
  --ios-bundle-id=com.example.shop.dev
```

Затем в `main` выбирайте нужные `options` по `appFlavor`.

## Обфускация

Обфускация — переименование классов и функций в бессмысленные имена (`a`, `b1`, `c2`), чтобы код было сложнее разобрать.

```bash
flutter build appbundle --flavor prod --obfuscate --split-debug-info=build/symbols
```

`--split-debug-info` складывает «словарь» для расшифровки в папку `build/symbols`. Сохраните её для каждой версии: без неё стек ошибок из Crashlytics будет нечитаемым (подробнее — в уроке [про аналитику](lesson:analitika-talker)).

## Типичные ошибки

- **«The Xcode project does not define custom schemes»** — во Flutter-проекте есть Android-flavors, но нет iOS-схемы с таким же именем.
- **Dev и prod не ставятся рядом** — забыли `applicationIdSuffix` / разный Bundle ID.
- **Пустой `API_URL` в релизе** — собрали без `--dart-define-from-file`.
- **Медленное приложение в debug** — это JIT, проверяйте в profile.
- **Логика внутри `assert`** — в release её нет.

## Практика

1. Запустите одно приложение в debug, profile и release на реальном устройстве и сравните плавность прокрутки длинного списка. Ожидаемый результат: в debug заметны подтормаживания, в profile и release — нет; hot reload работает только в debug.
2. Добавьте Android-flavors `dev` и `prod` с разными названиями. Ожидаемый результат: на телефоне стоят два приложения — «Shop Dev» и «Shop».
3. Создайте `config/dev.json` и `config/prod.json` с разными `API_URL` и выведите адрес на экран настроек. Ожидаемый результат: адрес меняется в зависимости от команды запуска.
4. Настройте схемы `dev` и `prod` в Xcode с разными Bundle ID. Ожидаемый результат: `flutter run --flavor dev` работает на iOS-симуляторе.
5. Покажите в углу dev-сборки баннер «DEV» (виджет `Banner`), если `appFlavor == 'dev'`. Ожидаемый результат: в prod баннера нет.

## Итоги

- JIT компилирует во время работы и даёт hot reload; AOT — заранее и даёт скорость.
- Debug — JIT; profile и release — AOT. Производительность меряйте в profile.
- `kDebugMode`/`kReleaseMode` позволяют выполнять код только в нужном режиме.
- Build type — «как собрать», flavor — «что собрать» (dev/stage/prod).
- Android: `productFlavors`; iOS: Build Configurations + Schemes с теми же именами.
- Настройки для Dart передают через `--dart-define-from-file`, но секреты в приложение не кладут.
