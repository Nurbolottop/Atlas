Когда в магазине появляются десятки UseCase и репозиториев, код начинает повторяться: одинаковые `try/catch`, одинаковые проверки статуса, одинаковые отступы. В этом уроке разберём инструменты, которые убирают повторы: **generics**, **базовые классы**, **enum**, **прослойки** между библиотеками и вашим кодом, **extensions** и пакет **ScreenUtil** для адаптивной вёрстки под разные экраны.

## Generics: коробка с этикеткой

**Generic (обобщённый тип)** — это класс или функция, которые работают с любым типом, но при этом помнят, с каким именно. Вы уже пользовались ими: `List<Product>`, `Future<String>`, `Bloc<ProductsEvent, ProductsState>`.

Аналогия: коробка с этикеткой. Коробка одна и та же, но на этикетке написано «Обувь» или «Книги», и вы точно знаете, что достанете.

```dart
class Box<T> {
  Box(this.value);
  final T value;
}

void main() {
  final a = Box<int>(42);
  final b = Box('кроссовки'); // T = String, Dart вывел сам

  int number = a.value;    // ок, тип известен
  String text = b.value;   // ок
  // int wrong = b.value;  // ошибка компиляции: String нельзя присвоить int
}
```

-   `<T>` — **параметр типа**. Вместо `T` при использовании подставляется конкретный тип.
-   Без generics пришлось бы писать `dynamic`, и ошибки всплывали бы только при запуске.

### Generic-функции и ограничения

Функция тоже может иметь параметр типа:

```dart
T? firstWhereOrNull<T>(List<T> items, bool Function(T) test) {
  for (final item in items) {
    if (test(item)) return item;
  }
  return null;
}

final cheap = firstWhereOrNull(products, (p) => p.price < 10); // Product?
```

Ограничить допустимые типы можно через `extends`: в `<T extends Equatable>` подойдёт только наследник `Equatable`.

## Result: generic вместо исключений

В прошлых уроках репозиторий бросал `Failure`, а Bloc ловил его через `try/catch`. Это работает, но легко забыть `catch`. Популярный подход — возвращать результат, в котором **либо данные, либо ошибка**:

```dart
// lib/core/result/result.dart
import '../error/failures.dart';

sealed class Result<T> {
  const Result();
}

final class Success<T> extends Result<T> {
  const Success(this.data);
  final T data;
}

final class Failed<T> extends Result<T> {
  const Failed(this.failure);
  final Failure failure;
}
```

Использование в Bloc:

```dart
final result = await _getProducts(const NoParams());

switch (result) {
  case Success(:final data):
    emit(ProductsLoaded(data));
  case Failed(:final failure):
    emit(ProductsError(failure.message));
}
```

-   `Result<List<Product>>` прямо в сигнатуре говорит: «здесь может быть ошибка, обработай её».
-   `sealed` + `switch` — компилятор не даст забыть ветку `Failed`.
-   Мы не назвали класс `Error`, потому что в Dart уже есть встроенный `Error` — совпадение имён только запутает.

<aside class="callout" data-icon="💡" markdown="1">

Ту же идею реализуют пакеты `fpdart` и `dartz` через тип `Either<L, R>`. Свой `Result` из десяти строк проще для понимания, а принцип один и тот же.

</aside>

## Базовые классы

**Базовый класс** — это общий «шаблон», от которого наследуются похожие классы. Он фиксирует единый контракт и убирает копипаст.

### Базовый UseCase

```dart
// lib/core/usecase/usecase.dart
import '../result/result.dart';

abstract class UseCase<Type, Params> {
  const UseCase();
  Future<Result<Type>> call(Params params);
}

/// Для UseCase, которым не нужны параметры
class NoParams {
  const NoParams();
}
```

Теперь все UseCase магазина выглядят одинаково:

