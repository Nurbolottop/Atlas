В этом уроке две темы. Первая — **Riverpod**, популярная альтернатива связке Bloc + GetIt: он одновременно и внедряет зависимости, и хранит состояние. Перепишем на нём каталог и корзину магазина, чтобы вы могли сравнить подходы. Вторая — **анимации**: неявные, явные через `AnimationController` и переходы **Hero**, которые делают магазин живым.

## Riverpod: что это и зачем

**Riverpod** — библиотека управления состоянием от автора пакета `provider`. Главная идея — **провайдер**: глобально объявленный «рецепт», как получить значение. Значением может быть что угодно: `Dio`, репозиторий, список товаров, корзина.

Аналогия: провайдер — это кран с водой. Вы не думаете, откуда вода приходит и как её очищают, — просто открываете кран (`ref.watch`) там, где она нужна. Если вода «поменялась», все, кто пьёт из крана, сразу получают новую.

Чем Riverpod отличается от того, что мы делали:

| Задача | Bloc + GetIt | Riverpod |
| --- | --- | --- |
| Внедрение зависимостей | `sl.registerLazySingleton(...)` | `Provider((ref) => ...)` |
| Асинхронная загрузка | Bloc + состояния loading/loaded/error | `FutureProvider` + `AsyncValue` |
| Изменяемое состояние | `Cubit` / `Bloc` | `Notifier` |
| Доступ в виджете | `BlocBuilder`, `context.read` | `ConsumerWidget`, `ref.watch`, `ref.read` |

Оба подхода хороши и встречаются в вакансиях. Bloc строже (события, явные состояния), Riverpod — короче.

### Установка

```bash
flutter pub add flutter_riverpod
```

Всё приложение оборачивается в `ProviderScope` — это «хранилище», где живут значения провайдеров:

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

void main() {
  runApp(const ProviderScope(child: ShopApp()));
}
```

## Provider: зависимости

Обычный `Provider` отдаёт значение, которое не меняется, — идеально для DI:

```dart
// lib/core/di/providers.dart
final dioProvider = Provider<Dio>(
  (ref) => Dio(BaseOptions(baseUrl: 'https://dummyjson.com')),
);

final apiClientProvider = Provider((ref) => ApiClient(ref.watch(dioProvider)));

final productRepositoryProvider = Provider<ProductRepository>(
  (ref) => ProductRepositoryImpl(
    ProductRemoteDataSourceImpl(ref.watch(apiClientProvider)),
  ),
);
```

-   `ref` — «пульт», через который провайдер обращается к другим провайдерам.
-   `ref.watch(dioProvider)` — получить `Dio`. Тип указывать не нужно: он известен из объявления.
-   Все слои Clean Architecture остаются прежними — меняется только способ их собрать.

## FutureProvider: загрузка каталога

```dart
// lib/features/products/presentation/providers/products_providers.dart
final productsProvider = FutureProvider<List<Product>>((ref) async {
  final result = await ref.watch(productRepositoryProvider).getProducts();
  return switch (result) {
    Success(:final data) => data,
    Failed(:final failure) => throw failure,
  };
});
```

`FutureProvider` сам следит за состоянием загрузки и отдаёт **`AsyncValue`** — значение в одном из трёх видов: данные, загрузка или ошибка. Именно то, что мы вручную описывали состояниями Bloc.

Экран:

```dart
class ProductsPage extends ConsumerWidget {
  const ProductsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final products = ref.watch(productsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Каталог')),
      body: products.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(
          child: Text(error is Failure ? error.message : 'Ошибка'),
        ),
        data: (items) => RefreshIndicator(
          onRefresh: () => ref.refresh(productsProvider.future),
          child: ListView.builder(
            itemCount: items.length,
            itemBuilder: (_, i) => ProductTile(product: items[i]),
          ),
        ),
      ),
    );
  }
}
```

-   `ConsumerWidget` — как `StatelessWidget`, но в `build` приходит ещё `WidgetRef ref`.
-   `ref.watch(productsProvider)` — подписаться: при изменении значения виджет перерисуется.
-   `.when(loading:, error:, data:)` — нарисовать каждый из трёх вариантов.
-   `ref.refresh(productsProvider.future)` — перезапустить загрузку и вернуть `Future` для `RefreshIndicator`.

### family: провайдер с параметром

Для карточки товара нужен id. Модификатор `.family` добавляет провайдеру параметр:

```dart
final productProvider = FutureProvider.family<Product, int>((ref, id) async {
  final result = await ref.watch(productRepositoryProvider).getProductById(id);
  return switch (result) {
    Success(:final data) => data,
    Failed(:final failure) => throw failure,
  };
});

// в виджете:
final product = ref.watch(productProvider(42));
```

Для каждого id создаётся своё значение: `productProvider(1)` и `productProvider(2)` не мешают друг другу.

## Notifier: корзина

Когда состояние меняется по действиям пользователя, используют `Notifier` — аналог Cubit:

```dart
// lib/features/cart/presentation/providers/cart_provider.dart
class CartNotifier extends Notifier<List<CartItem>> {
  @override
  List<CartItem> build() => const []; // начальное состояние

