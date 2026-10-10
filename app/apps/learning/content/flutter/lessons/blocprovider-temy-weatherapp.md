В этом уроке соберём первые знания месяца в одно работающее приложение. Сначала разберёмся, как `BlocProvider` раздаёт Bloc виджетам и сам закрывает его, затем сделаем светлую и тёмную тему с переключателем, а в конце напишем WeatherApp, который ищет город и показывает реальную погоду с бесплатного API Open-Meteo.

## BlocProvider

### Что это и зачем

Bloc нужно создать и передать виджетам. Через конструкторы неудобно: на пути бывает пять промежуточных виджетов, которым Bloc не нужен.

`BlocProvider` кладёт Bloc в дерево виджетов, и любой потомок может достать его через `context.read<T>()` или `BlocBuilder`. Аналогия — Wi-Fi-роутер в квартире: вы не тянете кабель к каждому устройству, все устройства в зоне покрытия просто подключаются.

```dart
BlocProvider(
  create: (context) => CounterCubit(),
  child: const CounterPage(),
)
```

- `create` — функция, которая создаёт Bloc. Вызывается **лениво**: при первом обращении, а не сразу. Чтобы создать сразу, укажите `lazy: false`.
- `child` — поддерево, которому будет доступен Bloc.
- Когда `BlocProvider` удаляется из дерева (например, закрыли экран), он **сам вызывает `close()`** у Bloc. Утечек памяти не будет.

### BlocProvider.value

Иногда Bloc уже создан, и его надо передать на другой экран, а не создавать новый:

```dart
Navigator.of(context).push(
  MaterialPageRoute(
    builder: (_) => BlocProvider.value(
      value: context.read<WeatherBloc>(),
      child: const DetailsPage(),
    ),
  ),
);
```

`BlocProvider.value` **не закрывает** Bloc при удалении — ведь создавал его не он. Правило: создаёте новый — `create`, передаёте существующий — `.value`.

<aside class="callout" data-icon="⚠️" markdown="1">

Никогда не пишите `BlocProvider.value(value: CounterCubit())`. Новый Cubit, созданный так, никто не закроет. И наоборот: не передавайте существующий Bloc через `create: (_) => existingBloc` — его закроют вместе с новым экраном, и старый экран сломается.

</aside>

### MultiBlocProvider и RepositoryProvider

Когда провайдеров несколько, вместо вложенной «лесенки» используйте `MultiBlocProvider`. А для объектов, которые не являются Bloc (репозитории, клиенты API), есть `RepositoryProvider`:

```dart
RepositoryProvider(
  create: (_) => WeatherRepository(Dio()),
  child: MultiBlocProvider(
    providers: [
      BlocProvider(create: (_) => ThemeCubit()),
      BlocProvider(create: (context) => WeatherBloc(context.read<WeatherRepository>())),
    ],
    child: const App(),
  ),
)
```

Обратите внимание: внутри `create` для `WeatherBloc` мы достаём репозиторий через `context.read` — он уже есть выше по дереву.

### Проблема с context

`context.read<CounterCubit>()` в том же методе `build`, где создан `BlocProvider`, упадёт: этот context находится *выше* провайдера. Решение то же, что в уроке [про Builder](lesson:changenotifier-futurebuilder): обернуть кнопку в `Builder` или вынести `child` в отдельный виджет со своим `build`.

## Светлая и тёмная тема

### ThemeData и ColorScheme

`ThemeData` — набор настроек оформления всего приложения: цвета, шрифты, форма кнопок. Самый простой способ получить красивую и согласованную палитру — `ColorScheme.fromSeed`: вы задаёте один «основной» цвет, а Flutter по правилам Material 3 рассчитывает остальные.

