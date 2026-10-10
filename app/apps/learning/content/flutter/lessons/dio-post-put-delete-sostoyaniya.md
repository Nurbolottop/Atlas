Получать данные мы уже умеем, но приложения ещё и создают, изменяют и удаляют записи: отправляют отзыв, редактируют профиль, удаляют город из избранного. В этом уроке разберём методы POST, PUT и DELETE в Dio, научимся ловить `DioException` и понимать коды ответов 400 и 500, а затем свяжем всё с Bloc через три понятных состояния: загрузка, успех и ошибка.

## HTTP-методы: короткая шпаргалка

Метод запроса — это глагол, который говорит серверу, что мы хотим сделать. Представьте библиотеку:

| Метод | Что делает | Аналогия | Тело запроса |
| --- | --- | --- | --- |
| `GET` | Получить данные | Посмотреть книгу | Нет |
| `POST` | Создать новую запись | Сдать новую книгу в фонд | Да |
| `PUT` | Заменить запись целиком | Заменить книгу новым изданием | Да |
| `PATCH` | Изменить часть записи | Исправить опечатку на странице | Да |
| `DELETE` | Удалить запись | Списать книгу | Обычно нет |

**Тело запроса (body)** — данные, которые мы отправляем на сервер, чаще всего JSON.

Для тренировки возьмём учебный сервер JSONPlaceholder с базовым адресом `https://jsonplaceholder.typicode.com`. Он принимает любые запросы и отвечает правдоподобно, но реально ничего не сохраняет — для практики это идеально.

## Модель для примеров

```dart
import 'package:equatable/equatable.dart';

class Note extends Equatable {
  const Note({this.id, required this.title, required this.body, required this.userId});

  final int? id; // у новой заметки id ещё нет — его выдаст сервер
  final String title;
  final String body;
  final int userId;

  factory Note.fromJson(Map<String, dynamic> json) => Note(
        id: json['id'] as int?,
        title: json['title'] as String,
        body: json['body'] as String,
        userId: json['userId'] as int,
      );

  Map<String, dynamic> toJson() => {
        if (id != null) 'id': id,
        'title': title,
        'body': body,
        'userId': userId,
      };

  @override
  List<Object?> get props => [id, title, body, userId];
}
```

`if (id != null) 'id': id` — «collection if» в Dart: ключ попадёт в словарь только если `id` есть. Модели мы подробно разбирали в уроке [про JSON и Dio GET](lesson:json-modeli-dio-get).

## POST: создаём запись

```dart
import 'package:dio/dio.dart';

final dio = Dio(BaseOptions(
  baseUrl: 'https://jsonplaceholder.typicode.com',
  connectTimeout: const Duration(seconds: 10),
  receiveTimeout: const Duration(seconds: 10),
));

Future<Note> createNote(Note note) async {
  final response = await dio.post<Map<String, dynamic>>(
    '/posts',
    data: note.toJson(),
  );
  return Note.fromJson(response.data!);
}
```

Разбор:

- `dio.post(path, data: ...)` — второй важный параметр `data`, это тело запроса.
- Передаём `Map` — Dio сам превратит его в JSON и поставит заголовок `Content-Type: application/json`.
- Сервер в ответ обычно возвращает созданную запись уже **с id** и код `201 Created`.

## PUT и PATCH: изменяем запись

```dart
Future<Note> updateNote(Note note) async {
  final response = await dio.put<Map<String, dynamic>>(
    '/posts/${note.id}',
    data: note.toJson(),
  );
  return Note.fromJson(response.data!);
}

Future<void> renameNote(int id, String newTitle) async {
  await dio.patch('/posts/$id', data: {'title': newTitle});
}
```

- В адресе указываем, **какую** запись меняем: `/posts/1`.
- `PUT` отправляет запись целиком: поля, которых нет в теле, сервер может обнулить.
- `PATCH` — только изменившиеся поля.

## DELETE: удаляем запись

```dart
Future<void> deleteNote(int id) async {
  await dio.delete('/posts/$id');
}
```

Обычно сервер отвечает `200 OK` или `204 No Content` (успех, но тело пустое). Поэтому функция возвращает `Future<void>` — нам важен только факт успеха.

### Заголовки и токен

Часто сервер требует подтвердить, кто вы. Для этого в заголовок `Authorization` кладут токен:

```dart
await dio.delete(
  '/posts/1',
  options: Options(headers: {'Authorization': 'Bearer YOUR_TOKEN'}),
);
```

Чтобы не писать это в каждом запросе, токен добавляют в перехватчике (interceptor):

```dart
dio.interceptors.add(
  InterceptorsWrapper(
    onRequest: (options, handler) {
      options.headers['Authorization'] = 'Bearer YOUR_TOKEN';
      handler.next(options); // обязательно передать запрос дальше
    },
  ),
);
```

Откуда берётся настоящий токен, разберём в уроке [Firebase Auth](lesson:firebase-auth).

## Коды ответа: 2xx, 4xx, 5xx

