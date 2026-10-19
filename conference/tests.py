from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class ConferenceAccessTests(TestCase):
    def test_anonymous_user_sees_customer_access_notice(self):
        response = self.client.get(reverse("conference:conference"))

        self.assertContains(response, "Sign in to plan your event")
        self.assertContains(response, "Create an account")
        self.assertNotContains(response, 'class="conference-enquiry-form"')

    def test_customer_sees_booking_form(self):
        user = get_user_model().objects.create_user(
            username="conference-customer",
            email="conference-customer@example.com",
            password="test-password",
            account_type="customer",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("conference:conference"))

        self.assertContains(response, 'class="conference-enquiry-form"')
        self.assertNotContains(response, "Sign in to plan your event")

    def test_staff_user_sees_customer_access_notice(self):
        user = get_user_model().objects.create_user(
            username="conference-staff",
            email="conference-staff@example.com",
            password="test-password",
            account_type="staff",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("conference:conference"))

        self.assertContains(response, "customer accounts")
        self.assertNotContains(response, 'class="conference-enquiry-form"')
