from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class StaffEventDetailsRouteTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            username="staff",
            email="staff@example.com",
            password="test-password",
            account_type="staff",
        )
        self.client.force_login(self.staff)

    def test_known_task_slug_renders_matching_detail(self):
        response = self.client.get(
            reverse(
                "staff_event_details:detail",
                kwargs={"task_id": "guest-list-check-in"},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Leah&#x27;s Birthday Bash")

    def test_unknown_task_slug_returns_not_found(self):
        response = self.client.get(
            reverse(
                "staff_event_details:detail",
                kwargs={"task_id": "unknown-task"},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_anonymous_visitor_is_redirected_to_login(self):
        self.client.logout()

        response = self.client.get(
            reverse(
                "staff_event_details:detail",
                kwargs={"task_id": "guest-list-check-in"},
            )
        )

        self.assertEqual(response.status_code, 302)
