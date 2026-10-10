Аватарки, фото товаров, фон с видом города — почти все картинки в приложении приходят из интернета. Загрузка может занять время, сеть может пропасть, а ссылка — оказаться битой. В этом уроке разберём, как показывать изображения из сети через `Image.network` и `NetworkImage`, как сделать красивый индикатор загрузки и запасной вариант при ошибке, и как кэшировать картинки на диске пакетом `cached_network_image`, чтобы они не скачивались каждый раз заново.

## Image.network: самый простой способ

```dart
Image.network(
  'https://picsum.photos/id/1018/800/400',
  width: double.infinity,
  height: 200,
  fit: BoxFit.cover,
)
```

Разбор:

- Первый аргумент — адрес картинки (URL).
- `width` и `height` задают размер области. Без них картинка займёт свой «родной» размер, и вёрстка будет «прыгать», когда она загрузится.
- `fit` — как вписать картинку в область:

| `BoxFit` | Что делает |
| --- | --- |
| `cover` | Заполняет всю область, лишнее обрезает. Идеально для фона и карточек |
| `contain` | Помещается целиком, могут остаться пустые поля |
| `fill` | Растягивает, искажая пропорции |
| `fitWidth` / `fitHeight` | Подгоняет по ширине или высоте |

<aside class="callout" data-icon="📌" markdown="1">

Всегда задавайте картинке размер — явно или через родителя (`SizedBox`, `AspectRatio`). Иначе при загрузке весь список «подпрыгивает», и пользователь промахивается по кнопкам.

</aside>

## NetworkImage: поставщик картинки

`Image.network` — это виджет. А **`NetworkImage`** — это `ImageProvider`, «поставщик» картинки: он знает, *откуда* взять изображение, но сам ничего не рисует. Аналогия: `NetworkImage` — служба доставки, `Image` — рамка на стене, куда доставленное вешают.

Поставщик нужен там, где виджет ожидает не виджет, а именно источник картинки:

```dart
// Аватарка
CircleAvatar(
  radius: 32,
  backgroundImage: const NetworkImage('https://i.pravatar.cc/150?img=3'),
  onBackgroundImageError: (error, stackTrace) => debugPrint('Аватар не загрузился'),
)

// Фон контейнера
Container(
  height: 180,
  decoration: BoxDecoration(
    borderRadius: BorderRadius.circular(16),
    image: const DecorationImage(
      image: NetworkImage('https://picsum.photos/id/1036/800/400'),
      fit: BoxFit.cover,
    ),
  ),
)

// Обычный Image с поставщиком — то же самое, что Image.network
const Image(image: NetworkImage('https://picsum.photos/200'))
```

На самом деле `Image.network(url)` внутри просто создаёт `Image(image: NetworkImage(url))`.

## loadingBuilder: что показать во время загрузки

Пока картинка грузится, по умолчанию на её месте пусто. `loadingBuilder` позволяет показать индикатор, причём с настоящим прогрессом:

```dart
Image.network(
  'https://picsum.photos/id/1015/1200/800',
  height: 220,
  width: double.infinity,
  fit: BoxFit.cover,
  loadingBuilder: (context, child, loadingProgress) {
    if (loadingProgress == null) return child; // загрузка завершена
    final total = loadingProgress.expectedTotalBytes;
    final loaded = loadingProgress.cumulativeBytesLoaded;
    return SizedBox(
      height: 220,
      child: Center(
        child: CircularProgressIndicator(value: total != null ? loaded / total : null),
      ),
    );
  },
)
```

Разбор по параметрам `loadingBuilder`:

1. `child` — сама картинка. Когда загрузка закончилась, возвращаем её.
2. `loadingProgress` — объект `ImageChunkEvent` с информацией о загрузке, или `null`, если всё загружено.
3. `cumulativeBytesLoaded` — сколько байт уже скачано.
4. `expectedTotalBytes` — сколько всего. Может быть `null`, если сервер не сообщил размер, — тогда показываем «бесконечный» индикатор (`value: null`).

<aside class="callout" data-icon="⚠️" markdown="1">

Частая ошибка — забыть строку `if (loadingProgress == null) return child;`. Тогда индикатор будет крутиться вечно, даже когда картинка уже загружена.

</aside>

## errorBuilder: если картинка не загрузилась

Без обработки ошибки битая ссылка или отсутствие интернета покажут в debug-режиме красный блок с текстом исключения, а в консоли появится длинная ошибка. `errorBuilder` заменяет это аккуратной заглушкой:

