Bloc — самый популярный во Flutter-командах способ управлять состоянием. Он чётко разделяет «что произошло» (события), «как на это реагировать» (логика) и «что показать» (состояние), поэтому код легко читать, тестировать и передавать коллегам. В этом уроке разберём Cubit и Bloc, научимся рисовать экран через `BlocBuilder` и выполнять одноразовые действия через `BlocListener`.

## Что такое Bloc и зачем он нужен

**BLoC** расшифровывается как *Business Logic Component* — «компонент бизнес-логики». Идея простая: виджеты ничего не считают и не ходят в сеть. Они только:

1. **сообщают**, что произошло (пользователь нажал кнопку, ввёл город);
2. **показывают** то состояние, которое им выдали.

Вся логика живёт в отдельном классе. Аналогия — кафе: посетитель (виджет) делает заказ официанту (событие), кухня (Bloc) готовит, а на стол приносят блюдо (состояние). Посетитель не заходит на кухню и не жарит котлету сам.

```text
Виджет ──событие──▶ Bloc ──новое состояние──▶ Виджет перерисовывается
```

В прошлом уроке ([ChangeNotifier](lesson:changenotifier-futurebuilder)) мы делали похожее, но там модель могла меняться как угодно и когда угодно. В Bloc каждое изменение — это новое, отдельное состояние, и всегда понятно, откуда оно взялось.

### Установка

```bash
flutter pub add flutter_bloc equatable
```

- `flutter_bloc` — сам Bloc плюс виджеты `BlocProvider`, `BlocBuilder`, `BlocListener`;
- `equatable` — помогает сравнивать состояния (подробно — в уроке [про JSON и модели](lesson:json-modeli-dio-get)).

## Cubit — упрощённый Bloc

Начнём с **Cubit**. Это Bloc без событий: вместо них — обычные методы. Внутри метода вы вызываете `emit(новоеСостояние)`, и все подписчики получают новое значение.

```dart
import 'package:flutter_bloc/flutter_bloc.dart';

class CounterCubit extends Cubit<int> {
  CounterCubit() : super(0); // начальное состояние — 0

  void increment() => emit(state + 1);
  void decrement() => emit(state - 1);
}
```

Разбор:

- `Cubit<int>` — состояние этого Cubit имеет тип `int`.
- `super(0)` — начальное состояние.
- `state` — текущее состояние, доступно внутри класса и снаружи.
- `emit(...)` — «выпустить» новое состояние. Если оно равно старому (`==`), подписчики уведомлены не будут.

## Bloc: события и состояния

### События (Event)

В полноценном Bloc виджет не вызывает методы, а **отправляет события** через `add(...)`. Событие — небольшой класс, описывающий факт: «нажали плюс», «запросили погоду для Бишкека».

Используем `sealed class` из Dart 3: компилятор будет знать полный список наследников и подскажет, если вы забыли какой-то обработать.

```dart
sealed class CounterEvent {}

final class CounterIncrementPressed extends CounterEvent {}

final class CounterDecrementPressed extends CounterEvent {}

final class CounterResetPressed extends CounterEvent {}
```

Имена событий принято писать в прошедшем времени или как факт: `...Pressed`, `...Requested`, `...Changed`. Событие — это то, что уже случилось, а не команда.

### Bloc с обработчиками

```dart
class CounterBloc extends Bloc<CounterEvent, int> {
  CounterBloc() : super(0) {
    on<CounterIncrementPressed>((event, emit) => emit(state + 1));
    on<CounterDecrementPressed>((event, emit) {
      if (state > 0) emit(state - 1);
    });
    on<CounterResetPressed>((event, emit) => emit(0));
  }
}
```

- `Bloc<CounterEvent, int>` — первый тип — события, второй — состояние.
- `on<Тип>(...)` регистрирует обработчик для конкретного события. Регистрация — в конструкторе.
- `emit` здесь приходит параметром обработчика.

Снаружи событие отправляют так: `bloc.add(CounterIncrementPressed());`.

### Состояния (State) посложнее

У счётчика состояние — просто число. В реальном экране состояний несколько: «ничего не загружено», «загружаю», «готово», «ошибка». Опишем их тоже через `sealed class`:

```dart
import 'package:equatable/equatable.dart';

sealed class WeatherState extends Equatable {
  const WeatherState();

  @override
  List<Object?> get props => [];
}

final class WeatherInitial extends WeatherState {}

final class WeatherLoading extends WeatherState {}

final class WeatherSuccess extends WeatherState {
  const WeatherSuccess(this.city, this.temperature);

  final String city;
  final double temperature;

  @override
  List<Object?> get props => [city, temperature];
}

final class WeatherFailure extends WeatherState {
  const WeatherFailure(this.message);

  final String message;

  @override
  List<Object?> get props => [message];
}
```

