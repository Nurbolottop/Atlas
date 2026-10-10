В первой части мы научились отправлять и читать сообщения одного чата. Теперь превратим это в настоящий мессенджер: сделаем список чатов с последним сообщением, покажем «в сети / был(а) недавно», правильно отсортируем данные, закроем базу правилами безопасности и разложим весь код по слоям Clean Architecture с Bloc.

## Список чатов

Вспомним структуру из [первой части](lesson:chat-firebase-1): у пользователя есть узел `userChats/{uid}`. Сделаем его не просто списком `true`, а «карточкой» для экрана — с собеседником, последним сообщением и временем:

```json
{
  "userChats": {
    "uid_aibek": {
      "uid_aibek_uid_mira": {
        "peerId": "uid_mira",
        "peerName": "Мира",
        "lastMessage": "До завтра!",
        "updatedAt": 1760000500000
      }
    }
  }
}
```

Тогда экран списка читает **один** узел и не трогает сообщения вообще.

### Атомарная запись в несколько мест

При отправке сообщения нужно обновить сразу три места: добавить сообщение и обновить карточки у обоих участников. Если делать три отдельных `set`, при обрыве сети может записаться только часть. Метод `update` с путями записывает всё **атомарно** — либо всё, либо ничего:

```dart
Future<void> sendMessage({
  required String chatId,
  required String myUid,
  required String myName,
  required String peerId,
  required String peerName,
  required String text,
}) async {
  final root = FirebaseDatabase.instance.ref();
  final messageId = root.child('messages/$chatId').push().key!;
  final now = ServerValue.timestamp;

  await root.update({
    'messages/$chatId/$messageId': {
      'senderId': myUid,
      'text': text,
      'createdAt': now,
    },
    'userChats/$myUid/$chatId': {
      'peerId': peerId,
      'peerName': peerName,
      'lastMessage': text,
      'updatedAt': now,
    },
    'userChats/$peerId/$chatId': {
      'peerId': myUid,
      'peerName': myName,
      'lastMessage': text,
      'updatedAt': now,
    },
  });
}
```

- `push().key` — берём только сгенерированный ключ, ничего не записывая.
- Ключи словаря в `update` — это **пути** от корня. Такой приём называют fan-out («разветвлённая запись»).
- Каждый путь перезаписывается целиком. Если в карточке есть другие поля (например, `unread`), пишите отдельные поля: `'userChats/$myUid/$chatId/lastMessage': text`.

### Модель карточки чата

Модель `ChatPreview` устроена так же, как `Message` из первой части: поля `chatId` (ключ узла), `peerId`, `peerName`, `lastMessage`, `updatedAt` (`DateTime`) и конструктор `ChatPreview.fromMap(String chatId, Map<Object?, Object?> map)` с защитой от пустых полей через `?? ''`. Напишите её сами — это первое задание практики.

## Сортировка

В RTDB запросы сортируют **только по возрастанию** и только по одному полю. Стандартный приём: взять последние N записей через `limitToLast` и перевернуть список на клиенте.

```dart
Stream<List<ChatPreview>> watchChats(String uid) {
  return FirebaseDatabase.instance
      .ref('userChats/$uid')
      .orderByChild('updatedAt')
      .limitToLast(100)
      .onValue
      .map((event) {
    final chats = event.snapshot.children
        .map((c) => ChatPreview.fromMap(c.key!, c.value as Map<Object?, Object?>))
        .toList();
    return chats.reversed.toList(); // свежие — сверху
  });
}
```

Кроме `orderByChild` есть `orderByKey()` (ключи `push()` идут по времени), а фильтровать можно через `startAt`, `endAt` и `equalTo`.

<aside class="callout" data-icon="⚠️" markdown="1">

Если в консоли появляется предупреждение «Using an unspecified index», добавьте индекс в правила: `".indexOn": ["updatedAt"]` (пример ниже). Без индекса Firebase скачивает весь узел и сортирует на устройстве — на больших данных это медленно.

</aside>

## Онлайн-статус

