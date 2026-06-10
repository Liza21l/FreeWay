import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)


class City(models.Model):
    name = models.CharField(max_length=100)   
    lat  = models.FloatField()                
    lon  = models.FloatField()                

    def __str__(self):
        return self.name

class Place(models.Model):
    CATEGORY_CHOICES = [
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
    name     = models.CharField(max_length=200)
    city     = models.ForeignKey(City, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    lat      = models.FloatField()
    lon      = models.FloatField()
    rating   = models.FloatField(blank=True, null=True) 
    is_open  = models.BooleanField(default=False, null=True)
    address  = models.CharField(max_length=300, blank=True)

    def __str__(self):
        return self.name

class UserRoute(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активний'),
        ('completed', 'Завершений'),
    ]
    VISIBILITY_CHOICES = [
        ('private', 'Особистий'),
        ('public', 'Публічний'),
    ]

    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True)
    places     = models.ManyToManyField(Place)
    created_at = models.DateTimeField(auto_now_add=True)
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    visibility  = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='private')
    distance_km = models.FloatField(default=0)
    share_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    friends = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="friend_routes", blank=True)
    has_start_location = models.BooleanField(default=False)
    start_lat = models.FloatField(null=True, blank=True)
    start_lon = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Маршрут {self.id} ({self.get_status_display()}, {self.get_visibility_display()})"

