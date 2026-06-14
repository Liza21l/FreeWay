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
            "language": "uk",
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
    places = []
    for category in categories:
        url = (
            f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            f"?location={lat},{lon}&radius=3000&type={category}&key={GOOGLE_API_KEY}"
        )
        response = requests.get(url)
        data = response.json()

        for result in data.get("results", []):
            photo_url = None
            if "photos" in result:
                photo_ref = result["photos"][0]["photo_reference"]
                photo_url = (
                    f"https://maps.googleapis.com/maps/api/place/photo"
                    f"?maxwidth=400&photo_reference={photo_ref}&key={GOOGLE_API_KEY}"
                )

            # окремий запит на деталі
            details_url = (
                f"https://maps.googleapis.com/maps/api/place/details/json"
                f"?place_id={result['place_id']}&fields=opening_hours&key={GOOGLE_API_KEY}"
            )
            details_resp = requests.get(details_url).json()
            opening_hours = details_resp.get("result", {}).get("opening_hours", {}).get("weekday_text", [])

            places.append({
                "id": result["place_id"],
                "lat": result["geometry"]["location"]["lat"], 
                "lon": result["geometry"]["location"]["lng"],
                "name": result.get("name"),
                "address": result.get("vicinity"),
                "rating": result.get("rating"),
                "is_open": result.get("opening_hours", {}).get("open_now"),
                "photo_url": photo_url,
                "opening_hours": opening_hours,   # ← тепер є графік роботи
                "category": category
            })
    return places
