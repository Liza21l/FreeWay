import math, json
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import City, Place, UserRoute
from django.http import JsonResponse, HttpResponse
from .services import fetch_places, GOOGLE_CATEGORIES
from django.contrib.auth.views import LoginView
from .form import CustomUserCreationForm
from django.db.models import Sum, Count
from django.contrib.auth import get_user_model
from geopy.distance import geodesic


def choose_route(request):
    return render(request, "places/choose_route.html")
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)
    return 2 * R * math.asin(math.sqrt(a))

@csrf_exempt
@login_required
def nearby_places(request):
    if request.method == "POST":
        data = json.loads(request.body)
        lat, lon = data["lat"], data["lon"]
        categories = data.get("categories", [])

        result = []
        for cat in categories:
            qs = Place.objects.filter(category=cat)
            if qs.exists():
                nearest = min(qs, key=lambda p: haversine(lat, lon, p.lat, p.lon))
                result.append({
                    "name": nearest.name,
                    "lat": nearest.lat,
                    "lon": nearest.lon,
                    "category": nearest.category,
                    "address": nearest.address,
                })

        return JsonResponse({"places": result})

    # Якщо GET — рендеримо HTML з формою і JS
    return render(request, "places/nearby.html")

@login_required
def shared_route_view(request, share_uuid):
    route = get_object_or_404(UserRoute, share_uuid=share_uuid, visibility="public")

    coords = [
        {
            "lat": p.lat,
            "lon": p.lon,
            "name": p.name,
            "category": p.category,
            "rating": p.rating,
        }
        for p in route.places.all()
    ]

    if request.method == "POST":
        # створюємо копію маршруту для поточного користувача
        new_route = UserRoute.objects.create(
            user=request.user,
            status="active",
            visibility="private",
            distance_km=route.distance_km
        )
        new_route.places.set(route.places.all())
        new_route.save()

        # додаємо користувача у "друзі по маршруту"
        route.friends.add(request.user)

        return redirect("user_routes")

    return render(request, "places/shared_route.html", {
        "route": route,
        "coords": coords,
})

@login_required
def home_view(request):
    """
    Головна сторінка — показує найновіший активний маршрут користувача.
    """
    latest_route = (
        UserRoute.objects.filter(user=request.user, status='active')
        .prefetch_related('places')
        .order_by('-created_at')
        .first()
    )

    coords = []
    if latest_route:
        coords = [
            {
                "lat": p.lat,
                "lon": p.lon,
                "name": p.name,
                "category": p.category,
            }
            for p in latest_route.places.all()
        ]

    return render(request, "places/home.html", {
        "latest_route": latest_route,
        "coords": coords,
    })
@login_required
def archived_routes_view(request):
    """
    Показує всі маршрути користувача зі статусом 'completed'
    """
    routes_qs = UserRoute.objects.filter(
        user=request.user, status='completed'
    ).prefetch_related('places')

    # перетворюємо QuerySet у список словників для JSON
    routes = []
    for r in routes_qs:
        routes.append({
            "id": r.id,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M"),
            "coords": [
                {"lat": p.lat, "lon": p.lon, "name": p.name, "category": p.category}
                for p in r.places.all()
            ]
        })

    return render(request, "places/archived_routes.html", {
        "routes_qs": routes_qs,  
        "routes": routes    
    })


@login_required
def all_public_routes_view(request):
    routes_qs = UserRoute.objects.filter(visibility='public').prefetch_related('places')
    return render(request, "places/public_routes.html", {"routes_qs": routes_qs})

@login_required
def toggle_route_status(request, route_id):
    route = get_object_or_404(UserRoute, id=route_id, user=request.user)
    if route.status == 'active':
        route.status = 'completed'
    else:
        route.status = 'active'
    route.save()
    return redirect('user_routes')
def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # автоматично логінить після реєстрації
            return redirect("home")  # перенаправлення на головну
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/register.html", {"form": form})

class CustomLoginView(LoginView):
    template_name = "registration/login.html"

# class CustomLogoutView(LogoutView):
#     next_page = "registration"
#     http_method_names = ["get", "post"]

def logout_view(request):
    logout(request)
    return redirect("register")