  void add(Product product) {
    final index = state.indexWhere((i) => i.product.id == product.id);
    if (index == -1) {
      state = [...state, CartItem(product: product, quantity: 1)];
    } else {
      final item = state[index];
      state = [
        for (final i in state)
          if (i == item) CartItem(product: i.product, quantity: i.quantity + 1) else i,
      ];
    }
  }

  void remove(int productId) =>
      state = state.where((i) => i.product.id != productId).toList();
}

final cartProvider =
    NotifierProvider<CartNotifier, List<CartItem>>(CartNotifier.new);
```

-   `build()` возвращает начальное состояние.
-   `state = ...` — то же, что `emit` в Cubit. Присваиваем **новый** список, а не меняем старый.
-   `CartNotifier.new` — ссылка на конструктор.

Использование:

```dart
class AddToCartButton extends ConsumerWidget {
  const AddToCartButton({super.key, required this.product});
  final Product product;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Перерисуемся, только если изменилось количество позиций
    final count = ref.watch(cartProvider.select((items) => items.length));

    return FilledButton(
      onPressed: () => ref.read(cartProvider.notifier).add(product),
      child: Text('В корзину ($count)'),
    );
  }
}
```

| Метод | Где использовать | Что делает |
| --- | --- | --- |
| `ref.watch(p)` | В `build` | Получить значение и перерисоваться при изменении |
| `ref.watch(p.select(...))` | В `build` | Перерисоваться только при изменении части — как `BlocSelector` |
| `ref.read(p)` | В обработчиках нажатий | Получить значение один раз, без подписки |
| `ref.listen(p, ...)` | В `build` | Побочные действия — как `BlocListener` |

<aside class="callout" data-icon="⚠️" markdown="1">

`ref.read` внутри `build` — частая ошибка: виджет получит значение один раз и не узнает об изменениях. В `build` — `watch`, в `onPressed` — `read`.

</aside>

<aside class="callout" data-icon="💡" markdown="1">

В Riverpod 3 старые `StateProvider` и `StateNotifierProvider` перенесены в `package:flutter_riverpod/legacy.dart` — в новом коде используйте `Notifier`. Есть и вариант с кодогенерацией через аннотацию `@riverpod` (пакет `riverpod_generator`) — подробности в [документации Riverpod](https://riverpod.dev).

</aside>

## Анимации: неявные

**Неявная (implicit) анимация** — виджет сам плавно анимирует переход, когда вы меняете его свойство. Вы говорите «стань зелёным», он плавно зеленеет. Такие виджеты начинаются со слова `Animated`.

```dart
class FavoriteButton extends StatefulWidget {
  const FavoriteButton({super.key});
  @override
  State<FavoriteButton> createState() => _FavoriteButtonState();
}

class _FavoriteButtonState extends State<FavoriteButton> {
  bool _isFavorite = false;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => setState(() => _isFavorite = !_isFavorite),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
        padding: EdgeInsets.all(_isFavorite ? 12 : 8),
        decoration: BoxDecoration(
          color: _isFavorite ? Colors.red : Colors.grey.shade300,
          shape: BoxShape.circle,
        ),
        child: Icon(Icons.favorite, color: _isFavorite ? Colors.white : Colors.grey),
      ),
    );
  }
}
```

`AnimatedContainer` при каждом `setState` сравнивает старые и новые `padding` и `color` и плавно переходит между ними за `duration`. `curve` — характер движения: `easeOut` быстро стартует и плавно тормозит.

Другие полезные неявные виджеты:

```dart
// Плавное появление/исчезание
AnimatedOpacity(opacity: inStock ? 1 : 0.4, duration: const Duration(milliseconds: 200), child: card);

// Анимированная смена содержимого: число в корзине «перелистывается»
AnimatedSwitcher(
  duration: const Duration(milliseconds: 250),
  transitionBuilder: (child, animation) => ScaleTransition(scale: animation, child: child),
  child: Text('$count', key: ValueKey(count)),
);

// Анимация любого значения от begin до end
TweenAnimationBuilder<double>(
  tween: Tween(begin: 0, end: product.rating),
  duration: const Duration(seconds: 1),
  builder: (context, value, _) => Text('★ ${value.toStringAsFixed(1)}'),
);
```

У `AnimatedSwitcher` важен `key`: по нему виджет понимает, что содержимое сменилось. Без `ValueKey(count)` анимации не будет.

## Анимации: явные

**Явная (explicit) анимация** — вы сами управляете ею через **`AnimationController`**: запускаете, останавливаете, повторяете. Нужна, когда анимация должна стартовать по событию, а не по изменению свойства, или повторяться.

Пример: значок корзины «подпрыгивает», когда добавили товар.

```dart
class CartIcon extends StatefulWidget {
  const CartIcon({super.key, required this.count});
  final int count;
  @override
  State<CartIcon> createState() => _CartIconState();
}

