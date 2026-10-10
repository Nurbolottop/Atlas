Почти любое приложение получает данные с сервера, и почти всегда они приходят в формате JSON. В этом уроке научимся превращать JSON в удобные Dart-классы (модели), сравнивать их через Equatable, генерировать `fromJson`/`toJson` автоматически с `json_serializable` и делать первый настоящий GET-запрос через Dio к бесплатному погодному API Open-Meteo.

## Что такое JSON

**JSON** — текстовый формат обмена данными. Сервер присылает строку, похожую на Dart-словарь:

```json
{
  "city": "Бишкек",
  "temperature": 21.5,
  "isDay": true,
  "tags": ["солнечно", "ветрено"]
}
```

В Dart после декодирования (`jsonDecode`) это превращается в `Map<String, dynamic>`:

| JSON | Dart |
| --- | --- |
| `{ ... }` объект | `Map<String, dynamic>` |
| `[ ... ]` массив | `List<dynamic>` |
| `"текст"` | `String` |
| `21` / `21.5` | `int` / `double` |
| `true` / `false` | `bool` |
| `null` | `null` |

Работать с `Map` напрямую неудобно: `data['temprature']` с опечаткой компилятор не поймает, а тип `dynamic` не подскажет, что внутри. Поэтому JSON превращают в **модель** — обычный класс с типизированными полями.

## Модель вручную: fromJson и toJson

```dart
class Weather {
  const Weather({
    required this.city,
    required this.temperature,
    required this.isDay,
  });

  final String city;
  final double temperature;
  final bool isDay;

  factory Weather.fromJson(Map<String, dynamic> json) {
    return Weather(
      city: json['city'] as String,
      temperature: (json['temperature'] as num).toDouble(),
      isDay: json['isDay'] as bool,
    );
  }

  Map<String, dynamic> toJson() => {
        'city': city,
        'temperature': temperature,
        'isDay': isDay,
      };
}
```

Разбор:

- **`fromJson`** — именованный `factory`-конструктор: принимает словарь и возвращает объект. «Из JSON в класс».
- **`toJson`** — обратное: объект в словарь, чтобы отправить на сервер или сохранить.
- `(json['temperature'] as num).toDouble()` — сервер может прислать `21` (int) вместо `21.0`. Приведение через `num` спасает от ошибки `type 'int' is not a subtype of type 'double'`.

Использование:

```dart
import 'dart:convert';

void main() {
  const raw = '{"city":"Бишкек","temperature":21,"isDay":true}';
  final map = jsonDecode(raw) as Map<String, dynamic>;
  final weather = Weather.fromJson(map);
  print(weather.temperature); // 21.0
  print(jsonEncode(weather.toJson()));
}
```

<aside class="callout" data-icon="⚠️" markdown="1">

Если ключа в JSON нет, `json['city']` вернёт `null`, и `as String` упадёт. Для необязательных полей делайте тип nullable (`String?`) или задавайте значение по умолчанию: `json['city'] as String? ?? 'Неизвестно'`.

</aside>

## Equatable: сравнение по значению

По умолчанию Dart сравнивает объекты **по ссылке**: два одинаковых `Weather` — разные объекты, и `==` вернёт `false`.

```dart
final a = Weather(city: 'Бишкек', temperature: 20, isDay: true);
final b = Weather(city: 'Бишкек', temperature: 20, isDay: true);
print(a == b); // false
```

Для Bloc это важно: он сравнивает новое состояние со старым и не перерисовывает экран, если они равны. Чтобы равенство работало «по содержимому», нужно переопределить `==` и `hashCode`. Вручную это долго и легко ошибиться, поэтому есть пакет **equatable**:

```dart
import 'package:equatable/equatable.dart';

class Weather extends Equatable {
  const Weather({required this.city, required this.temperature, required this.isDay});

  final String city;
  final double temperature;
  final bool isDay;

  @override
  List<Object?> get props => [city, temperature, isDay];
}
```

Теперь `a == b` вернёт `true`. В `props` перечисляйте **все** поля, которые определяют равенство. Забыли поле — объекты с разными значениями этого поля будут считаться одинаковыми.

<aside class="callout" data-icon="📌" markdown="1">

Поля моделей и состояний делайте `final`. Equatable рассчитан на неизменяемые (immutable) объекты: если хотите «изменить» объект, создайте новый. Для этого часто пишут метод `copyWith`.

</aside>

## json_serializable: генерация кода

Когда полей десятки, писать `fromJson` руками скучно. Пакет **json_serializable** генерирует этот код по аннотациям.

### Установка

```bash
flutter pub add json_annotation
flutter pub add dev:build_runner dev:json_serializable
```

- `json_annotation` — аннотации вроде `@JsonSerializable()`, нужны в приложении;
- `build_runner` и `json_serializable` — инструменты генерации, нужны только при разработке (`dev:`).

### Модель с аннотациями

Создадим модель под настоящий ответ Open-Meteo. Файл `lib/models/current_weather.dart`:

