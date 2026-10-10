В этом месяце мы строим интернет-магазин, и начинаем не с экранов, а с фундамента — с архитектуры. Разберём, что такое внедрение зависимостей (DI), как с ним помогает пакет **GetIt** и как разложить код по слоям **Clean Architecture**: domain, data и presentation. В первой части создадим сущности, интерфейс репозитория и первый UseCase, а во [второй части](lesson:getit-di-clean-2) подключим реальную сеть и Bloc.

## Зачем вообще архитектура

В WeatherApp был один экран и один запрос. В магазине будут каталог, карточка товара, корзина, авторизация, заказы. Без правил через месяц вы получите код, в котором:

-   запрос Dio вызывается прямо из виджета;
-   чтобы поменять адрес API, приходится править десяток файлов;
-   проверить логику без запуска приложения невозможно.

Архитектура — это договорённость, **где какой код живёт и кто кого может вызывать**. Аналогия — ресторан: официант принимает заказ (интерфейс), повар готовит (бизнес-логика), закупщик ходит на рынок (данные). Каждый занят своим, и замена одного не ломает работу остальных.

## Что такое зависимость и DI

**Зависимость** — это объект, без которого класс не может работать. Например, репозиторию товаров нужен `Dio`, чтобы ходить в сеть. Значит, `Dio` — зависимость репозитория.

Посмотрим на плохой вариант, где класс сам создаёт свою зависимость:

```dart
import 'package:dio/dio.dart';

class ProductService {
  // Класс сам создаёт Dio — жёсткая связь
  final Dio _dio = Dio(BaseOptions(baseUrl: 'https://dummyjson.com'));

  Future<List<dynamic>> loadProducts() async {
    final response = await _dio.get('/products');
    return response.data['products'] as List<dynamic>;
  }
}
```

Что здесь не так:

-   Нельзя подменить `Dio` на фейковый в тестах — класс всегда пойдёт в настоящую сеть.
-   10 таких сервисов — это 10 разных `Dio` с 10 копиями настроек и интерцепторов.

**Dependency Injection (внедрение зависимостей)** — это когда класс не создаёт зависимость сам, а **получает её снаружи**, обычно через конструктор:

```dart
import 'package:dio/dio.dart';

class ProductService {
  ProductService(this._dio); // Dio приходит снаружи

  final Dio _dio;
  // ...методы те же, что и выше
}

// Где-то при старте приложения:
final dio = Dio(BaseOptions(baseUrl: 'https://dummyjson.com'));
final service = ProductService(dio);
```

Аналогия: фонарик с запаянными батарейками против фонарика с отсеком, куда можно вставить любые — обычные, аккумуляторные, тестовые. Класс с DI — это фонарик с отсеком.

<aside class="callout" data-icon="📌" markdown="1">

Правило DI простое: **класс говорит, что ему нужно (в конструкторе), но не решает, где это взять**. Решение «откуда взять» принимается в одном месте — при старте приложения.

</aside>

## GetIt — склад готовых объектов

Собирать объекты вручную неудобно: `ProductsBloc` нужен `GetProducts`, ему — `ProductRepository`, ему — data source, ему — `Dio`.

**GetIt** — это **service locator**, «склад» объектов. Вы один раз при старте говорите складу, как создавать каждый объект, а потом в любом месте просите: «дай мне `ProductRepository`». Склад сам соберёт всё нужное.

Установка:

```bash
flutter pub add get_it
```

### Первый пример

```dart
import 'package:get_it/get_it.dart';

// Глобальная точка доступа к складу. Часто называют sl (service locator)
final sl = GetIt.instance;

class CartCounter {
  int count = 0;
}

void setupDependencies() {
  sl.registerLazySingleton<CartCounter>(() => CartCounter());
}

void main() {
  setupDependencies();

  final a = sl<CartCounter>();
  final b = sl<CartCounter>();
  a.count = 3;
  print(b.count); // 3 — это один и тот же объект
}
```

