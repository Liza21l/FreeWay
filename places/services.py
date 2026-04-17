import requests
from .models import City, Place

CATEGORY_TAGS = {
        'cafe':       ('amenity', 'cafe'),
        'restaurant': ('amenity', 'restaurant'),
        'museum':     ('tourism', 'museum'),
        'bar':        ('amenity', 'bar'),
        'park':       ('leisure', 'park'),
        'landmarks': ('tourism', 'attraction'),
}

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
            f'node["{key}"="{val}"](around:3000,{city.lat},{city.lon});'
        )

    if not union_parts:
        return

    query = f"""
    [out:json][timeout:20];
    (
      {''.join(union_parts)}
    );
    out 60;
    """

    try:
        resp = requests.post(
            'https://overpass-api.de/api/interpreter',
            data={'data': query},
            timeout=60
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Overpass помилка: {e}")
        return

    TAG_TO_CAT = {v: k for k, v in CATEGORY_TAGS.items()}

    for el in resp.json().get('elements', []):
        tags = el.get('tags', {})
        name = tags.get('name', '').strip()
        if not name:
            continue

        category = None
        for (key, val), cat in {
            ('amenity', 'cafe'):       'cafe',
            ('amenity', 'restaurant'): 'restaurant',
            ('tourism', 'museum'):     'museum',
            ('amenity', 'bar'): 'bar',
            ('leisure', 'park'): 'park',
            ('tourism', 'landmarks'): 'landmarks',

        }.items():
            if tags.get(key) == val:
                category = cat
                break

        if not category:
            continue

       
        Place.objects.get_or_create(
            name=name,
            city=city,
            category=category,
            defaults={
                'lat':     el['lat'],
                'lon':     el['lon'],
                'address': tags.get('addr:street', ''),
            }
        )