class _CartIconState extends State<CartIcon> with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 400),
  );

  late final Animation<double> _scale = TweenSequence<double>([
    TweenSequenceItem(tween: Tween(begin: 1, end: 1.4), weight: 50),
    TweenSequenceItem(tween: Tween(begin: 1.4, end: 1), weight: 50),
  ]).animate(CurvedAnimation(parent: _controller, curve: Curves.easeInOut));

  @override
  void didUpdateWidget(CartIcon oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.count > oldWidget.count) _controller.forward(from: 0);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ScaleTransition(
      scale: _scale,
      child: Badge(label: Text('${widget.count}'), child: const Icon(Icons.shopping_cart)),
    );
  }
}
```

Разбор:

-   **`AnimationController`** — «мотор» анимации. Он выдаёт числа от 0 до 1 за `duration`.
-   **`vsync: this`** и **`SingleTickerProviderStateMixin`** — подключают контроллер к частоте обновления экрана и ставят анимацию на паузу, когда виджет не виден.
-   **`Tween`** превращает 0…1 в нужный диапазон (1 → 1.4), **`TweenSequence`** склеивает несколько отрезков, **`CurvedAnimation`** задаёт характер движения.
-   **`didUpdateWidget`** вызывается, когда родитель передал новый `count`. Если товаров стало больше — запускаем с начала: `forward(from: 0)`.
-   **`ScaleTransition`** — готовый виджет, который масштабирует ребёнка по анимации. Есть также `FadeTransition`, `SlideTransition`, `RotationTransition`, а для своих эффектов — `AnimatedBuilder`.
-   **`dispose()`** обязателен: иначе контроллер продолжит работать после закрытия экрана.

Методы контроллера: `forward()` — вперёд, `reverse()` — назад, `repeat()` — по кругу (например, для скелетона загрузки), `stop()` — остановить.

| | Неявные | Явные |
| --- | --- | --- |
| Как запускаются | Изменением свойства в `setState` | Методами контроллера |
| Код | 3–5 строк | `StatefulWidget` + контроллер + `dispose` |
| Повтор, пауза, реверс | Нет | Да |
| Когда брать | Почти всегда | Сложные, повторяющиеся, по событию |

## Hero: полёт картинки между экранами

**Hero** — анимация, при которой виджет «перелетает» с одного экрана на другой. В магазине так обычно летит фото товара из списка в карточку.

```dart
// В списке
Hero(
  tag: 'product-image-${product.id}',
  child: Image.network(product.imageUrl, width: 56, height: 56, fit: BoxFit.cover),
)

// На экране товара
Hero(
  tag: 'product-image-${product.id}',
  child: Image.network(product.imageUrl, height: 300, fit: BoxFit.cover),
)
```

Flutter находит на старом и новом экранах `Hero` с **одинаковым `tag`** и при обычном `Navigator.push` плавно переносит картинку, меняя размер и положение. Больше ничего писать не нужно.

<aside class="callout" data-icon="⚠️" markdown="1">

`tag` должен быть уникален на экране. Если один товар показан и в «Хитах», и в «Новинках» с тегом `product-image-1`, приложение упадёт с ошибкой `There are multiple heroes that share the same tag`. Добавьте в тег название раздела.

</aside>

## Практика

1.  Подключите Riverpod и выведите каталог через `FutureProvider` и `ConsumerWidget` с `RefreshIndicator`.
2.  Сделайте экран товара на `FutureProvider.family` — по нажатию на элемент списка открывается подробная карточка по id.
3.  Перепишите корзину на `CartNotifier`. Кнопка «В корзину» должна использовать `ref.read(...notifier)`, а значок в `AppBar` — `ref.watch(cartProvider.select(...))`.
4.  Добавьте `FavoriteButton` на `AnimatedContainer` и счётчик корзины на `AnimatedSwitcher`.
5.  Сделайте «прыгающий» `CartIcon` на `AnimationController` и Hero-переход картинки из списка в карточку товара.

## Итоги

-   Riverpod объединяет DI и состояние: провайдеры — глобальные «рецепты» значений внутри `ProviderScope`.
-   `Provider` — для зависимостей, `FutureProvider` — для загрузки с `AsyncValue.when`, `Notifier` — для изменяемого состояния.
-   В `build` используем `ref.watch` (и `select`), в обработчиках — `ref.read`, для побочных действий — `ref.listen`.
-   Неявные анимации (`AnimatedContainer`, `AnimatedSwitcher`, `TweenAnimationBuilder`) запускаются изменением свойства.
-   Явные анимации управляются `AnimationController` с `vsync` и обязательно освобождаются в `dispose()`.
-   `Hero` с одинаковым `tag` на двух экранах даёт анимацию перехода без лишнего кода.
