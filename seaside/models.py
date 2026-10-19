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

    def __str__(self):
        return self.name


def price_nonnegative_constraint(model_name):
    return models.CheckConstraint(
        condition=Q(price__isnull=True) | Q(price__gte=0),
        name=f"seaside_{model_name}_price_nonnegative",
    )


class SeasideVenue(PricedCatalogItem):
    name = models.CharField(max_length=120, unique=True)
    location = models.CharField(max_length=160)
    description = models.TextField()
    image = models.CharField(max_length=255, blank=True)
    uploaded_image = models.ImageField(
        upload_to="seaside/catalog/venues/",
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
        verbose_name = "Seaside venue"
        verbose_name_plural = "Seaside venues"
        constraints = [
            price_nonnegative_constraint("seasidevenue"),
            models.CheckConstraint(
                condition=Q(capacity__isnull=True) | Q(capacity__gte=1),
                name="seaside_seasidevenue_capacity_positive",
            ),
        ]


class SeasidePackage(PricedCatalogItem):
    name = models.CharField(max_length=120, unique=True)
    tagline = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    image = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional path to an image in the project's static files.",
    )
    features = models.TextField(
        blank=True,
        help_text="Enter one package feature per line.",
    )
    uploaded_image = models.ImageField(
        upload_to="seaside/catalog/packages/",
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
            price_nonnegative_constraint("seasidepackage"),
            models.CheckConstraint(
                condition=Q(min_guests__gte=1),
                name="seaside_seasidepackage_min_guests_positive",
            ),
            models.CheckConstraint(
                condition=Q(max_guests__isnull=True)
                | Q(max_guests__gte=models.F("min_guests")),
                name="seaside_seasidepackage_guest_range_valid",
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


class SeasideService(PricedCatalogItem):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField()
    highlights = models.TextField(
        blank=True,
        help_text="Enter one service highlight per line.",
    )
    image = models.CharField(max_length=255, blank=True)
    uploaded_image = models.ImageField(
        upload_to="seaside/catalog/services/",
        blank=True,
        help_text="Optional uploaded image; takes precedence over the existing static image path.",
    )

    class Meta:
        ordering = ["position", "name"]
        verbose_name = "Seaside optional service"
        verbose_name_plural = "Seaside optional services"
        constraints = [price_nonnegative_constraint("seasideservice")]

    @property
    def highlight_list(self):
        return [
            highlight.strip()
            for highlight in self.highlights.splitlines()
            if highlight.strip()
        ]
