Чат — одна из самых популярных задач на собеседованиях и в реальных проектах: в нём сразу видно, умеет ли разработчик работать с данными, которые меняются «вживую». В этой части разберёмся, что такое `Stream` и как его показывать через `StreamBuilder`, подключим Firebase Realtime Database, спроектируем структуру данных чата и научимся отправлять и читать сообщения.

## Что такое Stream

Вы уже знаете `Future` — это **одно** значение, которое придёт в будущем: ответ сервера, прочитанный файл. `Stream` — это **поток** значений, которые приходят по очереди, сколько угодно раз.

Бытовая аналогия: `Future` — это посылка, которую вы ждёте один раз. `Stream` — это подписка на журнал: номера приходят каждую неделю, пока вы не отпишетесь.

| | `Future<T>` | `Stream<T>` |
| --- | --- | --- |
| Сколько значений | Одно (или ошибка) | Много, по очереди |
| Как получить | `await future` | `await for` или `.listen()` |
| Виджет | `FutureBuilder` | `StreamBuilder` |

### Создаём свой Stream

Самый простой способ — функция с `async*`. Звёздочка означает «эта функция возвращает поток», а `yield` — «отдай очередное значение»:

```dart
Stream<int> countdown(int from) async* {
  for (var i = from; i >= 0; i--) {
    await Future.delayed(const Duration(seconds: 1));
    yield i; // отдаём значение подписчику
  }
}

Future<void> main() async {
  await for (final value in countdown(3)) {
    print(value); // 3, 2, 1, 0 — по одному в секунду
  }
  print('Готово');
}
```

- `async*` — функция-генератор потока.
- `yield i` — отправляет число в поток и продолжает работу.
- `await for` — цикл, который ждёт каждое новое значение. Закончится, когда поток закроется.

### StreamController и подписка

Когда значения приходят «снаружи» (нажатия, сообщения из сети), используют `StreamController` — это «труба»: в один конец кладём данные (`sink`/`add`), из другого читаем (`stream`).

```dart
import 'dart:async';

void main() {
  final controller = StreamController<String>();

  final StreamSubscription<String> sub = controller.stream.listen(
    (text) => print('Новое сообщение: $text'),
    onError: (Object e) => print('Ошибка: $e'),
  );

  controller.add('Привет');
  controller.addError(Exception('Нет сети'));

  sub.cancel();
  controller.close();
}
```

`listen` возвращает `StreamSubscription` — «квитанцию о подписке». Через неё можно поставить поток на паузу (`pause`), продолжить (`resume`) и, главное, **отписаться** (`cancel`).

<aside class="callout" data-icon="⚠️" markdown="1">

Самая частая ошибка с потоками — забыть `cancel()`. Подписка живёт после закрытия экрана, тратит память и трафик, а `setState` в ней падает с «setState() called after dispose()». Отписывайтесь в `dispose()` или используйте `StreamBuilder` — он делает это сам.

</aside>

Обычный поток можно слушать только одному подписчику; если слушателей несколько, создают `StreamController.broadcast()`. Потоки Firebase можно слушать сколько угодно раз — каждый `listen` создаёт свою подписку.

## StreamBuilder: показываем поток на экране

`StreamBuilder` подписывается на поток, перерисовывает виджет при каждом новом значении и сам отписывается, когда виджет удаляется из дерева.

```dart
StreamBuilder<int>(
  stream: countdownStream, // поток создаём заранее, не в build!
  builder: (context, snapshot) {
    if (snapshot.hasError) {
      return Text('Ошибка: ${snapshot.error}');
    }
    if (snapshot.connectionState == ConnectionState.waiting) {
      return const CircularProgressIndicator();
    }
    return Text('Осталось: ${snapshot.data}');
  },
)
```

`snapshot` — это «снимок» потока в текущий момент:

| Поле | Что значит |
| --- | --- |
| `connectionState` | `waiting` — ждём первое значение, `active` — данные идут, `done` — поток закрыт |
| `hasData` / `data` | Есть ли последнее значение и само значение |
| `hasError` / `error` | Пришла ли ошибка |

<aside class="callout" data-icon="⚠️" markdown="1">

Не создавайте поток прямо в `stream:` внутри `build` (например, `stream: ref.onValue`). Каждая перерисовка создаст новую подписку, и экран будет мигать загрузкой. Создайте поток один раз в `initState` и сохраните в поле — или, как мы сделаем во второй части, держите подписку в Bloc.

</aside>

## Подключаем Firebase Realtime Database

**Realtime Database (RTDB)** — это облачная база данных Firebase, которая хранит всё как одно большое JSON-дерево и мгновенно присылает изменения всем подключённым клиентам. Свой сервер не нужен.

Firebase-проект у вас уже подключён после урока [Firebase: подключение и авторизация](lesson:firebase-auth). Осталось:

1. В [консоли Firebase](https://console.firebase.google.com) откройте **Build → Realtime Database → Create Database**, выберите регион и режим **locked mode** (правила напишем сами во второй части).
2. Добавьте пакет и обновите конфигурацию, чтобы в `firebase_options.dart` появился `databaseURL`:

```bash
flutter pub add firebase_database
flutterfire configure
```

Инициализация `Firebase.initializeApp(...)` в `main` остаётся прежней.

## Структура данных чата

В RTDB всё — одно JSON-дерево. Главное правило: **держите дерево плоским**. Когда вы читаете узел, Firebase скачивает его целиком со всеми вложенными данными. Если положить сообщения внутрь чата, то для списка чатов придётся скачать все сообщения всех чатов.

Поэтому сообщения не кладут внутрь чата, а выносят в отдельную ветку:

```json
{
  "users": {
    "uid_aibek": { "name": "Айбек", "online": true, "lastSeen": 1760000000000 }
  },
  "chats": {
    "chat_1": {
      "members": { "uid_aibek": true, "uid_mira": true },
      "lastMessage": "Привет",
      "updatedAt": 1760000000000
    }
  },
  "messages": {
    "chat_1": {
      "-NxA1b2": {
        "senderId": "uid_aibek",
        "text": "Привет",
        "createdAt": 1760000000000
      }
    }
  },
  "userChats": {
    "uid_aibek": { "chat_1": true },
    "uid_mira": { "chat_1": true }
  }
}
```

- `users` — профили и онлайн-статус.
- `chats` — «шапка» чата: участники и последнее сообщение для списка.
- `messages/{chatId}` — сами сообщения, читаем только когда открыли чат.
- `userChats/{uid}` — какие чаты есть у пользователя. Это **денормализация** — сознательное дублирование данных, чтобы быстро читать. В NoSQL это нормально.

Для личного чата удобно делать предсказуемый `chatId` из двух uid — тогда двое пользователей всегда попадут в один и тот же чат:

```dart
String buildChatId(String uid1, String uid2) {
  final ids = [uid1, uid2]..sort(); // сортируем, чтобы порядок не влиял
  return '${ids[0]}_${ids[1]}';
}
```

## Модель сообщения

Данные из RTDB приходят как `Map<Object?, Object?>`, поэтому модель создаётся из такой `Map`:

```dart
import 'package:equatable/equatable.dart';

class Message extends Equatable {
  const Message({
    required this.id,
    required this.senderId,
    required this.text,
    required this.createdAt,
  });

  final String id;
  final String senderId;
  final String text;
  final DateTime createdAt;

  factory Message.fromMap(String id, Map<Object?, Object?> map) {
    return Message(
      id: id,
      senderId: map['senderId'] as String? ?? '',
      text: map['text'] as String? ?? '',
      createdAt: DateTime.fromMillisecondsSinceEpoch(
        (map['createdAt'] as num?)?.toInt() ?? 0,
      ),
    );
  }

  bool isMine(String myUid) => senderId == myUid;

  @override
  List<Object?> get props => [id, senderId, text, createdAt];
}
```

Разбор:

- `id` не хранится внутри сообщения — это **ключ** узла (`-NxA1b2`), поэтому передаём его отдельно.
- `as String? ?? ''` — защита от отсутствующих полей.
- `createdAt` хранится как число миллисекунд (так Firebase хранит время), а в модели — удобный `DateTime`.
- `Equatable` — чтобы Bloc и `StreamBuilder` могли сравнивать сообщения (вы знаете его по уроку [про модели и JSON](lesson:json-modeli-dio-get)).

## Отправка сообщения

Ссылка на узел базы — `DatabaseReference`. Метод `push()` создаёт дочерний узел с уникальным ключом, который ещё и сортируется по времени создания:

```dart
import 'package:firebase_database/firebase_database.dart';

final _db = FirebaseDatabase.instance;

Future<void> sendMessage({
  required String chatId,
  required String senderId,
  required String text,
}) async {
  final trimmed = text.trim();
  if (trimmed.isEmpty) return; // пустые сообщения не шлём

  final newRef = _db.ref('messages/$chatId').push();
  await newRef.set({
    'senderId': senderId,
    'text': trimmed,
    'createdAt': ServerValue.timestamp,
  });
}
```

- `_db.ref('messages/$chatId')` — путь в дереве, как адрес папки.
- `push()` — генерирует ключ локально, `set(...)` — записывает данные в узел.
- `ServerValue.timestamp` — специальный маркер: сервер сам подставит своё текущее время. Часы на телефонах пользователей могут отличаться, и если брать `DateTime.now()`, сообщения перемешаются.

## Чтение сообщений в реальном времени

У `DatabaseReference` и запросов (`Query`) есть потоки. Главные: `onValue` — сразу и при любом изменении присылает **весь** узел; `onChildAdded`, `onChildChanged`, `onChildRemoved` — сообщают о каждом добавленном, изменённом или удалённом дочернем узле. Для начала возьмём `onValue` — он проще: всегда отдаёт актуальный список целиком.

```dart
Stream<List<Message>> watchMessages(String chatId) {
  final query = FirebaseDatabase.instance
      .ref('messages/$chatId')
      .orderByChild('createdAt')
      .limitToLast(50);

  return query.onValue.map((DatabaseEvent event) {
    return event.snapshot.children.map((child) {
      return Message.fromMap(
        child.key!,
        child.value as Map<Object?, Object?>,
      );
    }).toList();
  });
}
```

- `orderByChild('createdAt')` — сортируем по времени (по возрастанию).
- `limitToLast(50)` — берём только 50 последних, а не всю историю.
- `onValue.map(...)` — превращаем «сырое» событие базы в `List<Message>`.
- `snapshot.children` — дочерние узлы **в порядке запроса**. Не используйте `(snapshot.value as Map).values` — у `Map` порядок не гарантирован.

## Собираем экран чата

```dart
class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key, required this.chatId, required this.myUid});
  final String chatId;
  final String myUid;

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  late final Stream<List<Message>> _messages;
  final _controller = TextEditingController();

  @override
  void initState() {
    super.initState();
    _messages = watchMessages(widget.chatId); // поток создаём один раз
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final text = _controller.text;
    _controller.clear();
    await sendMessage(chatId: widget.chatId, senderId: widget.myUid, text: text);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Чат')),
      body: Column(
        children: [
          Expanded(
            child: StreamBuilder<List<Message>>(
              stream: _messages,
              builder: (context, snapshot) {
                if (snapshot.hasError) {
                  return Center(child: Text('Ошибка: ${snapshot.error}'));
                }
                if (!snapshot.hasData) {
                  return const Center(child: CircularProgressIndicator());
                }
                final messages = snapshot.data!.reversed.toList();
                return ListView.builder(
                  reverse: true, // новые сообщения снизу
                  itemCount: messages.length,
                  itemBuilder: (context, i) {
                    final m = messages[i];
                    final mine = m.isMine(widget.myUid);
                    return Align( // свои — справа, чужие — слева
                      alignment: mine ? Alignment.centerRight : Alignment.centerLeft,
                      child: Card(
                        color: mine ? Colors.blue.shade100 : null,
                        child: Padding(
                          padding: const EdgeInsets.all(10),
                          child: Text(m.text),
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          ),
          SafeArea(
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: const InputDecoration(hintText: 'Сообщение'),
                    onSubmitted: (_) => _send(),
                  ),
                ),
                IconButton(icon: const Icon(Icons.send), onPressed: _send),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
```

Ключевые моменты:

- Поток создаётся в `initState`, а не в `build`.
- `ListView` с `reverse: true` «прилипает» к низу, как в любом мессенджере, поэтому список тоже переворачиваем: самое новое сообщение — первым элементом.
- Поле очищаем **до** отправки: Firebase сначала показывает запись локально, поэтому сообщение появится мгновенно даже при медленной сети.

## Типичные ошибки

- **Permission denied** при чтении/записи — база создана в locked mode, а правила ещё не настроены. Для первой проверки можно временно разрешить доступ только авторизованным (`"auth != null"`), подробно — во второй части.
- **`databaseURL` не найден** — забыли заново выполнить `flutterfire configure` после создания базы.
- **Экран мигает загрузкой** — поток создаётся внутри `build`.
- **Вложенная структура** — сообщения внутри `chats`, и список чатов грузится долго.

## Практика

1. Напишите функцию `Stream<String> clock()` на `async*`, которая каждую секунду отдаёт текущее время в формате `HH:mm:ss`, и покажите её через `StreamBuilder`. Ожидаемый результат: часы на экране тикают.
2. Создайте в консоли Firebase базу, вручную добавьте узел `messages/test_chat` с двумя сообщениями и выведите их на экран через `watchMessages`. Ожидаемый результат: измените текст в консоли — он сразу поменяется в приложении.
3. Соберите `ChatScreen` и откройте его на двух эмуляторах (или эмуляторе и телефоне) с разными пользователями. Ожидаемый результат: сообщение с одного устройства появляется на другом за секунду.
4. Под каждым сообщением выведите время отправки в формате `14:05`. Ожидаемый результат: время берётся из `createdAt`, а не из `DateTime.now()`.

## Итоги

- `Future` — одно значение, `Stream` — поток значений; для чата нужен `Stream`.
- От потока важно отписываться; `StreamBuilder` делает это сам, но поток для него создают один раз.
- Realtime Database — JSON-дерево, которое мгновенно синхронизируется между клиентами.
- Структура чата должна быть плоской: `users`, `chats`, `messages/{chatId}`, `userChats/{uid}`.
- `push()` + `set()` отправляют сообщение, `ServerValue.timestamp` ставит единое серверное время.
- `orderByChild` + `limitToLast` + `onValue` дают живой список последних сообщений.
