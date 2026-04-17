from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.select, name='home_select'),
    path('places/', views.place_list, name='place_list'),
    path('route/', views.build_route, name='build_route'),
]