```dart
import 'package:flutter/material.dart';

class AppTheme {
  static const _seed = Colors.indigo;

  static final light = ThemeData(
    colorScheme: ColorScheme.fromSeed(seedColor: _seed),
  );

  static final dark = ThemeData(
    colorScheme: ColorScheme.fromSeed(
      seedColor: _seed,
      brightness: Brightness.dark,
    ),
  );
}
```

В `MaterialApp` есть три параметра:

| Параметр | Что задаёт |
| --- | --- |
| `theme` | Светлая тема |
| `darkTheme` | Тёмная тема |
| `themeMode` | Какую использовать: `ThemeMode.light`, `ThemeMode.dark` или `ThemeMode.system` (как в настройках телефона) |

### Цвета из темы в виджетах

Чтобы виджеты меняли цвет вместе с темой, не пишите `Colors.white` — берите цвета из темы:

```dart
final colors = Theme.of(context).colorScheme;

Container(
  color: colors.primaryContainer,
  child: Text(
    'Бишкек',
    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
          color: colors.onPrimaryContainer,
        ),
  ),
)
```

Пара `primaryContainer` / `onPrimaryContainer` читаема в обеих темах. Префикс `on` означает «цвет того, что лежит поверх».

<aside class="callout" data-icon="⚠️" markdown="1">

Захардкоженные цвета — главная причина «невидимого» текста: белые буквы на белом фоне в светлой теме или чёрные на чёрном в тёмной. Перед сдачей проекта всегда переключайте тему и проходите по всем экранам.

</aside>

### ThemeCubit: переключение

```dart
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

class ThemeCubit extends Cubit<ThemeMode> {
  ThemeCubit() : super(ThemeMode.system);

  void toggle() {
    emit(state == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark);
  }

  void setMode(ThemeMode mode) => emit(mode);
}
```

Подключаем к `MaterialApp`:

```dart
class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<ThemeCubit, ThemeMode>(
      builder: (context, mode) {
        return MaterialApp(
          title: 'WeatherApp',
          theme: AppTheme.light,
          darkTheme: AppTheme.dark,
          themeMode: mode,
          home: const WeatherPage(),
        );
      },
    );
  }
}
```

Кнопка в `AppBar`:

```dart
IconButton(
  tooltip: 'Сменить тему',
  icon: Icon(
    Theme.of(context).brightness == Brightness.dark ? Icons.light_mode : Icons.dark_mode,
  ),
  onPressed: () => context.read<ThemeCubit>().toggle(),
)
```

`Theme.of(context).brightness` — тема, применённая **сейчас** (важно в режиме `system`).

## WeatherApp на Open-Meteo

Теперь соберём приложение: пользователь вводит город → мы находим его координаты → загружаем погоду → показываем. Open-Meteo не требует ключа API.

### Шаг 1. Пакеты

```bash
flutter create weather_app
cd weather_app
flutter pub add flutter_bloc equatable dio
```

### Шаг 2. Репозиторий

Для краткости модели здесь ручные; в итоговом проекте их сгенерирует json_serializable (см. [урок про JSON](lesson:json-modeli-dio-get)).

```dart
import 'package:dio/dio.dart';

class Weather {
  const Weather({required this.city, required this.temperature, required this.windSpeed, required this.code});
  final String city;
  final double temperature;
  final double windSpeed;
  final int code;
}

class WeatherRepository {
  WeatherRepository(this._dio);
  final Dio _dio;

  Future<Weather> getByCity(String name) async {
    final geo = await _dio.get<Map<String, dynamic>>(
      'https://geocoding-api.open-meteo.com/v1/search',
      queryParameters: {'name': name, 'count': 1, 'language': 'ru'},
    );
    final results = geo.data?['results'] as List<dynamic>?;
    if (results == null || results.isEmpty) {
      throw Exception('Город «$name» не найден');
    }
    final place = results.first as Map<String, dynamic>;

    final forecast = await _dio.get<Map<String, dynamic>>(
      'https://api.open-meteo.com/v1/forecast',
      queryParameters: {
        'latitude': place['latitude'],
        'longitude': place['longitude'],
        'current': 'temperature_2m,wind_speed_10m,weather_code',
        'timezone': 'auto',
      },
    );
    final current = forecast.data!['current'] as Map<String, dynamic>;
    return Weather(
      city: place['name'] as String,
      temperature: (current['temperature_2m'] as num).toDouble(),
      windSpeed: (current['wind_speed_10m'] as num).toDouble(),
      code: current['weather_code'] as int,
    );
  }
}
```

