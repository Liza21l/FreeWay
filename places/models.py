from django.db import models
from django.contrib.auth.models import User

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
    user       = models.ForeignKey(User, on_delete=models.CASCADE)
    places     = models.ManyToManyField(Place)
    created_at = models.DateTimeField(auto_now_add=True)