```dart
class GetProducts extends UseCase<List<Product>, NoParams> {
  const GetProducts(this._repository);
  final ProductRepository _repository;

  @override
  Future<Result<List<Product>>> call(NoParams params) => _repository.getProducts();
}

class GetProductById extends UseCase<Product, int> {
  const GetProductById(this._repository);
  final ProductRepository _repository;

  @override
  Future<Result<Product>> call(int id) => _repository.getProductById(id);
}
```

В `UseCase<Type, Params>` первый параметр — что UseCase возвращает, второй — что принимает. Интерфейс `ProductRepository` теперь тоже возвращает `Result<...>`.

Если параметров несколько, заведите для них маленький класс, например `SearchParams(query: 'phone', limit: 20)`, и передайте его вторым типом: `UseCase<List<Product>, SearchParams>`.

### Базовый репозиторий

В прошлом уроке у `ProductRepositoryImpl` был метод `_guard`, который ловил `DioException`. Такой же нужен корзине, заказам, профилю. Вынесем его в базовый класс:

```dart
// lib/core/data/base_repository.dart
import 'package:dio/dio.dart';
import '../error/failures.dart';
import '../result/result.dart';

abstract class BaseRepository {
  Future<Result<T>> safeCall<T>(Future<T> Function() request) async {
    try {
      return Success(await request());
    } on DioException catch (e) {
      return Failed(_mapDioError(e));
    } on FormatException {
      return const Failed(ServerFailure('Сервер прислал неверные данные'));
    }
  }

  Failure _mapDioError(DioException e) => switch (e.type) {
        DioExceptionType.connectionError ||
        DioExceptionType.connectionTimeout ||
        DioExceptionType.receiveTimeout =>
          const NetworkFailure(),
        _ when e.response?.statusCode == 401 => const UnauthorizedFailure(),
        _ => ServerFailure('Ошибка сервера: ${e.response?.statusCode}'),
      };
}
```

```dart
class ProductRepositoryImpl extends BaseRepository implements ProductRepository {
  ProductRepositoryImpl(this._remote);
  final ProductRemoteDataSource _remote;

  @override
  Future<Result<List<Product>>> getProducts() => safeCall(() async {
        final models = await _remote.getProducts();
        return models.map((m) => m.toEntity()).toList();
      });

  // getProductById и searchProducts — так же через safeCall
}
```

-   `extends BaseRepository` — получаем `safeCall` по наследству.
-   `implements ProductRepository` — выполняем контракт domain. Одно другому не мешает.
-   `safeCall<T>` — generic: тип `T` берётся из того, что вернула лямбда (`List<Product>`).
-   `_ when ...` — guard в switch-выражении: ветка сработает, только если условие истинно.

## Прослойки: не пускаем библиотеки в весь код

**Прослойка (обёртка, wrapper)** — ваш класс между сторонней библиотекой и остальным приложением. Аналогия — переходник для розетки: техника подключается к переходнику, и при поездке в другую страну меняете только переходник.

Например, обёртка над Dio:

```dart
// lib/core/network/api_client.dart
import 'package:dio/dio.dart';

class ApiClient {
  ApiClient(this._dio);
  final Dio _dio;

  Future<Map<String, dynamic>> get(
    String path, {
    Map<String, dynamic>? query,
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(path, queryParameters: query);
    return response.data ?? {};
  }

  Future<Map<String, dynamic>> post(String path, {Object? body}) async {
    final response = await _dio.post<Map<String, dynamic>>(path, data: body);
    return response.data ?? {};
  }
}
```

Теперь data sources зависят от `ApiClient`, а не от Dio. Захотите добавить логирование всех запросов, общий заголовок языка или сменить Dio на `http` — правите один файл. Так же оборачивают хранилища (`TokenStorage` над `FlutterSecureStorage` в [уроке про авторизацию](lesson:avtorizaciya-secure-storage)) и аналитику.

<aside class="callout" data-icon="⚠️" markdown="1">

Не превращайте каждую мелочь в прослойку. Обёртка нужна там, где библиотека используется во многих местах или может смениться. Обёртка над `Text` или `Padding` — лишний код.

