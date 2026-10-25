from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.conf import settings


class WeddingPackage(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    min_guests = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    max_guests = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["display_order", "name"]


class WeddingEnquiry(models.Model):

    STATUS_CHOICES = [
        ("new", "New"),
        ("review", "Under Review"),
        ("quoted", "Quote Provided"),
        ("confirmed", "Confirmed"),
    ]

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wedding_enquiries"
    )

    package = models.ForeignKey(
        WeddingPackage,
        on_delete=models.PROTECT,
        related_name="enquiries"
    )

    event_date = models.DateField()
    venue = models.CharField(max_length=200, blank=True)
    custom_requirements = models.TextField(blank=True)  #connects to existing Django user account
    notes = models.TextField(blank=True)

    quoted_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer} - {self.package.name}"

    class Meta:
        ordering = ["-created_at"]


class WeddingVenue(models.Model):
    name = models.CharField(max_length=120, unique=True)
    location = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    image = models.CharField(max_length=255, blank=True)
    capacity = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "name"]

    def __str__(self):
        return self.name


class WeddingService(models.Model):
    class PriceBasis(models.TextChoices):
        PER_BOOKING = "per_booking", "Per booking"
        PER_GUEST = "per_guest", "Per guest"

    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    price_basis = models.CharField(max_length=16, choices=PriceBasis.choices, default=PriceBasis.PER_BOOKING)
    is_active = models.BooleanField(default=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(price__isnull=True) | Q(price__gte=0),
                name="wedding_service_price_nonnegative",
            ),
        ]

    def __str__(self):
        return self.name


class WeddingBookingRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    EVENT_TYPE = "Wedding"

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="wedding_booking_requests",
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    event_type = models.CharField(max_length=32, default=EVENT_TYPE, editable=False)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=32)
    event_name = models.CharField(max_length=120, blank=True)
    event_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    expected_guests = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    venue = models.ForeignKey(WeddingVenue, on_delete=models.PROTECT, related_name="booking_requests")
    package = models.ForeignKey(WeddingPackage, on_delete=models.PROTECT, related_name="booking_requests")
    services = models.ManyToManyField(WeddingService, blank=True, related_name="booking_requests")
    budget = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    estimated_total = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    price_breakdown = models.JSONField(default=list)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=Q(expected_guests__gte=1), name="wedding_request_guests_positive"),
            models.CheckConstraint(condition=Q(budget__gt=0), name="wedding_request_budget_positive"),
            models.CheckConstraint(condition=Q(estimated_total__gte=0), name="wedding_request_total_nonnegative"),
            models.CheckConstraint(condition=~Q(end_time=models.F("start_time")), name="wedding_request_end_differs_from_start"),
            models.UniqueConstraint(
                fields=["venue", "event_date"],
                condition=Q(status__in=["pending", "approved"]),
                name="wedding_one_active_request_per_venue_day",
            ),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.event_date}"
