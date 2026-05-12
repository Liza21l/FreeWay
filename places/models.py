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
        ('cafe',       'Кафе'),
        ('restaurant', 'Ресторан'),
        ('museum',     'Музей'),
        ('fast_food',   'Фастфуд'),
        ('bar',         'Бар'),
        ('supermarket', 'Супермаркет'),
        ('nightclub',   'Нічний клуб'),
        ('bakery',      'Пекарня'),
        ('theatre',     'Театр'),
        ('cinema',      'Кінотеатр'),
        ('park',        'Парк'),
        ('landmarks',   'Пам’ятки'),
    ]
    name     = models.CharField(max_length=200)
    city     = models.ForeignKey(City, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    lat      = models.FloatField()
    lon      = models.FloatField()
    address  = models.CharField(max_length=300, blank=True)

    def __str__(self):
        return self.name

class UserRoute(models.Model):
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    places     = models.ManyToManyField(Place)
    created_at = models.DateTimeField(auto_now_add=True)

