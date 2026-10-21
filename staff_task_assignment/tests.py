from datetime import date, time, timedelta
from decimal import Decimal
from itertools import count

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from booking.models import Booking

from authentication.admin_site import superadmin_site

from .admin import StaffAssignmentInline
from .models import StaffAssignment, StaffTask
from .queries import task_counts

_source_ids = count(1)


def make_booking(customer, status=Booking.Status.CONFIRMED, **overrides):
    fields = {
        "event_type": "Birthday",
        "event_name": "Family celebration",
        "event_date": date.today() + timedelta(days=30),
        "start_time": time(18, 0),
        "end_time": time(21, 0),
        "guests": 20,
        "venue_name": "Lagoon venue",
        "package_name": "Celebration package",
        "budget": Decimal("10000.00"),
        "estimated_total": Decimal("7000.00"),
        **overrides,
    }
    booking = Booking.objects.create(
        customer=customer,
        source_content_type=ContentType.objects.get_for_model(get_user_model()),
        source_object_id=next(_source_ids),
        **fields,
    )
    Booking.objects.filter(pk=booking.pk).update(status=status)
    booking.refresh_from_db()
    return booking


class StaffTestCase(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.customer = user_model.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="pass12345",
        )
        self.staff = user_model.objects.create_user(
            username="staff-one",
            email="staff1@example.com",
            password="pass12345",
            account_type="staff",
        )
        self.other_staff = user_model.objects.create_user(
            username="staff-two",
            email="staff2@example.com",
            password="pass12345",
            account_type="staff",
        )


class StaffAssignmentModelTests(StaffTestCase):
    def test_confirmed_booking_can_be_assigned(self):
        booking = make_booking(self.customer)

        assignment = StaffAssignment.objects.create(
            booking=booking, staff=self.staff, role="Decorator"
        )

        self.assertEqual(assignment.booking, booking)

    def test_unconfirmed_bookings_cannot_be_assigned(self):
        for status in (
            Booking.Status.PENDING,
            Booking.Status.APPROVED,
            Booking.Status.REJECTED,
            Booking.Status.COMPLETED,
            Booking.Status.CANCELLED,
        ):
            with self.subTest(status=status):
                booking = make_booking(self.customer, status=status)
                with self.assertRaises(ValidationError):
                    StaffAssignment.objects.create(
                        booking=booking, staff=self.staff, role="Decorator"
                    )

    def test_only_active_staff_accounts_can_be_assigned(self):
        booking = make_booking(self.customer)
        inactive = get_user_model().objects.create_user(
            username="inactive",
            email="inactive@example.com",
            password="pass12345",
            account_type="staff",
            is_active=False,
        )

        for user in (self.customer, inactive):
            with self.subTest(user=user.username):
                with self.assertRaises(ValidationError):
                    StaffAssignment.objects.create(
                        booking=booking, staff=user, role="Decorator"
                    )

    def test_staff_member_is_assigned_once_per_booking(self):
        booking = make_booking(self.customer)
        StaffAssignment.objects.create(booking=booking, staff=self.staff, role="A")

        with self.assertRaises(Exception):
            StaffAssignment.objects.create(booking=booking, staff=self.staff, role="B")

    def test_existing_assignment_can_be_edited_after_booking_completes(self):
        booking = make_booking(self.customer)
        assignment = StaffAssignment.objects.create(
            booking=booking, staff=self.staff, role="Decorator"
        )
        booking.mark_completed()

        assignment.role = "Lead decorator"
        assignment.save()

        assignment.refresh_from_db()
        self.assertEqual(assignment.role, "Lead decorator")

    def test_overlapping_assignments_on_same_day_are_reported(self):
        first = make_booking(self.customer)
        overlapping = make_booking(
            self.customer, event_date=first.event_date,
        )
        Booking.objects.filter(pk=overlapping.pk).update(
            start_time=time(20, 0), end_time=time(23, 0)
        )
        overlapping.refresh_from_db()
        StaffAssignment.objects.create(booking=first, staff=self.staff, role="A")
        second = StaffAssignment.objects.create(
            booking=overlapping, staff=self.staff, role="B"
        )

        self.assertEqual(
            [a.booking_id for a in second.conflicting_assignments()], [first.pk]
        )

    def test_back_to_back_and_other_staff_do_not_conflict(self):
        first = make_booking(self.customer)
        later = make_booking(self.customer, event_date=first.event_date)
        Booking.objects.filter(pk=later.pk).update(
            start_time=time(21, 0), end_time=time(23, 0)
        )
        later.refresh_from_db()
        StaffAssignment.objects.create(booking=first, staff=self.staff, role="A")
        same_staff = StaffAssignment.objects.create(
            booking=later, staff=self.staff, role="B"
        )
        other = StaffAssignment.objects.create(
            booking=first, staff=self.other_staff, role="C"
        )

        self.assertEqual(same_staff.conflicting_assignments(), [])
        self.assertEqual(other.conflicting_assignments(), [])