```dart
import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';

part 'current_weather.g.dart';

@JsonSerializable()
class CurrentWeather extends Equatable {
  const CurrentWeather({
    required this.time,
    required this.temperature,
    required this.windSpeed,
    required this.weatherCode,
  });

  final String time;

  @JsonKey(name: 'temperature_2m')
  final double temperature;

  @JsonKey(name: 'wind_speed_10m')
  final double windSpeed;

  @JsonKey(name: 'weather_code')
  final int weatherCode;

  factory CurrentWeather.fromJson(Map<String, dynamic> json) =>
      _$CurrentWeatherFromJson(json);

  Map<String, dynamic> toJson() => _$CurrentWeatherToJson(this);

  @override
  List<Object?> get props => [time, temperature, windSpeed, weatherCode];
}
```

Разбор:

- `part 'current_weather.g.dart';` — подключает файл, который сгенерирует build_runner. Имя должно совпадать с именем текущего файла плюс `.g.dart`.
- `@JsonSerializable()` — «сгенерируй для этого класса код JSON».
- `@JsonKey(name: 'temperature_2m')` — в JSON ключ называется по-другому, чем поле в Dart. Мы пишем красиво `temperature`, а генератор знает, что брать `temperature_2m`.
- `_$CurrentWeatherFromJson` и `_$CurrentWeatherToJson` — функции, которые появятся в `.g.dart`.

<aside class="callout" data-icon="💡" markdown="1">

Если в проекте все ключи JSON в стиле `snake_case`, не нужно писать `@JsonKey` на каждое поле. Укажите `@JsonSerializable(fieldRename: FieldRename.snake)` — и `windSpeed` автоматически станет `wind_speed`.

</aside>

### Запуск генерации

```bash
dart run build_runner build --delete-conflicting-outputs
```

Рядом появится `current_weather.g.dart`. Его не редактируют руками — при следующей генерации изменения затрутся. Во время активной разработки удобнее режим наблюдения:

```bash
dart run build_runner watch --delete-conflicting-outputs
```

Он сам перегенерирует код при каждом сохранении файла.

### Вложенные модели

Ответ Open-Meteo выглядит так (сокращённо):

```json
{
  "latitude": 42.875,
  "longitude": 74.625,
  "timezone": "Asia/Bishkek",
  "current": {
    "time": "2026-10-10T14:00",
    "temperature_2m": 17.3,
    "wind_speed_10m": 6.8,
    "weather_code": 2
  }
}
```

Внешний объект — тоже модель, внутри которой лежит `CurrentWeather`:

```dart
import 'package:json_annotation/json_annotation.dart';
import 'current_weather.dart';

part 'forecast_response.g.dart';

@JsonSerializable()
class ForecastResponse {
  const ForecastResponse({
    required this.latitude,
    required this.longitude,
    required this.timezone,
    required this.current,
  });

  final double latitude;
  final double longitude;
  final String timezone;
  final CurrentWeather current;

  factory ForecastResponse.fromJson(Map<String, dynamic> json) =>
      _$ForecastResponseFromJson(json);

  Map<String, dynamic> toJson() => _$ForecastResponseToJson(this);
}
```

Генератор видит, что у `CurrentWeather` есть `fromJson`, и вызовет его сам. Для вложенных объектов в `toJson` добавьте `@JsonSerializable(explicitToJson: true)`, иначе внутренний объект не превратится в `Map`.

## Dio: делаем GET-запрос

### Что такое Dio

**Dio** — HTTP-клиент для Dart. Он умеет то же, что встроенный пакет `http`, плюс: базовый адрес, таймауты, автоматический разбор JSON, перехватчики (interceptors), отмену запросов и понятные ошибки.

```bash
flutter pub add dio
```

### Что такое GET

HTTP-запрос — это «письмо» серверу. У письма есть **метод** — что мы хотим сделать. `GET` — «дай мне данные», ничего не меняя на сервере. Параметры GET-запроса передаются в адресе после `?`:

```text
https://api.open-meteo.com/v1/forecast?latitude=42.87&longitude=74.59&current=temperature_2m,wind_speed_10m,weather_code&timezone=auto
```

Open-Meteo бесплатен и не требует ключа API — идеально для учёбы.

### Создаём клиент

```dart
import 'package:dio/dio.dart';

final dio = Dio(
  BaseOptions(
    baseUrl: 'https://api.open-meteo.com/v1',
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 10),
  ),
);
```

- `baseUrl` — общая часть адреса; дальше в запросах пишем только путь.
- `connectTimeout` — сколько ждать соединения с сервером.
- `receiveTimeout` — сколько ждать ответа.

### Запрос

```dart
Future<ForecastResponse> fetchForecast(double lat, double lon) async {
  final response = await dio.get<Map<String, dynamic>>(
    '/forecast',
    queryParameters: {
      'latitude': lat,
      'longitude': lon,
      'current': 'temperature_2m,wind_speed_10m,weather_code',
      'timezone': 'auto',
    },
  );
  return ForecastResponse.fromJson(response.data!);
}
```

Разбор:

