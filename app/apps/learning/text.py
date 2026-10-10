import re

_TRANSLIT = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e', 'ж': 'zh', 'з': 'z',
    'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
    'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
}


def slugify(text, max_length=60):
    """Латинский slug из русского или английского заголовка."""
    text = ''.join(_TRANSLIT.get(ch, ch) for ch in text.lower())
    text = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
    if len(text) > max_length:
        text = text[:max_length].rsplit('-', 1)[0]
    return text


def normalize(text):
    """Приводит текст к виду для поиска: нижний регистр, ё → е."""
    return ' '.join(str(text).lower().replace('ё', 'е').split())


def plural(n, forms):
    """plural(3, ('урок', 'урока', 'уроков')) -> 'урока'."""
    n = abs(n) % 100
    if 10 < n < 20:
        return forms[2]
    n %= 10
    if n == 1:
        return forms[0]
    if 2 <= n <= 4:
        return forms[1]
    return forms[2]