class StaffTaskModelTests(StaffTestCase):
    def setUp(self):
        super().setUp()
        self.booking = make_booking(self.customer)
        self.assignment = StaffAssignment.objects.create(
            booking=self.booking, staff=self.staff, role="Decorator"
        )

    def _task(self, **kwargs):
        return StaffTask.objects.create(
            assignment=self.assignment,
            title="Prepare balloons",
            due_date=self.booking.event_date,
            **kwargs,
        )

    def test_new_tasks_start_pending_with_medium_priority(self):
        task = self._task()

        self.assertEqual(task.status, StaffTask.Status.PENDING)
        self.assertEqual(task.priority, StaffTask.Priority.MEDIUM)

    def test_valid_transition_path_and_completed_timestamp(self):
        task = self._task()

        task.transition_to(StaffTask.Status.IN_PROGRESS)
        task.transition_to(StaffTask.Status.BLOCKED)
        task.transition_to(StaffTask.Status.IN_PROGRESS)
        self.assertIsNone(task.completed_at)
        task.transition_to(StaffTask.Status.COMPLETED)

        self.assertEqual(task.status, StaffTask.Status.COMPLETED)
        self.assertIsNotNone(task.completed_at)

    def test_invalid_transitions_are_rejected(self):
        task = self._task()
        invalid = (
            (StaffTask.Status.PENDING, StaffTask.Status.COMPLETED),
            (StaffTask.Status.PENDING, StaffTask.Status.BLOCKED),
            (StaffTask.Status.COMPLETED, StaffTask.Status.IN_PROGRESS),
        )

        for current, target in invalid:
            with self.subTest(current=current, target=target):
                StaffTask.objects.filter(pk=task.pk).update(status=current)
                task.refresh_from_db()
                with self.assertRaises(ValidationError):
                    task.transition_to(target)

    def test_tasks_are_locked_once_the_booking_is_closed(self):
        task = self._task()
        task.transition_to(StaffTask.Status.IN_PROGRESS)
        self.booking.mark_completed()

        with self.assertRaises(ValidationError):
            task.transition_to(StaffTask.Status.COMPLETED)
        self.assertEqual(task.allowed_next_statuses(), ())

    def test_new_tasks_cannot_be_added_to_a_closed_booking(self):
        self.booking.mark_cancelled()
        task = StaffTask(
            assignment=self.assignment,
            title="Late task",
            due_date=self.booking.event_date,
        )

        with self.assertRaises(ValidationError):
            task.full_clean()


