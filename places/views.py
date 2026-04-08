from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import City, Place, UserRoute
from .services import fetch_places

def home(request):
    # Якщо вже увійшов — відразу на вибір міста
    if request.user.is_authenticated:
        return redirect('home_select')
 
    login_error = False
    reg_form    = UserCreationForm()
 
    if request.method == 'POST':
        action = request.POST.get('action')
 
        # ── ВХІД ──
        if action == 'login':
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f'Ласкаво просимо, {user.username}!')
                return redirect('home_select')
            else:
                login_error = True  # покажемо помилку в шаблоні
 
        # ── РЕЄСТРАЦІЯ ──
        elif action == 'register':
            reg_form = UserCreationForm(request.POST)
            if reg_form.is_valid():
                user = reg_form.save()
                login(request, user)
                messages.success(request, f'Акаунт створено! Ласкаво просимо, {user.username}!')
                return redirect('home_select')
            # якщо форма невалідна — reg_form.errors передається в шаблон,
            # і таб реєстрації відкриється автоматично
 
    return render(request, 'home.html', {
        'reg_form':    reg_form,
        'login_error': login_error,
    })
 
@login_required
def select(request):
    cities = City.objects.all()
    categories = [
        ('cafe', 'Кафе'),
        ('restaurant', 'Ресторан'),
        ('museum', 'Музей'),
        ('bar', 'Бари'),
        ('park', 'Парк'),
        ('landmarks', 'пам’ятки'),
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
    categories = request.GET.getlist('category')  # ['cafe'] або ['cafe','restaurant']

    if not city_id:
        return redirect('home_select')

    if not categories:
        categories = ['cafe']  # дефолт

    city = City.objects.get(id=city_id)

    # Завантажуємо з OSM тільки ті категорії яких ще немає в БД
    missing = [
        cat for cat in categories
        if not Place.objects.filter(city=city, category=cat).exists()
    ]
    if missing:
        fetch_places(city, missing)

    places = Place.objects.filter(city=city, category__in=categories)

    return render(request, 'places/list.html', {
        'places':              places,
        'city':                city,
        'selected_categories': categories,
        'all_categories': [
            ('cafe',       'Кафе'),
            ('restaurant', 'Ресторан'),
            ('museum',     'Музей'),
            ('bar', 'Бари'),
            ('park', 'Парк'),
            ('landmarks', 'пам’ятки'),
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