Разбор:

1. Первый запрос — **геокодинг**: по названию получаем координаты. Если город не найден, поля `results` в ответе просто нет — отсюда проверка на `null`.
2. Второй запрос — погода по координатам. Адреса полные: это два разных сервера.

### Шаг 3. Bloc

```dart
import 'package:dio/dio.dart';
import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

sealed class WeatherEvent {}

final class WeatherCityRequested extends WeatherEvent {
  WeatherCityRequested(this.city);
  final String city;
}

sealed class WeatherState extends Equatable {
  const WeatherState();
  @override
  List<Object?> get props => [];
}

final class WeatherInitial extends WeatherState {}

final class WeatherLoading extends WeatherState {}

final class WeatherSuccess extends WeatherState {
  const WeatherSuccess(this.weather);
  final Weather weather;
  @override
  List<Object?> get props => [weather.city, weather.temperature, weather.code];
}

final class WeatherError extends WeatherState {
  const WeatherError(this.message);
  final String message;
  @override
  List<Object?> get props => [message];
}

class WeatherBloc extends Bloc<WeatherEvent, WeatherState> {
  WeatherBloc(this._repo) : super(WeatherInitial()) {
    on<WeatherCityRequested>((event, emit) async {
      emit(WeatherLoading());
      try {
        emit(WeatherSuccess(await _repo.getByCity(event.city)));
      } on DioException {
        emit(const WeatherError('Проблема с сетью. Попробуйте ещё раз.'));
      } catch (e) {
        emit(WeatherError(e.toString().replaceFirst('Exception: ', '')));
      }
    });
  }

  final WeatherRepository _repo;
}
```

### Шаг 4. Код погоды → текст и иконка

Open-Meteo возвращает `weather_code` по стандарту WMO. Переведём основные коды:

```dart
(String, IconData) describeWeather(int code) => switch (code) {
      0 => ('Ясно', Icons.wb_sunny),
      1 || 2 => ('Переменная облачность', Icons.wb_cloudy),
      3 => ('Пасмурно', Icons.cloud),
      45 || 48 => ('Туман', Icons.foggy),
      >= 51 && <= 67 => ('Дождь', Icons.water_drop),
      >= 71 && <= 77 => ('Снег', Icons.ac_unit),
      >= 80 && <= 82 => ('Ливень', Icons.umbrella),
      >= 95 => ('Гроза', Icons.thunderstorm),
      _ => ('Неизвестно', Icons.help_outline),
    };
```

Функция возвращает **запись** (record) Dart 3 — пару значений без класса. Паттерн `1 || 2` — «одно из», `>= 51 && <= 67` — диапазон.

### Шаг 5. Экран

