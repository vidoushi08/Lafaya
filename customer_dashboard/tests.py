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

    def test_profile_links_and_event_themes_are_available(self):
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
            reverse("customer_dashboard:manage_profile"),
        )
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

    def test_customer_can_view_and_update_their_profile(self):
        user = get_user_model().objects.create_user(
            username="emma",
            email="emma@example.com",
            password="secure-pass-123",
            first_name="Emma",
            last_name="Clarke",
            account_type="customer",
            phone="+230 5123 4567",
            gender="female",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("customer_dashboard:manage_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Emma"')
        self.assertContains(response, 'value="emma@example.com"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

        response = self.client.post(
            reverse("customer_dashboard:manage_profile"),
            {
                "first_name": "Em",
                "last_name": "Clarke",
                "email": "EMMA@EXAMPLE.COM",
                "phone": "+230 5000 0000",
                "date_of_birth": "",
                "gender": "female",
                "address": "12 Oceanview Avenue",
                "city": "Grand Baie",
                "postal_code": "30501",
            },
        )

        self.assertRedirects(
            response,
            reverse("customer_dashboard:manage_profile"),
        )
        user.refresh_from_db()
        self.assertEqual(user.first_name, "Em")
        self.assertEqual(user.email, "emma@example.com")
        self.assertEqual(user.phone, "+230 5000 0000")
        self.assertEqual(user.postal_code, "30501")

    def test_profile_rejects_another_customers_email(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="emma",
            email="emma@example.com",
            password="secure-pass-123",
            account_type="customer",
            gender="female",
        )
        User.objects.create_user(
            username="olivia",
            email="olivia@example.com",
            password="secure-pass-123",
            account_type="customer",
            gender="female",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("customer_dashboard:manage_profile"),
            {
                "first_name": "",
                "last_name": "",
                "email": "OLIVIA@example.com",
                "phone": "",
                "date_of_birth": "",
                "gender": "female",
                "address": "",
                "city": "",
                "postal_code": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")
        user.refresh_from_db()
        self.assertEqual(user.email, "emma@example.com")

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get("/customer_dashboard/")

        self.assertRedirects(
            response,
            "/authentication/?next=/customer_dashboard/",
            fetch_redirect_response=False,
        )