Каждый ответ сервера содержит **статус-код** — трёхзначное число. Первая цифра говорит, кто «виноват»:

| Код | Значение | Кто виноват | Что показать пользователю |
| --- | --- | --- | --- |
| `200`, `201`, `204` | Успех | — | Результат |
| `400 Bad Request` | Неверные данные в запросе | Клиент | «Проверьте введённые данные» |
| `401 Unauthorized` | Нет или неверный токен | Клиент | Отправить на экран входа |
| `403 Forbidden` | Нет прав | Клиент | «Нет доступа» |
| `404 Not Found` | Такого ресурса нет | Клиент | «Не найдено» |
| `500 Internal Server Error` | Сломался сервер | Сервер | «Сервис временно недоступен» |
| `502`, `503` | Сервер перегружен или недоступен | Сервер | «Попробуйте позже» |

Запомнить просто: **4xx — ошибка в нашем запросе, 5xx — проблема на сервере**. При 400 повторять тот же запрос бессмысленно, нужно исправить данные. При 500 имеет смысл предложить «Повторить».

## DioException: ловим ошибки

По умолчанию Dio считает успешными только коды 2xx. Любой другой код, обрыв сети или таймаут превращаются в исключение **`DioException`**. Его поле `type` говорит, что именно случилось:

| `DioExceptionType` | Когда возникает |
| --- | --- |
| `connectionTimeout` | Не удалось подключиться за `connectTimeout` |
| `sendTimeout` / `receiveTimeout` | Слишком долго отправляли или ждали ответ |
| `badResponse` | Сервер ответил, но с кодом 4xx или 5xx |
| `connectionError` | Нет интернета, неверный адрес |
| `cancel` | Запрос отменили через `CancelToken` |
| `badCertificate` | Проблема с SSL-сертификатом |
| `unknown` | Всё остальное |

### Превращаем исключение в понятный текст

```dart
String describeError(DioException e) {
  switch (e.type) {
    case DioExceptionType.connectionTimeout:
    case DioExceptionType.sendTimeout:
    case DioExceptionType.receiveTimeout:
      return 'Сервер долго не отвечает. Проверьте интернет.';
    case DioExceptionType.connectionError:
      return 'Нет подключения к интернету.';
    case DioExceptionType.badResponse:
      final code = e.response?.statusCode ?? 0;
      if (code == 400) return 'Неверные данные запроса.';
      if (code == 401) return 'Нужно войти заново.';
      if (code == 404) return 'Данные не найдены.';
      if (code >= 500) return 'Ошибка сервера ($code). Попробуйте позже.';
      return 'Ошибка запроса ($code).';
    case DioExceptionType.cancel:
      return 'Запрос отменён.';
    default:
      return 'Что-то пошло не так.';
  }
}
```

- `e.response` есть только когда сервер ответил (`badResponse`). При отсутствии сети он `null` — поэтому `?.`.
- `e.response?.data` часто содержит текст ошибки от сервера, например `{"error": "email already used"}` — его можно показать пользователю.

### Своё исключение для слоя данных

Хорошая практика — не выпускать `DioException` за пределы репозитория. Bloc не должен знать, какая библиотека делает запросы:

```dart
class ApiException implements Exception {
  ApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

class NotesRepository {
  NotesRepository(this._dio);

  final Dio _dio;

  Future<Note> create(Note note) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>('/posts', data: note.toJson());
      return Note.fromJson(response.data!);
    } on DioException catch (e) {
      throw ApiException(describeError(e), statusCode: e.response?.statusCode);
    }
  }

  Future<void> delete(int id) async {
    try {
      await _dio.delete('/posts/$id');
    } on DioException catch (e) {
      throw ApiException(describeError(e), statusCode: e.response?.statusCode);
    }
  }
}
```

`on DioException catch (e)` ловит только ошибки Dio. Ошибки в вашем коде (например, опечатка в `fromJson`) пролетят дальше и не замаскируются под «нет интернета».

<aside class="callout" data-icon="⚠️" markdown="1">

Не пишите пустой `catch (e) {}`. Ошибка «проглотится», экран застрянет в загрузке, а вы не поймёте почему. Как минимум выпускайте состояние ошибки и печатайте её в консоль в режиме отладки.

</aside>

## Состояния: Loading, Success, Error

Любая операция с сетью проходит через одни и те же стадии. Опишем их один раз — и будем использовать везде:

```dart
import 'package:equatable/equatable.dart';

sealed class NotesState extends Equatable {
  const NotesState();
  @override
  List<Object?> get props => [];
}

final class NotesInitialState extends NotesState {
  const NotesInitialState();
}

final class NotesLoadingState extends NotesState {
  const NotesLoadingState();
}

final class NotesSuccessState extends NotesState {
  const NotesSuccessState(this.notes);
  final List<Note> notes;
  @override
  List<Object?> get props => [notes];
}

final class NotesErrorState extends NotesState {
  const NotesErrorState(this.message, {this.statusCode});
  final String message;
  final int? statusCode;
  @override
  List<Object?> get props => [message, statusCode];
}
```

