from datetime import date, time, timedelta
from decimal import Decimal
from itertools import count

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from booking.models import Booking

from authentication.admin_site import superadmin_site

from .admin import StaffAssignmentInline
from .models import StaffAssignment, StaffTask

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
