В [уроке про Bloc](lesson:bloc-event-state) вы освоили `BlocBuilder` и `BlocListener`. В интернет-магазине у них появляются ограничения: значок корзины перерисовывается при любом изменении корзины, а экран оформления заказа требует и перерисовки, и навигации одновременно. В этом уроке разберём два виджета, которые решают эти задачи: **BlocSelector** перерисовывает виджет только при изменении нужной части состояния, а **BlocConsumer** объединяет builder и listener.

## Повторим: Builder и Listener

| Виджет | Что делает | Когда вызывается |
| --- | --- | --- |
| `BlocBuilder` | Перерисовывает UI | На каждое новое состояние (или по `buildWhen`) |
| `BlocListener` | Выполняет **побочное действие**: SnackBar, навигация, диалог | Один раз на каждое новое состояние (или по `listenWhen`) |

**Побочное действие (side effect)** — то, что нельзя «нарисовать»: показать уведомление, открыть экран, вибрировать. Его нельзя делать в `builder`, потому что `builder` может вызываться много раз — например, при повороте экрана, — и SnackBar показался бы дважды.

## Корзина магазина: состояние

Для примеров возьмём корзину. Её состояние хранит позиции и статус оформления заказа:

```dart
// lib/features/cart/presentation/cubit/cart_state.dart
import 'package:equatable/equatable.dart';

enum CheckoutStatus { idle, submitting, success, failure }

class CartItem extends Equatable {
  const CartItem({required this.product, required this.quantity});
  final Product product;
  final int quantity;

  @override
  List<Object?> get props => [product, quantity];
}

class CartState extends Equatable {
  const CartState({
    this.items = const [],
    this.checkoutStatus = CheckoutStatus.idle,
    this.errorMessage,
  });

  final List<CartItem> items;
  final CheckoutStatus checkoutStatus;
  final String? errorMessage;

  int get totalCount => items.fold(0, (sum, i) => sum + i.quantity);
  double get totalPrice => items.fold(0.0, (sum, i) => sum + i.product.price * i.quantity);

  int quantityOf(int productId) =>
      items.where((i) => i.product.id == productId).firstOrNull?.quantity ?? 0;

  CartState copyWith({
    List<CartItem>? items,
    CheckoutStatus? checkoutStatus,
    String? errorMessage,
  }) =>
      CartState(
        items: items ?? this.items,
        checkoutStatus: checkoutStatus ?? this.checkoutStatus,
        errorMessage: errorMessage,
      );

  @override
  List<Object?> get props => [items, checkoutStatus, errorMessage];
}
```

И Cubit:

```dart
// lib/features/cart/presentation/cubit/cart_cubit.dart
class CartCubit extends Cubit<CartState> {
  CartCubit(this._placeOrder) : super(const CartState());

  final PlaceOrder _placeOrder; // UseCase оформления заказа

  void add(Product product) {
    final qty = state.quantityOf(product.id);
    final others = state.items.where((i) => i.product.id != product.id);
    emit(state.copyWith(items: [...others, CartItem(product: product, quantity: qty + 1)]));
  }

  void remove(int productId) {
    emit(state.copyWith(
      items: state.items.where((i) => i.product.id != productId).toList(),
    ));
  }

  Future<void> checkout() async {
    emit(state.copyWith(checkoutStatus: CheckoutStatus.submitting));
    final result = await _placeOrder(state.items);
    switch (result) {
      case Success():
        emit(const CartState(checkoutStatus: CheckoutStatus.success));
      case Failed(:final failure):
        emit(state.copyWith(
          checkoutStatus: CheckoutStatus.failure,
          errorMessage: failure.message,
        ));
    }
  }
}
```

`firstOrNull` — встроенное расширение из `dart:core` (Dart 3): первый элемент или `null`, если список пуст. `CartCubit` живёт всё время работы приложения, поэтому его предоставляют на уровне `MaterialApp`.

## Проблема: лишние перерисовки

Значок с количеством товаров в `AppBar`:

```dart
BlocBuilder<CartCubit, CartState>(
  builder: (context, state) => Badge(
    label: Text('${state.totalCount}'),
    child: const Icon(Icons.shopping_cart),
  ),
)
```

Он работает, но перерисовывается при **любом** изменении `CartState`: сменился `checkoutStatus` с `idle` на `submitting` — значок перерисован, хотя число не изменилось. Один значок — не страшно. Но в каталоге у каждой карточки есть счётчик «в корзине: 2», и при добавлении одного товара перерисуются все 20 карточек на экране.

Можно написать `buildWhen`:

