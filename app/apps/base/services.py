"""
Реестр сервисов платформы.

Каждый сервис — отдельное Django-приложение, которое регистрирует себя
в `AppConfig.ready()`. Главная страница, шапка и подвал строятся по этому
реестру, поэтому новый сервис подключается без правок существующего кода:

    from apps.base.services import Service, register

    class MyServiceConfig(AppConfig):
        def ready(self):
            register(Service(
                slug='my-service',
                title='Мой сервис',
                summary='Одна фраза для навигации.',
                description='Описание для карточки на главной.',
                url_name='my_service:index',
                steps=(('Шаг', 'Пояснение'),),
                order=20,
            ))
"""
from dataclasses import dataclass, field

from django.urls import reverse


@dataclass(frozen=True)
class Service:
    slug: str
    title: str
    summary: str
    description: str
    url_name: str
    action_label: str = 'Открыть'
    steps: tuple = field(default_factory=tuple)  # ((заголовок, пояснение), ...)
    order: int = 100
    # Необязательные шаблоны сервиса для главной: визуал первого экрана
    # (берётся у первого сервиса, где он задан) и превью в карточке.
    hero_template: str | None = None
    preview_template: str | None = None

    @property
    def url(self):
        return reverse(self.url_name)


def get_hero_service():
    return next((s for s in get_services() if s.hero_template), None)


_registry: dict[str, Service] = {}


def register(service: Service) -> None:
    if service.slug in _registry and _registry[service.slug] != service:
        raise ValueError(f'Сервис «{service.slug}» уже зарегистрирован')
    _registry[service.slug] = service


def get_services() -> list[Service]:
    return sorted(_registry.values(), key=lambda s: (s.order, s.title))