Разбор:

-   `registerLazySingleton<CartCounter>(() => CartCounter())` — «когда кто-то впервые попросит `CartCounter`, создай его этой функцией и дальше всегда отдавай тот же объект».
-   `sl<CartCounter>()` — получить объект. Это короткая запись для `sl.get<CartCounter>()`.

### Три способа регистрации

| Метод | Когда создаётся | Сколько экземпляров | Пример использования |
| --- | --- | --- | --- |
| `registerSingleton(obj)` | Сразу при регистрации | Один | Объект, который нужен с самого старта: настройки |
| `registerLazySingleton(() => obj)` | При первом запросе | Один | `Dio`, репозитории, data sources, UseCase |
| `registerFactory(() => obj)` | При каждом запросе | Каждый раз новый | Bloc и Cubit для экранов |

Почему Bloc регистрируют как `factory`? Bloc живёт вместе с экраном: экран закрылся — `BlocProvider` вызывает `close()`. Если бы Bloc был синглтоном, при повторном открытии экрана вы получили бы уже закрытый Bloc и ошибку `Cannot add new events after calling close`.

```dart
sl.registerFactory(() => ProductsBloc(sl()));       // новый на каждый экран
sl.registerLazySingleton(() => GetProducts(sl()));  // один на всё приложение
```

`sl()` внутри: GetIt по типу параметра конструктора сам поймёт, какой объект подставить.

<aside class="callout" data-icon="⚠️" markdown="1">

Частая ошибка — `Object/factory with type X is not registered inside GetIt`. Проверьте, что `setupDependencies()` вызывается **до** `runApp()`, а тип при регистрации совпадает с типом при запросе (интерфейс и реализация — разные типы!).

</aside>

## Clean Architecture: три слоя

**Clean Architecture** делит каждую фичу приложения на три слоя. Представьте торт из трёх коржей:

```text
┌─────────────────────────────────────────┐
│ presentation  — экраны, виджеты, Bloc   │  что видит пользователь
├─────────────────────────────────────────┤
│ domain        — сущности, UseCase,      │  бизнес-правила магазина
│                 интерфейсы репозиториев │
├─────────────────────────────────────────┤
│ data          — модели, data sources,   │  откуда берутся данные
│                 реализации репозиториев │
└─────────────────────────────────────────┘
```

-   **Domain (предметная область)** — сердце приложения. Здесь описано, что такое «товар», «корзина», «заказ» и что с ними можно делать. Этот слой — чистый Dart: никаких `Dio`, `Flutter`, JSON.
-   **Data (данные)** — знает, как достать данные: из API через Dio, из локальной базы, из кеша. Превращает JSON в объекты.
-   **Presentation (представление)** — виджеты и Bloc. Показывает данные и реагирует на нажатия.

### Правило зависимостей

Главное правило Clean Architecture: **зависимости направлены внутрь, к domain**.

```text
presentation  ──►  domain  ◄──  data
```

-   presentation знает о domain (вызывает UseCase, показывает сущности);
-   data знает о domain (реализует интерфейс репозитория, возвращает сущности);
-   **domain не знает ни о ком**. В файлах domain не должно быть `import 'package:dio/...'` или `import 'package:flutter/material.dart'`.

Зачем так строго? Если магазин переедет с REST на Firebase, поменяется только слой data.

### Структура папок

Мы используем подход **feature-first**: сначала папка фичи, внутри — слои.

```text
lib/
├── core/
│   ├── di/injection.dart          # регистрация зависимостей GetIt
│   ├── error/failures.dart        # ошибки уровня domain
│   └── network/dio_client.dart
├── features/
│   └── products/
│       ├── domain/
│       │   ├── entities/product.dart
│       │   ├── repositories/product_repository.dart
│       │   └── usecases/get_products.dart
│       ├── data/
│       │   ├── datasources/product_remote_data_source.dart
│       │   ├── models/product_model.dart
│       │   └── repositories/product_repository_impl.dart
│       └── presentation/
│           ├── bloc/products_bloc.dart
│           ├── pages/products_page.dart
│           └── widgets/product_card.dart
└── main.dart
```

