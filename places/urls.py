from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import register, CustomLoginView, CustomLogoutView

urlpatterns = [
    path('', views.select, name='home_select'),
    path('profile/', views.profile_view, name='profile'),
    path('places/', views.place_list, name='place_list'),
    path('route/', views.build_route, name='build_route'),
    path("register/", register, name="register"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path('my-routes/', views.user_routes_view, name='user_routes'),
]