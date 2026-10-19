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
        name=f"birthday_{model_name}_price_nonnegative",
    )


class BirthdayVenue(PricedCatalogItem):
    name = models.CharField(max_length=120, unique=True)
    location = models.CharField(max_length=160)
    description = models.TextField()
    image = models.CharField(max_length=255, blank=True)
    uploaded_image = models.ImageField(
        upload_to="birthday/catalog/venues/",
        blank=True,
        help_text="Optional uploaded image; takes precedence over the existing static image path.",
    )
    capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Maximum guests this venue holds. Leave empty for no limit.",
    )

    class Meta:
        ordering = ["position", "name"]
        verbose_name = "Birthday venue"
        verbose_name_plural = "Birthday venues"
        constraints = [
            price_nonnegative_constraint("venue"),
            models.CheckConstraint(
                condition=Q(capacity__isnull=True) | Q(capacity__gte=1),
                name="birthday_venue_capacity_positive",
            ),
        ]

    def __str__(self):
        return self.name


class BirthdayPackage(PricedCatalogItem):
    name = models.CharField(max_length=120, unique=True)
    tagline = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    image = models.CharField(max_length=255, blank=True)
    features = models.TextField(
        blank=True,
        help_text="Enter one package feature per line.",
    )
    uploaded_image = models.ImageField(
        upload_to="birthday/catalog/packages/",
        blank=True,
        help_text="Optional image shown with this package.",
    )
    is_featured = models.BooleanField(default=False)
    min_guests = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Smallest number of guests this package accepts.",
    )
    max_guests = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Largest number of guests this package accepts. Leave empty for no limit.",
    )

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            price_nonnegative_constraint("package"),
            models.CheckConstraint(
                condition=Q(min_guests__gte=1),
                name="birthday_package_min_guests_positive",
            ),
            models.CheckConstraint(
                condition=Q(max_guests__isnull=True)
                | Q(max_guests__gte=models.F("min_guests")),
                name="birthday_package_guest_range_valid",
            ),
        ]

    def clean(self):
        super().clean()
        if self.max_guests is not None and self.max_guests < self.min_guests:
            raise ValidationError(
                {"max_guests": "Maximum guests cannot be less than minimum guests."}
            )

    @property
    def feature_list(self):
        return [
            feature.strip()
            for feature in self.features.splitlines()
            if feature.strip()
        ]

    def __str__(self):
        return self.name


class BirthdayService(PricedCatalogItem):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField()
    highlights = models.TextField(
        blank=True,
        help_text="Enter one service highlight per line.",
    )
    image = models.CharField(max_length=255, blank=True)
    uploaded_image = models.ImageField(
        upload_to="birthday/catalog/services/",
        blank=True,
        help_text="Optional uploaded image; takes precedence over the existing static image path.",
    )

    class Meta:
        ordering = ["position", "name"]
        verbose_name = "Birthday optional service"
        verbose_name_plural = "Birthday optional services"
        constraints = [price_nonnegative_constraint("service")]

    @property
    def highlight_list(self):
        return [
            highlight.strip()
            for highlight in self.highlights.splitlines()
            if highlight.strip()
        ]

    def __str__(self):
        return self.name


class BirthdayBookingRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    EVENT_TYPE = "Birthday"

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="birthday_booking_requests",
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
    expected_guests = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    venue = models.ForeignKey(
        BirthdayVenue,
        on_delete=models.PROTECT,
        related_name="booking_requests",
    )
    package = models.ForeignKey(
        BirthdayPackage,
        on_delete=models.PROTECT,
        related_name="booking_requests",
    )
    services = models.ManyToManyField(
        BirthdayService,
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
        verbose_name = "Birthday booking request"
        constraints = [
            models.CheckConstraint(
                condition=Q(expected_guests__gte=1),
                name="birthday_request_guests_positive",
            ),
            models.CheckConstraint(
                condition=Q(budget__gt=0),
                name="birthday_request_budget_positive",
            ),
            models.CheckConstraint(
                condition=Q(estimated_total__gte=0),
                name="birthday_request_total_nonnegative",
            ),
            models.CheckConstraint(
                condition=~Q(end_time=models.F("start_time")),
                name="birthday_request_end_differs_from_start",
            ),
            models.UniqueConstraint(
                fields=["venue", "event_date"],
                condition=Q(status__in=["pending", "approved"]),
                name="birthday_one_active_request_per_venue_day",
            ),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.event_date}"
