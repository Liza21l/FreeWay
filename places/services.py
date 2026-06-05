import requests
from .models import City, Place
import os

# 🔑 Google Places API ключ
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")   # встав свій ключ тут

# 📍 Категорії для вибору (UI → Google Places types)
GOOGLE_CATEGORIES = [
    ('cafe', 'Кафе'),
    ('restaurant', 'Ресторан'),
    ('museum', 'Музей'),
    ('meal_takeaway', 'Фастфуд'),   
    ('bar', 'Бар'),
    ('supermarket', 'Супермаркет'),
    ('night_club', 'Нічний клуб'),      
    ('bakery', 'Пекарня'),
    ('movie_theater', 'Кінотеатр/Театр'), 
    ('park', 'Парк'),
    ('tourist_attraction', 'Пам’ятки'), 
]

# ==========================
# Google Places API функція
# ==========================

def fetch_places(city: City, categories: list):
    """
    Завантажує місця з Google Places API для вибраних категорій.
    Зберігає в БД. Повторний виклик не дублює дані.
    """

    api_key = GOOGLE_API_KEY
    print("Запитую Google Places для:", city.name, categories)

    for cat in categories:
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{city.lat},{city.lon}",
            "radius": 5000,   # радіус у метрах
            "type": cat,      # напряму Google Places type
            "key": api_key,
        }
        resp = requests.get(url, params=params).json()
        print("Отримано результатів:", len(resp.get("results", [])))

        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"Google Places помилка: {e}")
            continue

        for el in data.get("results", []):
            name = el.get("name")
            lat = el["geometry"]["location"]["lat"]
            lon = el["geometry"]["location"]["lng"]
            address = el.get("vicinity", "")
            rating = el.get("rating", None)
            is_open = el.get("opening_hours", {}).get("open_now")

            if not name:
                continue

            Place.objects.get_or_create(
                name=name,
                city=city,
                category=cat,
                defaults={
                    "lat": lat,
                    "lon": lon,
                    "address": address,
                    "rating": rating,
                    "is_open": is_open,
                }
            )


def fetch_places_nearby(lat, lon, categories):
    api_key = GOOGLE_API_KEY
    result = []

    for cat in categories:
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lon}",
            "radius": 3000,   # радіус пошуку у метрах
            "type": cat,
            "key": api_key,
            "opennow": True   # можна додати фільтр "відкрито зараз"
        }
        resp = requests.get(url, params=params).json()
        for el in resp.get("results", []):
            result.append({
                "name": el.get("name"),
                "lat": el["geometry"]["location"]["lat"],
                "lon": el["geometry"]["location"]["lng"],
                "category": cat,
                "address": el.get("vicinity", ""),
                "rating": el.get("rating"),
                "is_open": el.get("opening_hours", {}).get("open_now")
            })
    return result