class StaffAssignmentAdminTests(StaffTestCase):
    def setUp(self):
        super().setUp()
        self.admin_user = get_user_model().objects.create_superuser(
            username="boss",
            email="boss@example.com",
            password="pass12345",
        )
        self.client.force_login(self.admin_user)
        self.add_url = reverse("admin:staff_task_assignment_staffassignment_add")

    def _payload(self, booking, staff):
        return {
            "booking": booking.pk,
            "staff": staff.pk,
            "role": "Audio Lead",
            "tasks-TOTAL_FORMS": "0",
            "tasks-INITIAL_FORMS": "0",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
        }

    def test_admin_can_assign_staff_to_a_confirmed_booking(self):
        booking = make_booking(self.customer)

        response = self.client.post(self.add_url, self._payload(booking, self.staff))

        self.assertEqual(response.status_code, 302)
        assignment = StaffAssignment.objects.get()
        self.assertEqual(assignment.created_by, self.admin_user)

    def test_admin_cannot_assign_staff_to_an_unconfirmed_booking(self):
        booking = make_booking(self.customer, status=Booking.Status.APPROVED)

        response = self.client.post(self.add_url, self._payload(booking, self.staff))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(StaffAssignment.objects.exists())

    def test_overlap_shows_a_warning_but_still_saves(self):
        first = make_booking(self.customer)
        second = make_booking(self.customer, event_date=first.event_date)
        StaffAssignment.objects.create(booking=first, staff=self.staff, role="A")

        response = self.client.post(
            self.add_url, self._payload(second, self.staff), follow=True
        )

        self.assertEqual(StaffAssignment.objects.count(), 2)
        self.assertContains(response, "which overlaps this event")

    def test_booking_page_offers_assignment_only_when_confirmed(self):
        confirmed = make_booking(self.customer)
        approved = make_booking(self.customer, status=Booking.Status.APPROVED)
        inline = StaffAssignmentInline(Booking, superadmin_site)

        self.assertTrue(inline.has_add_permission(None, confirmed))
        self.assertFalse(inline.has_add_permission(None, approved))
        self.assertFalse(inline.has_change_permission(None, approved))
        page = self.client.get(
            reverse("admin:booking_booking_change", args=(confirmed.pk,))
        )
        self.assertContains(page, "staff_assignments-TOTAL_FORMS")

    def test_assignment_list_and_change_pages_render(self):
        booking = make_booking(self.customer)
        assignment = StaffAssignment.objects.create(
            booking=booking, staff=self.staff, role="Decorator"
        )
        StaffTask.objects.create(
            assignment=assignment, title="Set up", due_date=booking.event_date
        )

        list_response = self.client.get(
            reverse("admin:staff_task_assignment_staffassignment_changelist")
        )
        change_response = self.client.get(
            reverse(
                "admin:staff_task_assignment_staffassignment_change",
                args=(assignment.pk,),
            )
        )

        self.assertContains(list_response, booking.reference)
        self.assertContains(change_response, "Set up")


