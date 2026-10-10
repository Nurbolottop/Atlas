from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Feedback(models.Model):
    """Отзыв о платформе: благодарность, идея или сообщение о проблеме."""

    class Kind(models.TextChoices):
        THANKS = 'thanks', 'Спасибо'
        IDEA = 'idea', 'Идея'
        PROBLEM = 'problem', 'Проблема'

    kind = models.CharField('Тип', max_length=10, choices=Kind.choices, default=Kind.THANKS)
    rating = models.PositiveSmallIntegerField(
        'Оценка', null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    message = models.TextField('Отзыв', max_length=3000)
    name = models.CharField('Имя', max_length=100, blank=True)
    contact = models.CharField('Контакт для ответа', max_length=150, blank=True)
    page = models.CharField('Страница', max_length=300, blank=True, help_text='Откуда открыли форму')
    created_at = models.DateTimeField('Отправлен', auto_now_add=True)
    is_read = models.BooleanField('Прочитан', default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return f'{self.get_kind_display()}: {self.message[:60]}'