Позже рядом с `products` появятся `cart`, `auth`, `orders` с такой же структурой.

## Слой domain: сущности

**Сущность (entity)** — это объект предметной области в том виде, в каком он удобен приложению. Не в том, в каком его прислал сервер, а в том, как его понимает бизнес.

```dart
// lib/features/products/domain/entities/product.dart
import 'package:equatable/equatable.dart';

class Product extends Equatable {
  const Product({
    required this.id,
    required this.title,
    required this.description,
    required this.price,
    required this.imageUrl,
    required this.rating,
    required this.stock,
  });

  final int id;
  final String title;
  final String description;
  final double price;
  final String imageUrl;
  final double rating;
  final int stock;

  bool get inStock => stock > 0;

  @override
  List<Object?> get props => [id, title, description, price, imageUrl, rating, stock];
}
```

Разбор:

-   Все поля `final` — сущность неизменяема.
-   `Equatable` (вы знаете его по [уроку про JSON-модели](lesson:json-modeli-dio-get)) сравнивает объекты по полям. Bloc не будет перерисовывать экран, если пришёл такой же товар.
-   `inStock` — маленькое бизнес-правило прямо в сущности.
-   Здесь **нет** `fromJson`. Сущность не знает, что существует JSON, — это забота слоя data.

## Ошибки уровня domain: Failure

Слой data может получить `DioException`, ошибку парсинга, отсутствие интернета. Но domain и presentation не должны знать о Dio. Поэтому заводим свои понятные ошибки — **Failure**:

```dart
// lib/core/error/failures.dart
sealed class Failure {
  const Failure(this.message);
  final String message;
}

class NetworkFailure extends Failure {
  const NetworkFailure() : super('Нет подключения к интернету');
}

class ServerFailure extends Failure {
  const ServerFailure(super.message);
}

class UnauthorizedFailure extends Failure {
  const UnauthorizedFailure() : super('Нужно войти в аккаунт');
}
```

`sealed` (Dart 3) означает: все наследники `Failure` перечислены в этом файле. Благодаря этому `switch` по `Failure` компилятор проверит на полноту — если забудете обработать один из вариантов, получите предупреждение.

## Слой domain: интерфейс репозитория

**Репозиторий** — это «склад данных» для одной сущности. Domain описывает только **что** можно получить, но не **как**:

```dart
// lib/features/products/domain/repositories/product_repository.dart
import '../entities/product.dart';

abstract interface class ProductRepository {
  /// Список товаров. Бросает [Failure] при ошибке.
  Future<List<Product>> getProducts();

  /// Один товар по id.
  Future<Product> getProductById(int id);

  /// Поиск по названию.
  Future<List<Product>> searchProducts(String query);
}
```

-   `abstract interface class` — в Dart 3 это класс, который можно только **реализовать** (`implements`), но нельзя создать или унаследовать с кодом. По сути, это контракт.
-   Реализацию (`ProductRepositoryImpl` с Dio) напишем в слое data во второй части.

## Слой domain: UseCase

**UseCase (сценарий использования)** — это одно действие пользователя, оформленное как отдельный класс: «получить каталог», «добавить в корзину», «оформить заказ».

```dart
// lib/features/products/domain/usecases/get_products.dart
import '../entities/product.dart';
import '../repositories/product_repository.dart';

class GetProducts {
  const GetProducts(this._repository);

  final ProductRepository _repository;

  Future<List<Product>> call() => _repository.getProducts();
}
```

Разбор:

-   UseCase получает **интерфейс** `ProductRepository` через конструктор — это DI. Какая реализация придёт, UseCase не волнует.
-   Метод `call()` — особенный в Dart: объект с ним можно вызывать как функцию. `getProducts()` вместо `getProducts.call()`.

