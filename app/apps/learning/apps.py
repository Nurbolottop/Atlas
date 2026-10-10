from django.apps import AppConfig


class LearningConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.learning'
    verbose_name = 'Обучение'

    def ready(self):
        from apps.base.services import Service, register

        from . import checks  # noqa: F401 — регистрирует проверку контента

        register(Service(
            slug='learning',
            title='Обучение',
            summary='Курсы по разработке: теория, примеры кода и практика по шагам.',
            description=(
                'Курсы по разработке цифровых продуктов — от основ языка до баз данных и Django. '
                'Уроки с примерами кода, программа курса и поиск по материалам.'
            ),
            url_name='learning:index',
            action_label='Учиться',
            steps=(
                ('Выберите курс', 'Программа по разделам'),
                ('Проходите уроки', 'Теория и примеры кода'),
                ('Практикуйтесь', 'Задания в конце уроков'),
                ('Возвращайтесь', 'Продолжите с того же места'),
            ),
            order=5,
            preview_template='learning/includes/home_preview.html',
        ))
