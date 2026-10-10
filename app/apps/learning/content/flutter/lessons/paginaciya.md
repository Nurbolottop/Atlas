В каталоге интернет-магазина сотни товаров, и загружать их все сразу — долго и расточительно. Вместо этого приложение берёт товары **порциями**: первые 20, а когда пользователь долистал до конца, — следующие 20. Это и есть **пагинация**. В этом уроке реализуем бесконечную ленту каталога по всем слоям Clean Architecture: от запроса с параметрами до Bloc и `ScrollController`.

## Что такое пагинация и зачем она нужна

Аналогия — книга. Вы не читаете все страницы одновременно: открываете одну, дочитываете, переворачиваете. Так и приложение: показывает «страницу» товаров и подгружает следующую, когда нужно.

Без пагинации:

-   первый экран открывается медленно — ждём сотни товаров;
-   тратится мобильный трафик на товары, до которых пользователь не долистает;
-   растёт расход памяти.

### Виды пагинации

| Вид | Как выглядит запрос | Где встречается |
| --- | --- | --- |
| **Offset / limit** | `?skip=40&limit=20` — пропусти 40, дай 20 | Каталоги, таблицы |
| **Page / size** | `?page=3&size=20` — третья страница по 20 | То же самое, другая запись |
| **Cursor** | `?after=abc123&limit=20` — дай 20 после элемента `abc123` | Ленты, чаты, где данные часто меняются |

Offset и page — одно и то же: `skip = (page - 1) * size`. Cursor надёжнее, когда сверху постоянно добавляются новые элементы: при offset товары могут «сдвинуться» и повториться. Наш API `dummyjson.com` использует offset:

```text
GET /products?limit=20&skip=0    → товары 1–20
GET /products?limit=20&skip=20   → товары 21–40
```

Ответ содержит `total` — общее количество товаров. По нему мы поймём, что дальше грузить нечего.

## Слой domain: страница как сущность

Опишем «страницу» один раз через generic — она пригодится и для заказов, и для отзывов:

```dart
// lib/core/pagination/paginated.dart
class Paginated<T> {
  const Paginated({required this.items, required this.total, required this.skip});

  final List<T> items;
  final int total;
  final int skip;

  /// Есть ли ещё данные после этой страницы
  bool get hasMore => skip + items.length < total;
}
```

Пример: `skip = 180`, пришло 14 товаров, `total = 194`. `180 + 14 = 194`, значит `hasMore == false` — это последняя страница.

Добавим метод в интерфейс репозитория и новый UseCase (базовый `UseCase` и `Result` — из [урока про generics](lesson:generics-enum-screenutil)):

```dart
// domain/repositories/product_repository.dart
abstract interface class ProductRepository {
  Future<Result<Paginated<Product>>> getProductsPage({required int skip, required int limit});
  // ...остальные методы
}
```

```dart
// domain/usecases/get_products_page.dart
class PageParams {
  const PageParams({required this.skip, this.limit = 20});
  final int skip;
  final int limit;
}

class GetProductsPage extends UseCase<Paginated<Product>, PageParams> {
  const GetProductsPage(this._repository);
  final ProductRepository _repository;

  @override
  Future<Result<Paginated<Product>>> call(PageParams params) =>
      _repository.getProductsPage(skip: params.skip, limit: params.limit);
}
```

Domain по-прежнему не знает, что на сервере параметры называются `skip` и `limit` в URL. Если бэкенд перейдёт на `page/size`, пересчёт сделает слой data.

## Слой data: запрос с параметрами

```dart
// data/datasources/product_remote_data_source.dart
@override
Future<({List<ProductModel> items, int total})> getProductsPage({
  required int skip,
  required int limit,
}) async {
  final json = await _api.get(
    '/products',
    query: {'skip': skip, 'limit': limit},
  );
  final items = (json['products'] as List)
      .map((e) => ProductModel.fromJson(e as Map<String, dynamic>))
      .toList();
  return (items: items, total: json['total'] as int);
}
```

`_api` — наша прослойка `ApiClient` над Dio. Метод возвращает record с моделями и общим количеством.

```dart
// data/repositories/product_repository_impl.dart
@override
Future<Result<Paginated<Product>>> getProductsPage({
  required int skip,
  required int limit,
}) =>
    safeCall(() async {
      final page = await _remote.getProductsPage(skip: skip, limit: limit);
      return Paginated(
        items: page.items.map((m) => m.toEntity()).toList(),
        total: page.total,
        skip: skip,
      );
    });
```

Репозиторий, как обычно, превращает модели в сущности, а ошибки — в `Failed` через `safeCall`.

## Слой presentation: Bloc для ленты

### Состояние

Для ленты одного статуса мало: нужно хранить уже загруженные товары, пока грузится следующая страница. Поэтому состояние — один класс с полями и `copyWith`:

