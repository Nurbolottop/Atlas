from urllib.parse import quote

from django.core.cache import cache
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import FeedbackForm
from .models import Feedback
from .notify import notify

RATE_LIMIT = 5  # отзывов в час с одного адреса


def _back_url(request, value):
    """Страница, с которой пришли, — только адреса этого сайта."""
    if value and url_has_allowed_host_and_scheme(value, allowed_hosts={request.get_host()}) and value.startswith('/'):
        return value[:300]
    return ''


def feedback(request):
    back = _back_url(request, request.POST.get('from') or request.GET.get('from'))
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        ip = request.META.get('HTTP_X_REAL_IP') or request.META.get('REMOTE_ADDR', '')
        key = f'feedback:{ip}'
        if cache.get(key, 0) >= RATE_LIMIT:
            form.add_error(None, 'Вы отправили много отзывов подряд. Попробуйте чуть позже.')
        elif form.is_valid():
            if not form.is_spam:
                item = form.save(commit=False)
                item.page = back
                item.save()
                notify(item)
                cache.set(key, cache.get(key, 0) + 1, 3600)
            request.session['feedback_kind'] = form.cleaned_data['kind']
            return redirect(reverse('feedback_thanks') + (f'?from={quote(back)}' if back else ''))
    else:
        kind = request.GET.get('kind')
        form = FeedbackForm(initial={'kind': kind if kind in Feedback.Kind.values else Feedback.Kind.THANKS})
    return render(request, 'contacts/feedback.html', {'form': form, 'back': back})


def feedback_thanks(request):
    return render(request, 'contacts/feedback_thanks.html', {
        'kind': request.session.pop('feedback_kind', 'thanks'),
        'back': _back_url(request, request.GET.get('from')),
    })
