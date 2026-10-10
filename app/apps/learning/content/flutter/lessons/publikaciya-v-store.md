Приложение готово, работает на вашем телефоне — пора отдать его людям. Публикация в магазины пугает новичков количеством шагов: ключи подписи, иконки, версии, анкеты, тестирование. В этом уроке пройдём весь путь по порядку — от подготовки сборки до TestFlight и внутреннего тестирования в Google Play — и наведём порядок в проекте с помощью README и Makefile.

## Чек-лист перед первой сборкой

Перед тем как идти в магазины, проверьте основы:

- **Уникальный идентификатор**: `applicationId` (Android) и Bundle ID (iOS), например `com.yourcompany.shop`. После публикации его **нельзя изменить** — это будет уже другое приложение. Никаких `com.example`.
- **Название** приложения — `android:label` в манифесте и `CFBundleDisplayName` в `Info.plist`.
- **Иконка и splash-экран** — свои, а не стандартные Flutter.
- **Версия** в `pubspec.yaml`.
- **Боевой flavor и конфиг** — `prod`, правильный адрес API (см. [урок про сборки и flavors](lesson:build-types-jit-aot)).
- **Нет отладочного мусора**: `print`, тестовые кнопки, открытые логи с токенами.
- **Политика конфиденциальности** — страница в интернете. Оба магазина требуют ссылку на неё.

## Версии приложения

Версия задаётся одной строкой в `pubspec.yaml`:

```yaml
version: 1.4.2+17
```

| Часть | Что это | Android | iOS |
| --- | --- | --- | --- |
| `1.4.2` | Версия для людей (видна в магазине) | `versionName` | `CFBundleShortVersionString` |
| `17` | Номер сборки (build number) | `versionCode` | `CFBundleVersion` |

Версию для людей обычно ведут по **семантическому версионированию** `MAJOR.MINOR.PATCH`: `PATCH` — исправили баги (1.4.2 → 1.4.3), `MINOR` — новая функция (1.4.3 → 1.5.0), `MAJOR` — большие несовместимые изменения (1.5.0 → 2.0.0).

<aside class="callout" data-icon="📌" markdown="1">

Номер сборки после `+` должен **расти с каждой загрузкой** в магазин. Google Play и App Store отклонят файл с уже использованным номером, даже если вы его удалили. Переопределить значения можно и при сборке: `flutter build appbundle --build-name=1.4.3 --build-number=18`.

</aside>

## Иконки и splash-экран

