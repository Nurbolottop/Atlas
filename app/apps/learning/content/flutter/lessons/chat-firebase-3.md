Firebase удобен, но во многих компаниях чат работает на собственном бэкенде, и мобильное приложение общается с ним через WebSocket. В этой части разберёмся, что такое сокеты, чем они отличаются от Firebase, подключимся через `web_socket_channel` и `socket_io_client`, научимся переподключаться при обрыве связи и сделаем две фичи любого мессенджера — индикатор «печатает…» и счётчик непрочитанных.

## Что такое WebSocket

Обычный HTTP-запрос (как в Dio) работает по схеме «спросил — получил ответ — разговор окончен». Чтобы узнать о новом сообщении, пришлось бы спрашивать сервер каждые пару секунд. Это называется **polling**, и это расточительно.

**WebSocket** — это постоянное двустороннее соединение. Один раз «позвонили» серверу и держим трубку: и клиент, и сервер могут что-то сказать в любой момент.

```text
HTTP:       клиент → запрос → сервер → ответ → соединение закрыто
WebSocket:  клиент ⇄ сервер (соединение открыто, сообщения идут в обе стороны)
```

Адреса начинаются с `ws://` (без шифрования, только для локальной разработки) или `wss://` (с шифрованием, как HTTPS).

## WebSocket или Firebase

| | Firebase Realtime Database | Свой сервер на WebSocket |
| --- | --- | --- |
| Сервер | Не нужен, всё готово | Нужно писать и поддерживать |
| Хранение истории | Встроено | Сервер сам сохраняет в БД |
| Офлайн-кэш | Встроен | Делаете сами |
| Переподключение | Автоматическое | Пишете сами |
| Гибкость логики | Ограничена правилами | Любая |
| Стоимость | Растёт с трафиком | Свои серверы |

Вывод: для MVP и учебных проектов Firebase быстрее. В компании с бэкенд-командой почти всегда будет свой сокет-сервер. Хорошая новость: если вы спрятали Firebase за `ChatRepository` (см. [вторую часть](lesson:chat-firebase-2)), смена транспорта затронет только data-слой.

## web_socket_channel: «чистый» WebSocket

```bash
flutter pub add web_socket_channel
```

```dart
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/status.dart' as status;

Future<void> main() async {
  final channel = WebSocketChannel.connect(
    Uri.parse('wss://chat.example.com/ws?token=YOUR_TOKEN'),
  );
  await channel.ready; // ждём, пока соединение установится

  channel.stream.listen(
    (raw) {
      final data = jsonDecode(raw as String) as Map<String, dynamic>;
      print('Пришло: ${data['type']}');
    },
    onError: (Object e) => print('Ошибка: $e'),
    onDone: () => print('Соединение закрыто: ${channel.closeCode}'),
  );

  channel.sink.add(jsonEncode({
    'type': 'message',
    'chatId': 'chat_1',
    'text': 'Привет!',
  }));

  // при выходе с экрана:
  await channel.sink.close(status.normalClosure);
}
```

- `WebSocketChannel.connect` — открывает соединение. Работает на Android, iOS и в вебе.
- `channel.ready` — `Future`, который завершится при успешном подключении или выбросит ошибку.
- `channel.stream` — входящие сообщения (это обычный `Stream`, всё из [первой части](lesson:chat-firebase-1) работает и здесь).
- `channel.sink.add` — отправка. WebSocket передаёт строки или байты, поэтому JSON кодируем через `jsonEncode`.
- Поле `type` — договорённость с бэкендом: по нему понятно, что пришло (`message`, `typing`, `read`).

<aside class="callout" data-icon="🔐" markdown="1">

Токен в `?token=` в адресе — частая, но не лучшая практика: адреса попадают в логи серверов. Если бэкенд поддерживает, передавайте токен заголовком (`IOWebSocketChannel.connect(uri, headers: {'Authorization': 'Bearer ...'})` на мобильных) или первым сообщением после подключения.

</aside>

## socket.io: протокол с удобствами

