До сих пор вы обновляли экран через `setState` внутри одного `StatefulWidget`. Это работает, пока данные живут в одном виджете, но в реальном приложении одни и те же данные нужны сразу нескольким экранам. В этом уроке разберём встроенные во Flutter инструменты состояния — `ChangeNotifier` и `ValueNotifier`, научимся показывать асинхронные данные через `FutureBuilder` и поймём, зачем нужен маленький, но важный виджет `Builder`.

## Что такое состояние и почему setState мало

**Состояние (state)** — это любые данные, от которых зависит внешний вид экрана: число на счётчике, список городов, флаг «идёт загрузка», выбранная тема.

`setState` хорош для локального состояния: например, открыт ли выпадающий список. Проблемы начинаются, когда:

- одни данные нужны в разных местах (корзина в шапке и на странице оформления);
- логика смешивается с вёрсткой — метод `build` разрастается до сотен строк;
- при каждом `setState` перестраивается весь виджет, даже если поменялась одна цифра.

Решение — вынести данные и логику в отдельный объект, который сам сообщает: «я изменился». Виджеты подписываются на него и перерисовываются, когда приходит сигнал. Это паттерн **«наблюдатель»** (observer): как подписка на канал — вы не проверяете канал каждые пять минут, вам приходит уведомление о новом видео.

## ChangeNotifier

### Что это

`ChangeNotifier` — класс из пакета `flutter/foundation.dart`. У него есть список слушателей и метод `notifyListeners()`, который «звонит» всем подписчикам. Вы наследуете от него свой класс, храните в нём данные и вызываете `notifyListeners()` после каждого изменения.

### Пример: модель счётчика

```dart
import 'package:flutter/foundation.dart';

class CounterModel extends ChangeNotifier {
  int _count = 0;

  int get count => _count;

  void increment() {
    _count++;
    notifyListeners();
  }

  void reset() {
    _count = 0;
    notifyListeners();
  }
}
```

Разбор:

- `_count` — приватное поле. Снаружи его нельзя поменять напрямую, только через методы. Так никто не забудет вызвать `notifyListeners()`.
- `get count` — геттер, чтобы читать значение.
- `increment()` меняет данные и сразу оповещает слушателей.

### Как подписать виджет: ListenableBuilder

Чтобы экран реагировал на изменения, используем `ListenableBuilder`. Он принимает любой `Listenable` (а `ChangeNotifier` им является) и вызывает `builder` при каждом `notifyListeners()`.

```dart
import 'package:flutter/material.dart';

class CounterPage extends StatefulWidget {
  const CounterPage({super.key});

  @override
  State<CounterPage> createState() => _CounterPageState();
}

class _CounterPageState extends State<CounterPage> {
  final _model = CounterModel();

  @override
  void dispose() {
    _model.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('ChangeNotifier')),
      body: Center(
        child: ListenableBuilder(
          listenable: _model,
          builder: (context, child) {
            return Text(
              'Нажатий: ${_model.count}',
              style: Theme.of(context).textTheme.headlineMedium,
            );
          },
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _model.increment,
        child: const Icon(Icons.add),
      ),
    );
  }
}
```

Что здесь важно:

1. Модель создаётся **один раз** — как поле `State`, а не внутри `build`. Иначе при каждой перерисовке появлялся бы новый счётчик с нулём.
2. `ListenableBuilder` перестраивает только `Text`, а не весь `Scaffold`. Мы ни разу не вызвали `setState`.
3. `onPressed: _model.increment` — передаём ссылку на метод, без скобок.
4. В `dispose()` освобождаем модель: она отписывает всех слушателей и больше не держит память.

<aside class="callout" data-icon="⚠️" markdown="1">

Частая ошибка — поменять данные и забыть `notifyListeners()`. Значение в модели изменится, но экран об этом не узнает. Если «ничего не происходит» — первым делом проверьте этот вызов.

</aside>

<aside class="callout" data-icon="💡" markdown="1">

В старых статьях вместо `ListenableBuilder` используют `AnimatedBuilder` — он работает так же, просто имя сбивает с толку. В новом коде берите `ListenableBuilder`.

</aside>

### Параметр child: не перестраивать лишнее

Если внутри `builder` есть тяжёлая часть, которая от данных не зависит, передайте её в `child`. Она построится один раз и будет переиспользоваться:

```dart
ListenableBuilder(
  listenable: _model,
  child: const Icon(Icons.touch_app, size: 64), // строится один раз
  builder: (context, child) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        child!,
        Text('Нажатий: ${_model.count}'),
      ],
    );
  },
)
```

## ValueNotifier

### Что это

`ValueNotifier<T>` — это готовый `ChangeNotifier`, который хранит **одно значение** в поле `value`. Когда вы присваиваете новое значение, он сам вызывает `notifyListeners()`. Идеален для простых вещей: число, флаг, выбранный элемент.

Для отображения есть парный виджет — `ValueListenableBuilder`. Он сразу передаёт значение в `builder`.

