import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('thanks', 'Спасибо'), ('idea', 'Идея'), ('problem', 'Проблема')], default='thanks', max_length=10, verbose_name='Тип')),
                ('rating', models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='Оценка')),
                ('message', models.TextField(max_length=3000, verbose_name='Отзыв')),
                ('name', models.CharField(blank=True, max_length=100, verbose_name='Имя')),
                ('contact', models.CharField(blank=True, max_length=150, verbose_name='Контакт для ответа')),
                ('page', models.CharField(blank=True, help_text='Откуда открыли форму', max_length=300, verbose_name='Страница')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Отправлен')),
                ('is_read', models.BooleanField(default=False, verbose_name='Прочитан')),
            ],
            options={
                'verbose_name': 'Отзыв',
                'verbose_name_plural': 'Отзывы',
                'ordering': ['-created_at'],
            },
        ),
    ]