</aside>

## Enum: перечисления

**Enum** — тип с фиксированным набором значений. Вместо «магических строк» вроде `'pending'` получаем значения, которые проверяет компилятор.

```dart
enum LoadStatus { initial, loading, success, failure }

final status = LoadStatus.loading;
print(status.name);                       // loading
print(LoadStatus.values);                 // все значения
print(LoadStatus.values.byName('success')); // LoadStatus.success
```

### Enhanced enum: enum с полями

В Dart 3 у enum могут быть поля, конструктор и методы. Статусы заказа в магазине:

```dart
import 'package:flutter/material.dart';

enum OrderStatus {
  pending('Ожидает оплаты', Colors.orange),
  paid('Оплачен', Colors.blue),
  shipped('В пути', Colors.purple),
  delivered('Доставлен', Colors.green),
  cancelled('Отменён', Colors.red);

  const OrderStatus(this.label, this.color);

  final String label;
  final Color color;

  bool get canCancel => this == pending || this == paid;

  static OrderStatus fromApi(String value) => OrderStatus.values.firstWhere(
        (s) => s.name == value,
        orElse: () => OrderStatus.pending,
      );
}
```

```dart
Widget statusChip(OrderStatus status) => Chip(
      label: Text(status.label),
      backgroundColor: status.color.withValues(alpha: 0.15),
    );
```

-   Каждое значение вызывает конструктор: `pending('Ожидает оплаты', Colors.orange)`.
-   Поля enum всегда `final`, а конструктор `const`.
-   `fromApi` превращает строку с сервера в enum; `orElse` защищает от неизвестного значения.

### Enum и switch

```dart
String deliveryHint(OrderStatus status) => switch (status) {
      OrderStatus.pending => 'Оплатите заказ в течение часа',
      OrderStatus.paid => 'Скоро передадим в доставку',
      OrderStatus.shipped => 'Курьер уже едет',
      OrderStatus.delivered => 'Спасибо за покупку!',
      OrderStatus.cancelled => 'Заказ отменён',
    };
```

Добавите статус `returned` и забудете его здесь — проект не скомпилируется. Это плюс.

## Extensions: новые методы для чужих классов

**Extension (расширение)** добавляет методы к существующему классу, не меняя его и не наследуясь. Вы уже видели `toEntity()` в [уроке про data-слой](lesson:getit-di-clean-2).

```dart
// lib/core/extensions/extensions.dart
import 'package:flutter/material.dart';

extension PriceX on num {
  String get asPrice => '\$${toStringAsFixed(2)}';
}

extension StringX on String {
  String get capitalized =>
      isEmpty ? this : '${this[0].toUpperCase()}${substring(1)}';
}

extension ContextX on BuildContext {
  ThemeData get theme => Theme.of(this);
  TextTheme get textTheme => Theme.of(this).textTheme;
  Size get screenSize => MediaQuery.sizeOf(this);

  void showSnack(String message) => ScaffoldMessenger.of(this)
      .showSnackBar(SnackBar(content: Text(message)));
}
```

```dart
Text(product.price.asPrice, style: context.textTheme.titleMedium); // $9.99
Text('beauty'.capitalized);                                         // Beauty
context.showSnack('Товар добавлен в корзину');
```

-   `extension PriceX on num` — «добавить к `num` геттер `asPrice`». Работает и для `int`, и для `double`.
-   Внутри расширения `this` — это сам объект (число, строка, контекст).
-   Расширение видно только там, где импортирован его файл.

## ScreenUtil: адаптивные размеры

Дизайнер рисует макет под один экран, например 375×812. Если писать `width: 160`, на узком телефоне карточки не влезут, а на широком будут пустоты.

Пакет `flutter_screenutil` пересчитывает размеры из макета пропорционально реальному экрану.

```bash
flutter pub add flutter_screenutil
```

### Подключение