```dart
class WeatherPage extends StatefulWidget {
  const WeatherPage({super.key});
  @override
  State<WeatherPage> createState() => _WeatherPageState();
}

class _WeatherPageState extends State<WeatherPage> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _search() {
    final city = _controller.text.trim();
    if (city.isNotEmpty) context.read<WeatherBloc>().add(WeatherCityRequested(city));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('WeatherApp'),
        actions: [
          IconButton(
            icon: const Icon(Icons.brightness_6),
            onPressed: () => context.read<ThemeCubit>().toggle(),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _controller,
              textInputAction: TextInputAction.search,
              onSubmitted: (_) => _search(),
              decoration: InputDecoration(
                hintText: 'Город, например Бишкек',
                suffixIcon: IconButton(icon: const Icon(Icons.search), onPressed: _search),
              ),
            ),
            const SizedBox(height: 32),
            Expanded(
              child: BlocBuilder<WeatherBloc, WeatherState>(
                builder: (context, state) => switch (state) {
                  WeatherInitial() => const Text('Введите город'),
                  WeatherLoading() => const Center(child: CircularProgressIndicator()),
                  WeatherError(:final message) => Text(message),
                  WeatherSuccess(:final weather) => _WeatherCard(weather),
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _WeatherCard extends StatelessWidget {
  const _WeatherCard(this.weather);
  final Weather weather;

  @override
  Widget build(BuildContext context) {
    final (label, icon) = describeWeather(weather.code);
    final text = Theme.of(context).textTheme;
    return Column(
      children: [
        Icon(icon, size: 96, color: Theme.of(context).colorScheme.primary),
        Text(weather.city, style: text.headlineMedium),
        Text('${weather.temperature.round()}°C', style: text.displayMedium),
        Text('$label · ветер ${weather.windSpeed} км/ч'),
      ],
    );
  }
}
```

`final (label, icon) = describeWeather(...)` — деструктуризация записи в две переменные.

### Шаг 6. main.dart

```dart
void main() {
  runApp(
    RepositoryProvider(
      create: (_) => WeatherRepository(Dio()),
      child: MultiBlocProvider(
        providers: [
          BlocProvider(create: (_) => ThemeCubit()),
          BlocProvider(create: (context) => WeatherBloc(context.read<WeatherRepository>())),
        ],
        child: const App(),
      ),
    ),
  );
}
```

Провайдеры стоят **над** `MaterialApp`, поэтому `ThemeCubit` и `WeatherBloc` доступны на всех экранах приложения.

## Типичные ошибки

- `BlocProvider` поставили внутри `home`, а `ThemeCubit` читают в `MaterialApp` — провайдер должен быть выше.
- Цвета `Colors.black` в тексте — в тёмной теме текст пропадает.
- Нет проверки `results == null` в геокодинге — при опечатке в названии приложение падает.

## Практика

1. **Три режима темы.** Замените кнопку-переключатель на `SegmentedButton<ThemeMode>` с вариантами «Светлая», «Тёмная», «Как в системе». Ожидаемый результат: режим `system` следует настройкам эмулятора.
2. **Своя палитра.** Поменяйте `seedColor` и настройте `appBarTheme` и `cardTheme` в обеих темах. Ожидаемый результат: все экраны читаемы в обеих темах.
3. **Кнопка «Обновить».** Сохраните последний город в Bloc и добавьте `RefreshIndicator` для повторного запроса. Ожидаемый результат: свайп вниз обновляет погоду.
4. **Детальный экран.** По нажатию на карточку открывайте `DetailsPage`, передав `WeatherBloc` через `BlocProvider.value`. Ожидаемый результат: на новом экране та же погода без повторного запроса.
5. **Запоминание темы.** Сохраните выбор темы (`mode.name`) в `shared_preferences` и читайте его при старте. Ожидаемый результат: после перезапуска приложения тема остаётся прежней.

## Итоги

- `BlocProvider(create:)` создаёт Bloc лениво и закрывает его сам; `BlocProvider.value` передаёт существующий.
- `MultiBlocProvider` и `RepositoryProvider` убирают вложенность и раздают зависимости.
- Тема задаётся через `ThemeData` + `ColorScheme.fromSeed`, а `MaterialApp` принимает `theme`, `darkTheme` и `themeMode`.
- Переключение темы — это просто `Cubit<ThemeMode>` и `BlocBuilder` над `MaterialApp`.
- Цвета в виджетах берите из `Theme.of(context).colorScheme`.
- WeatherApp: геокодинг → прогноз → Bloc → экран с состояниями загрузки, ошибки и успеха.
