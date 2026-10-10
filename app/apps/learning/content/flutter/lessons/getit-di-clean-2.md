В [первой части](lesson:getit-di-clean-1) мы описали domain интернет-магазина: сущность `Product`, ошибки `Failure`, интерфейс `ProductRepository` и UseCase. Теперь оживим его: напишем слой data (data sources, модели и мапперы), соберём все зависимости в GetIt, подключим Bloc и посмотрим, как всё это укладывается в паттерн **MVVM**. В итоге каталог будет грузиться из настоящего API.

## Слой data: что в нём лежит

Слой data отвечает на вопрос «**как** достать данные»:

| Класс | Задача | Знает о |
| --- | --- | --- |
| **Data source** | Делает запрос: HTTP, база, кеш | Dio, JSON, SharedPreferences |
| **Модель (Model)** | Описывает данные так, как их прислал сервер, умеет `fromJson` | JSON |
| **Репозиторий (RepositoryImpl)** | Реализует интерфейс из domain, превращает модели в сущности, исключения — в `Failure` | data sources и domain |

В качестве API используем публичный тестовый сервис `https://dummyjson.com`. Ответ на `GET /products` выглядит так:

```json
{
  "products": [
    {
      "id": 1,
      "title": "Essence Mascara Lash Princess",
      "description": "Popular mascara...",
      "price": 9.99,
      "rating": 4.94,
      "stock": 5,
      "thumbnail": "https://cdn.dummyjson.com/.../thumbnail.png"
    }
  ],
  "total": 194,
  "skip": 0,
  "limit": 30
}
```

## Модель и json_serializable

Модель — «зеркало» JSON. `fromJson` генерируем через `json_serializable`, как в [уроке про JSON](lesson:json-modeli-dio-get):

```bash
flutter pub add json_annotation
flutter pub add --dev json_serializable build_runner
```

```dart
// lib/features/products/data/models/product_model.dart
import 'package:json_annotation/json_annotation.dart';

part 'product_model.g.dart';

@JsonSerializable(createToJson: false) // toJson нам не нужен
class ProductModel {
  const ProductModel({
    required this.id,
    required this.title,
    required this.description,
    required this.price,
    required this.thumbnail,
    this.rating = 0,
    this.stock = 0,
  });

  final int id;
  final String title;
  final String description;
  final double price;
  final String thumbnail;
  final double rating;
  final int stock;

  factory ProductModel.fromJson(Map<String, dynamic> json) =>
      _$ProductModelFromJson(json);
}
```

Запустите генерацию:

```bash
dart run build_runner build --delete-conflicting-outputs
```

-   Поле называется `thumbnail`, как на сервере. В сущности оно называется `imageUrl` — так удобнее приложению.
-   Для `double` генератор сам пишет `(json['price'] as num).toDouble()`, поэтому цена `10` (целое) тоже распарсится.

## Маппер: модель → сущность

**Маппер** — код, который переводит объект одного слоя в объект другого, как переводчик между сервером и приложением.

```dart
// lib/features/products/data/mappers/product_mapper.dart
import '../../domain/entities/product.dart';
import '../models/product_model.dart';

extension ProductModelMapper on ProductModel {
  Product toEntity() => Product(
        id: id,
        title: title,
        description: description,
        price: price,
        imageUrl: thumbnail,
        rating: rating,
        stock: stock,
      );
}
```

`extension` добавляет метод `toEntity()` к `ProductModel`, не меняя сам класс. Теперь можно писать `model.toEntity()`. Подробнее о расширениях — в уроке [Generics, базовые классы и extensions](lesson:generics-enum-screenutil).

Зачем разделять модель и сущность? Если сервер переименует `thumbnail` в `image_url`, правим только модель и маппер — остальное приложение ничего не заметит.

## Remote data source

Data source делает HTTP-запрос и парсинг. Интерфейс + реализация — чтобы подменять его в тестах.

```dart
// lib/features/products/data/datasources/product_remote_data_source.dart
import 'package:dio/dio.dart';
import '../models/product_model.dart';

abstract interface class ProductRemoteDataSource {
  Future<List<ProductModel>> getProducts();
  Future<ProductModel> getProductById(int id);
  Future<List<ProductModel>> searchProducts(String query);
}

class ProductRemoteDataSourceImpl implements ProductRemoteDataSource {
  const ProductRemoteDataSourceImpl(this._dio);

  final Dio _dio;

  @override
  Future<List<ProductModel>> getProducts() async {
    final response = await _dio.get<Map<String, dynamic>>('/products');
    return _parseList(response.data!);
  }

  @override
  Future<ProductModel> getProductById(int id) async {
    final response = await _dio.get<Map<String, dynamic>>('/products/$id');
    return ProductModel.fromJson(response.data!);
  }

  @override
  Future<List<ProductModel>> searchProducts(String query) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/products/search',
      queryParameters: {'q': query},
    );
    return _parseList(response.data!);
  }

  List<ProductModel> _parseList(Map<String, dynamic> json) =>
      (json['products'] as List)
          .map((e) => ProductModel.fromJson(e as Map<String, dynamic>))
          .toList();
}
```

