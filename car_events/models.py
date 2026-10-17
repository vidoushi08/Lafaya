from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Venue(models.Model):
    name = models.CharField(max_length=120, unique=True)
    location = models.CharField(max_length=160)
    description = models.TextField()
    image = models.CharField(
        max_length=255,
        blank=True,
        help_text="Static image path, for example car_events/images/car_venue_svicc.png",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class EventPackage(models.Model):
    name = models.CharField(max_length=120, unique=True)
    tagline = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class PackageFeature(models.Model):
    event_package = models.ForeignKey(
        EventPackage, on_delete=models.CASCADE, related_name="features"
    )
    text = models.CharField(max_length=180)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"{self.event_package.name}: {self.text}"


class ExtraService(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField()
    image = models.CharField(max_length=255, blank=True, help_text="Static image path")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CarEventEnquiry(models.Model):
    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("confirmed", "Confirmed"),
        ("closed", "Closed"),
    ]

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="car_event_enquiries",
    )
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    preferred_date = models.DateField()
    expected_attendees = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="enquiries")
    event_package = models.ForeignKey(
        EventPackage, on_delete=models.PROTECT, related_name="enquiries"
    )
    extras = models.ManyToManyField(ExtraService, blank=True, related_name="enquiries")
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Car event enquiries"

    def __str__(self):
        return f"{self.full_name} - {self.event_package.name}"
