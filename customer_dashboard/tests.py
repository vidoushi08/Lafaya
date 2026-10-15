from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class CustomerDashboardTests(TestCase):
    def test_customer_sees_dashboard_with_their_account_details(self):
        user = get_user_model().objects.create_user(
            username="emma",
            email="emma@example.com",
            password="correct-horse-battery-staple",
            first_name="Emma",
            last_name="Clarke",
            account_type="customer",
            phone="+230 5123 4567",
            address="12 Oceanview Avenue",
            city="Grand Baie",
            gender="female",
        )
        self.client.force_login(user)

        response = self.client.get("/customer_dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Emma Clarke")
        self.assertContains(response, "emma@example.com")
        self.assertContains(response, "+230 5123 4567")
        self.assertContains(response, "12 Oceanview Avenue")
        self.assertContains(response, "Grand Baie, Mauritius")
        self.assertContains(response, "customer_dashboard/css/dashboard.css")
        self.assertContains(response, "authentication/password/change/")

    def test_profile_controls_are_inert_and_event_themes_are_available(self):
        user = get_user_model().objects.create_user(
            username="emma",
            email="emma@example.com",
            password="correct-horse-battery-staple",
            account_type="customer",
            gender="female",
        )
        self.client.force_login(user)

        response = self.client.get("/customer_dashboard/")

        self.assertContains(
            response,
            '<button class="customer-manage-button" type="button" '
            'aria-disabled="true">Manage Profile</button>',
        )
        self.assertNotContains(response, 'href="#personal-details"')
        self.assertContains(response, "customer-action-create-menu")
        for route_name in (
            "car_events:car_events",
            "wedding:wedding",
            "concert:concert",
            "birthday:birthday",
            "conference:conference",
            "seaside:seaside",
        ):
            self.assertContains(response, reverse(route_name))

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get("/customer_dashboard/")

        self.assertRedirects(
            response,
            "/authentication/?next=/customer_dashboard/",
            fetch_redirect_response=False,
        )