```dart
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

class ShopApp extends StatelessWidget {
  const ShopApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ScreenUtilInit(
      designSize: const Size(375, 812), // размер макета из Figma
      minTextAdapt: true,
      splitScreenMode: true,
      builder: (context, child) => MaterialApp(
        title: 'Shop',
        home: child,
      ),
      child: const ProductsPage(),
    );
  }
}
```

### Единицы измерения

| Расширение | Что значит | Пример |
| --- | --- | --- |
| `.w` | ширина пропорционально ширине экрана | `width: 160.w` |
| `.h` | высота пропорционально высоте экрана | `SizedBox(height: 16.h)` |
| `.r` | по меньшей стороне — для квадратов и радиусов | `BorderRadius.circular(12.r)` |
| `.sp` | размер шрифта | `fontSize: 14.sp` |

Карточка товара с ScreenUtil:

```dart
class ProductCard extends StatelessWidget {
  const ProductCard({super.key, required this.product});
  final Product product;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 160.w,
      padding: EdgeInsets.all(8.r),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12.r),
        color: context.theme.colorScheme.surfaceContainerHighest,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Image.network(product.imageUrl, height: 120.r, fit: BoxFit.cover),
          SizedBox(height: 8.h),
          Text(product.title, maxLines: 2, style: TextStyle(fontSize: 14.sp)),
          Text(product.price.asPrice, style: TextStyle(fontSize: 16.sp)),
        ],
      ),
    );
  }
}
```

### Типичные ошибки со ScreenUtil

-   **`const` с `.w`.** `const SizedBox(height: 16.h)` не скомпилируется: `16.h` вычисляется во время работы. Уберите `const`.
-   **`.h` для квадратов.** Картинка `width: 100.w, height: 100.h` станет прямоугольной на длинных экранах. Для квадратов и кругов используйте `.r`.
-   **ScreenUtil без `ScreenUtilInit`.** Размеры будут неверными или приложение упадёт — `ScreenUtilInit` должен оборачивать `MaterialApp`.
-   **Масштабирование всего подряд.** На планшете всё станет огромным. Для планшетов часто делают отдельную раскладку через `LayoutBuilder`, а ScreenUtil оставляют для телефонов.

## Практика

1.  Напишите generic-класс `Pair<A, B>` с полями `first` и `second`. Создайте `Pair<String, int>('Кроссовки', 2)` и выведите поля.
2.  Добавьте в проект `Result<T>`, `UseCase<Type, Params>` и `NoParams`. Переведите `GetProducts` и `ProductsBloc` на `Result` — `try/catch` в Bloc должен исчезнуть.
3.  Вынесите обработку ошибок в `BaseRepository.safeCall` и унаследуйте от него `ProductRepositoryImpl`.
4.  Создайте enhanced enum `SortOption` (по цене ↑, по цене ↓, по рейтингу) с полем `label` и методом `List<Product> apply(List<Product> items)`. Покажите выбор сортировки в `DropdownButton`.
5.  Подключите ScreenUtil с макетом 375×812 и переверстайте карточку товара через `.w`, `.h`, `.r`, `.sp`. Запустите на маленьком и большом эмуляторе — пропорции должны сохраниться.

## Итоги

-   Generics (`<T>`) дают переиспользуемый код без потери типов; `extends` ограничивает допустимые типы.
-   `Result<T>` с `Success` и `Failed` делает ошибки частью сигнатуры, а `switch` не даст их забыть.
-   Базовые классы (`UseCase<Type, Params>`, `BaseRepository`) убирают копипаст и задают единый стиль.
-   Прослойки (`ApiClient`, `TokenStorage`) изолируют сторонние библиотеки в одном месте.
-   Enhanced enum хранит поля и методы, а `switch` по enum проверяется на полноту.
-   Extensions добавляют удобные методы к `num`, `String`, `BuildContext`.
-   ScreenUtil масштабирует размеры из макета: `.w`, `.h`, `.r`, `.sp`, но без `const`.
