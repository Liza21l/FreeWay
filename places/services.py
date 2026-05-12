import requests
from .models import City, Place

CATEGORY_TAGS = {
    'cafe':         ('amenity', 'cafe'),
    'fast_food':    ('amenity', 'fast_food'),
    'restaurant':   ('amenity', 'restaurant'),
    'museum':       ('tourism', 'museum'),
    'bar':          ('amenity', 'bar'),
    'nightclub':    ('amenity', 'nightclub'),
    'park':         ('leisure', 'park'),
    'landmarks':    ('tourism', 'attraction'),
    'bakery':       ('shop', 'bakery'),
    'supermarket':  ('shop', 'supermarket'),
    'theatre':      ('amenity', 'theatre'),
    'cinema':       ('amenity', 'cinema'),
}

# список серверів без російського дзеркала
OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
]

def fetch_places(city: City, categories: list):
    """
    Завантажує місця з Overpass API одним запитом
    для всіх вибраних категорій одночасно.
    Зберігає в БД. Повторний виклик не дублює дані.
    """

    union_parts = []
    for cat in categories:
        if cat not in CATEGORY_TAGS:
            continue
        key, val = CATEGORY_TAGS[cat]
        union_parts.append(
            f'node["{key}"="{val}"](around:1000,{city.lat},{city.lon});'
            f'way["{key}"="{val}"](around:1000,{city.lat},{city.lon});'
            f'relation["{key}"="{val}"](around:1000,{city.lat},{city.lon});'
        )

    if not union_parts:
        return

    query = f"""
    [out:json][timeout:25];
    (
        {''.join(union_parts)}
    );
    out center;
    """
    print("Overpass query:", query)

    resp = None
    for server in OVERPASS_SERVERS:
        try:
            resp = requests.post(server, data={'data': query}, timeout=60)
            resp.raise_for_status()
            print(f"Успішний запит до {server}")
            break
        except requests.RequestException as e:
            print(f"Overpass помилка на {server}: {e}")
            resp = None

    if not resp:
        return

    # Зворотний словник для визначення категорії
    TAG_TO_CAT = {(k, v): cat for cat, (k, v) in CATEGORY_TAGS.items()}

    for el in resp.json().get('elements', []):
        tags = el.get('tags', {})
        name = tags.get('name', '').strip()
        if not name:
            continue

        category = None
        for key, val in tags.items():
            if (key, val) in TAG_TO_CAT:
                category = TAG_TO_CAT[(key, val)]
                break

        if not category:
            continue

        Place.objects.get_or_create(
            name=name,
            city=city,
            category=category,
            defaults={
                'lat': el.get('lat') or el.get('center', {}).get('lat'),
                'lon': el.get('lon') or el.get('center', {}).get('lon'),
                'address': tags.get('addr:street', ''),
            }
        )
