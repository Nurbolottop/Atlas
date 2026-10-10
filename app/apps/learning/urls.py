from django.urls import path

from . import views

app_name = 'learning'

urlpatterns = [
    path('', views.index, name='index'),
    path('<slug:course>/', views.course_detail, name='course'),
    path('<slug:course>/<slug:lesson>/', views.lesson_detail, name='lesson'),
]
