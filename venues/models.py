from django.db import models


class EventType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Venue(models.Model):
    name = models.CharField(max_length=150)
    location = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    event_types = models.ManyToManyField(
        EventType,
        related_name="venues",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
