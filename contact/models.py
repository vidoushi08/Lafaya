from django.db import models


class ContactMessage(models.Model):
    class Topic(models.TextChoices):
        GENERAL = "general", "General enquiry"
        EVENT = "event", "Event planning and bookings"
        PARTNERSHIP = "partnership", "Partnerships"
        OTHER = "other", "Something else"

    class Status(models.TextChoices):
        NEW = "new", "New"
        READ = "read", "Read"
        REPLIED = "replied", "Replied"
        CLOSED = "closed", "Closed"

    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=32, blank=True)
    topic = models.CharField(max_length=20, choices=Topic.choices, default=Topic.GENERAL)
    subject = models.CharField(max_length=160)
    message = models.TextField(max_length=4000)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} — {self.name}"
