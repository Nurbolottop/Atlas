Магазин уже работает, но на реальном телефоне всплывают проблемы: жёлто-чёрные полосы у длинного названия товара, подтормаживание ленты, нагрев телефона на экране с анимацией. В этом уроке научимся находить такие проблемы инструментами **Flutter Inspector** и **Flutter DevTools** и исправлять их: разберём overflow, лишние перерисовки (rebuild), `const` и `RepaintBoundary`.

## Что такое DevTools

**Flutter DevTools** — набор инструментов для отладки, который открывается в браузере или прямо в IDE. Аналогия — приборная панель и диагностический сканер в автосервисе: машина едет, а механик видит обороты, температуру и ошибки датчиков.

Основные вкладки:

| Вкладка | Для чего |
| --- | --- |
| **Inspector** | Дерево виджетов, размеры и отступы, поиск ошибок вёрстки |
| **Performance** | Время отрисовки кадров, поиск «тормозов» (jank) |
| **CPU Profiler** | Какие функции съедают процессор |
| **Memory** | Расход памяти и утечки |
| **Network** | Все HTTP-запросы: адрес, заголовки, ответ |
| **Logging** | Логи приложения и фреймворка |

### Как открыть

-   **VS Code**: запустите приложение в режиме отладки, затем `Ctrl+Shift+P` (`Cmd+Shift+P` на macOS) → **Flutter: Open DevTools**.
-   **Android Studio**: панели **Flutter Inspector** и **Flutter Performance** справа; полный DevTools открывается кнопкой в панели запуска.
-   **Терминал**: после `flutter run` в консоли появится ссылка на DevTools — откройте её в браузере.

### Режимы сборки

```bash
flutter run             # debug: горячая перезагрузка, Inspector, но работает медленнее
flutter run --profile   # profile: скорость как в релизе, доступна вкладка Performance
```

<aside class="callout" data-icon="📌" markdown="1">