Как узнать, что пользователь вышел, если приложение просто убили или пропал интернет? Для этого в RTDB есть два инструмента:

- специальный путь **`.info/connected`** — поток `true/false`: есть ли сейчас связь с сервером;
- **`onDisconnect()`** — «завещание»: вы заранее говорите серверу, что записать, когда соединение оборвётся. Сервер выполнит это сам.

```dart
class PresenceService {
  PresenceService(this._db);
  final FirebaseDatabase _db;
  StreamSubscription<DatabaseEvent>? _sub;

  void start(String uid) {
    final statusRef = _db.ref('users/$uid');
    _sub = _db.ref('.info/connected').onValue.listen((event) async {
      final connected = event.snapshot.value as bool? ?? false;
      if (!connected) return;

      // 1. Сначала оставляем «завещание» на случай обрыва
      await statusRef.onDisconnect().update({
        'online': false,
        'lastSeen': ServerValue.timestamp,
      });
      // 2. Потом отмечаемся онлайн
      await statusRef.update({'online': true});
    });
  }

  Future<void> stop(String uid) async {
    await _sub?.cancel();
    await _db.ref('users/$uid').update({
      'online': false,
      'lastSeen': ServerValue.timestamp,
    });
  }
}
```

Разбор:

- Слушаем `.info/connected`: при каждом переподключении заново регистрируем `onDisconnect` — после обрыва «завещание» уже использовано.
- Порядок важен: сначала `onDisconnect`, потом `online: true`. Иначе при обрыве между этими шагами пользователь навсегда «зависнет» онлайн.
- `stop` вызываем при выходе из аккаунта (`signOut`).

Показать статус собеседника — обычный поток:

```dart
Stream<String> watchPeerStatus(String peerId) {
  return FirebaseDatabase.instance.ref('users/$peerId').onValue.map((e) {
    final data = e.snapshot.value as Map<Object?, Object?>? ?? {};
    if (data['online'] == true) return 'в сети';
    final lastSeen = (data['lastSeen'] as num?)?.toInt();
    if (lastSeen == null) return 'не в сети';
    final time = DateTime.fromMillisecondsSinceEpoch(lastSeen);
    return 'был(а) в ${time.hour}:${time.minute.toString().padLeft(2, '0')}';
  });
}
```

<aside class="callout" data-icon="💡" markdown="1">

В фоне соединение может жить ещё долго. Чтобы сразу показывать «не в сети», используйте `AppLifecycleListener` и вызывайте `FirebaseDatabase.instance.goOffline()` / `goOnline()`.

</aside>

## Правила безопасности

В locked mode никто ничего не читает, а открыть всё (`".read": true`) нельзя: любой прочитает чужую переписку. Правила пишутся в консоли: **Realtime Database → Rules** — это JSON, который проверяется на сервере при каждом запросе.

```json
{
  "rules": {
    "users": {
      "$uid": {
        ".read": "auth != null",
        ".write": "auth != null && auth.uid === $uid"
      }
    },
    "userChats": {
      "$uid": {
        ".read": "auth != null && auth.uid === $uid",
        ".indexOn": ["updatedAt"],
        "$chatId": {
          ".write": "auth != null && $chatId.contains(auth.uid)"
        }
      }
    },
    "messages": {
      "$chatId": {
        ".read": "auth != null && $chatId.contains(auth.uid)",
        ".indexOn": ["createdAt"],
        "$messageId": {
          ".write": "auth != null && !data.exists() && $chatId.contains(auth.uid)",
          ".validate": "newData.hasChildren(['senderId', 'text', 'createdAt']) && newData.child('senderId').val() === auth.uid && newData.child('text').isString() && newData.child('text').val().length > 0 && newData.child('text').val().length <= 1000"
        }
      }
    }
  }
}
```

Что здесь происходит:

| Элемент | Значение |
| --- | --- |
| `auth` | Данные вошедшего пользователя из Firebase Auth; `null`, если не вошёл |
| `$uid`, `$chatId` | «Переменная пути» — подставляется ключ узла |
| `data` / `newData` | Данные до записи / данные, которые хотят записать |
| `.validate` | Проверка формата данных |
| `!data.exists()` | Можно только создавать сообщения, но не менять чужие старые |