```dart
Image.network(
  'https://example.com/broken.jpg',
  height: 220,
  width: double.infinity,
  fit: BoxFit.cover,
  errorBuilder: (context, error, stackTrace) {
    return Container(
      height: 220,
      color: Theme.of(context).colorScheme.surfaceContainerHighest,
      alignment: Alignment.center,
      child: const Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.broken_image_outlined, size: 48),
          SizedBox(height: 8),
          Text('Не удалось загрузить фото'),
        ],
      ),
    );
  },
)
```

- `error` — что случилось (404, нет сети, файл не является картинкой).
- `stackTrace` — стек вызовов, пригодится для логирования.
- Цвет заглушки берём из темы, чтобы она хорошо смотрелась и в тёмном режиме (см. урок [про темы](lesson:blocprovider-temy-weatherapp)).

### frameBuilder: плавное появление

`frameBuilder` вызывается, когда готов первый кадр. С его помощью картинка может появляться плавно, а не «выпрыгивать»:

```dart
Image.network(
  url,
  fit: BoxFit.cover,
  frameBuilder: (context, child, frame, wasSynchronouslyLoaded) {
    if (wasSynchronouslyLoaded) return child; // уже была в кэше — без анимации
    return AnimatedOpacity(
      opacity: frame == null ? 0 : 1,
      duration: const Duration(milliseconds: 300),
      child: child,
    );
  },
)
```

`frame == null` — первый кадр ещё не готов, картинка прозрачная. Как только кадр появился — прозрачность плавно меняется до 1.

## Переиспользуемый виджет

Чтобы не копировать три билдера по всему проекту, соберём свой виджет:

```dart
class AppNetworkImage extends StatelessWidget {
  const AppNetworkImage(this.url, {super.key, this.height = 200, this.radius = 12});

  final String url;
  final double height;
  final double radius;

  @override
  Widget build(BuildContext context) {
    final placeholderColor = Theme.of(context).colorScheme.surfaceContainerHighest;
    return ClipRRect(
      borderRadius: BorderRadius.circular(radius),
      child: Image.network(
        url,
        height: height,
        width: double.infinity,
        fit: BoxFit.cover,
        loadingBuilder: (context, child, progress) => progress == null
            ? child
            : Container(
                height: height,
                color: placeholderColor,
                alignment: Alignment.center,
                child: const CircularProgressIndicator(),
              ),
        errorBuilder: (context, error, stackTrace) => Container(
          height: height,
          color: placeholderColor,
          alignment: Alignment.center,
          child: const Icon(Icons.image_not_supported_outlined),
        ),
      ),
    );
  }
}
```

`ClipRRect` обрезает углы картинки по радиусу — так фото выглядят аккуратнее в карточках.

## Кэширование

### Что такое кэш

**Кэш** — сохранённая копия данных, чтобы не загружать их повторно. Как блокнот у вас в кармане: проще посмотреть номер в нём, чем каждый раз звонить в справочную.

У Flutter есть встроенный кэш **в памяти** (`ImageCache`): если та же картинка уже показывалась и не была вытеснена, она берётся мгновенно. Но этот кэш живёт только пока работает приложение. После перезапуска все картинки скачиваются заново — это трафик пользователя и время.

### cached_network_image: кэш на диске

```bash
flutter pub add cached_network_image
```

Пакет сохраняет скачанные картинки в файлы на устройстве. При следующем показе — даже после перезапуска — они берутся с диска.

```dart
import 'package:cached_network_image/cached_network_image.dart';

CachedNetworkImage(
  imageUrl: 'https://picsum.photos/id/1043/800/400',
  height: 200,
  width: double.infinity,
  fit: BoxFit.cover,
  placeholder: (context, url) => const Center(child: CircularProgressIndicator()),
  errorWidget: (context, url, error) => const Icon(Icons.error_outline),
  fadeInDuration: const Duration(milliseconds: 300),
)
```

Сравните с `Image.network`:

| `Image.network` | `CachedNetworkImage` |
| --- | --- |
| `url` первым аргументом | `imageUrl:` |
| `loadingBuilder` | `placeholder` или `progressIndicatorBuilder` |
| `errorBuilder` | `errorWidget` |
| `frameBuilder` для анимации | `fadeInDuration` уже встроен |
| Кэш только в памяти | Кэш в памяти и на диске |

Если нужен процент загрузки — вместо `placeholder` используйте `progressIndicatorBuilder`:

```dart
CachedNetworkImage(
  imageUrl: url,
  progressIndicatorBuilder: (context, url, progress) =>
      Center(child: CircularProgressIndicator(value: progress.progress)),
  errorWidget: (context, url, error) => const Icon(Icons.error_outline),
)
```

