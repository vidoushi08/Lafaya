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
        self.assertContains(response, "authentication/password/change/")
        self.assertNotContains(response, '<h1>Customer Dashboard</h1>')
        self.assertNotContains(response, 'class="customer-logout-button"')
        self.assertNotContains(response, 'class="customer-sidebar-brand"')
        self.assertContains(response, 'class="customer-password-link"')
        self.assertContains(response, "Change password</span>")
        self.assertContains(response, 'class="navbar-auth"')
        self.assertContains(response, "Log out</button>")

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
