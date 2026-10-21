from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from booking.models import Booking
from staff_task_assignment.models import StaffAssignment, StaffTask
from staff_task_assignment.tests import StaffTestCase, make_booking


class StaffEventDetailsTests(StaffTestCase):
    def setUp(self):
        super().setUp()
        self.booking = make_booking(
            self.customer,
            client_name="Jane Client",
            client_email="jane@example.com",
            client_phone="5555 1234",
            services_summary="Live band, Photography",
        )
        self.assignment = StaffAssignment.objects.create(
            booking=self.booking, staff=self.staff, role="Audio Lead"
        )
        self.task = StaffTask.objects.create(
            assignment=self.assignment,
            title="Set up speakers",
            due_date=timezone.localdate() + timedelta(days=5),
        )
        self.url = reverse(
            "staff_event_details:detail", kwargs={"assignment_id": self.assignment.pk}
        )

    def test_shows_snapshot_role_services_and_tasks(self):
        self.client.force_login(self.staff)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        for text in (
            "Family celebration",
            "Lagoon venue",
            "Jane Client",
            "jane@example.com",
            "Audio Lead",
            "Live band",
            "Photography",
            "Set up speakers",
        ):
            self.assertContains(response, text)

    def test_other_staff_member_gets_404(self):
        self.client.force_login(self.other_staff)

        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_unknown_assignment_returns_404(self):
        self.client.force_login(self.staff)
        url = reverse("staff_event_details:detail", kwargs={"assignment_id": 99999})

        self.assertEqual(self.client.get(url).status_code, 404)

    def test_customer_is_forbidden(self):
        self.client.force_login(self.customer)

        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_anonymous_visitor_is_redirected_to_login(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_closed_booking_hides_update_buttons(self):
        Booking.objects.filter(pk=self.booking.pk).update(
            status=Booking.Status.COMPLETED
        )
        self.client.force_login(self.staff)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            reverse("staff_task_assignment:update_task", args=[self.task.pk]),
        )