- Профиль может изменить только его владелец.
- Список чатов видит только сам пользователь.
- Читать и писать сообщения могут только участники: `chatId` составлен из двух uid, поэтому для учебного проекта хватает `contains(auth.uid)`. В продакшене надёжнее проверять список участников: `root.child('chats/' + $chatId + '/members/' + auth.uid).exists()`.
- Нельзя подделать отправителя: `senderId` обязан совпадать с `auth.uid`.

<aside class="callout" data-icon="🔐" markdown="1">

Проверки в приложении (`if (text.isEmpty)`) — для удобства пользователя. Защищают данные **только** правила на сервере: приложение можно разобрать и отправить запрос напрямую. Перед публикацией проверьте правила во встроенном **Rules Playground** в консоли. Подробнее — [документация по правилам](https://firebase.google.com/docs/database/security).

</aside>

Учтите: правила `.read` **не фильтруют** данные. Если у пользователя нет права читать `messages`, запрос `ref('messages')` целиком вернёт ошибку `permission-denied`, а не «только мои». Поэтому мы читаем конкретные пути: `messages/$chatId`, `userChats/$uid`.

## Архитектура чата с Bloc

Сейчас вызовы Firebase разбросаны по виджетам. Разложим их по слоям, как в уроке [GetIt, DI и Clean Architecture](lesson:getit-di-clean-1):

```text
lib/features/chat/
├── data/
│   ├── datasources/chat_remote_data_source.dart   # работа с Firebase
│   └── repositories/chat_repository_impl.dart
├── domain/
│   ├── entities/message.dart, chat_preview.dart
│   └── repositories/chat_repository.dart          # абстракция
└── presentation/
    ├── bloc/chat_bloc.dart, chat_event.dart, chat_state.dart
    └── pages/chat_page.dart, chats_page.dart
```

### Domain: контракт

```dart
abstract interface class ChatRepository {
  Stream<List<Message>> watchMessages(String chatId);
  Stream<List<ChatPreview>> watchChats(String uid);
  Future<void> sendMessage(SendMessageParams params);
}
```

Domain не знает про Firebase — только про потоки сущностей. Заменим Firebase на WebSocket ([третья часть](lesson:chat-firebase-3)) — Bloc и экраны не изменятся. Реализация `ChatRepositoryImpl` просто делегирует вызовы в `ChatRemoteDataSource`, где лежат функции из этого урока.

### Bloc: подписка на поток

Главный инструмент — `emit.forEach`. Он подписывается на поток, на каждое значение вызывает `onData` и выдаёт новое состояние, а при закрытии Bloc сам отменяет подписку.

```dart
// chat_event.dart
sealed class ChatEvent {}
final class ChatStarted extends ChatEvent {}
final class ChatMessageSent extends ChatEvent {
  ChatMessageSent(this.text);
  final String text;
}

// chat_state.dart
enum ChatStatus { loading, success, failure }

final class ChatState extends Equatable {
  const ChatState({
    this.status = ChatStatus.loading,
    this.messages = const [],
    this.error,
  });
  final ChatStatus status;
  final List<Message> messages;
  final String? error;

  ChatState copyWith({ChatStatus? status, List<Message>? messages, String? error}) =>
      ChatState(
        status: status ?? this.status,
        messages: messages ?? this.messages,
        error: error,
      );

  @override
  List<Object?> get props => [status, messages, error];
}

// chat_bloc.dart
class ChatBloc extends Bloc<ChatEvent, ChatState> {
  ChatBloc({required ChatRepository repository, required this.chatId, required this.myUid})
      : _repository = repository,
        super(const ChatState()) {
    on<ChatStarted>(_onStarted);
    on<ChatMessageSent>(_onMessageSent);
  }

  final ChatRepository _repository;
  final String chatId;
  final String myUid;

  Future<void> _onStarted(ChatStarted event, Emitter<ChatState> emit) {
    return emit.forEach<List<Message>>(
      _repository.watchMessages(chatId),
      onData: (messages) => state.copyWith(status: ChatStatus.success, messages: messages),
      onError: (error, _) => state.copyWith(status: ChatStatus.failure, error: '$error'),
    );
  }

  Future<void> _onMessageSent(ChatMessageSent event, Emitter<ChatState> emit) async {
    final text = event.text.trim();
    if (text.isEmpty) return;
    try {
      await _repository.sendMessage(
        SendMessageParams(chatId: chatId, senderId: myUid, text: text),
      );
    } catch (e) {
      emit(state.copyWith(error: 'Не удалось отправить: $e'));
    }
  }
}
```

Разбор:

- `ChatStarted` запускает подписку один раз — обычно сразу при создании: `ChatBloc(...)..add(ChatStarted())`.
- `return emit.forEach(...)` — обработчик «живёт», пока жив поток. Не забудьте `return` или `await`, иначе подписка оборвётся сразу.
- После отправки мы **не** добавляем сообщение в `state` руками — оно само придёт из потока. Источник правды один — база.
- `SendMessageParams` здесь сокращён; для fan-out в него добавляют данные собеседника из карточки чата.

### Presentation

```dart
BlocProvider(
  create: (_) => ChatBloc(
    repository: getIt<ChatRepository>(),
    chatId: chatId,
    myUid: myUid,
  )..add(ChatStarted()),
  child: BlocBuilder<ChatBloc, ChatState>(
    builder: (context, state) => switch (state.status) {
      ChatStatus.loading => const Center(child: CircularProgressIndicator()),
      ChatStatus.failure => Center(child: Text(state.error ?? 'Ошибка')),
      ChatStatus.success => MessagesList(messages: state.messages, myUid: myUid),
    },
  ),
)
```

Ошибку отправки показывайте через `BlocListener` в `SnackBar` ([BlocSelector и BlocConsumer](lesson:blocselector-blocconsumer)). Так же устроен `ChatsBloc` для списка чатов — он подписывается на `watchChats(uid)`.

## Типичные ошибки

- **`permission-denied` при чтении всего узла** — правила не фильтруют, читайте конкретный путь.
- **Пользователь «вечно онлайн»** — `online: true` записали раньше, чем `onDisconnect()`.
- **Список чатов в обратном порядке** — забыли `reversed` после `limitToLast`.
- **Часть данных записалась** — несколько `set` подряд вместо одного `update`.
- **Bloc не получает новые сообщения** — в обработчике нет `return`/`await` у `emit.forEach`.

## Практика

1. Напишите модель `ChatPreview` и экран «Чаты» на `ChatsBloc`: имя собеседника, последнее сообщение, время. Ожидаемый результат: после отправки сообщения чат поднимается наверх списка.
2. Добавьте в `AppBar` экрана чата статус собеседника «в сети / был(а) в 14:05». Ожидаемый результат: закройте приложение на втором устройстве — статус сменится в течение минуты.
3. Вставьте правила из урока и проверьте в Rules Playground, что пользователь A не может прочитать `messages` чата B и C. Ожидаемый результат: симулятор показывает «Denied».
4. Напишите тест для `ChatBloc` с фейковым репозиторием, у которого `watchMessages` возвращает `Stream.fromIterable([[], [message]])`. Ожидаемый результат: из начального `loading` Bloc выдаёт `success` с пустым списком, затем `success` с одним сообщением.

## Итоги

- Список чатов читается из денормализованного узла `userChats/{uid}` с последним сообщением.
- `update` с путями записывает данные в несколько мест атомарно.
- RTDB сортирует только по возрастанию: `limitToLast` + `reversed` на клиенте.
- Онлайн-статус — `.info/connected` + `onDisconnect()`, именно в таком порядке.
- Безопасность обеспечивают только правила на сервере; они не фильтруют данные.
- В Bloc поток подключается через `emit.forEach`, а Firebase спрятан за `ChatRepository`.
