"""Уведомление о новом отзыве в Telegram — если заданы токен бота и id чата."""
import json
import logging
import threading
import urllib.request
from html import escape

from django.conf import settings

logger = logging.getLogger(__name__)

ICONS = {'thanks': '💚', 'idea': '💡', 'problem': '🐞'}


def _text(feedback):
    lines = [f'{ICONS.get(feedback.kind, "✉️")} <b>{escape(feedback.get_kind_display())}</b>']
    if feedback.rating:
        lines[0] += ' ' + '★' * feedback.rating + '☆' * (5 - feedback.rating)
    lines.append('')
    lines.append(escape(feedback.message))
    who = ', '.join(escape(x) for x in (feedback.name, feedback.contact) if x)
    if who:
        lines.append(f'\n— {who}')
    if feedback.page:
        lines.append(f'Страница: {escape(feedback.page)}')
    return '\n'.join(lines)


def _send(token, chat_id, text):
    body = json.dumps({'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}).encode()
    request = urllib.request.Request(
        f'https://api.telegram.org/bot{token}/sendMessage', data=body,
        headers={'content-type': 'application/json'},
    )
    try:
        urllib.request.urlopen(request, timeout=10).close()
    except Exception:  # отзыв уже сохранён — уведомление не должно ломать страницу
        logger.exception('Не удалось отправить отзыв в Telegram')


def notify(feedback):
    token = settings.FEEDBACK_TELEGRAM_TOKEN
    chat_id = settings.FEEDBACK_TELEGRAM_CHAT_ID
    if not token or not chat_id:
        return
    # В фоне, чтобы пользователь не ждал ответа Telegram.
    threading.Thread(target=_send, args=(token, chat_id, _text(feedback)), daemon=True).start()