```dart
buildWhen: (prev, curr) => prev.totalCount != curr.totalCount,
```

Это работает, но приходится дважды думать о `totalCount`: в условии и в `builder`. Есть способ удобнее.

## BlocSelector

**BlocSelector** берёт из состояния только нужное значение и перерисовывает виджет, только когда **это значение** изменилось.

Аналогия: вы подписаны на новостной канал, но включили уведомления только о погоде. Новостей много, а телефон звенит, только когда меняется прогноз.

```dart
BlocSelector<CartCubit, CartState, int>(
  selector: (state) => state.totalCount,
  builder: (context, count) => Badge(
    isLabelVisible: count > 0,
    label: Text('$count'),
    child: const Icon(Icons.shopping_cart),
  ),
)
```

Разбор:

-   Три параметра типа: `<CartCubit, CartState, int>` — какой Bloc, его состояние и **тип выбранного значения**.
-   `selector` — функция «из состояния достань вот это». Вызывается на каждое новое состояние.
-   `builder` получает уже не всё состояние, а только `count`. Он вызывается, только если новое значение `!=` предыдущему.

### Счётчик на карточке товара

```dart
class InCartCounter extends StatelessWidget {
  const InCartCounter({super.key, required this.productId});
  final int productId;

  @override
  Widget build(BuildContext context) {
    return BlocSelector<CartCubit, CartState, int>(
      selector: (state) => state.quantityOf(productId),
      builder: (context, qty) {
        if (qty == 0) return const SizedBox.shrink();
        return Text('В корзине: $qty');
      },
    );
  }
}
```

Теперь при добавлении кроссовок перерисуется только счётчик кроссовок. Остальные 19 карточек получили новое состояние, вызвали `selector`, увидели то же число и ничего не сделали.

### context.select — то же самое короче

Внутри `build` можно использовать расширение из `flutter_bloc`:

```dart
@override
Widget build(BuildContext context) {
  final total = context.select((CartCubit cubit) => cubit.state.totalPrice);
  return Text('Итого: ${total.toStringAsFixed(2)} \$');
}
```

`context.select` перерисует **весь** этот виджет при изменении `totalPrice`. `BlocSelector` удобнее, когда перерисовывать нужно только кусочек большого виджета.

<aside class="callout" data-icon="⚠️" markdown="1">

Selector сравнивает значения через `==`. Если он каждый раз создаёт **новый** объект — `selector: (s) => s.items.where((i) => i.quantity > 1).toList()` — то два одинаковых списка всё равно будут «разными», и перерисовка случится всегда. Выбирайте простые значения (числа, строки, bool) или объекты с `Equatable`.

</aside>

## BlocConsumer

Экран оформления заказа должен:

1.  **рисовать** кнопку «Оформить» и показывать на ней индикатор, пока заказ отправляется;
2.  при успехе **перейти** на экран «Спасибо за заказ»;
3.  при ошибке **показать** SnackBar.

Пункт 1 — работа для `BlocBuilder`, пункты 2 и 3 — для `BlocListener`. Можно вложить один в другой, но есть **BlocConsumer** — это builder и listener в одном виджете.

```dart
class CheckoutPage extends StatelessWidget {
  const CheckoutPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Оформление заказа')),
      body: BlocConsumer<CartCubit, CartState>(
        listenWhen: (prev, curr) => prev.checkoutStatus != curr.checkoutStatus,
        listener: (context, state) {
          switch (state.checkoutStatus) {
            case CheckoutStatus.success:
              Navigator.of(context).pushReplacement(
                MaterialPageRoute(builder: (_) => const OrderSuccessPage()),
              );
            case CheckoutStatus.failure:
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text(state.errorMessage ?? 'Ошибка')),
              );
            case CheckoutStatus.idle || CheckoutStatus.submitting:
              break;
          }
        },
        buildWhen: (prev, curr) =>
            prev.items != curr.items || prev.checkoutStatus != curr.checkoutStatus,
        builder: (context, state) {
          final isSubmitting = state.checkoutStatus == CheckoutStatus.submitting;
          return Column(
            children: [
              Expanded(
                child: ListView(
                  children: [
                    for (final item in state.items)
                      ListTile(
                        title: Text(item.product.title),
                        trailing: Text('× ${item.quantity}'),
                      ),
                  ],
                ),
              ),
              Padding(
                padding: const EdgeInsets.all(16),
                child: FilledButton(
                  onPressed: isSubmitting || state.items.isEmpty
                      ? null
                      : () => context.read<CartCubit>().checkout(),
                  child: isSubmitting
                      ? const SizedBox.square(
                          dimension: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : Text('Оформить на ${state.totalPrice.toStringAsFixed(2)} \$'),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
```

