from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import City, Place, UserRoute
from .services import fetch_places
from django.contrib.auth.views import LoginView, LogoutView
from .form import CustomUserCreationForm



def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # автоматично логінить після реєстрації
            return redirect("home_select")  # перенаправлення на головну
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/register.html", {"form": form})

class CustomLoginView(LoginView):
    template_name = "registration/login.html"

class CustomLogoutView(LogoutView):
    next_page = "login"
    http_method_names = ["get", "post"] 

@login_required
def profile_view(request):
    """
    Показує профіль користувача:
    ім’я, username, email, телефон і кнопку для перегляду маршрутів.
    """
    user = request.user
    return render(request, 'places/profile.html', {
        'user': user
    })

@login_required
def user_routes_view(request):
    """
    Показує всі маршрути, створені користувачем.
    """
    routes = UserRoute.objects.filter(user=request.user).prefetch_related('places')
    return render(request, 'places/my_routes.html', {
        'routes': routes
    })
@login_required
def select(request):
    cities = City.objects.all()
    categories = [
        ('cafe', 'Кафе'),
        ('fast_food', 'Фастфуд'),
        ('restaurant', 'Ресторан'),
        ('bar', 'Бар'),
        ('nightclub', 'Нічний клуб'),
        ('bakery', 'Пекарня'),
        ('supermarket', 'Супермаркет'),
        ('theatre', 'Театр'),
        ('cinema', 'Кінотеатр'),
        ('museum', 'Музей'),
        ('park', 'Парк'),
        ('landmarks', 'Пам’ятки'),
    ]
    return render(request, 'places/home_select.html', {
        'cities': cities,
        'categories': categories,
    })


@login_required
def place_list(request):
    """
    Крок 2 — вибір категорій і перегляд списку місць.
    Підтримує як одну категорію так і декілька одночасно.
    """
    city_id = request.GET.get('city')
    categories = request.GET.getlist('category')

    if not city_id:
        return redirect('home_select')

    if not categories:
        categories = ['cafe']  # дефолт

    city = City.objects.get(id=city_id)

    # Завантажуємо з OSM тільки ті категорії, яких ще немає в БД
    missing = [
        cat for cat in categories
        if not Place.objects.filter(city=city, category=cat).exists()
    ]

    # 🔎 ТУТ головна зміна — цикл по категоріях
    for cat in missing:
        fetch_places(city, [cat])

    # Вибираємо всі місця для вибраних категорій
    places = Place.objects.filter(city=city, category__in=categories)

    return render(request, 'places/list.html', {
        'places': places,
        'city': city,
        'selected_categories': categories,
        'all_categories': [
            ('cafe', 'Кафе'),
            ('fast_food', 'Фастфуд'),
            ('restaurant', 'Ресторан'),
            ('bar', 'Бар'),
            ('nightclub', 'Нічний клуб'),
            ('bakery', 'Пекарня'),
            ('supermarket', 'Супермаркет'),
            ('theatre', 'Театр'),
            ('cinema', 'Кінотеатр'),
            ('museum', 'Музей'),
            ('park', 'Парк'),
            ('landmarks', 'Пам’ятки'),
        ],
    })
@login_required
def build_route(request):
    """
    Крок 3 — отримує вибрані місця і будує маршрут.
    Порядок точок = порядок в якому користувач ставив галочки.
    """
    if request.method != 'POST':
        return redirect('home_select')

    selected_ids = request.POST.getlist('place_ids')

    if not selected_ids:
        return redirect('home_select')

    places = Place.objects.filter(id__in=selected_ids)

    # Зберігаємо маршрут в БД
    route = UserRoute.objects.create(user=request.user)
    route.places.set(places)

    # Координати в порядку вибору користувача
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

    return render(request, 'places/map.html', {'coords': coords})