Разбор:

-   `get<Map<String, dynamic>>` — подсказываем Dio тип ответа.
-   Data source возвращает **модели** и может бросить `DioException`. Ошибки он не обрабатывает — это задача репозитория.

Кроме remote бывает **local data source** — кеш в памяти, `shared_preferences`, Hive или drift. Он устроен так же: интерфейс + реализация, а репозиторий решает, когда брать данные из сети, а когда из кеша.

## Реализация репозитория

Репозиторий превращает модели в сущности, а `DioException` — в понятный `Failure`.

```dart
// lib/features/products/data/repositories/product_repository_impl.dart
import 'package:dio/dio.dart';
import '../../../../core/error/failures.dart';
import '../../domain/entities/product.dart';
import '../../domain/repositories/product_repository.dart';
import '../datasources/product_remote_data_source.dart';
import '../mappers/product_mapper.dart';

class ProductRepositoryImpl implements ProductRepository {
  const ProductRepositoryImpl(this._remote);

  final ProductRemoteDataSource _remote;

  @override
  Future<List<Product>> getProducts() => _guard(() async {
        final models = await _remote.getProducts();
        return models.map((m) => m.toEntity()).toList();
      });

  @override
  Future<Product> getProductById(int id) =>
      _guard(() async => (await _remote.getProductById(id)).toEntity());

  @override
  Future<List<Product>> searchProducts(String query) => _guard(() async {
        final models = await _remote.searchProducts(query);
        return models.map((m) => m.toEntity()).toList();
      });

  // Выполняет запрос и превращает DioException в Failure
  Future<T> _guard<T>(Future<T> Function() action) async {
    try {
      return await action();
    } on DioException catch (e) {
      throw _mapError(e);
    }
  }

  Failure _mapError(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionError:
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.receiveTimeout:
        return const NetworkFailure();
      default:
        if (e.response?.statusCode == 401) return const UnauthorizedFailure();
        return ServerFailure('Ошибка сервера: ${e.response?.statusCode ?? '—'}');
    }
  }
}
```

Разбор:

-   Репозиторий зависит от **интерфейса** `ProductRemoteDataSource`, а не от реализации.
-   `models.map((m) => m.toEntity())` — маппер в действии: наружу уходят только сущности.
-   `_guard<T>` — общий «обёрточный» метод: он выполняет любой запрос и ловит `DioException`. `<T>` — это generic, тип результата (подробно — в [следующем уроке](lesson:generics-enum-screenutil)).
-   `_mapError` — единственное место, где `DioException` превращается в `Failure`. Выше по слоям Dio уже не виден.

## Регистрация зависимостей в GetIt

Собираем всё в одном файле снизу вверх: внешние библиотеки → data → domain → presentation.

```dart
// lib/core/di/injection.dart
import 'package:dio/dio.dart';
import 'package:get_it/get_it.dart';
// + импорты классов фичи products

final sl = GetIt.instance;

Future<void> initDependencies() async {
  // External
  sl.registerLazySingleton<Dio>(
    () => Dio(BaseOptions(baseUrl: 'https://dummyjson.com')),
  );

  // Data
  sl.registerLazySingleton<ProductRemoteDataSource>(
    () => ProductRemoteDataSourceImpl(sl()),
  );
  sl.registerLazySingleton<ProductRepository>(
    () => ProductRepositoryImpl(sl()),
  );

  // Domain
  sl.registerLazySingleton(() => GetProducts(sl()));
  sl.registerLazySingleton(() => SearchProducts(sl()));

  // Presentation
  sl.registerFactory(() => ProductsBloc(sl()));
}
```

```dart
// lib/main.dart
import 'package:flutter/material.dart';
import 'core/di/injection.dart';
import 'features/products/presentation/pages/products_page.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initDependencies();
  runApp(const ShopApp());
}

// ShopApp — MaterialApp(home: ProductsPage())
```

Ключевой момент — `registerLazySingleton<ProductRepository>(() => ProductRepositoryImpl(...))`. В угловых скобках стоит **интерфейс**. Все получат реализацию, не зная о ней, а в тестах под этим типом можно зарегистрировать `FakeProductRepository`.

## Связка с Bloc

Bloc получает UseCase через конструктор. События и состояния описываем через `sealed class`, как в [уроке про Bloc](lesson:bloc-event-state).