### Пример: переключатель «показывать в °F»

```dart
class UnitsSwitch extends StatefulWidget {
  const UnitsSwitch({super.key});

  @override
  State<UnitsSwitch> createState() => _UnitsSwitchState();
}

class _UnitsSwitchState extends State<UnitsSwitch> {
  final _isFahrenheit = ValueNotifier<bool>(false);

  @override
  void dispose() {
    _isFahrenheit.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    const celsius = 21.0;
    return ValueListenableBuilder<bool>(
      valueListenable: _isFahrenheit,
      builder: (context, isF, _) {
        final temp = isF ? celsius * 9 / 5 + 32 : celsius;
        return SwitchListTile(
          title: Text('Сейчас ${temp.toStringAsFixed(1)}°${isF ? 'F' : 'C'}'),
          value: isF,
          onChanged: (v) => _isFahrenheit.value = v,
        );
      },
    );
  }
}
```

Разбор:

- `ValueNotifier<bool>(false)` — начальное значение `false`.
- `onChanged: (v) => _isFahrenheit.value = v` — присвоили, и всё: уведомление ушло автоматически.
- В `builder` второй параметр `isF` — текущее значение, третий (`_`) — тот же `child`, он нам не нужен.

<aside class="callout" data-icon="⚠️" markdown="1">

`ValueNotifier` уведомляет только если новое значение **не равно** старому (`==`). Если внутри лежит список и вы делаете `notifier.value.add(x)`, ссылка на список не меняется — уведомления не будет. Присваивайте новый список: `notifier.value = [...notifier.value, x];`.

</aside>

### Что выбрать

| | `ChangeNotifier` | `ValueNotifier<T>` |
| --- | --- | --- |
| Сколько данных | Сколько угодно полей и методов | Одно значение |
| Уведомление | Вручную, `notifyListeners()` | Автоматически при `value = ...` |
| Виджет для UI | `ListenableBuilder` | `ValueListenableBuilder` |
| Пример | Корзина, форма входа | Флаг, индекс вкладки, тема |

Оба инструмента встроены во Flutter и не требуют пакетов. Для больших приложений позже возьмём Bloc ([урок про Bloc](lesson:bloc-event-state)), но идея «объект сообщает об изменении — UI перерисовывается» останется той же.

## FutureBuilder

### Что это и зачем

`Future<T>` — это «обещание» значения, которое придёт позже: ответ сервера, чтение файла, запрос к базе. Пока ответа нет, экрану нужно что-то показать — индикатор загрузки. Если пришла ошибка — сообщение об ошибке. Писать это вручную через `setState` и три флага утомительно.

`FutureBuilder` делает это за вас: принимает `future` и перерисовывается, когда тот меняет состояние.

### Объект snapshot

В `builder` приходит `AsyncSnapshot<T> snapshot` — «снимок» текущего состояния Future:

| Поле | Что означает |
| --- | --- |
| `snapshot.connectionState` | `none`, `waiting` (ждём), `done` (готово) |
| `snapshot.hasData` / `snapshot.data` | Есть ли результат и сам результат |
| `snapshot.hasError` / `snapshot.error` | Есть ли ошибка и сама ошибка |

### Пример: «загрузка» погоды

Пока у нас нет настоящего API (он появится в уроке [про Dio](lesson:json-modeli-dio-get)), имитируем запрос через `Future.delayed`:

```dart
Future<double> fetchTemperature() async {
  await Future.delayed(const Duration(seconds: 2));
  // раскомментируйте, чтобы проверить ветку с ошибкой:
  // throw Exception('Нет интернета');
  return 18.5;
}

class WeatherPreview extends StatefulWidget {
  const WeatherPreview({super.key});

  @override
  State<WeatherPreview> createState() => _WeatherPreviewState();
}

class _WeatherPreviewState extends State<WeatherPreview> {
  late Future<double> _future;

  @override
  void initState() {
    super.initState();
    _future = fetchTemperature();
  }

  void _reload() {
    setState(() {
      _future = fetchTemperature();
    });
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<double>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('Ошибка: ${snapshot.error}'),
                TextButton(onPressed: _reload, child: const Text('Повторить')),
              ],
            ),
          );
        }
        return Center(child: Text('Сейчас ${snapshot.data}°C'));
      },
    );
  }
}
```

Разбор по частям:

1. `late Future<double> _future;` — поле, где хранится **один и тот же** Future. `late` говорит Dart: «значение присвою чуть позже, до первого чтения».
2. В `initState` запускаем запрос один раз при создании экрана.
3. `_reload` создаёт новый Future и через `setState` отдаёт его `FutureBuilder` — так делается кнопка «Повторить».
4. В `builder` проверяем три случая по порядку: ждём → ошибка → данные.

<aside class="callout" data-icon="⚠️" markdown="1">

Самая частая ошибка с `FutureBuilder` — писать `future: fetchTemperature()` прямо в `build`. Метод `build` вызывается много раз (поворот экрана, открытие клавиатуры, смена темы), и каждый раз будет уходить новый запрос, а пользователь будет видеть бесконечную загрузку. Future создавайте в `initState` и храните в поле.