Пока этот UseCase просто передаёт вызов дальше, но бизнес-логика растёт. Пример — UseCase поиска:

```dart
// lib/features/products/domain/usecases/search_products.dart
import '../entities/product.dart';
import '../repositories/product_repository.dart';

class SearchProducts {
  const SearchProducts(this._repository);

  final ProductRepository _repository;

  Future<List<Product>> call(String query) async {
    final trimmed = query.trim();
    // Бизнес-правило: короткие запросы не отправляем на сервер
    if (trimmed.length < 2) return const [];

    final products = await _repository.searchProducts(trimmed);
    // Бизнес-правило: товары в наличии показываем первыми
    return [...products]..sort((a, b) {
        if (a.inStock == b.inStock) return 0;
        return a.inStock ? -1 : 1;
      });
  }
}
```

Правила «не искать по одной букве» и «сначала товары в наличии» — это решения бизнеса. Они не относятся ни к Dio, ни к виджетам, поэтому живут в UseCase. Их легко протестировать без эмулятора.

## Как это связывается с Bloc

Bloc находится в слое presentation и вызывает UseCase: `final products = await _getProducts();`. Он ничего не знает про Dio и JSON, а ошибки получает в виде `Failure`. Полный `ProductsBloc` напишем во [второй части](lesson:getit-di-clean-2).

Вся цепочка вызовов в магазине выглядит так:

```text
Виджет ──событие──► ProductsBloc ──► GetProducts ──► ProductRepository (интерфейс)
                                                         ▲
                                       ProductRepositoryImpl ──► RemoteDataSource ──► Dio
```

А GetIt соберёт эту цепочку за нас — регистрацию напишем во второй части.

## Типичные ошибки

-   **Импорт Flutter или Dio в domain.** Если в `entities` или `usecases` видите `package:flutter` или `package:dio` — слои перепутаны.
-   **Возврат моделей вместо сущностей.** Репозиторий в domain возвращает `Product`, а не `ProductModel` и не `Map<String, dynamic>`.
-   **Bloc как синглтон.** Регистрируйте Bloc через `registerFactory`.
-   **Огромный UseCase «на всё».** Один UseCase — одно действие. `ProductsUseCase` с десятью методами — это снова сервис-свалка.

## Практика

1.  Создайте проект `shop_app` и папки по структуре из урока. Результат: дерево папок и файл `lib/core/di/injection.dart` с `final sl = GetIt.instance;`.
2.  Напишите сущность `Product` с `Equatable` и геттером `inStock`. Проверьте в `main()`, что два товара с одинаковыми полями равны (`==` возвращает `true`).
3.  Опишите `abstract interface class ProductRepository` и создайте `FakeProductRepository implements ProductRepository`, который возвращает три захардкоженных товара (один — со `stock: 0`).
4.  Напишите UseCase `SearchProducts` и проверьте его с фейковым репозиторием: запрос `"a"` возвращает пустой список, а товар без остатка оказывается в конце.
5.  Зарегистрируйте в GetIt `FakeProductRepository` как `ProductRepository` (`registerLazySingleton<ProductRepository>(...)`) и `GetProducts`. Получите `sl<GetProducts>()` в `main()` и выведите названия товаров в консоль.

## Итоги

-   DI — класс получает зависимости снаружи, а не создаёт их сам. Это делает код гибким и тестируемым.
-   GetIt — склад объектов: `registerSingleton`, `registerLazySingleton`, `registerFactory`; Bloc регистрируем фабрикой.
-   Clean Architecture делит фичу на domain, data и presentation; зависимости направлены к domain.
-   Domain — чистый Dart: сущности, Failure, интерфейсы репозиториев, UseCase.
-   Репозиторий в domain — это контракт «что получить», реализация «как получить» живёт в data.
-   UseCase — одно действие пользователя с бизнес-правилами; Bloc вызывает UseCase, а не Dio.