```dart
// lib/features/products/presentation/bloc/products_bloc.dart
import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../core/error/failures.dart';
import '../../domain/entities/product.dart';
import '../../domain/usecases/get_products.dart';

// События
sealed class ProductsEvent {}

final class ProductsRequested extends ProductsEvent {}

// Состояния
sealed class ProductsState extends Equatable {
  const ProductsState();
  @override
  List<Object?> get props => [];
}

final class ProductsLoading extends ProductsState {
  const ProductsLoading();
}

final class ProductsLoaded extends ProductsState {
  const ProductsLoaded(this.products);
  final List<Product> products;
  @override
  List<Object?> get props => [products];
}

final class ProductsError extends ProductsState {
  const ProductsError(this.message);
  final String message;
  @override
  List<Object?> get props => [message];
}

// Bloc
class ProductsBloc extends Bloc<ProductsEvent, ProductsState> {
  ProductsBloc(this._getProducts) : super(const ProductsLoading()) {
    on<ProductsRequested>(_onRequested);
  }

  final GetProducts _getProducts;

  Future<void> _onRequested(
    ProductsRequested event,
    Emitter<ProductsState> emit,
  ) async {
    emit(const ProductsLoading());
    try {
      emit(ProductsLoaded(await _getProducts()));
    } on Failure catch (f) {
      emit(ProductsError(f.message));
    }
  }
}
```

Экран берёт Bloc из GetIt:

```dart
// lib/features/products/presentation/pages/products_page.dart
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../core/di/injection.dart';
import '../bloc/products_bloc.dart';

class ProductsPage extends StatelessWidget {
  const ProductsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => sl<ProductsBloc>()..add(ProductsRequested()),
      child: Scaffold(
        appBar: AppBar(title: const Text('Каталог')),
        body: BlocBuilder<ProductsBloc, ProductsState>(
          builder: (context, state) => switch (state) {
            ProductsLoading() =>
              const Center(child: CircularProgressIndicator()),
            ProductsError(:final message) => Center(child: Text(message)),
            ProductsLoaded(:final products) => ListView.builder(
                itemCount: products.length,
                itemBuilder: (_, i) => ListTile(
                  leading: Image.network(products[i].imageUrl, width: 56),
                  title: Text(products[i].title),
                  trailing: Text('\$${products[i].price}'),
                ),
              ),
          },
        ),
      ),
    );
  }
}
```

-   `sl<ProductsBloc>()` — GetIt создаёт новый Bloc (фабрика), подставив `GetProducts`, а тот — `ProductRepository` и так далее.
-   `ProductsError(:final message)` — паттерн Dart 3: поле прямо в `switch`.

## MVVM: как это называется

**MVVM (Model–View–ViewModel)** — паттерн о том, как экран общается с данными.

| Часть MVVM | Что это в нашем магазине | Задача |
| --- | --- | --- |
| **Model** | Сущности, UseCase, репозитории (domain + data) | Данные и бизнес-логика |
| **View** | `ProductsPage`, виджеты | Показать состояние, передать действия пользователя |
| **ViewModel** | `ProductsBloc` или `Cubit` | Хранить состояние экрана, вызывать Model |

Главное правило MVVM: **View глупая**. Она не принимает решений — только рисует то, что дала ViewModel, и сообщает о нажатиях.

ViewModel можно писать и на `Cubit` — это Bloc без событий, с обычными методами вроде `load(id)`. Для экрана товара без бизнес-правил Cubit может вызывать репозиторий напрямую, без UseCase; как только правила появятся — выносите их в UseCase.

## Типичные ошибки

-   **Регистрация реализации без интерфейса.** `sl.registerLazySingleton(() => ProductRepositoryImpl(...))` зарегистрирует тип `ProductRepositoryImpl`, и `sl<ProductRepository>()` упадёт. Указывайте тип явно: `registerLazySingleton<ProductRepository>`.
-   **`sl()` где попало.** Вызывайте GetIt только в `injection.dart` и в `BlocProvider`; остальные классы получают зависимости через конструктор.
-   **Забыли `build_runner`.** Ошибка `Target of URI hasn't been generated: product_model.g.dart` — запустите генерацию.

## Практика

1.  Напишите `ProductModel` и маппер `toEntity()`. Проверьте, что JSON из урока превращается в `Product` с правильным `imageUrl`.
2.  Реализуйте `ProductRemoteDataSourceImpl` и `ProductRepositoryImpl`, зарегистрируйте всё в `initDependencies()`. Ожидаемый результат: экран каталога показывает товары с dummyjson.com.
3.  Выключите интернет на эмуляторе и перезапустите экран. Должен появиться текст «Нет подключения к интернету», а не красный экран с `DioException`.
4.  Сделайте экран товара на `ProductDetailsCubit` с методом `load(int id)` и своими sealed-состояниями. По нажатию на элемент списка открывается страница с картинкой, описанием и ценой.
5.  Добавьте в `ProductsBloc` событие поиска `ProductsSearched(String query)`, которое вызывает UseCase `SearchProducts` из первой части. Поле поиска — `TextField` в `AppBar`.

## Итоги

-   Слой data состоит из data sources (запросы), моделей (JSON) и реализации репозитория.
-   Маппер `toEntity()` отделяет формат сервера от сущностей приложения.
-   Репозиторий — единственное место, где `DioException` превращается в `Failure`.
-   В GetIt регистрируем снизу вверх и под типом интерфейса: `registerLazySingleton<ProductRepository>(...)`.
-   Bloc получает UseCase через конструктор, а экран берёт Bloc через `sl<ProductsBloc>()`.
-   MVVM: View рисует, ViewModel (Bloc/Cubit) хранит состояние, Model — domain и data.
