from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import CarEventEnquiryForm
from .models import CarEventEnquiry, EventPackage, ExtraService, PackageFeature, Venue


class CarEventPageTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(
            name="Test Venue",
            location="Port Louis",
            description="A test event space.",
            image="car_events/images/car_venue_svicc.png",
        )
        self.package = EventPackage.objects.create(
            name="Test Package", tagline="For testing", is_featured=True
        )
        PackageFeature.objects.create(event_package=self.package, text="Coordination")
        self.extra = ExtraService.objects.create(
            name="Test Extra", description="An optional service."
        )

    def test_page_displays_active_car_event_content_and_form(self):
        response = self.client.get(reverse("car_events:car_events"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Venue")
        self.assertContains(response, "Test Package")
        self.assertContains(response, "Coordination")
        self.assertContains(response, "Test Extra")
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

    def test_enquiry_submission_saves_extra_and_redirects(self):
        response = self.client.post(
            reverse("car_events:car_events"),
            {
                "full_name": "Test Customer",
                "email": "customer@example.com",
                "phone": "+230 5555 0101",
                "preferred_date": (timezone.localdate() + timedelta(days=1)).isoformat(),
                "expected_attendees": 30,
                "venue": self.venue.pk,
                "event_package": self.package.pk,
                "extras": [self.extra.pk],
                "message": "Please get in touch.",
            },
            follow=True,
        )

        self.assertEqual(response.redirect_chain, [(reverse("car_events:car_events"), 302)])
        enquiry = CarEventEnquiry.objects.get()
        self.assertEqual(enquiry.status, "new")
        self.assertEqual(enquiry.extras.get(), self.extra)
        self.assertContains(response, "submitted successfully")

    def test_inactive_options_are_not_available(self):
        self.venue.is_active = False
        self.venue.save()
        self.package.is_active = False
        self.package.save()
        self.extra.is_active = False
        self.extra.save()

        response = self.client.get(reverse("car_events:car_events"))
        form = response.context["form"]

        self.assertQuerySetEqual(form.fields["venue"].queryset, [])
        self.assertQuerySetEqual(form.fields["event_package"].queryset, [])
        self.assertQuerySetEqual(form.fields["extras"].queryset, [])

    def test_past_preferred_date_is_rejected(self):
        form = CarEventEnquiryForm(
            {
                "full_name": "Test Customer",
                "email": "customer@example.com",
                "phone": "+230 5555 0101",
                "preferred_date": (timezone.localdate() - timedelta(days=1)).isoformat(),
                "expected_attendees": 30,
                "venue": self.venue.pk,
                "event_package": self.package.pk,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("preferred_date", form.errors)

    def test_seed_command_is_idempotent(self):
        call_command("seed_car_events", verbosity=0)
        call_command("seed_car_events", verbosity=0)

        self.assertEqual(
            Venue.objects.filter(name__in=["SVICC", "Côte d'Or", "Tribeca Mall"]).count(),
            3,
        )
        self.assertEqual(
            EventPackage.objects.filter(
                name__in=["Starter Meet", "Premium Meet", "Festival Experience"]
            ).count(),
            3,
        )
        self.assertEqual(
            PackageFeature.objects.filter(
                event_package__name__in=[
                    "Starter Meet",
                    "Premium Meet",
                    "Festival Experience",
                ]
            ).count(),
            12,
        )
        self.assertEqual(
            ExtraService.objects.filter(
                name__in=["VIP Experience", "Show & Shine", "JDM Experience"]
            ).count(),
            3,
        )