`props` перечисляет поля, по которым два состояния считаются равными. Без этого два `WeatherSuccess('Бишкек', 20)` были бы разными объектами, и экран перерисовывался бы зря.

### Асинхронный обработчик

Bloc особенно хорош для асинхронной логики: обработчик может быть `async`, а `emit` можно вызывать несколько раз.

```dart
sealed class WeatherEvent {}

final class WeatherRequested extends WeatherEvent {
  WeatherRequested(this.city);
  final String city;
}

class WeatherBloc extends Bloc<WeatherEvent, WeatherState> {
  WeatherBloc() : super(WeatherInitial()) {
    on<WeatherRequested>(_onRequested);
  }

  Future<void> _onRequested(
    WeatherRequested event,
    Emitter<WeatherState> emit,
  ) async {
    emit(WeatherLoading());
    try {
      await Future.delayed(const Duration(seconds: 1)); // имитация сети
      if (event.city.trim().isEmpty) throw Exception('Пустое название');
      emit(WeatherSuccess(event.city, 21.5));
    } catch (e) {
      emit(WeatherFailure('Не удалось загрузить: $e'));
    }
  }
}
```

Разбор:

1. Обработчик вынесен в отдельный метод `_onRequested` — так конструктор остаётся коротким.
2. Сначала `emit(WeatherLoading())` — экран сразу покажет индикатор.
3. Потом ждём «ответ» и выпускаем либо `WeatherSuccess`, либо `WeatherFailure`.
4. `Emitter<WeatherState>` — тип параметра `emit`.

<aside class="callout" data-icon="⚠️" markdown="1">

Не вызывайте `emit` после того, как обработчик завершился (например, внутри `.then()` без `await` или в таймере). Bloc выбросит ошибку «emit was called after an event handler completed». Всегда пишите `await` перед асинхронными вызовами внутри обработчика.

</aside>

## Cubit или Bloc — сравнение

| | Cubit | Bloc |
| --- | --- | --- |
| Как вызвать | Метод: `cubit.increment()` | Событие: `bloc.add(Incremented())` |
| Кода | Меньше | Больше (классы событий) |
| Отслеживаемость | Видно только состояния | Видны и события, и состояния |
| Особые возможности | — | Трансформеры событий (debounce, отмена старых запросов) |
| Когда брать | Простые экраны: тема, счётчик, фильтр | Поиск, формы, сложные сценарии |

Правило для старта: начинайте с Cubit; если логика разрастается или нужна обработка частых событий (поиск при наборе текста) — переходите на Bloc. Виджеты для них одинаковые.

## BlocBuilder: рисуем экран по состоянию

Чтобы виджеты получили доступ к Bloc, его нужно «положить» в дерево через `BlocProvider`. Подробно мы разберём его в уроке [BlocProvider и темы](lesson:blocprovider-temy-weatherapp), а пока просто используем:

```dart
void main() {
  runApp(
    MaterialApp(
      home: BlocProvider(
        create: (_) => WeatherBloc(),
        child: const WeatherPage(),
      ),
    ),
  );
}
```

`BlocBuilder` подписывается на Bloc и вызывает `builder` при каждом новом состоянии:

```dart
class WeatherPage extends StatelessWidget {
  const WeatherPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Погода')),
      body: BlocBuilder<WeatherBloc, WeatherState>(
        builder: (context, state) {
          return switch (state) {
            WeatherInitial() => const Center(child: Text('Введите город')),
            WeatherLoading() => const Center(child: CircularProgressIndicator()),
            WeatherSuccess(:final city, :final temperature) =>
              Center(child: Text('$city: $temperature°C')),
            WeatherFailure(:final message) => Center(child: Text(message)),
          };
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.read<WeatherBloc>().add(WeatherRequested('Бишкек')),
        child: const Icon(Icons.refresh),
      ),
    );
  }
}
```

Разбор:

- `BlocBuilder<WeatherBloc, WeatherState>` — указываем тип Bloc и тип состояния.
- `switch (state)` с паттернами Dart 3: так как `WeatherState` — `sealed`, компилятор проверит, что мы обработали **все** четыре варианта.
- `WeatherSuccess(:final city, :final temperature)` — деструктуризация: достаём поля прямо в паттерне.
- `context.read<WeatherBloc>()` — получить Bloc из дерева без подписки, чтобы отправить событие.

### buildWhen: перерисовывать не всегда

```dart
BlocBuilder<WeatherBloc, WeatherState>(
  buildWhen: (previous, current) => current is! WeatherLoading,
  builder: (context, state) => /* ... */ const SizedBox(),
)
```

`buildWhen` получает старое и новое состояние и возвращает `true`, если нужно перерисовать. Здесь при загрузке на экране остаются старые данные, а не спиннер.