Скорость **всегда** проверяйте в режиме `--profile` на реальном устройстве. В debug приложение специально работает медленнее, а эмулятор не похож на телефон покупателя. Подробнее о режимах — в документации [Flutter performance](https://docs.flutter.dev/perf).

</aside>

## Flutter Inspector

Inspector показывает **дерево виджетов** вашего экрана, как оно есть в данный момент.

Главные инструменты:

-   **Select Widget Mode** — включите и нажмите на элемент в приложении. Inspector подсветит его в дереве и покажет свойства: размер, отступы, ограничения (constraints).
-   **Layout Explorer** — для `Row`, `Column` и `Flex` наглядно показывает, сколько места занимает каждый ребёнок и как работают `flex`, `mainAxisAlignment`.
-   **Show Guidelines** — рисует рамки и отступы всех виджетов прямо на экране.
-   **Highlight Repaints** — каждая перерисованная область обводится рамкой нового цвета. Мигает весь экран — что-то перерисовывается лишний раз.
-   **Highlight Oversized Images** — подсвечивает картинки, загруженные в гораздо большем размере, чем показаны.

Рамки и подсветку можно включить и из кода:

```dart
import 'package:flutter/rendering.dart';

void main() {
  debugPaintSizeEnabled = true;        // то же, что Show Guidelines
  debugRepaintRainbowEnabled = true;   // то же, что Highlight Repaints
  runApp(const ShopApp());
}
```

Не забудьте убрать эти строки после отладки.

## Overflow: жёлто-чёрные полосы

Самая частая ошибка вёрстки — **overflow** («переполнение»): виджету не хватило места. В debug Flutter рисует жёлто-чёрную полосу и пишет в консоль:

```text
A RenderFlex overflowed by 42 pixels on the right.
The relevant error-causing widget was:
  Row  lib/features/products/presentation/widgets/product_tile.dart:18:12
```

Чтобы понимать причины, запомните главное правило вёрстки Flutter:

> **Ограничения идут вниз, размеры идут вверх, позицию задаёт родитель.**

Родитель говорит ребёнку: «ты можешь быть шириной от 0 до 360». Ребёнок выбирает размер в этих пределах и сообщает его родителю. Но `Row` даёт детям **бесконечную** ширину — и если дети в сумме шире экрана, получается overflow.

### Случай 1. Длинный текст в Row

```dart
// ❌ Название товара не помещается — overflow справа
Row(
  children: [
    Image.network(product.imageUrl, width: 56),
    const SizedBox(width: 12),
    Text(product.title),
    Text(product.price.asPrice),
  ],
)
```

```dart
// ✅ Текст занимает оставшееся место и обрезается многоточием
Row(
  children: [
    Image.network(product.imageUrl, width: 56),
    const SizedBox(width: 12),
    Expanded(
      child: Text(
        product.title,
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
      ),
    ),
    Text(product.price.asPrice),
  ],
)
```

`Expanded` говорит: «отдай этому ребёнку всё оставшееся место, но не больше». Теперь у `Text` есть конечная ширина, и он переносится на вторую строку или обрезается.

### Случай 2. Экран не помещается по высоте

Форма входа на маленьком телефоне: открылась клавиатура — и снизу overflow.

```dart
// ✅ Содержимое можно прокрутить
Scaffold(
  body: SingleChildScrollView(
    padding: const EdgeInsets.all(16),
    child: Column(
      children: [
        // поля логина и пароля, кнопка
      ],
    ),
  ),
)
```

### Случай 3. Ряд тегов или фильтров

Категории «Косметика», «Смартфоны», «Мебель» в `Row` не влезут. `Wrap` переносит детей на новую строку:

```dart
Wrap(
  spacing: 8,
  runSpacing: 8,
  children: [for (final c in categories) Chip(label: Text(c))],
)
```

### Случай 4. ListView внутри Column

```text
Vertical viewport was given unbounded height.
```

`Column` даёт детям бесконечную высоту, а `ListView` хочет занять всю доступную высоту — то есть бесконечность. Решение — ограничить высоту:

```dart
Column(
  children: [
    const SearchField(),
    Expanded(child: ListView.builder(/* ... */)), // ✅ занимает остаток экрана
  ],
)
```

<aside class="callout" data-icon="⚠️" markdown="1">

Ошибку часто «лечат» через `shrinkWrap: true`. Это работает, но заставляет `ListView` построить **все** элементы сразу, чтобы узнать свою высоту. Для каталога в 200 товаров это серьёзный удар по скорости. Используйте `Expanded` или `CustomScrollView` со slivers.

</aside>

## Лишние rebuild

**Rebuild** — повторный вызов метода `build`. Сам по себе он дешёвый, но если при нажатии на одну кнопку перестраивается весь экран с лентой из 50 карточек, лента начинает подтормаживать.

### Как найти

Самый простой способ — `debugPrint` в `build`:

```dart
@override
Widget build(BuildContext context) {
  debugPrint('ProductTile ${product.id} rebuild');
  // ...
}
```

В DevTools для этого есть отслеживание перестроений: на вкладке **Performance** включите **Track widget builds** (в разделе Enhance Tracing), и на временной шкале появятся события `build` для каждого виджета. В новых версиях DevTools есть также статистика перестроений (**Rebuild Stats**) — список виджетов с количеством вызовов `build`.

### Пример проблемы

```dart
// ❌ Таймер акции обновляется раз в секунду — и перестраивает ВЕСЬ экран
import 'dart:async'; // для Timer

class _HomePageState extends State<HomePage> {
  Duration _left = const Duration(hours: 2);
  late final Timer _timer;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      setState(() => _left -= const Duration(seconds: 1));
    });
  }

  @override
  void dispose() {
    _timer.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text('До конца акции: $_left'),
        const Expanded(child: CatalogList()), // каталог тоже под ударом
      ],
    );
  }
}
```

`setState` перестраивает весь `build` текущего `State`. Решение — **опустить состояние вниз**: вынести таймер в отдельный маленький виджет.

```dart
// ✅ Раз в секунду перестраивается только этот виджет
class SaleTimer extends StatefulWidget {
  const SaleTimer({super.key});
  @override
  State<SaleTimer> createState() => _SaleTimerState();
}

class _SaleTimerState extends State<SaleTimer> {
  Duration _left = const Duration(hours: 2);
  late final Timer _timer;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      setState(() => _left -= const Duration(seconds: 1));
    });
  }

  @override
  void dispose() {
    _timer.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Text('До конца акции: $_left');
}

// HomePage стал StatelessWidget:
Column(
  children: const [
    SaleTimer(),
    Expanded(child: CatalogList()),
  ],
)
```

Другие способы уменьшить rebuild:

-   **`BlocSelector`, `buildWhen`, `ref.watch(p.select(...))`** — перерисовывать только при изменении нужного поля (см. [урок про BlocSelector](lesson:blocselector-blocconsumer)).
-   **Выносить части экрана в отдельные классы-виджеты**, а не в методы `Widget _buildHeader()`. У отдельного класса свой `build`, и Flutter может пропустить его перестройку; метод вызывается заново всегда вместе с родителем.
-   **Не создавать тяжёлое в `build`.** `FutureBuilder(future: repository.getProducts())` в `build` запускает новый запрос при каждой перерисовке. Создавайте Future в `initState` или используйте Bloc/Riverpod.

## const: бесплатная оптимизация

**`const`** говорит Dart: «этот объект известен уже при компиляции и никогда не изменится». Такой объект создаётся один раз и переиспользуется.

```dart
const SizedBox(height: 16)
const Icon(Icons.shopping_cart)
const Text('Каталог')
const EdgeInsets.all(16)
```

Почему это ускоряет: когда родитель перестраивается, Flutter сравнивает старый и новый виджет. Если это **тот же самый** `const`-экземпляр, Flutter понимает, что ничего не поменялось, и **не вызывает его `build` вообще**, а значит, не перестраивает и всё поддерево.

```dart
@override
Widget build(BuildContext context) {
  return Column(
    children: [
      Text('Итого: $total'),    // зависит от данных — без const
      const Divider(),          // никогда не меняется
      const CheckoutHints(),    // свой виджет тоже может быть const
    ],
  );
}
```

Чтобы ваш виджет можно было создавать с `const`, у него должен быть `const`-конструктор и только `final`-поля:

```dart
class CheckoutHints extends StatelessWidget {
  const CheckoutHints({super.key});
  // ...
}
```

Не расставляйте `const` вручную — включите линтер. В `analysis_options.yaml`:

```yaml
include: package:flutter_lints/flutter.yaml

linter:
  rules:
    prefer_const_constructors: true
    prefer_const_literals_to_create_immutables: true
```

Теперь IDE подсветит, где можно добавить `const`, а команда `dart fix --apply` расставит их автоматически.

## RepaintBoundary

После build идёт **paint** — рисование пикселей. По умолчанию соседние виджеты рисуются на одном «холсте» (слое), и если один из них меняется 60 раз в секунду, перерисовывается и всё, что рядом.

**`RepaintBoundary`** выделяет виджет на отдельный слой. Аналогия — прозрачная плёнка поверх рисунка: рисуете на плёнке сколько угодно, основной рисунок не трогается.

```dart
ListView(
  children: [
    const RepaintBoundary(
      child: PromoBannerCarousel(), // автоматически листается каждые 3 секунды
    ),
    for (final p in products) ProductTile(product: p),
  ],
)
```

Как проверить: включите **Highlight Repaints**. До `RepaintBoundary` при каждом перелистывании баннера рамка меняется у всей ленты, после — только у баннера.

<aside class="callout" data-icon="💡" markdown="1">

`ListView.builder` и `GridView.builder` уже оборачивают каждый элемент в `RepaintBoundary`. Добавляйте его вручную точечно: вокруг анимаций, видео, таймеров, которые часто меняются. Каждый слой расходует память, поэтому оборачивать всё подряд не нужно.

</aside>

## Вкладка Performance: ищем тормоза

Для плавной картинки при 60 Гц у Flutter есть около **16 мс** на кадр (при 120 Гц — около 8 мс). Не успел — кадр пропущен, пользователь видит рывок (**jank**).

На вкладке **Performance** (в режиме `--profile`) каждый кадр — столбик:

-   **UI** — время на build и layout вашего Dart-кода;
-   **Raster** — время на отрисовку на GPU.

Красные столбики — кадры, которые не уложились в лимит. Нажмите на такой кадр, и ниже появится временная шкала: какой виджет или функция заняли больше всего времени. Высокий UI — ищите лишние rebuild и тяжёлые вычисления в `build`. Высокий Raster — сложные эффекты: тени, `Opacity`, `ClipRRect`, огромные картинки.

Быстро посмотреть столбики прямо на телефоне можно через `showPerformanceOverlay`:

```dart
MaterialApp(
  showPerformanceOverlay: true,
  home: const CatalogPage(),
)
```

## Типичные ошибки

-   **Проверка скорости в debug.** Всегда `flutter run --profile` на реальном устройстве.
-   **`shrinkWrap: true` для больших списков.** Используйте `Expanded` или slivers.
-   **`setState` высоко в дереве.** Опускайте состояние в маленький виджет.
-   **Методы `_buildX()` вместо виджетов-классов** там, где важна производительность.
-   **Создание Future или контроллеров в `build`.** Только в `initState` или в Bloc/Notifier.
-   **`RepaintBoundary` везде.** Только вокруг часто меняющихся частей.

## Практика

1.  Откройте DevTools для вашего магазина. С помощью **Select Widget Mode** найдите в дереве карточку товара и посмотрите её размеры и constraints.
2.  Создайте overflow: поставьте длинное название в `Row` без `Expanded`. Прочитайте сообщение в консоли, найдите виджет по указанной строке и исправьте через `Expanded` и `TextOverflow.ellipsis`.
3.  Поместите `ListView` в `Column` без ограничений, получите ошибку `unbounded height` и исправьте через `Expanded`.
4.  Добавьте на главный экран таймер акции через `setState` и `debugPrint` в `build` карточек. Убедитесь, что карточки перестраиваются раз в секунду, затем вынесите таймер в `SaleTimer` — сообщения должны прекратиться.
5.  Включите `prefer_const_constructors`, выполните `dart fix --apply`. Затем запустите `--profile`, включите **Highlight Repaints** и оберните автолистающийся баннер в `RepaintBoundary`. Ожидаемый результат: подсветка мигает только у баннера.

## Итоги

-   DevTools — приборная панель приложения: Inspector, Performance, CPU, Memory, Network, Logging.
-   Скорость измеряем в `--profile` на реальном устройстве; лимит кадра — около 16 мс.
-   Overflow лечится `Expanded`/`Flexible`, `TextOverflow.ellipsis`, `SingleChildScrollView`, `Wrap`; `ListView` в `Column` — через `Expanded`.
-   Лишние rebuild уменьшаем: опускаем состояние вниз, выносим виджеты в классы, используем селекторы.
-   `const`-виджеты не перестраиваются; линтер `prefer_const_constructors` расставит их за вас.
-   `RepaintBoundary` выносит часто меняющуюся часть на отдельный слой, но ставится точечно.
