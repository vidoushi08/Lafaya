from decimal import Decimal

from django.db import models

from venues.models import Venue


class BirthdayPackage(models.Model):
    PACKAGE_TYPE_FIXED = "fixed"
    PACKAGE_TYPE_CUSTOM = "custom"
    PACKAGE_TYPE_CHOICES = [
        (PACKAGE_TYPE_FIXED, "Fixed"),
        (PACKAGE_TYPE_CUSTOM, "Custom"),
    ]

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPE_CHOICES, default=PACKAGE_TYPE_FIXED)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    default_venue = models.ForeignKey(
        Venue,
        on_delete=models.SET_NULL,
        related_name="birthday_packages",
        null=True,
        blank=True,
    )
    features = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "id"]

    def __str__(self):
        return self.name

    @property
    def display_price(self):
        if self.package_type == self.PACKAGE_TYPE_CUSTOM:
            return "Price to be confirmed"
        return f"${self.price:.2f}" if self.price is not None else "Price to be confirmed"


class BirthdayEnquiry(models.Model):
    STATUS_NEW = "new"
    STATUS_REVIEW = "review"
    STATUS_QUOTED = "quoted"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_REVIEW, "In review"),
        (STATUS_QUOTED, "Quoted"),
        (STATUS_CONFIRMED, "Confirmed"),
    ]

    customer_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    event_date = models.DateField()
    selected_package = models.ForeignKey(BirthdayPackage, on_delete=models.PROTECT, related_name="enquiries")
    quoted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    venue = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True, blank=True, related_name="birthday_enquiries")
    custom_requirements = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer_name} - {self.selected_package.name}"

    def save(self, *args, **kwargs):
        if self.selected_package.package_type == "fixed" and self.quoted_price is None:
            self.quoted_price = self.selected_package.price
        elif self.selected_package.package_type == "custom":
            self.quoted_price = None
        super().save(*args, **kwargs)