Рисовать иконки всех размеров вручную не нужно — это делает пакет [flutter_launcher_icons](https://pub.dev/packages/flutter_launcher_icons). Подготовьте квадратную картинку 1024×1024 без прозрачности (iOS не принимает прозрачные иконки).

```bash
flutter pub add dev:flutter_launcher_icons
```

```yaml
flutter_launcher_icons:
  android: true
  ios: true
  image_path: "assets/icon/icon.png"
  remove_alpha_ios: true
  adaptive_icon_background: "#FFFFFF"
  adaptive_icon_foreground: "assets/icon/icon_foreground.png"
```

```bash
dart run flutter_launcher_icons
```

- `adaptive_icon_*` — адаптивная иконка Android: передний план отдельно от фона, чтобы система могла обрезать её кругом или квадратом.
- Команда сама сгенерирует все размеры в `android/app/src/main/res/` и `ios/Runner/Assets.xcassets/`.

Splash-экран аналогично генерирует пакет [flutter_native_splash](https://pub.dev/packages/flutter_native_splash) командой `dart run flutter_native_splash:create`.

## Android: подпись приложения

Каждый APK/AAB должен быть подписан. Подпись — как печать компании: доказывает, что обновление пришло от того же разработчика.

### Шаг 1. Создаём ключ загрузки

```bash
keytool -genkey -v -keystore ~/upload-keystore.jks \
  -keyalg RSA -keysize 2048 -validity 10000 -alias upload
```

Команда спросит пароль и данные владельца. На выходе — файл `upload-keystore.jks`. `keytool` входит в JDK; если команды нет, используйте ту, что лежит внутри Android Studio.

### Шаг 2. Файл key.properties

Создайте `android/key.properties`:

```text
storePassword=YOUR_STORE_PASSWORD
keyPassword=YOUR_KEY_PASSWORD
keyAlias=upload
storeFile=/Users/you/upload-keystore.jks
```

<aside class="callout" data-icon="🔐" markdown="1">

`key.properties` и `.jks` **никогда** не коммитят — добавьте их в `.gitignore`. Храните копию ключа и паролей в надёжном месте (менеджер паролей). Потеряли ключ загрузки — придётся просить Google сбросить его, а это время. Для CI ключ передают через секреты (переменные окружения).

</aside>

### Шаг 3. Подключаем ключ в Gradle

В `android/app/build.gradle.kts`:

```text
import java.util.Properties
import java.io.FileInputStream

val keystoreProperties = Properties()
val keystorePropertiesFile = rootProject.file("key.properties")
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(FileInputStream(keystorePropertiesFile))
}

android {
    // ...
    signingConfigs {
        create("release") {
            keyAlias = keystoreProperties["keyAlias"] as String
            keyPassword = keystoreProperties["keyPassword"] as String
            storeFile = keystoreProperties["storeFile"]?.let { file(it) }
            storePassword = keystoreProperties["storePassword"] as String
        }
    }
    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
        }
    }
}
```

- Первые строки читают `key.properties`, если он есть.
- `signingConfigs` описывает ключ, а `buildTypes.release` говорит «подписывай release этим ключом».

Теперь `flutter build appbundle --release` (с вашим `--flavor` и `--dart-define-from-file`) выдаст подписанный AAB.

### Play App Signing

В Google Play используется схема из двух ключей. Вы подписываете файл **ключом загрузки** (upload key), а Google переподписывает приложение своим **ключом приложения**, который хранится у него. Если ключ загрузки утечёт или потеряется, его можно заменить через поддержку — приложение не «умрёт».

## Google Play: внутреннее тестирование

1. Зарегистрируйте аккаунт разработчика в [Google Play Console](https://play.google.com/console) (разовый взнос).
2. **Create app**: название, язык, приложение или игра, бесплатное или платное.
3. Заполните раздел **App content**: политика конфиденциальности, **Data safety** (какие данные собираете), возрастной рейтинг, целевая аудитория, реклама.
4. **Testing → Internal testing → Create new release**, загрузите `.aab`, напишите, что нового.
5. Добавьте тестировщиков списком email и отправьте им ссылку-приглашение.

| Трек | Для кого | Особенности |
| --- | --- | --- |
| Internal testing | До 100 человек, ваша команда | Доступно почти сразу, без полной проверки |
| Closed testing | Выбранные группы | Нужно для новых личных аккаунтов перед продакшеном |
| Open testing | Любой желающий | Публичная страница в магазине |
| Production | Все пользователи | Полная проверка Google, можно раскатывать постепенно (staged rollout) |

<aside class="callout" data-icon="⚠️" markdown="1">

Для новых **личных** аккаунтов разработчика Google требует перед выходом в продакшен провести закрытое тестирование с определённым числом тестировщиков в течение нескольких недель. Требования периодически меняются — проверяйте актуальные условия в Play Console и [справке Google Play](https://support.google.com/googleplay/android-developer). Также Google каждый год поднимает минимальный target API level — обновляйте Flutter, чтобы `targetSdk` оставался свежим.

</aside>

## iOS: сборка и TestFlight

Для публикации в App Store нужен Mac с Xcode и платный аккаунт **Apple Developer Program**.

### Шаг 1. Bundle ID и подпись

1. Откройте `ios/Runner.xcworkspace` в Xcode.
2. **Runner → Signing & Capabilities**: выберите свою команду (Team) и включите **Automatically manage signing**. Xcode сам создаст сертификаты и provisioning profile.
3. Проверьте **Bundle Identifier** — он должен совпадать с тем, что вы создадите в App Store Connect.
4. Здесь же добавляйте capabilities — Push Notifications, Associated Domains (для Universal Links) и т. д.

**Сертификат** подтверждает, кто вы, а **provisioning profile** — что это приложение с этим Bundle ID можно подписать вашим сертификатом. Автоматическое управление избавляет от ручной возни.

### Шаг 2. Карточка в App Store Connect

В [App Store Connect](https://appstoreconnect.apple.com) → **Apps → New App**: платформа iOS, название, язык, Bundle ID, SKU (любой внутренний код). Затем заполните **App Privacy** — какие данные собирает приложение (включая те, что собирают Firebase Analytics и Crashlytics).

### Шаг 3. Сборка и загрузка

```bash
flutter build ipa --release --flavor prod --dart-define-from-file=config/prod.json
```

Готовый файл — в `build/ios/ipa/`. Загрузить его можно приложением **Transporter** от Apple (перетащить `.ipa`) или через Xcode: откройте `build/ios/archive/Runner.xcarchive` и нажмите **Distribute App** в окне Organizer.

### Шаг 4. TestFlight

**TestFlight** — официальная бета-площадка Apple. Через 10–30 минут после загрузки сборка появится во вкладке TestFlight.

| | Внутренние тестировщики | Внешние тестировщики |
| --- | --- | --- |
| Кто | Участники вашей команды в App Store Connect | Любые люди по email или публичной ссылке |
| Лимит | До 100 | До 10 000 |
| Проверка Apple | Не нужна | Нужна Beta App Review для первой сборки версии |

Тестировщики устанавливают приложение **TestFlight** из App Store и получают вашу сборку. Сборка живёт 90 дней.

<aside class="callout" data-icon="💡" markdown="1">

Самые частые причины отказа на ревью App Store: приложение падает или «пустое», нет тестового аккаунта для проверяющего (укажите логин и пароль в **App Review Information**), нет кнопки удаления аккаунта при наличии регистрации, описание не совпадает с функциями. Внимательно читайте ответ ревьюера — там всегда указан пункт правил.

</aside>

## README: лицо проекта

`README.md` — первое, что видит новый разработчик (и работодатель, открывший ваш GitHub). Хороший README отвечает на вопросы: что это, как запустить, как устроено.

```text
# Shop — интернет-магазин на Flutter

Мобильное приложение магазина: каталог, корзина, авторизация, чат с поддержкой.

## Стек
Flutter 3, Dart 3, flutter_bloc, dio, get_it, firebase (auth, database, analytics, crashlytics)

## Архитектура
Clean Architecture: lib/features/<feature>/{data, domain, presentation}

## Запуск
1. flutter pub get
2. Скопируйте config/dev.example.json в config/dev.json и заполните значения
3. make run-dev

## Сборка
make build-android   — AAB для Google Play
make build-ios       — IPA для App Store

## Скриншоты
(3–4 скриншота основных экранов)
```

В реальном README команды оформляют блоками кода, а скриншоты кладут в папку `docs/`. Главное правило: человек должен запустить проект за 5 минут, ни о чём вас не спрашивая.

## Makefile: команды в одно слово

Команды сборки длинные, их легко забыть или ошибиться в флаге. **Makefile** — файл с короткими псевдонимами для таких команд. Утилита `make` есть на macOS и Linux из коробки.

```text
.PHONY: get gen run-dev build-android build-ios clean

get:
	flutter pub get

gen:
	dart run build_runner build --delete-conflicting-outputs

run-dev:
	flutter run --flavor dev --dart-define-from-file=config/dev.json

build-android:
	flutter build appbundle --release --flavor prod \
		--dart-define-from-file=config/prod.json \
		--obfuscate --split-debug-info=build/symbols

build-ios:
	flutter build ipa --release --flavor prod \
		--dart-define-from-file=config/prod.json \
		--obfuscate --split-debug-info=build/symbols

clean:
	flutter clean && flutter pub get
```

Запуск: `make gen`, `make build-android`.

- `get:` — имя команды (цель, target), под ней — что выполнить.
- `.PHONY` — говорит `make`, что это команды, а не имена файлов.
- `\` в конце строки — перенос длинной команды.

<aside class="callout" data-icon="⚠️" markdown="1">

Строки команд в Makefile должны начинаться с **табуляции**, а не с пробелов. Иначе получите ошибку `missing separator`. Проверьте, что редактор не заменяет Tab на пробелы в этом файле.

</aside>

## Типичные ошибки

- **«Version code has already been used»** — не увеличили номер сборки после `+`.
- **Приложение подписано debug-ключом** — Google Play не примет такой файл; проверьте `signingConfig` в `release`.
- **Прозрачная иконка на iOS** — App Store отклонит загрузку; используйте `remove_alpha_ios: true`.
- **Ключ в репозитории** — `key.properties` и `.jks` закоммичены в Git.
- **Bundle ID в Xcode не совпадает** с App Store Connect — загрузка не находит приложение.

## Практика

1. Сгенерируйте свою иконку через `flutter_launcher_icons` и поднимите версию до `1.0.0+1`. Ожидаемый результат: на телефоне новая иконка, в настройках приложения — версия 1.0.0.
2. Создайте ключ загрузки, настройте подпись и соберите `flutter build appbundle`. Ожидаемый результат: подписанный AAB в `build/app/outputs/bundle/`, а `key.properties` не попал в `git status`.
3. Напишите Makefile с целями `get`, `gen`, `run-dev`, `build-android`. Ожидаемый результат: `make build-android` собирает релиз одной командой.
4. Оформите README для своего проекта по шаблону из урока. Ожидаемый результат: одногруппник запускает проект по README без ваших подсказок.
5. Если есть доступ к аккаунтам разработчика — загрузите сборку во внутреннее тестирование Google Play или TestFlight и установите её на свой телефон. Ожидаемый результат: приложение ставится из магазина.

## Итоги

- Идентификатор приложения выбирают один раз и навсегда; `com.example` не годится.
- `version: 1.4.2+17` — версия для людей и номер сборки, который растёт с каждой загрузкой.
- Иконки и splash генерируют пакетами, а не вручную.
- Android-релиз подписывается ключом загрузки; ключ и пароли не попадают в Git.
- Сначала — внутреннее тестирование в Google Play и TestFlight, потом продакшен.
- README объясняет, как запустить проект, а Makefile превращает длинные команды в короткие.