Разбор:

-   **`listenWhen`** — слушаем только смену статуса. Добавление товара в корзину listener не тревожит.
-   **`listener`** — навигация и SnackBar. Вызывается **один раз** на каждое подходящее состояние, даже если builder перерисуется ещё десять раз.
-   **`buildWhen`** — перерисовываем, когда изменились позиции или статус.
-   **`onPressed: null`** — делает кнопку неактивной во время отправки. Пользователь не оформит заказ дважды двойным нажатием.
-   **`case CheckoutStatus.idle || CheckoutStatus.submitting`** — паттерн «или» из Dart 3: обе ветки ничего не делают, но `switch` остаётся полным.

<aside class="callout" data-icon="📌" markdown="1">

Правило: **в `builder` только рисуем, в `listener` только действуем**. Навигация или `showSnackBar` внутри `builder` — классическая ошибка, из-за которой экран открывается дважды.

</aside>

### Когда нужен MultiBlocListener

Если реагировать надо на несколько Bloc сразу — например, на корзину и на авторизацию (выход из аккаунта очищает корзину), — используйте `MultiBlocListener`:

```dart
MultiBlocListener(
  listeners: [
    BlocListener<AuthCubit, AuthStatus>(
      listenWhen: (_, curr) => curr == AuthStatus.unauthenticated,
      listener: (context, _) => context.read<CartCubit>().clear(),
    ),
    BlocListener<CartCubit, CartState>(
      listenWhen: (prev, curr) => prev.totalCount < curr.totalCount,
      listener: (context, _) => ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Добавлено в корзину'))),
    ),
  ],
  child: const HomePage(),
)
```

Метод `clear()` добавьте в `CartCubit` сами: `void clear() => emit(const CartState());`.

## Что выбрать: шпаргалка

| Задача | Виджет |
| --- | --- |
| Нарисовать UI по всему состоянию | `BlocBuilder` |
| Нарисовать по одному полю состояния | `BlocSelector` или `context.select` |
| Только побочное действие (SnackBar, навигация) | `BlocListener` |
| И рисовать, и действовать по одному Bloc | `BlocConsumer` |
| Действовать по нескольким Bloc | `MultiBlocListener` |
| Вызвать метод (по нажатию кнопки) | `context.read<T>()` |

## Типичные ошибки

-   **Побочные действия в `builder`.** Двойная навигация и повторные SnackBar. Переносите в `listener`.
-   **`context.watch` или `context.select` внутри `onPressed`.** В обработчиках нажатий — только `context.read`; `watch` и `select` работают лишь в `build`.
-   **Selector, возвращающий новый объект.** Перерисовка на каждое состояние — выбирайте примитивы или `Equatable`.
-   **BlocConsumer там, где нужен только builder.** Пустой `listener: (_, __) {}` — знак, что хватит `BlocBuilder`.
-   **Мутация списка в Cubit** (`state.items.add(...)`). Equatable не увидит изменений; создавайте новый список.

## Практика

1.  Создайте `CartCubit` и `CartState` из урока и добавьте кнопку «В корзину» на карточку товара.
2.  Сделайте значок корзины в `AppBar` через `BlocSelector`. Добавьте в его `builder` вызов `debugPrint('badge rebuild')` и убедитесь, что при смене `checkoutStatus` сообщение не появляется.
3.  Добавьте на каждую карточку `InCartCounter`. Проверьте через `debugPrint`, что при добавлении одного товара перерисовывается только его счётчик.
4.  Соберите `CheckoutPage` с `BlocConsumer`. Для проверки сделайте фейковый `PlaceOrder`, который ждёт 2 секунды и случайно возвращает успех или ошибку. Ожидаемый результат: индикатор на кнопке, затем переход на экран «Спасибо» или SnackBar.
5.  Добавьте `MultiBlocListener`: при выходе из аккаунта корзина очищается, при добавлении товара показывается SnackBar.

## Итоги

-   `BlocBuilder` рисует, `BlocListener` выполняет побочные действия; в `builder` никаких SnackBar и навигации.
-   `BlocSelector<Bloc, State, T>` перерисовывает виджет только при изменении выбранного значения.
-   `context.select` — короткая запись селектора внутри `build`.
-   Selector сравнивает через `==`: выбирайте простые значения или `Equatable`.
-   `BlocConsumer` объединяет builder и listener, а `listenWhen` / `buildWhen` уточняют, когда их вызывать.
-   `MultiBlocListener` — для реакций на несколько Bloc сразу.