1. `dio.get<Map<String, dynamic>>` — в угловых скобках тип, который мы ожидаем в `response.data`. Dio сам декодирует JSON — `jsonDecode` не нужен.
2. `queryParameters` — Dio сам соберёт `?latitude=...&longitude=...` и правильно закодирует символы. Не склеивайте адрес строками вручную.
3. `response.data!` — тело ответа. Восклицательный знак — потому что тип nullable; при успешном ответе с JSON тело будет.
4. Возвращаем уже готовую модель, а не сырой `Map`.

Объект `Response` содержит и другие полезные поля: `response.statusCode` (например, `200`), `response.headers`, `response.requestOptions`.

### Логирование запросов

Чтобы видеть в консоли, что уходит и приходит, добавьте встроенный перехватчик:

```dart
dio.interceptors.add(LogInterceptor(responseBody: true));
```

<aside class="callout" data-icon="🔐" markdown="1">

`LogInterceptor` печатает заголовки, а в них часто лежат токены. В релизной сборке его отключают: `if (kDebugMode) dio.interceptors.add(...)` (`kDebugMode` — из `package:flutter/foundation.dart`).

</aside>

### Собираем вместе: репозиторий

Код запросов не пишут в виджетах. Его кладут в отдельный класс — **репозиторий**, который отдаёт наружу модели:

```dart
class WeatherRepository {
  WeatherRepository(this._dio);

  final Dio _dio;

  Future<CurrentWeather> getCurrent(double lat, double lon) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/forecast',
      queryParameters: {
        'latitude': lat,
        'longitude': lon,
        'current': 'temperature_2m,wind_speed_10m,weather_code',
        'timezone': 'auto',
      },
    );
    return ForecastResponse.fromJson(response.data!).current;
  }
}
```

Bloc получает репозиторий в конструкторе и вызывает `getCurrent` в обработчике события. Обработку ошибок (нет сети, код 500) добавим в следующем уроке — [Dio: POST, PUT, DELETE и состояния](lesson:dio-post-put-delete-sostoyaniya).

### Проверка на экране

Самый быстрый способ проверить — `FutureBuilder` из урока [ChangeNotifier и FutureBuilder](lesson:changenotifier-futurebuilder):

```dart
class _HomeState extends State<Home> {
  late final Future<CurrentWeather> _future =
      WeatherRepository(dio).getCurrent(42.87, 74.59);

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<CurrentWeather>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.hasError) return Text('Ошибка: ${snapshot.error}');
        if (!snapshot.hasData) return const CircularProgressIndicator();
        final w = snapshot.data!;
        return Text('${w.temperature}°C, ветер ${w.windSpeed} км/ч');
      },
    );
  }
}
```

`late final` с инициализатором создаёт Future один раз — при первом обращении, а не при каждой перерисовке.

## Типичные ошибки

- **`type 'int' is not a subtype of type 'double'`** — сервер прислал целое число. В ручном `fromJson` используйте `(x as num).toDouble()`; json_serializable делает это сам.
- **`Target of URI hasn't been generated`** — забыли запустить build_runner или имя в `part` не совпадает с именем файла.
- **Поле всегда `null`** — опечатка в `@JsonKey(name: ...)`; сверьте с реальным ответом сервера.
- **Склейка URL строкой** — пробелы и кириллица в адресе ломают запрос; используйте `queryParameters`.
- **Android без интернета** — в релизе нужен `<uses-permission android:name="android.permission.INTERNET"/>` в `AndroidManifest.xml` (в debug он добавлен автоматически).

## Практика

1. **Ручная модель.** Напишите класс `City` с полями `name`, `latitude`, `longitude`, `country`, методами `fromJson`/`toJson` и Equatable. Ожидаемый результат: `City.fromJson(city.toJson()) == city` возвращает `true`.
2. **Генерация.** Перепишите `City` на `json_serializable` и запустите build_runner. Ожидаемый результат: появился `city.g.dart`, код работает так же.
3. **Первый запрос.** Выполните GET к Open-Meteo для своего города и выведите температуру в консоль через `print`. Ожидаемый результат: в консоли реальное число, а с `LogInterceptor` — весь ответ.
4. **Геокодинг.** Сделайте запрос к `https://geocoding-api.open-meteo.com/v1/search` с параметрами `name`, `count: 5`, `language: 'ru'`. Ответ содержит массив `results`. Опишите модель `GeocodingResponse` со списком `List<City>?` (`results` может отсутствовать). Ожидаемый результат: по слову «Ош» выводится список найденных городов.
5. **Почасовой прогноз.** Добавьте параметр `hourly: 'temperature_2m'`. В ответе придут два массива — `hourly.time` и `hourly.temperature_2m`. Сделайте модель и покажите первые 12 часов в `ListView`. Ожидаемый результат: список «время — температура».

## Итоги

- JSON после декодирования — это `Map<String, dynamic>`; работать удобнее с типизированной моделью.
- `fromJson` превращает словарь в объект, `toJson` — объект в словарь.
- Equatable даёт сравнение по значению через `props` — это важно для Bloc.
- json_serializable + build_runner генерируют код; `@JsonKey(name:)` связывает поле с ключом JSON.
- Dio: `BaseOptions` с `baseUrl` и таймаутами, `dio.get(path, queryParameters: ...)`, `response.data`.
- Запросы живут в репозитории, а не в виджетах.