Почему отдельные классы, а не флаги `isLoading`, `error`, `data` в одном? С флагами легко получить невозможную комбинацию: `isLoading = true` и одновременно `error != null`. С `sealed`-классами состояние всегда ровно одно.

### Cubit, который работает с репозиторием

```dart
import 'package:flutter_bloc/flutter_bloc.dart';

class NotesCubit extends Cubit<NotesState> {
  NotesCubit(this._repository) : super(const NotesInitialState());

  final NotesRepository _repository;
  final List<Note> _notes = [];

  Future<void> add(String title, String body) async {
    emit(const NotesLoadingState());
    try {
      final created = await _repository.create(Note(title: title, body: body, userId: 1));
      _notes.add(created);
      emit(NotesSuccessState(List.unmodifiable(_notes)));
    } on ApiException catch (e) {
      emit(NotesErrorState(e.message, statusCode: e.statusCode));
    }
  }

  Future<void> remove(int id) async {
    emit(const NotesLoadingState());
    try {
      await _repository.delete(id);
      _notes.removeWhere((n) => n.id == id);
      emit(NotesSuccessState(List.unmodifiable(_notes)));
    } on ApiException catch (e) {
      emit(NotesErrorState(e.message, statusCode: e.statusCode));
    }
  }
}
```

`List.unmodifiable(_notes)` создаёт **новый** список. Если отдать тот же `_notes`, Equatable решит, что состояние не изменилось (та же ссылка с тем же содержимым), и экран не обновится.

### Экран

```dart
class NotesView extends StatelessWidget {
  const NotesView({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocConsumer<NotesCubit, NotesState>(
      listener: (context, state) {
        if (state is NotesErrorState && state.statusCode == 401) {
          // здесь будет переход на экран входа
        }
      },
      builder: (context, state) {
        return switch (state) {
          NotesInitialState() => const Center(child: Text('Заметок пока нет')),
          NotesLoadingState() => const Center(child: CircularProgressIndicator()),
          NotesErrorState(:final message) => Center(child: Text(message)),
          NotesSuccessState(:final notes) => ListView(
              children: [for (final n in notes) ListTile(title: Text(n.title))],
            ),
        };
      },
    );
  }
}
```

`BlocConsumer` объединяет `BlocBuilder` и `BlocListener` из урока [про Bloc](lesson:bloc-event-state): `builder` рисует, `listener` выполняет одноразовые действия.

<aside class="callout" data-icon="💡" markdown="1">

Чтобы проверить экран ошибки без поломки сервера, отправьте запрос на несуществующий путь (`/postsss`) — получите 404. А чтобы проверить отсутствие сети — включите авиарежим на эмуляторе.

</aside>

## Типичные ошибки

- Передали в `data` строку `jsonEncode(...)` и забыли заголовок — проще передавать `Map`, Dio всё сделает сам.
- Используют `catch (e)` вместо `on DioException catch (e)` и прячут баги в своём коде.
- Обращаются к `e.response!.statusCode` при отсутствии сети — `response` там `null`, будет падение.
- Мутируют список в состоянии вместо создания нового — UI не обновляется.
- Показывают пользователю сырой текст исключения вроде `DioException [bad response]...` вместо понятного сообщения.

## Практика

1. **POST.** Отправьте на `/posts` новую заметку и выведите в консоль `id` и `statusCode` ответа. Ожидаемый результат: `id: 101`, `statusCode: 201`.
2. **PUT и DELETE.** Измените заголовок записи `/posts/1` через PUT и удалите `/posts/1` через DELETE. Ожидаемый результат: в консоли статусы `200`.
3. **Ошибки.** Вызовите GET на `/posts/999999` и на несуществующий домен. Прогоните исключения через `describeError`. Ожидаемый результат: «Данные не найдены.» и «Нет подключения к интернету.».
4. **Cubit с тремя состояниями.** Соберите экран заметок с формой (два `TextField` и кнопка «Добавить») и удалением по долгому нажатию. Ожидаемый результат: при каждом действии виден спиннер, затем обновлённый список.
5. **Повтор при 5xx.** Добавьте в `NotesErrorState` кнопку «Повторить», которая видна только если `statusCode` больше или равен 500 или его нет (проблема сети). Ожидаемый результат: при 404 кнопки нет, при отсутствии интернета — есть.

## Итоги

- `POST` создаёт, `PUT` заменяет, `PATCH` частично меняет, `DELETE` удаляет; данные передаются в `data`.
- Коды 4xx — ошибка запроса (400 — неверные данные), 5xx — ошибка сервера (500 — сервер упал).
- Dio превращает ошибки в `DioException`; смотрите `e.type` и `e.response?.statusCode`.
- Репозиторий переводит `DioException` в своё исключение с понятным текстом.
- Состояния Loading, Success, Error описываются `sealed`-классами — состояние всегда ровно одно.
- Для обновления UI выпускайте новый объект состояния с новым списком.
