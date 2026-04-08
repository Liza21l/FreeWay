from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('select/',        views.select, name='home_select'),
    path('places/', views.place_list,  name='place_list'),
    path('route/',  views.build_route, name='build_route'),
]