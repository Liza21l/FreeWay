from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import register, CustomLoginView

urlpatterns = [
    path('', views.home_view, name='home'),
    path('home_select/', views.select, name='home_select'),
    path('profile/', views.profile_view, name='profile'),
    path('places/', views.place_list, name='place_list'),
    path('route/', views.build_route, name='build_route'),
    path("register/", register, name="register"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path('my-routes/', views.user_routes_view, name='user_routes'),
    path('my-routes/<int:route_id>/toggle/', views.toggle_route_status, name='toggle_route_status'),
    path("public-routes/", views.all_public_routes_view, name="all_public_routes"),
    path("my-routes/archive/", views.archived_routes_view, name="archived_routes"),
    path("nearby/", views.nearby_places, name="nearby_places"),
    path("choose-route/", views.choose_route, name="choose_route"),
    path("routes/share/<uuid:share_uuid>/", views.shared_route_view, name="shared_route"),
    path("my-routes/delete/<int:route_id>/", views.delete_route, name="delete_route"),
    path("routes/<int:route_id>/toggle_visibility/", views.toggle_route_visibility, name="toggle_route_visibility"),
    path("places/category/<str:category>/", views.category_places, name="category_places"),
    path("places/category_all/<str:category>/", views.category_all_places, name="category_all_places"),
    path("ai_route/", views.ai_route, name="ai_route"),
    path("save_ai_route/", views.save_ai_route, name="save_ai_route"),
    path("ai_route_page/", views.ai_route_page, name="ai_route_page"),
    path("privacy_policy/", views.privacy_policy, name="privacy_policy")
]