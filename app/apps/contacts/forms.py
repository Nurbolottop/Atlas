from django import forms

from .models import Feedback


class FeedbackForm(forms.ModelForm):
    # Ловушка для ботов: поле скрыто от людей, спам-боты заполняют его.
    website = forms.CharField(required=False)

    class Meta:
        model = Feedback
        fields = ['kind', 'rating', 'message', 'name', 'contact']
        error_messages = {
            'message': {'required': 'Напишите пару слов — без текста отзыв не отправить.'},
        }

    def clean_message(self):
        message = self.cleaned_data['message'].strip()
        if len(message) < 3:
            raise forms.ValidationError('Слишком коротко — напишите хотя бы пару слов.')
        return message

    @property
    def is_spam(self):
        return bool(self.cleaned_data.get('website'))
