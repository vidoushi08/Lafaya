from django.db import models
from django.conf import settings


class WeddingPackage(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
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