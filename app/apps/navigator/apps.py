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
            summary='Визуальные направления и промпты для ИИ-разработчика',
            description=(
                'Каталог визуальных направлений: от минимализма до Bento-компоновки. '
                'Для каждого стиля — демонстрации сайта, приложения и веб-платформы, '
                'палитры, шрифты с кириллицей, правила для компонентов и готовый промпт, '
                'который объясняет ИИ-разработчику, как реализовать стиль.'
            ),
            url_name='navigator:catalog',
            how_text=(
                'Сервис формирует инструкцию по дизайну. Вы передаёте её своему ИИ-разработчику '
                'вместе с задачей проекта — функции и содержание остаются вашими.'
            ),
            steps=(
                ('Выберите направление', 'Найдите стиль в каталоге по названию, описанию или тегам.'),
                ('Изучите стиль', 'Посмотрите демонстрации, признаки, палитры, типографику и типичные ошибки.'),
                ('Укажите тип продукта', 'Сайт, мобильное приложение или веб-платформа — больше ничего не нужно.'),
                ('Передайте промпт ИИ', 'Скопируйте или скачайте инструкцию и отправьте её ИИ вместе с задачей проекта.'),
            ),
            order=10,
            hero_template='navigator/includes/home_hero.html',
            preview_template='navigator/includes/home_preview.html',
        ))