```dart
// presentation/bloc/catalog_state.dart
// LoadStatus { initial, loading, success, failure } — enum из урока про generics

class CatalogState extends Equatable {
  const CatalogState({
    this.status = LoadStatus.initial,
    this.products = const [],
    this.hasReachedMax = false,
    this.errorMessage,
  });

  final LoadStatus status;
  final List<Product> products;
  final bool hasReachedMax;
  final String? errorMessage;

  CatalogState copyWith({
    LoadStatus? status,
    List<Product>? products,
    bool? hasReachedMax,
    String? errorMessage,
  }) =>
      CatalogState(
        status: status ?? this.status,
        products: products ?? this.products,
        hasReachedMax: hasReachedMax ?? this.hasReachedMax,
        errorMessage: errorMessage,
      );

  @override
  List<Object?> get props => [status, products, hasReachedMax, errorMessage];
}
```

-   `products` растёт с каждой страницей.
-   `hasReachedMax` — «дошли до конца, больше не грузим».
-   `errorMessage` в `copyWith` без `??`: при каждом новом состоянии ошибка сбрасывается, если её явно не передали.

### События и Bloc

```bash
flutter pub add bloc_concurrency
```

```dart
// presentation/bloc/catalog_bloc.dart
import 'package:bloc_concurrency/bloc_concurrency.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

sealed class CatalogEvent {}
final class CatalogNextPageRequested extends CatalogEvent {}
final class CatalogRefreshed extends CatalogEvent {}

class CatalogBloc extends Bloc<CatalogEvent, CatalogState> {
  CatalogBloc(this._getPage) : super(const CatalogState()) {
    on<CatalogNextPageRequested>(_onNextPage, transformer: droppable());
    on<CatalogRefreshed>(_onRefresh, transformer: droppable());
  }

  final GetProductsPage _getPage;
  static const _limit = 20;

  Future<void> _onNextPage(
    CatalogNextPageRequested event,
    Emitter<CatalogState> emit,
  ) async {
    if (state.hasReachedMax) return;
    emit(state.copyWith(status: LoadStatus.loading));

    final result = await _getPage(
      PageParams(skip: state.products.length, limit: _limit),
    );

    switch (result) {
      case Success(:final data):
        emit(state.copyWith(
          status: LoadStatus.success,
          products: [...state.products, ...data.items],
          hasReachedMax: !data.hasMore,
        ));
      case Failed(:final failure):
        emit(state.copyWith(
          status: LoadStatus.failure,
          errorMessage: failure.message,
        ));
    }
  }

  Future<void> _onRefresh(
    CatalogRefreshed event,
    Emitter<CatalogState> emit,
  ) async {
    emit(state.copyWith(status: LoadStatus.loading));
    final result = await _getPage(const PageParams(skip: 0, limit: _limit));
    switch (result) {
      case Success(:final data):
        emit(CatalogState(
          status: LoadStatus.success,
          products: data.items,
          hasReachedMax: !data.hasMore,
        ));
      case Failed(:final failure):
        emit(state.copyWith(status: LoadStatus.failure, errorMessage: failure.message));
    }
  }
}
```

Разбор главного:

-   **`skip: state.products.length`** — сколько товаров уже есть, столько и пропускаем. Отдельный счётчик страниц не нужен.
-   **`[...state.products, ...data.items]`** — создаём **новый** список из старых и новых товаров. Если сделать `state.products.addAll(...)`, Equatable не увидит изменений (тот же объект списка), и экран не обновится.
-   **`droppable()`** из `bloc_concurrency` — пока событие обрабатывается, новые такие же события **отбрасываются**. Пользователь быстро крутит ленту, `ScrollController` шлёт десять событий подряд, но запрос уйдёт один.
-   **Refresh** при успехе заменяет список целиком, а при ошибке оставляет старые товары на экране.

<aside class="callout" data-icon="📌" markdown="1">

Без `droppable()` пагинация почти всегда ломается одинаково: одна и та же страница загружается два-три раза, и в списке появляются дубли. Это первое, что стоит проверить, если товары повторяются.

</aside>

Регистрация, как всегда, фабрикой: `sl.registerFactory(() => CatalogBloc(sl()));` и `sl.registerLazySingleton(() => GetProductsPage(sl()));`.

## Экран: бесконечная лента