class StaffPortalViewTests(StaffTestCase):
    def setUp(self):
        super().setUp()
        self.booking = make_booking(self.customer, event_name="Garden party")
        self.assignment = StaffAssignment.objects.create(
            booking=self.booking, staff=self.staff, role="Decorator"
        )
        self.task = StaffTask.objects.create(
            assignment=self.assignment,
            title="Hang lanterns",
            due_date=timezone.localdate() + timedelta(days=1),
        )
        other_booking = make_booking(self.customer, event_name="Secret gala")
        other_assignment = StaffAssignment.objects.create(
            booking=other_booking, staff=self.other_staff, role="Lead"
        )
        self.other_task = StaffTask.objects.create(
            assignment=other_assignment,
            title="Other people's job",
            due_date=other_booking.event_date,
        )
        self.update_url = reverse(
            "staff_task_assignment:update_task", args=[self.task.pk]
        )
        self.client.force_login(self.staff)

    def test_task_list_only_shows_own_tasks(self):
        response = self.client.get(reverse("staff_task_assignment:tasks"))

        self.assertContains(response, "Hang lanterns")
        self.assertNotContains(response, "Other people")

    def test_task_list_search_and_status_filter(self):
        url = reverse("staff_task_assignment:tasks")

        self.assertContains(self.client.get(url, {"q": "lanterns"}), "Hang lanterns")
        self.assertNotContains(self.client.get(url, {"q": "zzz"}), "Hang lanterns")
        self.assertNotContains(
            self.client.get(url, {"status": "completed"}), "Hang lanterns"
        )

    def test_update_moves_task_forward_and_redirects(self):
        response = self.client.post(self.update_url, {"status": "in_progress"})

        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, StaffTask.Status.IN_PROGRESS)

    def test_update_rejects_invalid_transition(self):
        self.client.post(self.update_url, {"status": "completed"})

        self.task.refresh_from_db()
        self.assertEqual(self.task.status, StaffTask.Status.PENDING)

    def test_update_rejects_get(self):
        self.assertEqual(self.client.get(self.update_url).status_code, 405)

    def test_update_of_another_staff_members_task_is_404(self):
        url = reverse(
            "staff_task_assignment:update_task", args=[self.other_task.pk]
        )

        self.assertEqual(
            self.client.post(url, {"status": "in_progress"}).status_code, 404
        )
        self.other_task.refresh_from_db()
        self.assertEqual(self.other_task.status, StaffTask.Status.PENDING)

    def test_update_blocked_once_booking_is_closed(self):
        Booking.objects.filter(pk=self.booking.pk).update(
            status=Booking.Status.COMPLETED
        )

        self.client.post(self.update_url, {"status": "in_progress"})

        self.task.refresh_from_db()
        self.assertEqual(self.task.status, StaffTask.Status.PENDING)

    def test_next_redirect_ignores_external_urls(self):
        response = self.client.post(
            self.update_url, {"status": "in_progress", "next": "https://evil.example/"}
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(response["Location"].startswith("http"))

    def test_customer_and_anonymous_cannot_update(self):
        self.client.force_login(self.customer)
        self.assertEqual(
            self.client.post(self.update_url, {"status": "in_progress"}).status_code,
            403,
        )
        self.client.logout()
        self.assertEqual(
            self.client.post(self.update_url, {"status": "in_progress"}).status_code,
            302,
        )

    def test_dashboard_shows_real_counts(self):
        counts = task_counts(self.staff)

        self.assertEqual(counts["total"], 1)
        self.assertEqual(counts["pending"], 1)
        self.assertEqual(counts["due_soon"], 1)
        response = self.client.get(reverse("staff:staff"))
        self.assertEqual(response.context["counts"]["total"], 1)

    def test_history_lists_only_own_bookings_with_filters(self):
        url = reverse("staff_booking_history:history")

        response = self.client.get(url)
        self.assertContains(response, "Garden party")
        self.assertNotContains(response, "Secret gala")
        self.assertNotContains(
            self.client.get(url, {"status": "cancelled"}), "Garden party"
        )
        self.assertContains(
            self.client.get(url, {"q": self.booking.reference}), "Garden party"
        )
        self.assertNotContains(self.client.get(url, {"q": "nomatch"}), "Garden party")

    def test_history_paginates(self):
        for _ in range(11):
            StaffAssignment.objects.create(
                booking=make_booking(self.customer), staff=self.staff, role="Extra"
            )

        response = self.client.get(reverse("staff_booking_history:history"))

        self.assertEqual(response.context["page"].paginator.num_pages, 2)
        self.assertEqual(len(response.context["page"]), 10)

    def test_history_empty_state(self):
        self.client.force_login(self.customer.__class__.objects.create_user(
            username="newstaff", email="n@example.com", password="x-Pass-12345",
            account_type="staff",
        ))

        response = self.client.get(reverse("staff_booking_history:history"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["page"]), 0)


class ClosedEventDisplayTests(StaffTestCase):
    def setUp(self):
        super().setUp()
        self.booking = make_booking(self.customer, event_name="Done event")
        assignment = StaffAssignment.objects.create(
            booking=self.booking, staff=self.staff, role="Decorator"
        )
        self.task = StaffTask.objects.create(
            assignment=assignment, title="Still open", due_date=self.booking.event_date
        )
        self.task.transition_to(StaffTask.Status.IN_PROGRESS)
        self.client.force_login(self.staff)

    def test_completed_event_flags_tasks_and_leaves_status_unchanged(self):
        self.booking.mark_completed()

        response = self.client.get(reverse("staff_task_assignment:tasks"))

        self.assertContains(response, "Event completed")
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, StaffTask.Status.IN_PROGRESS)

    def test_cancelled_event_flags_tasks(self):
        self.booking.mark_cancelled()

        response = self.client.get(
            reverse(
                "staff_event_details:detail",
                kwargs={"assignment_id": self.task.assignment_id},
            )
        )

        self.assertContains(response, "Event cancelled")

    def test_open_event_has_no_badge(self):
        response = self.client.get(reverse("staff_task_assignment:tasks"))

        self.assertNotContains(response, "staff-event-closed-badge")

    def test_counts_ignore_tasks_on_closed_events(self):
        self.assertEqual(task_counts(self.staff)["in_progress"], 1)

        self.booking.mark_completed()

        counts = task_counts(self.staff)
        self.assertEqual(counts["in_progress"], 0)
        self.assertEqual(counts["total"], 1)
