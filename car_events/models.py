from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class PricedCatalogItem(models.Model):
    class PriceBasis(models.TextChoices):
        PER_BOOKING = "per_booking", "Per booking"
        PER_GUEST = "per_guest", "Per guest"

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Enter a non-negative price before offering this item for booking.",
    )
    price_basis = models.CharField(
        max_length=16,
        choices=PriceBasis.choices,
        default=PriceBasis.PER_BOOKING,
    )
    is_active = models.BooleanField(default=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        abstract = True


def price_nonnegative_constraint(model_name):
    return models.CheckConstraint(
        condition=Q(price__isnull=True) | Q(price__gte=0),
        name=f"car_events_{model_name}_price_nonnegative",
    )


class Venue(PricedCatalogItem):
    name = models.CharField(max_length=120, unique=True)
    location = models.CharField(max_length=160)
    description = models.TextField()
    image = models.CharField(
        max_length=255,
        blank=True,
        help_text="Static image path, for example car_events/images/car_venue_svicc.png",
    )
    uploaded_image = models.ImageField(
        upload_to="car_events/catalog/venues/",
        blank=True,
        help_text="Optional uploaded image; takes precedence over the existing static image path.",
    )
    min_attendees = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Smallest number of attendees this venue accepts.",
    )
    max_attendees = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Largest number of attendees this venue holds. Leave empty for no limit.",
    )

    class Meta:
        ordering = ["position", "name"]
        constraints = [
            price_nonnegative_constraint("venue"),
            models.CheckConstraint(
                condition=Q(min_attendees__gte=1),
                name="car_events_venue_min_attendees_positive",
            ),
            models.CheckConstraint(
                condition=Q(max_attendees__isnull=True)
                | Q(max_attendees__gte=models.F("min_attendees")),
                name="car_events_venue_attendee_range_valid",
            ),
        ]

    def clean(self):
        super().clean()
        if self.max_attendees is not None and self.max_attendees < self.min_attendees:
            raise ValidationError(
                {"max_attendees": "Maximum attendees cannot be less than minimum attendees."}
            )

    def __str__(self):
        return self.name


class EventPackage(PricedCatalogItem):
    name = models.CharField(max_length=120, unique=True)
    tagline = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False)
    image = models.CharField(max_length=255, blank=True)
    uploaded_image = models.ImageField(
        upload_to="car_events/catalog/packages/",
        blank=True,
        help_text="Optional image shown with this package.",
    )
    min_attendees = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Smallest number of attendees this package accepts.",
    )
    max_attendees = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Largest number of attendees this package accepts. Leave empty for no limit.",
    )

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            price_nonnegative_constraint("eventpackage"),
            models.CheckConstraint(
                condition=Q(min_attendees__gte=1),
                name="car_events_package_min_attendees_positive",
            ),
            models.CheckConstraint(
                condition=Q(max_attendees__isnull=True)
                | Q(max_attendees__gte=models.F("min_attendees")),
                name="car_events_package_attendee_range_valid",
            ),
        ]

    def clean(self):
        super().clean()
        if self.max_attendees is not None and self.max_attendees < self.min_attendees:
            raise ValidationError(
                {"max_attendees": "Maximum attendees cannot be less than minimum attendees."}
            )

    @property
    def feature_list(self):
        return [feature.text for feature in self.features.all()]

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


class ExtraService(PricedCatalogItem):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField()
    image = models.CharField(max_length=255, blank=True, help_text="Static image path")
    highlights = models.TextField(
        blank=True,
        help_text="Enter one service highlight per line.",
    )
    uploaded_image = models.ImageField(
        upload_to="car_events/catalog/services/",
        blank=True,
        help_text="Optional uploaded image; takes precedence over the existing static image path.",
    )

    class Meta:
        ordering = ["position", "name"]
        verbose_name = "Car event optional service"
        verbose_name_plural = "Car event optional services"
        constraints = [price_nonnegative_constraint("extraservice")]

    @property
    def highlight_list(self):
        return [
            highlight.strip()
            for highlight in self.highlights.splitlines()
            if highlight.strip()
        ]

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


class CarEventBookingRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    EVENT_TYPE = "Car Event"

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="car_event_booking_requests",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    event_type = models.CharField(max_length=32, default=EVENT_TYPE, editable=False)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=32)
    event_name = models.CharField(max_length=120, blank=True)
    event_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    expected_attendees = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    venue = models.ForeignKey(
        Venue,
        on_delete=models.PROTECT,
        related_name="booking_requests",
    )
    package = models.ForeignKey(
        EventPackage,
        on_delete=models.PROTECT,
        related_name="booking_requests",
    )
    services = models.ManyToManyField(
        ExtraService,
        blank=True,
        related_name="booking_requests",
    )
    budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    estimated_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    price_breakdown = models.JSONField(
        default=list,
        help_text="Prices as they were when the request was made.",
    )
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Car event booking request"
        constraints = [
            models.CheckConstraint(
                condition=Q(expected_attendees__gte=1),
                name="car_events_request_attendees_positive",
            ),
            models.CheckConstraint(
                condition=Q(budget__gt=0),
                name="car_events_request_budget_positive",
            ),
            models.CheckConstraint(
                condition=Q(estimated_total__gte=0),
                name="car_events_request_total_nonnegative",
            ),
            models.CheckConstraint(
                condition=~Q(end_time=models.F("start_time")),
                name="car_events_request_end_differs_from_start",
            ),
            models.UniqueConstraint(
                fields=["venue", "event_date"],
                condition=Q(status__in=["pending", "approved"]),
                name="car_events_one_active_request_per_venue_day",
            ),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.event_date}"
