from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class CustomerDashboardTests(TestCase):
    def test_customer_navigation_links_dashboard_and_keeps_home_available(self):
        user = get_user_model().objects.create_user(
            username="emma",
            email="emma@example.com",
            password="C0mpl3x+event-planning-2026!",
            account_type="customer",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("homepage:homepage"))

        self.assertContains(
            response,
            f'href="{reverse("customer_dashboard:customer_dashboard")}"',
        )
        self.assertContains(response, "> Customer Dashboard</a>")
        self.assertContains(response, f'href="{reverse("homepage:homepage")}"')
        self.assertContains(response, "> Home</a>")
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

    def test_customer_navigation_is_visible_on_the_dashboard(self):
        user = get_user_model().objects.create_user(
            username="emma",
            email="emma@example.com",
            password="C0mpl3x+event-planning-2026!",
            account_type="customer",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("customer_dashboard:customer_dashboard"))

        self.assertContains(response, "> Customer Dashboard</a>")
        self.assertContains(response, "> Home</a>")
        self.assertLess(
            response.content.index(b"> Contact</a>"),
            response.content.index(b"> Customer Dashboard</a>"),
        )

    def test_staff_navigation_links_to_staff_dashboard(self):
        staff_user = get_user_model().objects.create_user(
            username="staff-member",
            email="staff@example.com",
            password="C0mpl3x+event-planning-2026!",
            account_type="staff",
        )
        self.client.force_login(staff_user)

        response = self.client.get(reverse("homepage:homepage"))

        self.assertContains(response, f'href="{reverse("staff:staff")}"')
        self.assertContains(response, "> Staff Dashboard</a>")
        self.assertNotContains(response, "> Customer Dashboard</a>")

        dashboard_response = self.client.get(reverse("staff:staff"))
        self.assertContains(dashboard_response, "> Staff Dashboard</a>")
        self.assertContains(dashboard_response, "> Home</a>")

    def test_superadmin_navigation_links_to_admin(self):
        admin_user = get_user_model().objects.create_superuser(
            username="lafaya-admin",
            email="admin@example.com",
            password="C0mpl3x+event-planning-2026!",
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse("homepage:homepage"))

        self.assertContains(response, f'href="{reverse("admin:index")}"')
        self.assertContains(response, "> Admin Dashboard</a>")
        self.assertNotContains(response, "> Customer Dashboard</a>")
        self.assertNotContains(response, "> Staff Dashboard</a>")

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
        self.assertNotContains(response, '<h1>Customer Dashboard</h1>')
        self.assertNotContains(response, 'class="customer-logout-button"')
        self.assertNotContains(response, 'class="customer-sidebar-brand"')
        self.assertNotContains(response, 'class="customer-password-link"')
        self.assertNotContains(response, "Change password</span>")
        self.assertContains(response, 'class="navbar-auth"')
        self.assertContains(response, "Log out</button>")

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

    def test_dashboard_booking_history_links_open_customer_history(self):
        user = get_user_model().objects.create_user(
            username="emma",
            email="emma@example.com",
            password="test-password",
            account_type="customer",
        )
        self.client.force_login(user)

        history_url = reverse("customer_dashboard:booking_history")
        response = self.client.get(reverse("customer_dashboard:customer_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.count(f'href="{history_url}"'.encode()), 2)
        self.assertNotContains(response, f'href="{reverse("booking:booking")}"')

        history_response = self.client.get(history_url)
        self.assertEqual(history_response.status_code, 200)
        self.assertContains(history_response, "All bookings")

    def test_customer_sidebar_dropdown_is_shared_across_account_pages(self):
        user = get_user_model().objects.create_user(
            username="emma",
            email="emma@example.com",
            password="test-password",
            account_type="customer",
        )
        self.client.force_login(user)

        for route_name in (
            "customer_dashboard:customer_dashboard",
            "customer_dashboard:booking_history",
            "customer_dashboard:manage_profile",
        ):
            with self.subTest(route=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'class="customer-create-menu" open')
                for event_route in (
                    "car_events:car_events",
                    "wedding:wedding",
                    "concert:concert",
                    "birthday:birthday",
                    "conference:conference",
                    "seaside:seaside",
                ):
                    self.assertContains(response, reverse(event_route))

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
        self.assertContains(response, 'class="customer-password-link"')
        self.assertContains(response, 'class="fa-solid fa-lock"')
        self.assertContains(
            response,
            f'href="{reverse("authentication:password_change")}"',
        )

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
