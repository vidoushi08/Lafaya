from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from booking.models import Booking


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
        self.assertContains(response, "<strong>Manage Profile</strong>")
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

    def test_booking_history_offers_every_event_theme_without_existing_bookings(self):
        user = get_user_model().objects.create_user(
            username="emma",
            email="emma@example.com",
            password="test-password",
            account_type="customer",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("customer_dashboard:booking_history"))

        for event_type, label in (
            ("Seaside", "Seaside"),
            ("Conference", "Conference"),
            ("Wedding", "Wedding"),
            ("Birthday", "Birthday"),
            ("Car Event", "Car Meet"),
            ("Concert", "Concert"),
        ):
            with self.subTest(event_type=event_type):
                self.assertContains(response, f'<option value="{event_type}"')
                self.assertContains(response, f">{label}</option>")

    def test_booking_history_pagination_preserves_filters(self):
        user = get_user_model().objects.create_user(
            username="emma",
            email="emma@example.com",
            password="test-password",
            account_type="customer",
        )
        content_type = ContentType.objects.get_for_model(user)
        for index in range(11):
            Booking.objects.create(
                customer=user,
                source_content_type=content_type,
                source_object_id=10000 + index,
                event_type="Car Event",
                event_name=f"Car meetup {index}",
                event_date=date.today() + timedelta(days=30),
                start_time=time(18, 0),
                end_time=time(21, 0),
                guests=20,
                venue_name="Event venue",
                package_name="Event package",
                budget=Decimal("10000.00"),
                estimated_total=Decimal("7000.00"),
            )
        self.client.force_login(user)

        first_page = self.client.get(
            reverse("customer_dashboard:booking_history"),
            {"event_type": "Car Event", "status": "pending"},
        )

        self.assertContains(first_page, "page=2")
        self.assertContains(first_page, "event_type=Car+Event")
        self.assertContains(first_page, "status=pending")
        self.assertEqual(first_page.context["page_obj"].number, 1)

        second_page = self.client.get(
            reverse("customer_dashboard:booking_history"),
            {"event_type": "Car Event", "status": "pending", "page": 2},
        )
        self.assertEqual(second_page.context["page_obj"].number, 2)
        self.assertEqual(len(second_page.context["bookings"]), 1)

    def test_booking_history_displays_completed_and_cancelled_statuses_correctly(self):
        user = get_user_model().objects.create_user(
            username="emma",
            email="emma@example.com",
            password="test-password",
            account_type="customer",
        )
        content_type = ContentType.objects.get_for_model(user)
        common_fields = {
            "customer": user,
            "source_content_type": content_type,
            "event_type": "Car Event",
            "event_date": date.today() + timedelta(days=30),
            "start_time": time(18, 0),
            "end_time": time(21, 0),
            "guests": 20,
            "venue_name": "Event venue",
            "package_name": "Event package",
            "budget": Decimal("10000.00"),
            "estimated_total": Decimal("7000.00"),
        }
        Booking.objects.create(
            source_object_id=20001,
            event_name="Finished meetup",
            status=Booking.Status.COMPLETED,
            **common_fields,
        )
        Booking.objects.create(
            source_object_id=20002,
            event_name="Cancelled meetup",
            status=Booking.Status.CANCELLED,
            **common_fields,
        )
        Booking.objects.create(
            source_object_id=20003,
            event_name="Rejected meetup",
            status=Booking.Status.REJECTED,
            **common_fields,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("customer_dashboard:booking_history"))

        self.assertContains(response, "Finished meetup")
        self.assertContains(response, "Completed")
        self.assertContains(response, "Cancelled meetup")
        self.assertContains(response, "Cancelled")
        self.assertContains(response, "Rejected meetup")
        self.assertContains(response, "Rejected")
        self.assertEqual(response.context["completed_count"], 1)
        self.assertEqual(response.context["rejected_count"], 1)
        self.assertNotIn("cancelled_count", response.context)
        self.assertNotContains(response, 'option value="cancelled"')

        rejected_response = self.client.get(
            reverse("customer_dashboard:booking_history"),
            {"status": "rejected"},
        )
        self.assertEqual(rejected_response.context["page_obj"].paginator.count, 1)
        self.assertContains(rejected_response, "Rejected meetup")
        self.assertNotContains(rejected_response, "Cancelled meetup")

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
