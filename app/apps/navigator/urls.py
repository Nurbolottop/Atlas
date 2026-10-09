from django.urls import path

from . import views

app_name = 'navigator'

urlpatterns = [
    path('', views.catalog, name='catalog'),
    path('<slug:slug>/', views.style_detail, name='style'),
    path('<slug:slug>/use/', views.style_use, name='use'),
    path('<slug:slug>/prompt/', views.prompt_type, name='prompt_type'),
    path('<slug:slug>/prompt/<slug:product>/', views.prompt_result, name='prompt_result'),
    path('<slug:slug>/prompt/<slug:product>/download.txt', views.prompt_download, name='prompt_download'),
]