<aside class="callout" data-icon="📌" markdown="1">

`builder` в `BlocBuilder` может вызываться много раз и в любой момент. Внутри него — только построение виджетов. Никаких переходов на другой экран, SnackBar и запросов. Для этого есть `BlocListener`.

</aside>

## BlocListener: одноразовые действия

Некоторые реакции должны выполниться **один раз** на изменение состояния: показать SnackBar с ошибкой, открыть диалог, перейти на другой экран. Для этого — `BlocListener`. Он ничего не рисует, а вызывает `listener`.

```dart
BlocListener<WeatherBloc, WeatherState>(
  listenWhen: (previous, current) => current is WeatherFailure,
  listener: (context, state) {
    if (state is WeatherFailure) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(state.message)),
      );
    }
  },
  child: const WeatherView(),
)
```

- `listenWhen` — как `buildWhen`, только для слушателя.
- `listener` вызывается ровно один раз на каждое подходящее новое состояние.
- `child` — обычный виджет, который рисуется как есть.

Если слушателей несколько, используйте `MultiBlocListener`, чтобы не строить «лесенку» вложенности:

```dart
MultiBlocListener(
  listeners: [
    BlocListener<WeatherBloc, WeatherState>(listener: (context, state) {}),
    BlocListener<CounterCubit, int>(listener: (context, state) {}),
  ],
  child: const WeatherView(),
)
```

<aside class="callout" data-icon="💡" markdown="1">

Когда нужны одновременно и перерисовка, и одноразовое действие, есть `BlocConsumer` — `BlocBuilder` и `BlocListener` в одном виджете. Его и `BlocSelector` мы подробно разберём в пятом месяце, в уроке [BlocSelector и BlocConsumer](lesson:blocselector-blocconsumer).

</aside>

## context.read и context.watch

| Метод | Что делает | Где использовать |
| --- | --- | --- |
| `context.read<T>()` | Берёт Bloc один раз, не подписывается | В `onPressed`, `initState`, колбэках |
| `context.watch<T>()` | Берёт Bloc и перерисовывает виджет при изменении | Только в `build` |

```dart
// внутри build
final count = context.watch<CounterCubit>().state;
return Text('$count');
```

Обычно `BlocBuilder` удобнее `watch`, потому что перерисовывает только свою часть, а не весь `build`.

## Типичные ошибки

- **`ProviderNotFoundException`** — вы обращаетесь к Bloc, которого нет выше по дереву. Проверьте, что `BlocProvider` стоит над этим виджетом.
- **Состояние «не обновляется»** — вы изменили поле старого состояния вместо создания нового объекта, или забыли поля в `props`.
- **SnackBar показывается многократно** — его вызвали в `builder`, а не в `listener`.
- **`context.watch` в `onPressed`** — бросит ошибку; в колбэках только `read`.
- **Логика в виджетах** — если в `onPressed` больше одной строки, скорее всего, эту логику пора перенести в Bloc.

## Практика

1. **Cubit-счётчик.** Сделайте `CounterCubit` с методами `increment`, `decrement`, `reset` и экран с тремя кнопками через `BlocBuilder`. Ожидаемый результат: число меняется, кнопки вызывают методы через `context.read`.
2. **Тот же счётчик на Bloc.** Перепишите его на `CounterBloc` с `sealed`-событиями. Ожидаемый результат: поведение не изменилось, а виджеты почти не поменялись — сравните объём кода.
3. **Слушатель рубежа.** Добавьте `BlocListener`, который показывает SnackBar «Десятка!», когда счётчик становится кратным 10. Ожидаемый результат: SnackBar появляется один раз при каждом достижении, а не при каждом нажатии.
4. **Погода-заглушка.** Соберите `WeatherBloc` из урока с `TextField` для ввода города. Пустой ввод → `WeatherFailure` и SnackBar через `BlocListener`. Ожидаемый результат: видны все четыре состояния.
5. **buildWhen.** В погоде сделайте так, чтобы при повторной загрузке старый результат оставался на экране, а сверху появлялась тонкая полоска `LinearProgressIndicator`. Ожидаемый результат: текст не исчезает на время загрузки.

## Итоги

- Bloc отделяет логику от UI: виджет отправляет события и показывает состояния.
- Cubit — упрощённый Bloc с методами и `emit`; Bloc — с классами событий и обработчиками `on<Event>`.
- Состояния и события удобно описывать `sealed`-классами и обрабатывать через `switch`.
- `BlocBuilder` рисует UI по состоянию, `buildWhen` ограничивает перерисовки.
- `BlocListener` — для одноразовых действий: SnackBar, диалоги, навигация.
- `context.read` — в колбэках, `context.watch` — только в `build`.