@login_required
def profile_view(request):
    user = request.user

    # якщо користувач натиснув "Зберегти" у формі
    if request.method == "POST":
        user.first_name = request.POST.get("name")
        user.username = request.POST.get("username")
        user.email = request.POST.get("email")
        user.phone_number = request.POST.get("phone")
        user.save()
        messages.success(request, "Профіль успішно оновлено ✅")
        return redirect("profile")

    # всі маршрути користувача
    routes = UserRoute.objects.filter(user=user)

    # кількість завершених
    completed_routes = routes.filter(status='completed')
    completed_count = completed_routes.count()

    # кількість унікальних закладів у завершених маршрутах
    places_count = Place.objects.filter(userroute__in=completed_routes).distinct().count()

    # сумарна довжина тільки завершених
    total_km = completed_routes.aggregate(
        Sum('distance_km')
    )['distance_km__sum'] or 0

    User = get_user_model()
    friend_ids = UserRoute.objects.filter(user=user).values_list('friends', flat=True)
    friends_qs = (
        User.objects
            .filter(id__in=friend_ids)
            .annotate(routes_count=Count('userroute'))
            .distinct()
    )

    friends_list = [
        {
            "name": f.first_name or f.username,  # fallback на username
            "routes_count": f.routes_count
        }
        for f in friends_qs
    ]

    return render(request, 'places/profile.html', {
        'user': user,
        'completed_count': completed_count,
        'places_count': places_count,
        'total_km': round(total_km, 2),
        'friends_count': friends_qs.count(),
        'friends_list': friends_list,
        'member_since': user.date_joined,
    })
@login_required
def user_routes_view(request):
    """
    Показує всі маршрути, створені користувачем.
    """
    routes_qs = UserRoute.objects.filter(user=request.user).prefetch_related('places')
    private_routes = routes_qs.filter(visibility='private', status='active')
    public_routes  = routes_qs.filter(visibility='public', status='active')

    # перетворюємо QuerySet у список словників для JSON
    routes = []
    for r in routes_qs:
        routes.append({
            "id": r.id,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M"),
            "coords": [
                {"lat": p.lat, "lon": p.lon, "name": p.name, "category": p.category}
                for p in r.places.all()
            ]
        })

    return render(request, "places/my_routes.html", {
        "routes": routes,
        "private_routes": private_routes,
        "public_routes": public_routes  
    })
@login_required
def select(request):
    cities = City.objects.all()
    categories = GOOGLE_CATEGORIES
    return render(request, 'places/home_select.html', {
        'cities': cities,
        'categories': categories,
    })
@login_required
def place_list(request):
    city_id = request.GET.get('city')
    categories = request.GET.getlist('category')

    if not city_id:
        return redirect('home')
    if not categories:
        categories = ['cafe']  # дефолт

    city = City.objects.get(id=city_id)

    # Завантажуємо з Google Places тільки ті категорії, яких ще немає в БД
    missing = [
        cat for cat in categories
        if not Place.objects.filter(city=city, category=cat).exists()
    ]

    for cat in missing:
        fetch_places(city, [cat])

    places = Place.objects.filter(city=city, category__in=categories)

    return render(request, 'places/list.html', {
        'places': places,
        'city': city,
        'selected_categories': categories,
        'all_categories': GOOGLE_CATEGORIES,
    })

@login_required
def build_route(request):
    if request.method != 'POST':
        return redirect('home')

    selected_ids = request.POST.getlist('place_ids')
    visibility = request.POST.get('visibility', 'private') 

    if not selected_ids:
        return redirect('home')

    places = Place.objects.filter(id__in=selected_ids)

    route = UserRoute.objects.create(user=request.user, visibility=visibility)
    route.places.set(places)

    coords = []
    for pid in selected_ids:
        try:
            p = places.get(id=pid)
            coords.append({
                'lat':      p.lat,
                'lon':      p.lon,
                'name':     p.name,
                'category': p.category,
            })
        except Place.DoesNotExist:
            continue

    total_km = 0
    for i in range(len(coords)-1):
        p1 = (coords[i]['lat'], coords[i]['lon'])
        p2 = (coords[i+1]['lat'], coords[i+1]['lon'])
        total_km += geodesic(p1, p2).km

    route.distance_km = round(total_km, 2)
    route.save()

    return render(request, 'places/map.html', {'coords': coords})