```dart
// presentation/pages/catalog_page.dart
class CatalogPage extends StatelessWidget {
  const CatalogPage({super.key});

  @override
  Widget build(BuildContext context) => BlocProvider(
        create: (_) => sl<CatalogBloc>()..add(CatalogNextPageRequested()),
        child: const CatalogView(),
      );
}

class CatalogView extends StatefulWidget {
  const CatalogView({super.key});
  @override
  State<CatalogView> createState() => _CatalogViewState();
}

class _CatalogViewState extends State<CatalogView> {
  final _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
  }

  void _onScroll() {
    final position = _scrollController.position;
    // До конца осталось меньше 300 пикселей — грузим следующую страницу
    if (position.pixels >= position.maxScrollExtent - 300) {
      context.read<CatalogBloc>().add(CatalogNextPageRequested());
    }
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Каталог')),
      body: BlocBuilder<CatalogBloc, CatalogState>(
        builder: (context, state) {
          if (state.products.isEmpty) {
            return switch (state.status) {
              LoadStatus.failure => _ErrorView(message: state.errorMessage),
              _ => const Center(child: CircularProgressIndicator()),
            };
          }
          return RefreshIndicator(
            onRefresh: () async {
              final bloc = context.read<CatalogBloc>()..add(CatalogRefreshed());
              await bloc.stream.firstWhere((s) => s.status != LoadStatus.loading);
            },
            child: ListView.builder(
              controller: _scrollController,
              itemCount: state.products.length + (state.hasReachedMax ? 0 : 1),
              itemBuilder: (context, i) {
                if (i < state.products.length) {
                  return ProductTile(product: state.products[i]);
                }
                return _BottomLoader(state: state);
              },
            ),
          );
        },
      ),
    );
  }
}
```

```dart
class _BottomLoader extends StatelessWidget {
  const _BottomLoader({required this.state});
  final CatalogState state;

  @override
  Widget build(BuildContext context) {
    if (state.status == LoadStatus.failure) {
      return TextButton(
        onPressed: () => context.read<CatalogBloc>().add(CatalogNextPageRequested()),
        child: const Text('Ошибка загрузки. Повторить'),
      );
    }
    return const Padding(
      padding: EdgeInsets.all(16),
      child: Center(child: CircularProgressIndicator()),
    );
  }
}
```

Разбор:

-   **`itemCount: products.length + 1`** — лишний элемент в конце списка: там показываем индикатор загрузки или кнопку «Повторить». Когда `hasReachedMax`, его нет.
-   **`_onScroll`** срабатывает при каждом сдвиге ленты. Запас в 300 пикселей нужен, чтобы следующая страница начала грузиться заранее и пользователь не упирался в конец.
-   **`RefreshIndicator`** — «потяни вниз, чтобы обновить». `onRefresh` должен вернуть `Future`: индикатор крутится, пока Future не завершится. Поэтому `_onRefresh` сначала выдаёт `loading`, а мы ждём первое состояние после него. Если бы Bloc сразу выдал такое же состояние, как текущее, Equatable отбросил бы его, и индикатор крутился бы вечно.
-   **Ошибка первой страницы** — на весь экран (`_ErrorView` с текстом и кнопкой, напишите сами). Ошибка следующей страницы — внизу, чтобы не терять уже загруженные товары.

<aside class="callout" data-icon="💡" markdown="1">

Для сложных случаев (сетка, разделители, пустое состояние) есть пакет [infinite_scroll_pagination](https://pub.dev/packages/infinite_scroll_pagination). Но понимать, как пагинация устроена изнутри, нужно в любом случае — об этом часто спрашивают на собеседованиях.

</aside>

## Типичные ошибки

-   **Дубли в списке.** Нет `droppable()` или проверки `hasReachedMax` — одна страница грузится несколько раз.
-   **Первая страница не заполняет экран.** Если `limit` маленький (например, 5), ленту нельзя прокрутить, и `_onScroll` никогда не сработает. Берите `limit` с запасом — 20 и больше.
-   **Изменение списка на месте** (`state.products.add(...)`). Экран не перерисуется. Всегда создавайте новый список.
-   **Забыли `dispose()` у `ScrollController`.** Утечка памяти и ошибки после закрытия экрана.
-   **Сброс списка при ошибке.** Ошибка второй страницы не должна стирать первую.

## Практика

1.  Добавьте `Paginated<T>` и проверьте `hasMore`: для `skip: 180, items: 14 шт., total: 194` должно быть `false`, для `skip: 0, items: 20, total: 194` — `true`.
2.  Реализуйте `getProductsPage` в data source и репозитории и выведите в консоль названия товаров со второй страницы (`skip: 20`).
3.  Соберите `CatalogBloc` и экран с бесконечной лентой. Ожидаемый результат: при прокрутке подгружаются новые товары, внизу крутится индикатор, после 194-го товара он исчезает.
4.  Отключите интернет, долистайте до конца загруженного — внизу должна появиться кнопка «Повторить», а уже загруженные товары остаться на месте.
5.  Добавьте пагинацию для поиска: событие `CatalogQueryChanged(String query)` сбрасывает список и грузит первую страницу `GET /products/search?q=...&limit=20&skip=0`.

## Итоги

-   Пагинация — загрузка данных порциями: offset/limit, page/size или cursor.
-   Generic-класс `Paginated<T>` хранит элементы, `total` и умеет отвечать `hasMore`.
-   Domain описывает «дай страницу», а data превращает это в параметры запроса.
-   Состояние ленты — один класс с `status`, `products`, `hasReachedMax` и `copyWith`.
-   `skip = products.length`, новые товары добавляем в **новый** список.
-   `droppable()` из `bloc_concurrency` защищает от повторной загрузки одной страницы.
-   `ScrollController` с запасом до конца ленты, нижний индикатор и `RefreshIndicator` — основа UI.
