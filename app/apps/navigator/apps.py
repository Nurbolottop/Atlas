from django.apps import AppConfig


class NavigatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.navigator'
    verbose_name = 'Навигатор дизайна'

    def ready(self):
        from apps.base.services import Service, register

        from . import checks  # noqa: F401 — регистрирует проверку контента

        register(Service(
            slug='design-navigator',
            title='Навигатор дизайна',
            summary='Стили интерфейсов с примерами и готовым промптом для ИИ.',
            description=(
                'Каталог визуальных направлений с демонстрациями сайта, приложения и веб-платформы '
                'и готовым промптом для ИИ-разработчика.'
            ),
            url_name='navigator:catalog',
            steps=(
                ('Выберите стиль', 'Каталог направлений'),
                ('Изучите', 'Демо, палитры, шрифты'),
                ('Укажите продукт', 'Сайт, приложение или платформа'),
                ('Получите промпт', 'Скопируйте или скачайте'),
            ),
            order=10,
            hero_template='navigator/includes/home_hero.html',
            preview_template='navigator/includes/home_preview.html',
        ))
