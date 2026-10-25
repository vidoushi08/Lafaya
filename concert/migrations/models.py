from django.db import models


class Concert(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300)
    description = models.TextField()
    hero_image = models.ImageField(upload_to='concert/')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Venue(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='venues/')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ProductionElement(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='production/')
    features = models.TextField(blank=True)

    def __str__(self):
        return self.name


class TicketPackage(models.Model):
    tier = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    features = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name