Многие бэкенды на Node.js используют **Socket.IO** — это надстройка над WebSocket со своим протоколом: именованные события, «комнаты» и встроенное переподключение. Важно: обычный `web_socket_channel` к серверу Socket.IO **не подключится**, нужен пакет [socket_io_client](https://pub.dev/packages/socket_io_client), версия которого совпадает с версией сервера (смотрите таблицу совместимости на pub.dev).

```bash
flutter pub add socket_io_client
```

```dart
import 'package:socket_io_client/socket_io_client.dart' as io;

final socket = io.io(
  'https://chat.example.com',
  io.OptionBuilder()
      .setTransports(['websocket'])        // сразу WebSocket, без long-polling
      .setAuth({'token': 'YOUR_TOKEN'})    // данные для авторизации
      .disableAutoConnect()
      .enableReconnection()
      .build(),
);

void connect() {
  socket.onConnect((_) {
    print('Подключились');
    socket.emit('join', {'chatId': 'chat_1'}); // войти в «комнату» чата
  });
  socket.on('message', (data) => print('Новое сообщение: $data'));
  socket.onDisconnect((_) => print('Отключились'));
  socket.connect();
}

void send(String text) {
  socket.emit('message', {'chatId': 'chat_1', 'text': text});
}

void dispose() => socket.dispose();
```

- `on('событие', ...)` — подписка на событие, `emit('событие', данные)` — отправка.
- `join` — типичное событие «войти в комнату»: сервер будет рассылать сообщения этого чата только участникам. Название события придумывает бэкенд.
- `dispose()` — закрывает соединение и снимает все обработчики.

## Переподключение

Мобильный интернет постоянно рвётся: лифт, метро, смена Wi-Fi на 4G. Socket.IO переподключается сам, а с «чистым» WebSocket это ваша задача. Правильный подход — **экспоненциальная задержка** (exponential backoff): после каждой неудачи ждём всё дольше — 1, 2, 4, 8… секунд, но не больше предела. Так тысячи клиентов не «положат» сервер одновременными попытками.

```dart
import 'dart:async';
import 'dart:math';
import 'package:web_socket_channel/web_socket_channel.dart';

class ReconnectingSocket {
  ReconnectingSocket(this.uri);
  final Uri uri;

  final _incoming = StreamController<String>.broadcast();
  Stream<String> get messages => _incoming.stream;

  WebSocketChannel? _channel;
  Timer? _retryTimer;
  int _attempt = 0;
  bool _closedByUser = false;

  Future<void> connect() async {
    _closedByUser = false;
    try {
      final channel = WebSocketChannel.connect(uri);
      await channel.ready;
      _channel = channel;
      _attempt = 0; // успешно — сбрасываем счётчик
      channel.stream.listen(
        (data) => _incoming.add(data as String),
        onDone: _scheduleReconnect,
        onError: (_) => _scheduleReconnect(),
      );
    } catch (_) {
      _scheduleReconnect();
    }
  }

  void _scheduleReconnect() {
    if (_closedByUser) return;
    _retryTimer?.cancel();
    final seconds = min(30, pow(2, _attempt).toInt()); // 1, 2, 4 ... 30
    _attempt++;
    _retryTimer = Timer(Duration(seconds: seconds), connect);
  }

  void send(String data) => _channel?.sink.add(data);

  Future<void> close() async {
    _closedByUser = true;
    _retryTimer?.cancel();
    await _channel?.sink.close();
    await _incoming.close();
  }
}
```

Разбор:

- Наружу отдаём **один** поток `messages`, который не прерывается при переподключении. Bloc подписывается на него один раз.
- `onDone` срабатывает, когда сервер закрыл соединение, `onError` — при ошибке сети. В обоих случаях планируем новую попытку.
- `_closedByUser` отличает «пропала сеть» от «пользователь ушёл с экрана» — во втором случае переподключаться не надо.
- После переподключения сообщения, пришедшие во время обрыва, потеряны. Обычно клиент запрашивает у сервера историю «после последнего известного id» через REST — договоритесь об этом с бэкендом.

<aside class="callout" data-icon="💡" markdown="1">

Пакет `connectivity_plus` сообщает, когда появилась сеть. Если по этому событию сбрасывать задержку и переподключаться сразу, чат «оживает» быстрее. Но помните: «есть Wi-Fi» ещё не значит «есть интернет», так что backoff всё равно нужен.

</aside>

## Индикатор «печатает…»

Идея простая: пока пользователь набирает текст, отправляем событие `typing`, а собеседник показывает надпись. Сложность — не завалить сервер событием на каждую букву. Решение — отправить `typing: true` один раз при начале набора и `typing: false` через пару секунд тишины.

```dart
class TypingNotifier {
  TypingNotifier(this._send);
  final void Function(bool isTyping) _send;

  Timer? _stopTimer;
  bool _isTyping = false;

  void onTextChanged(String text) {
    if (!_isTyping && text.isNotEmpty) {
      _isTyping = true;
      _send(true); // начали печатать — сообщаем один раз
    }
    _stopTimer?.cancel();
    _stopTimer = Timer(const Duration(seconds: 2), stop); // 2 с тишины — стоп
  }

  void stop() {
    _stopTimer?.cancel();
    if (_isTyping) {
      _isTyping = false;
      _send(false);
    }
  }
}
```

Подключение к полю ввода:

```dart
final typing = TypingNotifier(
  (isTyping) => socket.emit('typing', {'chatId': chatId, 'isTyping': isTyping}),
);

TextField(
  controller: _controller,
  onChanged: typing.onTextChanged,
);
// после отправки сообщения и в dispose(): typing.stop();
```

На стороне собеседника слушаем событие и держим флаг в состоянии Bloc. Защитимся от «вечного печатает» на случай, если `false` потерялось: сбрасываем флаг по таймеру.

```dart
socket.on('typing', (data) {
  final map = data as Map<String, dynamic>;
  if (map['userId'] == myUid) return;
  bloc.add(PeerTypingChanged(map['isTyping'] as bool));
});
// В Bloc: при isTyping == true запускаем Timer на 5 секунд,
// который сам добавит PeerTypingChanged(false).
```

С Firebase то же делается узлом `typing/{chatId}/{uid}: true` и `onDisconnect().remove()`, чтобы флаг исчез, если приложение закрылось на полуслове.

## Непрочитанные сообщения

Есть два популярных способа.

**1. Счётчик.** У каждого участника в карточке чата хранится число `unread`. При отправке сервер (или клиент) увеличивает счётчик собеседника, при открытии чата — обнуляет свой. В Firebase для этого есть атомарный `ServerValue.increment`:

```dart
await FirebaseDatabase.instance.ref().update({
  'messages/$chatId/$messageId': messageMap,
  'userChats/$peerId/$chatId/lastMessage': text,
  'userChats/$peerId/$chatId/unread': ServerValue.increment(1),
});

// Когда пользователь открыл чат:
await FirebaseDatabase.instance.ref('userChats/$myUid/$chatId/unread').set(0);
```

`increment` выполняется на сервере, поэтому два сообщения, отправленные одновременно, не «перетрут» друг друга.

**2. Отметка «прочитано до».** Храним `lastReadAt` — время последнего прочитанного сообщения. Непрочитанные — те, у которых `createdAt > lastReadAt`. Этот способ ещё и даёт галочки «прочитано» у отправителя: если `lastReadAt` собеседника больше времени сообщения — рисуем две галочки.

```dart
int countUnread(List<Message> messages, DateTime lastReadAt, String myUid) {
  return messages
      .where((m) => !m.isMine(myUid) && m.createdAt.isAfter(lastReadAt))
      .length;
}
```

В сокет-чате обычно отправляют событие `read` с id последнего прочитанного сообщения, а сервер пересчитывает счётчики и рассылает их участникам.

<aside class="callout" data-icon="📌" markdown="1">

Обнулять непрочитанные нужно, когда пользователь действительно видит чат: при открытии экрана и при новых сообщениях, пока экран открыт и приложение на переднем плане. Если приложение в фоне — сообщение остаётся непрочитанным, а пользователь получает push.

</aside>

## Типичные ошибки

- **Подключение к Socket.IO через `web_socket_channel`** — протоколы разные, нужен `socket_io_client`.
- **Переподключение без задержки** в бесконечном цикле — сажает батарею и перегружает сервер.
- **Соединение не закрыто в `dispose`** — после выхода с экрана сокет живёт и получает данные.
- **Событие `typing` на каждую букву** — используйте таймер, как в `TypingNotifier`.
- **`ws://` в релизе** — трафик не зашифрован и его можно подслушать, а политики платформ (App Transport Security на iOS, запрет cleartext-трафика на Android) могут такие соединения блокировать; используйте `wss://`.

## Практика

1. Подключитесь через `web_socket_channel` к любому публичному echo-серверу (или поднимите локальный) и выведите ответы в `ListView`. Ожидаемый результат: отправленный текст возвращается и появляется в списке.
2. Добавьте `TypingNotifier` в чат на Firebase через узел `typing/{chatId}/{uid}`. Ожидаемый результат: на втором устройстве под именем собеседника появляется «печатает…» и исчезает через 2 секунды после остановки.
3. Реализуйте счётчик `unread` через `ServerValue.increment` и покажите бейдж на экране списка чатов. Ожидаемый результат: бейдж растёт с каждым сообщением и обнуляется при открытии чата.
4. Напишите `SocketChatRepository implements ChatRepository` на основе `ReconnectingSocket`. Ожидаемый результат: заменив регистрацию в GetIt, вы переключаете чат с Firebase на сокеты без изменений в Bloc и экранах.

## Итоги

- WebSocket — постоянное двустороннее соединение; это эффективнее, чем опрашивать сервер по HTTP.
- Firebase даёт готовые хранение, офлайн и переподключение; свой сокет-сервер — гибкость и контроль.
- `web_socket_channel` — для «чистого» WebSocket, `socket_io_client` — для серверов Socket.IO.
- Переподключение — экспоненциальная задержка с пределом и один непрерывный поток наружу.
- «Печатает…» отправляют при начале набора и выключают по таймеру тишины.
- Непрочитанные считают счётчиком с `ServerValue.increment` или через отметку `lastReadAt`.
