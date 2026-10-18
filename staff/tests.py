from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class StaffDashboardTests(TestCase):
    def test_staff_dashboard_uses_shared_navbar_for_branding_and_logout(self):
        staff_user = get_user_model().objects.create_user(
            username="staff-member",
            email="staff@example.com",
            password="C0mpl3x+event-planning-2026!",
            account_type="staff",
            is_active=True,
            first_name="Ravi",
            last_name="Khan",
            phone="+230 5555 9876",
            address="12 Garden Lane",
            city="Curepipe",
        )
        self.client.force_login(staff_user)

        response = self.client.get(reverse("staff:staff"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "> Staff Dashboard</a>")
        self.assertEqual(response.content.count(b'class="lafaya-logo"'), 1)
        self.assertEqual(response.content.count(b'Log out</button>'), 1)
        self.assertNotContains(response, "STAFF DASHBOARD")
        self.assertNotContains(response, 'class="staff-logout-btn"')
        self.assertContains(response, "Ravi Khan")
        self.assertContains(response, "staff@example.com")
        self.assertContains(response, "Username: staff-member")
        self.assertContains(response, "+230 5555 9876")
        self.assertContains(response, "12 Garden Lane")
        self.assertNotContains(response, "Emma Watson")
        self.assertContains(
            response,
            f'href="{reverse("authentication:password_change")}"',
        )
        self.assertContains(response, 'class="staff-password-link"')
        self.assertContains(response, "Change password</span>")

    def test_staff_portal_subpages_use_shared_logo_and_logout(self):
        staff_user = get_user_model().objects.create_user(
            username="staff-member",
            email="staff@example.com",
            password="C0mpl3x+event-planning-2026!",
            account_type="staff",
            is_active=True,
        )
        self.client.force_login(staff_user)
        portal_pages = (
            ("staff_booking_history:history", {}),
            ("staff_task_assignment:tasks", {}),
            ("staff_profile:profile", {}),
            (
                "staff_event_details:detail",
                {"task_id": "floral-styling-review"},
            ),
        )

        for route_name, kwargs in portal_pages:
            with self.subTest(route=route_name):
                response = self.client.get(reverse(route_name, kwargs=kwargs))

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content.count(b'class="lafaya-logo"'), 1)
                self.assertEqual(response.content.count(b'Log out</button>'), 1)
                if route_name == "staff_task_assignment:tasks":
                    self.assertContains(response, "staff-member")
                    self.assertNotContains(response, "Emma Watson")
                if route_name == "staff_profile:profile":
                    self.assertContains(response, 'class="staff-profile-password-link"')
                    self.assertContains(response, "Change password</span>")
                else:
                    self.assertNotContains(
                        response,
                        reverse("authentication:password_change").encode(),
                    )
                    self.assertNotContains(response, "Change password")


class StaffProfileTests(TestCase):
    def setUp(self):
        self.staff_user = get_user_model().objects.create_user(
            username="assigned-staff",
            email="assigned.staff@example.com",
            password="test-password-123",
            account_type="staff",
            is_active=True,
            first_name="Asha",
            last_name="Ramdass",
            phone="+230 5555 1111",
            address="5 Palm Street",
            city="Quatre Bornes",
            postal_code="72201",
            gender="female",
        )
        self.client.force_login(self.staff_user)
        self.profile_url = reverse("staff_profile:profile")

    def test_profile_shows_logged_in_staff_details(self):
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Username: assigned-staff")
        self.assertContains(response, 'value="Asha"')
        self.assertContains(response, 'value="Ramdass"')
        self.assertContains(
            response,
            '<input class="staff-profile-readonly" type="email" value="assigned.staff@example.com" autocomplete="email" readonly aria-readonly="true">',
        )
        self.assertNotContains(response, 'name="email"')
        self.assertContains(response, 'value="+230 5555 1111"')
        self.assertNotContains(response, "Emma")
        self.assertNotContains(response, "Watson")

    def test_staff_can_save_profile_fields(self):
        response = self.client.post(
            self.profile_url,
            {
                "first_name": "Asha",
                "last_name": "Ramdass",
                "phone": "+230 5555 2222",
                "date_of_birth": "1998-05-14",
                "gender": "female",
                "address": "22 New Road",
                "city": "Rose Hill",
                "postal_code": "71301",
            },
        )

        self.assertRedirects(response, self.profile_url)
        self.staff_user.refresh_from_db()
        self.assertEqual(self.staff_user.email, "assigned.staff@example.com")
        self.assertEqual(self.staff_user.phone, "+230 5555 2222")
        self.assertEqual(self.staff_user.date_of_birth.isoformat(), "1998-05-14")
        self.assertEqual(self.staff_user.address, "22 New Road")
        self.assertEqual(self.staff_user.city, "Rose Hill")
        self.assertEqual(self.staff_user.postal_code, "71301")

    def test_staff_cannot_change_email_by_posting_a_modified_value(self):
        response = self.client.post(
            self.profile_url,
            {
                "first_name": "Asha",
                "last_name": "Ramdass",
                "email": "changed@example.com",
                "phone": "+230 5555 1111",
                "date_of_birth": "",
                "gender": "female",
                "address": "5 Palm Street",
                "city": "Quatre Bornes",
                "postal_code": "72201",
            },
        )

        self.assertRedirects(response, self.profile_url)
        self.staff_user.refresh_from_db()
        self.assertEqual(self.staff_user.email, "assigned.staff@example.com")
