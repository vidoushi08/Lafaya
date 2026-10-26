from datetime import date, time, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from authentication.admin_site import superadmin_site
from birthday.admin import BirthdayBookingRequestAdmin
from birthday.models import BirthdayBookingRequest
from booking.models import Booking
from car_events.admin import CarEventBookingRequestAdmin
from car_events.models import CarEventBookingRequest
from conference.admin import ConferenceBookingRequestAdmin
from conference.models import ConferenceBookingRequest
from payments.models import Payment
from seaside.admin import SeasideBookingRequestAdmin
from seaside.models import SeasideBookingRequest, SeasidePackage, SeasideVenue


User = get_user_model()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PaymentWorkflowTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="test-password",
            first_name="Casey",
            last_name="Customer",
        )
        self.client.force_login(self.customer)
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="test-password",
        )
        venue = SeasideVenue.objects.create(
            name="Lagoon venue",
            location="West coast",
            description="Venue description",
            price=Decimal("1000.00"),
            capacity=100,
        )
        package = SeasidePackage.objects.create(
            name="Celebration package",
            tagline="A package",
            price=Decimal("3000.00"),
            min_guests=1,
            max_guests=100,
        )
        self.request = SeasideBookingRequest.objects.create(
            customer=self.customer,
            first_name="Casey",
            last_name="Customer",
            email=self.customer.email,
            phone="555-0100",
            event_date=timezone.localdate() + timedelta(days=30),
            start_time=time(17, 0),
            end_time=time(20, 0),
            expected_guests=20,
            venue=venue,
            package=package,
            budget=Decimal("10000.00"),
            estimated_total=Decimal("7000.00"),
        )
        self.booking = Booking.objects.get(
            source_object_id=self.request.pk,
            source_content_type__app_label="seaside",
            source_content_type__model="seasidebookingrequest",
        )
        self.payment = self.booking.payment

    def approve_booking(self):
        self.payment.amount = Decimal("7000.00")
        self.payment.save(update_fields=("amount",))
        self.booking.approve()

    def test_request_creates_one_canonical_booking_and_payment(self):
        self.assertEqual(Booking.objects.filter(customer=self.customer).count(), 1)
        self.assertEqual(self.booking.event_type, "Seaside")
        self.assertEqual(self.booking.guests, 20)
        self.assertEqual(self.payment.amount, Decimal("7000.00"))
        self.assertEqual(self.payment.status, Payment.Status.AWAITING_PAYMENT)

    def test_demo_card_payment_confirms_booking_without_card_details(self):
        self.approve_booking()
        detail_url = reverse("payments:payment_detail", args=(self.booking.pk,))
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Credit / Debit Card")
        self.assertContains(response, "card details stay in your browser")
        self.assertContains(response, "not sent to or stored by Lafaya")
        self.assertContains(response, 'id="demoCardNumber"')
        self.assertContains(response, 'placeholder="4242 4242 4242 4242"')
        self.assertContains(response, "use 4242 4242 4242 4242")
        self.assertContains(response, 'id="demoCardholderName"')
        self.assertContains(response, 'id="demoCardExpiry"')
        self.assertContains(response, 'id="demoCardCvv"')
        self.assertContains(response, "No real charge will be made.")
        self.assertContains(response, reverse("payments:demo_payment", args=(self.booking.pk,)))
        self.assertNotContains(response, "name=\"demoCardNumber\"")
        self.assertNotContains(response, "name=\"demoCardholderName\"")
        self.assertNotContains(response, "name=\"demoCardExpiry\"")
        self.assertNotContains(response, "name=\"demoCardCvv\"")
        self.assertNotContains(response, "transaction_reference")

        response = self.client.post(
            reverse("payments:demo_payment", args=(self.booking.pk,))
        )
        self.assertRedirects(response, detail_url)
        self.payment.refresh_from_db()
        self.booking.refresh_from_db()
        self.request.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.DEMO_PAID)
        self.assertIsNotNone(self.payment.paid_at)
        self.assertIsNotNone(self.payment.receipt_email_sent_at)
        self.assertEqual(self.booking.status, Booking.Status.CONFIRMED)
        self.assertIsNotNone(self.booking.confirmed_at)
        self.assertEqual(self.request.status, "approved")
        self.assertEqual(len(mail.outbox), 1)
        receipt = mail.outbox[0]
        self.assertEqual(receipt.to, [self.customer.email])
        self.assertIn("payment successful", receipt.subject.lower())
        self.assertIn(self.booking.reference, receipt.body)
        self.assertIn("MUR 7,000.00", receipt.body)
        self.assertIn("No real card was charged", receipt.body)
        self.assertNotIn("demoCardNumber", receipt.body)
        self.assertNotIn("CVV", receipt.body)

        response = self.client.get(detail_url)
        self.assertContains(response, "Demo payment completed")
        self.assertContains(response, "No real card was charged")
        self.assertContains(response, f"Receipt email sent to {self.customer.email}")

    def test_demo_payment_is_post_only_and_only_for_approved_bookings(self):
        demo_url = reverse("payments:demo_payment", args=(self.booking.pk,))
        response = self.client.get(demo_url)
        self.assertEqual(response.status_code, 405)

        response = self.client.post(demo_url)
        self.assertRedirects(
            response,
            reverse("payments:payment_detail", args=(self.booking.pk,)),
        )
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.AWAITING_PAYMENT)

    def test_demo_payment_cannot_be_repeated_to_reconfirm_booking(self):
        self.approve_booking()
        self.payment.complete_demo_payment()
        self.payment.refresh_from_db()
        first_paid_at = self.payment.paid_at
        self.assertFalse(self.payment.complete_demo_payment())
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.paid_at, first_paid_at)

    def test_cancelled_booking_cannot_be_paid_or_show_payment_checkout(self):
        Booking.objects.filter(pk=self.booking.pk).update(
            status=Booking.Status.CANCELLED
        )
        detail_url = reverse("payments:payment_detail", args=(self.booking.pk,))

        response = self.client.get(detail_url)

        self.assertContains(response, "This booking was cancelled.")
        self.assertNotContains(response, "Payment will be available after Lafaya approves")
        self.assertNotContains(response, reverse("payments:demo_payment", args=(self.booking.pk,)))
        with self.assertRaises(ValidationError):
            self.payment.complete_demo_payment()

    def test_completed_booking_displays_completed_instead_of_confirmed(self):
        self.approve_booking()
        self.payment.complete_demo_payment()
        self.booking.mark_completed()

        response = self.client.get(
            reverse("payments:payment_detail", args=(self.booking.pk,))
        )

        self.assertContains(response, "This event is completed.")
        self.assertNotContains(response, "Your booking is confirmed.")
        self.assertContains(response, "Demo payment completed.")

    def test_failed_receipt_can_be_retried_without_charging_demo_payment_twice(self):
        self.approve_booking()
        demo_url = reverse("payments:demo_payment", args=(self.booking.pk,))
        with patch(
            "payments.notifications.send_mail",
            side_effect=[OSError("mail service unavailable"), 1],
        ) as send_mail:
            response = self.client.post(demo_url)
            self.assertRedirects(
                response,
                reverse("payments:payment_detail", args=(self.booking.pk,)),
            )
            self.payment.refresh_from_db()
            self.booking.refresh_from_db()
            first_paid_at = self.payment.paid_at
            self.assertEqual(self.payment.status, Payment.Status.DEMO_PAID)
            self.assertIsNone(self.payment.receipt_email_sent_at)
            self.assertEqual(self.booking.status, Booking.Status.CONFIRMED)

            response = self.client.post(demo_url)
            self.assertRedirects(
                response,
                reverse("payments:payment_detail", args=(self.booking.pk,)),
            )
            self.payment.refresh_from_db()
            self.assertEqual(self.payment.paid_at, first_paid_at)
            self.assertIsNotNone(self.payment.receipt_email_sent_at)
            self.assertEqual(send_mail.call_count, 2)
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.get(
            reverse("payments:payment_detail", args=(self.booking.pk,))
        )
        self.assertContains(response, f"Receipt email sent to {self.customer.email}")

    def test_successful_demo_payment_sends_only_one_receipt(self):
        self.approve_booking()
        demo_url = reverse("payments:demo_payment", args=(self.booking.pk,))
        self.client.post(demo_url)
        self.client.post(demo_url)
        self.assertEqual(len(mail.outbox), 1)

    def test_demo_payment_rejects_nonpositive_amount(self):
        self.payment.amount = Decimal("0.00")
        self.payment.save(update_fields=("amount",))
        self.booking.status = Booking.Status.APPROVED
        self.booking.save(update_fields=("status",))
        with self.assertRaises(ValidationError):
            self.payment.complete_demo_payment()
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.AWAITING_PAYMENT)

    def test_customer_cannot_access_another_customers_payment(self):
        other_customer = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="test-password",
        )
        other_booking = Booking.objects.create(
            customer=other_customer,
            source_content_type=self.booking.source_content_type,
            source_object_id=999,
            event_type="Birthday",
            event_date=date.today() + timedelta(days=40),
            start_time=time(18, 0),
            end_time=time(21, 0),
            guests=10,
            venue_name="Other venue",
            package_name="Other package",
            budget=Decimal("5000.00"),
            estimated_total=Decimal("4000.00"),
        )
        response = self.client.get(
            reverse("payments:payment_detail", args=(other_booking.pk,))
        )
        self.assertEqual(response.status_code, 404)

    def test_booking_pages_require_customer_login(self):
        self.client.logout()
        response = self.client.get(reverse("payments:payments"))
        self.assertRedirects(
            response,
            f"{reverse('authentication:login')}?next={reverse('payments:payments')}",
        )

    def test_approval_email_failure_does_not_undo_saved_decision(self):
        self.approve_booking()
        with patch("payments.notifications.send_mail", side_effect=OSError("mail down")):
            from payments.notifications import send_booking_decision

            delivered = send_booking_decision(
                self.booking,
                True,
                "https://example.test/payments/1/",
            )
        self.assertFalse(delivered)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.APPROVED)

    def test_event_request_admin_queues_expose_approval_actions(self):
        for model, model_admin_class in (
            (SeasideBookingRequest, SeasideBookingRequestAdmin),
            (BirthdayBookingRequest, BirthdayBookingRequestAdmin),
            (CarEventBookingRequest, CarEventBookingRequestAdmin),
            (ConferenceBookingRequest, ConferenceBookingRequestAdmin),
        ):
            with self.subTest(model=model):
                self.assertIsInstance(
                    superadmin_site._registry[model],
                    model_admin_class,
                )
                self.assertIn("approve_booking_requests", model_admin_class.actions)
                self.assertIn("reject_booking_requests", model_admin_class.actions)

        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("admin:seaside_seasidebookingrequest_changelist")
        )
        self.assertContains(response, "Approve selected booking requests")

    def test_admin_can_approve_request_from_its_request_queue(self):
        self.payment.amount = Decimal("7000.00")
        self.payment.save(update_fields=("amount",))
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin:seaside_seasidebookingrequest_changelist"),
            {
                "action": "approve_booking_requests",
                "_selected_action": [str(self.request.pk)],
                "index": "0",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.booking.refresh_from_db()
        self.request.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.APPROVED)
        self.assertEqual(self.request.status, "approved")
        self.assertEqual(len(mail.outbox), 1)

    def test_admin_approval_still_requires_a_positive_payment_amount(self):
        self.payment.amount = Decimal("0.00")
        self.payment.save(update_fields=("amount",))
        self.client.force_login(self.admin)
        self.client.post(
            reverse("admin:seaside_seasidebookingrequest_changelist"),
            {
                "action": "approve_booking_requests",
                "_selected_action": [str(self.request.pk)],
                "index": "0",
            },
        )
        self.booking.refresh_from_db()
        self.request.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.PENDING)
        self.assertEqual(self.request.status, "pending")