<aside class="callout" data-icon="⚠️" markdown="1">

`placeholder` и `progressIndicatorBuilder` нельзя указывать одновременно — пакет выбросит ошибку. Выберите что-то одно.

</aside>

### CachedNetworkImageProvider

Для `CircleAvatar` и `DecorationImage` есть кэширующий поставщик — замена `NetworkImage`:

```dart
CircleAvatar(
  radius: 32,
  backgroundImage: CachedNetworkImageProvider(user.avatarUrl),
)
```

### Экономим память

Фото с сервера часто огромные (4000×3000 пикселей), а показываем мы их размером 100×100. Декодированная картинка занимает память по своему **реальному** размеру. Попросите Flutter уменьшить её при декодировании:

```dart
Image.network(url, cacheWidth: 300);              // встроенный Image
CachedNetworkImage(imageUrl: url, memCacheWidth: 300); // cached_network_image
```

Хорошая практика — запрашивать у сервера уже уменьшенные версии (многие API принимают размер в URL, как `picsum.photos/300/200`).

### Предзагрузка и очистка

```dart
// заранее скачать картинку следующего экрана
await precacheImage(const NetworkImage('https://picsum.photos/id/1050/800/400'), context);

// удалить одну картинку из кэша, например после смены аватара
await CachedNetworkImage.evictFromCache(user.avatarUrl);
```

## Картинки в WeatherApp

В погодном приложении удобно показывать фон по городу и аватар пользователя из Firebase Auth (`user.photoURL`, если он вошёл через Google):

```dart
Stack(
  children: [
    CachedNetworkImage(
      imageUrl: 'https://picsum.photos/seed/${Uri.encodeComponent(city)}/800/400',
      height: 220,
      width: double.infinity,
      fit: BoxFit.cover,
      errorWidget: (context, url, error) =>
          Container(height: 220, color: Theme.of(context).colorScheme.primaryContainer),
    ),
    Positioned(
      left: 16,
      bottom: 16,
      child: Text(city, style: Theme.of(context).textTheme.headlineMedium),
    ),
  ],
)
```

`seed/<город>` у picsum.photos возвращает одну и ту же картинку для одного и того же слова — у каждого города будет «свой» фон. `Uri.encodeComponent` нужен, потому что в названии могут быть пробелы и кириллица.

## Типичные ошибки

- Нет размера у картинки — список «прыгает» при загрузке.
- Нет `errorBuilder` — красный блок ошибки в debug и пустота в релизе.
- В `loadingBuilder` не возвращают `child` при `null` — вечная загрузка.
- Используют `http://` вместо `https://` — Android и iOS по умолчанию блокируют незащищённые соединения.
- Огромные картинки в маленьких превью без `cacheWidth` — приложение тормозит и падает по памяти на слабых устройствах.

## Практика

1. **Галерея.** Сделайте `GridView` из 30 картинок `https://picsum.photos/id/<номер>/300/300` через `Image.network` с `loadingBuilder` и `errorBuilder`. Ожидаемый результат: при прокрутке видны индикаторы, а не пустые ячейки.
2. **Ошибка.** Добавьте в галерею несколько заведомо битых адресов. Ожидаемый результат: на их месте аккуратная иконка, без красных блоков.
3. **Профиль.** Сделайте шапку профиля с фоном через `DecorationImage(image: NetworkImage(...))` и круглым аватаром `CircleAvatar`. Ожидаемый результат: оба изображения корректно обрезаны и не искажены.
4. **Кэш на диске.** Переведите галерею на `CachedNetworkImage`, откройте её, затем включите авиарежим и перезапустите приложение. Ожидаемый результат: ранее просмотренные картинки показываются без интернета.
5. **WeatherApp.** Добавьте в карточку погоды фон города через `CachedNetworkImage` и плавное появление. Ожидаемый результат: при смене города фон меняется, а при повторном выборе того же города грузится мгновенно.

## Итоги

- `Image.network` — виджет для картинки из сети; `NetworkImage` — поставщик (`ImageProvider`) для `CircleAvatar`, `DecorationImage` и `Image`.
- Всегда задавайте размер и `fit`, чаще всего `BoxFit.cover`.
- `loadingBuilder` показывает загрузку (не забудьте `return child` при `null`), `errorBuilder` — заглушку при ошибке.
- Встроенный кэш Flutter живёт только в памяти; `cached_network_image` хранит картинки на диске.
- `CachedNetworkImage` использует `placeholder`/`progressIndicatorBuilder` и `errorWidget`, а для аватаров есть `CachedNetworkImageProvider`.
- `cacheWidth` / `memCacheWidth` экономят память на больших фото.