</aside>

## Builder

### Проблема: «не тот» context

`BuildContext` — это адрес виджета в дереве. Методы вида `Theme.of(context)`, `Scaffold.of(context)`, `Navigator.of(context)` ищут нужный объект **выше** этого адреса.

Посмотрите на код:

```dart
class BrokenPage extends StatelessWidget {
  const BrokenPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      drawer: const Drawer(child: Center(child: Text('Меню'))),
      body: Center(
        child: ElevatedButton(
          // Ошибка: context принадлежит BrokenPage, а Scaffold — ниже него
          onPressed: () => Scaffold.of(context).openDrawer(),
          child: const Text('Открыть меню'),
        ),
      ),
    );
  }
}
```

`context` здесь — это контекст `BrokenPage`. `Scaffold` создаётся *внутри* `build`, то есть находится ниже по дереву. `Scaffold.of(context)` ищет вверх, ничего не находит и падает с ошибкой «Scaffold.of() called with a context that does not contain a Scaffold».

### Решение: Builder

`Builder` — виджет, который просто даёт **новый context**, расположенный в месте, где вы его поставили:

```dart
class FixedPage extends StatelessWidget {
  const FixedPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      drawer: const Drawer(child: Center(child: Text('Меню'))),
      body: Center(
        child: Builder(
          builder: (innerContext) {
            return ElevatedButton(
              onPressed: () => Scaffold.of(innerContext).openDrawer(),
              child: const Text('Открыть меню'),
            );
          },
        ),
      ),
    );
  }
}
```

Теперь `innerContext` находится внутри `Scaffold`, и поиск вверх его находит. Аналогия: вы спрашиваете дорогу к соседнему дому, стоя на улице (старый context), а надо спросить, уже войдя во двор (новый context).

<aside class="callout" data-icon="📌" markdown="1">

`Builder` понадобится постоянно: с `Scaffold.of`, с `Form.of`, а особенно с Bloc — когда вы создаёте `BlocProvider` и сразу хотите прочитать его в том же `build`. Подробнее — в уроке [BlocProvider и темы](lesson:blocprovider-temy-weatherapp).

</aside>

## Типичные ошибки урока

- Модель или `Future` создаются внутри `build` — состояние сбрасывается, запросы дублируются.
- Забыли `notifyListeners()` в `ChangeNotifier`.
- Мутировали список внутри `ValueNotifier` вместо присвоения нового.
- Не вызвали `dispose()` для созданных вами нотифаеров — утечка памяти.
- В `FutureBuilder` обратились к `snapshot.data!` до проверки ошибки и загрузки.
- Использовали `context` уровня страницы там, где нужен контекст ниже `Scaffold` — лечится `Builder`.

## Практика

1. **Счётчик с минусом.** Добавьте в `CounterModel` метод `decrement()`, который не опускает счётчик ниже нуля. Добавьте вторую кнопку. Ожидаемый результат: при нуле нажатие «минус» ничего не меняет.
2. **Индекс вкладки.** Сделайте `ValueNotifier<int>` для выбранной вкладки и `NavigationBar` с тремя пунктами внутри `ValueListenableBuilder`. Ожидаемый результат: подсветка меняется без единого `setState`.
3. **Список городов.** Создайте `CitiesModel extends ChangeNotifier` со списком строк и методами `add(String)` и `remove(String)`. Покажите список в `ListView` через `ListenableBuilder`, добавление — через `TextField`. Ожидаемый результат: города добавляются и удаляются свайпом (`Dismissible`).
4. **FutureBuilder с ошибкой.** Сделайте функцию, которая случайно (через `Random().nextBool()`) возвращает число или бросает исключение. Покажите загрузку, ошибку с кнопкой «Повторить» и результат. Ожидаемый результат: повторное нажатие запускает новый запрос и снова показывает индикатор.
5. **Builder и SnackBar.** Внутри `Scaffold` с `drawer` сделайте кнопку, которая открывает меню через `Builder`, и вторую, которая показывает `SnackBar` через `ScaffoldMessenger.of(context)`. Ожидаемый результат: обе кнопки работают без ошибок в консоли.

## Итоги

- Состояние — данные, от которых зависит экран; `setState` годится только для локальных мелочей.
- `ChangeNotifier` хранит данные и логику, `notifyListeners()` сообщает об изменениях, `ListenableBuilder` перерисовывает UI.
- `ValueNotifier<T>` — упрощённый вариант для одного значения в паре с `ValueListenableBuilder`.
- `FutureBuilder` показывает загрузку, ошибку и данные по `AsyncSnapshot`; Future создаётся в `initState`, а не в `build`.
- `Builder` даёт новый `context` ниже по дереву, когда `X.of(context)` не находит нужный виджет.
- Всё, что вы создали сами (нотифаеры, контроллеры), освобождайте в `dispose()`.
