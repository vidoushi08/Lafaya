import re
from datetime import date
from datetime import timedelta

from django.contrib.auth import authenticate, get_user_model
from django.core import mail
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone



class UserModelTests(TestCase):
	def test_identity_fields_are_required_and_customer_is_default(self):
		User = get_user_model()

		self.assertFalse(User._meta.get_field("username").blank)
		self.assertFalse(User._meta.get_field("email").blank)
		self.assertEqual(User._meta.get_field("account_type").default, "customer")

	def test_gender_choices_are_limited_to_male_and_female(self):
		gender_choices = {
			value for value, _label in get_user_model().Gender.choices
		}

		self.assertEqual(gender_choices, {"female", "male"})

	def test_account_type_is_only_for_customers_and_staff(self):
		account_type_values = {
			value for value, _label in get_user_model().AccountType.choices
		}

		self.assertEqual(account_type_values, {"customer", "staff"})

	def test_customer_creation_hashes_password_and_sets_account_type(self):
		user = get_user_model().objects.create_user(
			username="customer-one",
			email="customer@example.com",
			password="A-strong-test-password-42",
		)

		self.assertEqual(user.account_type, "customer")
		self.assertTrue(get_user_model()._meta.get_field("account_type").blank)
		self.assertTrue(user.check_password("A-strong-test-password-42"))
		self.assertNotEqual(user.password, "A-strong-test-password-42")
		self.assertEqual(
			authenticate(username="customer-one", password="A-strong-test-password-42"),
			user,
		)

	def test_shared_profile_fields_are_persisted(self):
		user = get_user_model().objects.create_user(
			username="profile-customer",
			email="profile@example.com",
			password="A-strong-test-password-42",
			phone="+230 5555 1234",
			date_of_birth=date(1995, 6, 15),
			gender="female",
			address="12 Example Street",
			city="Port Louis",
			postal_code="11302",
		)
		user.refresh_from_db()

		self.assertEqual(user.phone, "+230 5555 1234")
		self.assertEqual(user.date_of_birth, date(1995, 6, 15))
		self.assertEqual(user.gender, "female")
		self.assertEqual(user.address, "12 Example Street")
		self.assertEqual(user.city, "Port Louis")
		self.assertEqual(user.postal_code, "11302")

	def test_django_superuser_creation_remains_supported(self):
		user = get_user_model().objects.create_superuser(
			username="lafaya-admin",
			email="admin@example.com",
			password="Another-strong-test-password-42",
		)

		self.assertTrue(user.is_superuser)
		self.assertTrue(user.is_staff)
		self.assertTrue(user.is_active)
		self.assertEqual(user.account_type, "")

	def test_database_rejects_customer_type_for_superuser(self):
		user = get_user_model().objects.create_superuser(
			username="lafaya-admin",
			email="admin@example.com",
			password="C0mpl3x+event-planning-2026!",
		)

		with self.assertRaises(IntegrityError):
			with transaction.atomic():
				get_user_model().objects.filter(pk=user.pk).update(
					account_type="customer",
				)

	def test_database_rejects_case_insensitive_duplicate_email(self):
		User = get_user_model()
		User.objects.create_user(
			username="first-email",
			email="Unique.Email@example.com",
			password="C0mpl3x+event-planning-2026!",
		)

		with self.assertRaises(IntegrityError):
			with transaction.atomic():
				User.objects.create_user(
					username="second-email",
					email="unique.email@EXAMPLE.com",
					password="C0mpl3x+event-planning-2026!",
				)


class RegisterPageTests(TestCase):
	def registration_data(self, **overrides):
		data = {
			"first_name": "New",
			"last_name": "Customer",
			"username": "new-customer",
			"email": "customer@example.com",
			"phone": "+230 5555 1234",
			"date_of_birth": "1995-06-15",
			"gender": "female",
			"address": "12 Example Street",
			"city": "Port Louis",
			"password1": "C0mpl3x+event-planning-2026!",
			"password2": "C0mpl3x+event-planning-2026!",
		}
		data.update(overrides)
		return data

	def _create_verification_link(self):
		self.client.post(
			"/authentication/register/",
			self.registration_data(),
		)
		match = re.search(
			r"http://testserver(/authentication/verify/[^\s]+)",
			mail.outbox[0].body,
		)
		self.assertIsNotNone(match)
		return match.group(1)

	def _csrf_token_for_verification(self, client, verify_path):
		response = client.get(verify_path)
		self.assertEqual(response.status_code, 200)
		match = re.search(
			r'name="csrfmiddlewaretoken" value="([^"]+)"',
			response.content.decode(),
		)
		self.assertIsNotNone(match)
		return match.group(1)

	def test_register_page_shows_profile_fields_and_city_options(self):
		response = self.client.get("/authentication/register/")

		self.assertEqual(response.status_code, 200)
		for field_name in (
			"username",
			"first_name",
			"last_name",
			"email",
			"phone",
			"date_of_birth",
			"gender",
			"address",
			"city",
			"password1",
			"password2",
		):
			self.assertContains(response, f'name="{field_name}"')

		self.assertNotContains(response, 'name="postal_code"')
		self.assertContains(response, '<option value="Port Louis">Port Louis</option>')
		self.assertContains(response, 'name="gender" id="gender" autocomplete="sex" required')
		self.assertContains(response, "select gender")
		for value, label in get_user_model().Gender.choices:
			self.assertContains(response, f'<option value="{value}">{label}</option>')

	@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
	def test_registration_requires_email_verification_before_login(self):
		response = self.client.post(
			"/authentication/register/",
			self.registration_data(
				email="Customer@Example.com",
				account_type="staff",
			),
		)

		self.assertRedirects(response, reverse("authentication:verification_sent"))
		user = get_user_model().objects.get(username="new-customer")
		self.assertEqual(user.email, "customer@example.com")
		self.assertEqual(user.account_type, "customer")
		self.assertEqual(user.postal_code, "11302")
		self.assertTrue(user.check_password("C0mpl3x+event-planning-2026!"))
		self.assertNotEqual(user.password, "C0mpl3x+event-planning-2026!")
		self.assertFalse(user.is_active)
		self.assertEqual(len(mail.outbox), 1)
		self.assertIn(user.email, mail.outbox[0].to)

		login_response = self.client.post(
			reverse("authentication:login"),
			{
				"identifier": user.email,
				"password": "C0mpl3x+event-planning-2026!",
			},
		)
		self.assertContains(
			login_response,
			"Invalid email/username or password.",
		)
		self.assertNotIn("_auth_user_id", self.client.session)

		verify_match = re.search(
			r"http://testserver(/authentication/verify/[^\s]+)",
			mail.outbox[0].body,
		)
		self.assertIsNotNone(verify_match)
		verify_path = verify_match.group(1)
		verify_token = verify_path.rstrip("/").rsplit("/", 1)[-1]
		self.assertRegex(verify_token, r"^[0-9a-f]{30}$")
		verify_response = self.client.get(verify_path)
		self.assertContains(verify_response, "Confirm your email address")
		self.assertEqual(verify_response["Referrer-Policy"], "no-referrer")
		self.assertIn("no-store", verify_response["Cache-Control"])
		user.refresh_from_db()
		self.assertFalse(user.is_active)
		self.assertTrue(user.onboarding_token_hash)

		verify_response = self.client.post(verify_path)
		self.assertContains(verify_response, "email verified")
		user.refresh_from_db()
		self.assertTrue(user.is_active)
		self.assertEqual(user.onboarding_token_hash, "")

		second_verification = self.client.get(verify_path)
		self.assertContains(second_verification, "link unavailable")
		login_response = self.client.post(
			reverse("authentication:login"),
			{
				"identifier": user.email,
				"password": "C0mpl3x+event-planning-2026!",
			},
		)
		self.assertRedirects(login_response, "/customer_dashboard/")

	@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
	def test_verification_accepts_null_origin_only_for_same_origin_browser_post(self):
		verify_path = self._create_verification_link()
		client = Client(enforce_csrf_checks=True)
		csrf_token = self._csrf_token_for_verification(client, verify_path)

		response = client.post(
			verify_path,
			{"csrfmiddlewaretoken": csrf_token},
			HTTP_ORIGIN="null",
			HTTP_SEC_FETCH_SITE="same-origin",
		)

		self.assertContains(response, "email verified")
		user = get_user_model().objects.get(username="new-customer")
		self.assertTrue(user.is_active)

	@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
	def test_verification_still_requires_csrf_token_for_null_origin_post(self):
		verify_path = self._create_verification_link()
		client = Client(enforce_csrf_checks=True)
		client.get(verify_path)

		response = client.post(
			verify_path,
			HTTP_ORIGIN="null",
			HTTP_SEC_FETCH_SITE="same-origin",
		)

		self.assertEqual(response.status_code, 403)
		user = get_user_model().objects.get(username="new-customer")
		self.assertFalse(user.is_active)

	@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
	def test_verification_rejects_null_origin_cross_site_post(self):
		verify_path = self._create_verification_link()
		client = Client(enforce_csrf_checks=True)
		csrf_token = self._csrf_token_for_verification(client, verify_path)

		response = client.post(
			verify_path,
			{"csrfmiddlewaretoken": csrf_token},
			HTTP_ORIGIN="null",
			HTTP_SEC_FETCH_SITE="cross-site",
		)

		self.assertEqual(response.status_code, 403)
		user = get_user_model().objects.get(username="new-customer")
		self.assertFalse(user.is_active)

	@override_settings(
		EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
		ONBOARDING_EMAIL_RESEND_COOLDOWN=0,
	)
	def test_customer_resend_replaces_previous_verification_link(self):
		self.client.post(
			"/authentication/register/",
			self.registration_data(),
		)
		first_message = mail.outbox[0]
		first_match = re.search(
			r"http://testserver(/authentication/verify/[^\s]+)",
			first_message.body,
		)
		self.assertIsNotNone(first_match)

		response = self.client.post(
			reverse("authentication:resend_verification"),
			{"email": "CUSTOMER@example.com"},
		)
		self.assertRedirects(
			response,
			reverse("authentication:verification_resend_done"),
		)
		self.assertEqual(len(mail.outbox), 2)
		self.assertContains(
			self.client.get(reverse("authentication:verification_resend_done")),
			"If that address has a pending customer account",
		)
		self.assertContains(
			self.client.get(first_match.group(1)),
			"link unavailable",
		)

		second_match = re.search(
			r"http://testserver(/authentication/verify/[^\s]+)",
			mail.outbox[1].body,
		)
		self.assertIsNotNone(second_match)
		verify_path = second_match.group(1)
		self.assertContains(self.client.get(verify_path), "Confirm your email address")
		user = get_user_model().objects.get(username="new-customer")
		self.assertFalse(user.is_active)
		self.assertContains(self.client.post(verify_path), "email verified")

	@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
	def test_customer_verification_link_expires(self):
		self.client.post(
			"/authentication/register/",
			self.registration_data(),
		)
		user = get_user_model().objects.get(username="new-customer")
		match = re.search(
			r"http://testserver(/authentication/verify/[^\s]+)",
			mail.outbox[0].body,
		)
		self.assertIsNotNone(match)
		user.onboarding_token_created_at = timezone.now() - timedelta(days=2)
		user.save(update_fields=("onboarding_token_created_at",))

		response = self.client.get(match.group(1))
		self.assertContains(response, "link unavailable")
		self.client.post(match.group(1))
		user.refresh_from_db()
		self.assertFalse(user.is_active)

	@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
	def test_customer_verification_token_cannot_be_used_for_staff_invitation(self):
		self.client.post(
			"/authentication/register/",
			self.registration_data(),
		)
		match = re.search(
			r"/authentication/verify/([^/]+)/([^/\s]+)",
			mail.outbox[0].body,
		)
		self.assertIsNotNone(match)
		staff_invitation_path = reverse(
			"authentication:staff_invitation",
			kwargs={"uidb64": match.group(1), "token": match.group(2)},
		)

		response = self.client.get(staff_invitation_path)
		self.assertContains(response, "invitation link unavailable")
		user = get_user_model().objects.get(username="new-customer")
		self.assertFalse(user.is_active)

	@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
	def test_customer_verification_token_is_invalidated_when_email_changes(self):
		self.client.post(
			"/authentication/register/",
			self.registration_data(),
		)
		match = re.search(
			r"http://testserver(/authentication/verify/[^\s]+)",
			mail.outbox[0].body,
		)
		self.assertIsNotNone(match)
		user = get_user_model().objects.get(username="new-customer")
		user.email = "updated-customer@example.com"
		user.save(update_fields=("email",))

		response = self.client.get(match.group(1))
		self.assertContains(response, "link unavailable")
		self.assertFalse(get_user_model().objects.get(pk=user.pk).is_active)

	@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
	def test_resend_verification_response_is_generic_and_cooldown_limits_mail(self):
		self.client.post(
			"/authentication/register/",
			self.registration_data(),
		)
		initial_mail_count = len(mail.outbox)

		pending_response = self.client.post(
			reverse("authentication:resend_verification"),
			{"email": "customer@example.com"},
		)
		unknown_response = self.client.post(
			reverse("authentication:resend_verification"),
			{"email": "unknown@example.com"},
		)

		self.assertRedirects(
			pending_response,
			reverse("authentication:verification_resend_done"),
		)
		self.assertRedirects(
			unknown_response,
			reverse("authentication:verification_resend_done"),
		)
		self.assertEqual(len(mail.outbox), initial_mail_count)

	def test_registration_rejects_duplicate_email_case_insensitively(self):
		get_user_model().objects.create_user(
			username="existing-customer",
			email="customer@example.com",
			password="C0mpl3x+existing-password-2026!",
		)

		response = self.client.post(
			"/authentication/register/",
			self.registration_data(email="CUSTOMER@example.com"),
		)

		self.assertEqual(response.status_code, 200)
		self.assertIn("email", response.context["form"].errors)
		self.assertEqual(get_user_model().objects.count(), 1)

	def test_registration_rejects_mismatched_passwords(self):
		response = self.client.post(
			"/authentication/register/",
			self.registration_data(password2="Different+password-2026!"),
		)

		self.assertEqual(response.status_code, 200)
		self.assertIn("password2", response.context["form"].errors)
		self.assertEqual(get_user_model().objects.count(), 0)

	def test_registration_uses_configured_password_validators(self):
		response = self.client.post(
			"/authentication/register/",
			self.registration_data(
				password1="password",
				password2="password",
			),
		)

		self.assertEqual(response.status_code, 200)
		self.assertIn("password2", response.context["form"].errors)
		self.assertEqual(get_user_model().objects.count(), 0)

	def test_registration_rejects_unknown_city(self):
		response = self.client.post(
			"/authentication/register/",
			self.registration_data(city="Not a city"),
		)

		self.assertEqual(response.status_code, 200)
		self.assertIn("city", response.context["form"].errors)
		self.assertEqual(get_user_model().objects.count(), 0)


class LoginFlowTests(TestCase):
	def create_account(self, account_type="customer", **kwargs):
		return get_user_model().objects.create_user(
			username=kwargs.pop("username", f"{account_type}-user"),
			email=kwargs.pop("email", f"{account_type}@example.com"),
			password="C0mpl3x+event-planning-2026!",
			account_type=account_type,
			**kwargs,
		)

	def test_customer_login_uses_email_and_redirects_to_customer_dashboard(self):
		user = self.create_account(email="customer@example.com")

		response = self.client.post(
			"/authentication/",
			{
				"identifier": "CUSTOMER@example.com",
				"password": "C0mpl3x+event-planning-2026!",
			},
		)

		self.assertRedirects(response, "/customer_dashboard/")
		self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

	def test_customer_login_accepts_username(self):
		self.create_account(username="customer-username")

		response = self.client.post(
			"/authentication/",
			{
				"identifier": "customer-username",
				"password": "C0mpl3x+event-planning-2026!",
			},
		)

		self.assertRedirects(response, "/customer_dashboard/")

	def test_superadmin_login_accepts_username(self):
		get_user_model().objects.create_superuser(
			username="lafaya-admin",
			email="admin@example.com",
			password="C0mpl3x+event-planning-2026!",
		)

		response = self.client.post(
			"/authentication/",
			{
				"identifier": "lafaya-admin",
				"password": "C0mpl3x+event-planning-2026!",
			},
		)

		self.assertRedirects(response, "/admin/")

	def test_staff_login_redirects_to_staff_dashboard(self):
		self.create_account(
			account_type="staff",
			email="assigned-staff@example.com",
		)

		response = self.client.post(
			"/authentication/",
			{
				"identifier": "assigned-staff@example.com",
				"password": "C0mpl3x+event-planning-2026!",
			},
		)

		self.assertRedirects(response, "/staff/")

	def test_superadmin_login_redirects_to_superadmin_admin(self):
		get_user_model().objects.create_superuser(
			username="lafaya-admin",
			email="admin@example.com",
			password="C0mpl3x+event-planning-2026!",
		)

		response = self.client.post(
			"/authentication/",
			{
				"identifier": "admin@example.com",
				"password": "C0mpl3x+event-planning-2026!",
			},
		)

		self.assertRedirects(response, "/admin/")

	def test_invalid_credentials_show_generic_error_and_do_not_log_in(self):
		self.create_account()

		response = self.client.post(
			"/authentication/",
			{"identifier": "customer@example.com", "password": "incorrect-password"},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Invalid email/username or password.")
		self.assertNotIn("_auth_user_id", self.client.session)

	def test_unknown_email_uses_the_same_generic_error(self):
		response = self.client.post(
			"/authentication/",
			{"identifier": "unknown@example.com", "password": "incorrect-password"},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Invalid email/username or password.")
		self.assertNotIn("_auth_user_id", self.client.session)

	def test_safe_next_url_is_honored_and_external_next_is_ignored(self):
		self.create_account()
		credentials = {
			"identifier": "customer@example.com",
			"password": "C0mpl3x+event-planning-2026!",
		}

		safe_response = self.client.post(
			"/authentication/?next=/contact/",
			credentials,
		)
		self.assertRedirects(safe_response, "/contact/")

		self.client.logout()
		external_response = self.client.post(
			"/authentication/",
			{**credentials, "next": "https://example.com/"},
		)
		self.assertRedirects(external_response, "/customer_dashboard/")

	def test_unchecked_remember_me_expires_when_browser_closes(self):
		self.create_account()

		self.client.post(
			"/authentication/",
			{
				"identifier": "customer@example.com",
				"password": "C0mpl3x+event-planning-2026!",
			},
		)

		self.assertTrue(self.client.session.get_expire_at_browser_close())

	def test_checked_remember_me_uses_default_session_expiry(self):
		self.create_account()

		self.client.post(
			"/authentication/",
			{
				"identifier": "customer@example.com",
				"password": "C0mpl3x+event-planning-2026!",
				"remember": "on",
			},
		)

		self.assertGreater(self.client.session.get_expiry_age(), 0)


class SuperAdminAccessTests(TestCase):
	def test_superadmin_can_access_admin_and_manage_users(self):
		superadmin = get_user_model().objects.create_superuser(
			username="lafaya-admin",
			email="admin@example.com",
			password="C0mpl3x+event-planning-2026!",
		)
		self.client.force_login(superadmin)

		response = self.client.get("/admin/authentication/user/")

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Users")
		self.assertContains(response, "Superadmin")
		add_response = self.client.get("/admin/authentication/user/add/")
		self.assertEqual(add_response.status_code, 200)
		self.assertContains(add_response, 'name="account_type"')

	def test_admin_login_accepts_superadmin_email(self):
		get_user_model().objects.create_superuser(
			username="lafaya-admin",
			email="admin@example.com",
			password="C0mpl3x+event-planning-2026!",
		)

		response = self.client.post(
			"/admin/login/",
			{
				"username": "admin@example.com",
				"password": "C0mpl3x+event-planning-2026!",
				"next": "/admin/",
			},
		)

		self.assertRedirects(response, "/admin/")
		self.assertIn("_auth_user_id", self.client.session)

	@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
	def test_superadmin_creates_staff_account_with_setup_invitation(self):
		superadmin = get_user_model().objects.create_superuser(
			username="lafaya-admin",
			email="admin@example.com",
			password="C0mpl3x+event-planning-2026!",
		)
		self.client.force_login(superadmin)
		add_page = self.client.get("/admin/authentication/user/add/")
		self.assertEqual(add_page.status_code, 200)
		self.assertNotContains(add_page, 'name="password1"')
		self.assertNotContains(add_page, 'name="password2"')

		response = self.client.post(
			"/admin/authentication/user/add/",
			{
				"username": "assigned-staff",
				"email": "assigned-staff@example.com",
				"account_type": "staff",
			},
		)

		self.assertEqual(response.status_code, 302)
		staff = get_user_model().objects.get(username="assigned-staff")
		self.assertEqual(staff.account_type, "staff")
		self.assertFalse(staff.is_staff)
		self.assertFalse(staff.is_superuser)
		self.assertFalse(staff.is_active)
		self.assertFalse(staff.has_usable_password())
		self.assertEqual(len(mail.outbox), 1)
		self.assertIn(staff.email, mail.outbox[0].to)

		invitation_match = re.search(
			r"http://testserver(/authentication/staff-invitation/[^\s]+)",
			mail.outbox[0].body,
		)
		self.assertIsNotNone(invitation_match)
		invitation_path = invitation_match.group(1)
		token_parts = re.search(
			r"/authentication/staff-invitation/([^/]+)/([^/\s]+)",
			invitation_path,
		)
		self.assertIsNotNone(token_parts)
		customer_verification_path = reverse(
			"authentication:verify_email",
			kwargs={
				"uidb64": token_parts.group(1),
				"token": token_parts.group(2),
			},
		)
		self.assertContains(
			self.client.get(customer_verification_path),
			"link unavailable",
		)
		response = self.client.get(invitation_path)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "set your password")
		self.assertEqual(response["Referrer-Policy"], "no-referrer")
		self.assertIn("no-store", response["Cache-Control"])
		staff.refresh_from_db()
		self.assertFalse(staff.is_active)
		self.assertFalse(staff.has_usable_password())
		self.assertTrue(staff.onboarding_token_hash)
		response = self.client.post(
			invitation_path,
			{
				"new_password1": "C0mpl3x+staff-password-2026!",
				"new_password2": "C0mpl3x+staff-password-2026!",
			},
		)
		self.assertRedirects(
			response,
			reverse("authentication:staff_invitation_complete"),
		)

		staff.refresh_from_db()
		self.assertTrue(staff.is_active)
		self.assertTrue(staff.has_usable_password())
		self.assertTrue(staff.check_password("C0mpl3x+staff-password-2026!"))
		self.assertEqual(staff.email, "assigned-staff@example.com")
		self.assertEqual(staff.username, "assigned-staff")
		self.assertEqual(staff.account_type, "staff")
		self.assertEqual(staff.onboarding_token_hash, "")
		self.assertContains(
			self.client.get(invitation_path),
			"invitation link unavailable",
		)

		self.client.logout()
		login_response = self.client.post(
			reverse("authentication:login"),
			{
				"identifier": staff.username,
				"password": "C0mpl3x+staff-password-2026!",
			},
		)
		self.assertRedirects(login_response, "/staff/")

	@override_settings(
		EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
		ONBOARDING_EMAIL_RESEND_COOLDOWN=0,
	)
	def test_superadmin_can_resend_pending_staff_invitation(self):
		superadmin = get_user_model().objects.create_superuser(
			username="lafaya-admin",
			email="admin@example.com",
			password="C0mpl3x+event-planning-2026!",
		)
		self.client.force_login(superadmin)
		self.client.post(
			"/admin/authentication/user/add/",
			{
				"username": "assigned-staff",
				"email": "assigned-staff@example.com",
				"account_type": "staff",
			},
		)
		staff = get_user_model().objects.get(username="assigned-staff")
		first_match = re.search(
			r"http://testserver(/authentication/staff-invitation/[^\s]+)",
			mail.outbox[0].body,
		)
		self.assertIsNotNone(first_match)

		response = self.client.post(
			"/admin/authentication/user/",
			{
				"action": "resend_staff_invitation",
				"_selected_action": [str(staff.pk)],
				"index": "0",
			},
			follow=True,
		)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(mail.outbox), 2)
		self.assertContains(
			self.client.get(first_match.group(1)),
			"invitation link unavailable",
		)

		second_match = re.search(
			r"http://testserver(/authentication/staff-invitation/[^\s]+)",
			mail.outbox[1].body,
		)
		self.assertIsNotNone(second_match)
		self.assertContains(
			self.client.get(second_match.group(1)),
			"set your password",
		)

	@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
	def test_expired_staff_invitation_cannot_activate_account(self):
		superadmin = get_user_model().objects.create_superuser(
			username="lafaya-admin",
			email="admin@example.com",
			password="C0mpl3x+event-planning-2026!",
		)
		self.client.force_login(superadmin)
		self.client.post(
			"/admin/authentication/user/add/",
			{
				"username": "expired-staff",
				"email": "expired-staff@example.com",
				"account_type": "staff",
			},
		)
		staff = get_user_model().objects.get(username="expired-staff")
		match = re.search(
			r"http://testserver(/authentication/staff-invitation/[^\s]+)",
			mail.outbox[0].body,
		)
		self.assertIsNotNone(match)
		staff.onboarding_token_created_at = timezone.now() - timedelta(days=4)
		staff.save(update_fields=("onboarding_token_created_at",))

		response = self.client.get(match.group(1))
		self.assertContains(response, "invitation link unavailable")
		staff.refresh_from_db()
		self.assertFalse(staff.is_active)

	def test_admin_display_uses_superuser_flag_for_superadmin_role(self):
		superadmin = get_user_model().objects.create_superuser(
			username="lafaya-admin",
			email="admin@example.com",
			password="C0mpl3x+event-planning-2026!",
		)
		customer = get_user_model().objects.create_user(
			username="customer-user",
			email="customer@example.com",
			password="C0mpl3x+event-planning-2026!",
		)
		self.client.force_login(superadmin)

		response = self.client.post(
			f"/admin/authentication/user/{customer.pk}/change/",
			{
				"username": customer.username,
				"email": customer.email,
				"first_name": "",
				"last_name": "",
				"date_joined_0": customer.date_joined.strftime("%Y-%m-%d"),
				"date_joined_1": customer.date_joined.strftime("%H:%M:%S"),
				"is_active": "on",
				"is_staff": "on",
				"is_superuser": "on",
				"account_type": "",
				"groups": [],
				"user_permissions": [],
				"phone": "",
				"date_of_birth": "",
				"gender": "female",
				"address": "",
				"city": "",
				"postal_code": "",
			},
		)

		self.assertEqual(response.status_code, 302)
		customer.refresh_from_db()
		self.assertTrue(customer.is_superuser)
		self.assertEqual(customer.account_type, "")
		list_response = self.client.get("/admin/authentication/user/")
		self.assertContains(list_response, "Superadmin")

	def test_staff_admin_flag_does_not_grant_superadmin_area_access(self):
		staff = get_user_model().objects.create_user(
			username="staff-user",
			email="staff@example.com",
			password="C0mpl3x+event-planning-2026!",
			account_type="staff",
			is_staff=True,
		)
		self.client.force_login(staff)

		response = self.client.get("/admin/")

		self.assertEqual(response.status_code, 302)
		self.assertIn("/admin/login/", response["Location"])


class AccountAreaAccessTests(TestCase):
	def create_account(self, account_type):
		return get_user_model().objects.create_user(
			username=f"{account_type}-access",
			email=f"{account_type}-access@example.com",
			password="C0mpl3x+event-planning-2026!",
			account_type=account_type,
		)

	def test_anonymous_visitors_are_redirected_from_account_areas(self):
		protected_paths = (
			"/customer_dashboard/",
			"/staff/",
			"/staff-booking-history/",
			"/staff-profile/",
			"/staff-task-assignment/",
			"/staff-event-details/floral-styling-review/",
		)

		for path in protected_paths:
			with self.subTest(path=path):
				response = self.client.get(path)
				self.assertEqual(response.status_code, 302)
				self.assertTrue(response["Location"].startswith("/authentication/?next="))

	def test_customer_and_staff_can_only_access_their_own_account_areas(self):
		customer = self.create_account("customer")
		staff = self.create_account("staff")
		staff_paths = (
			"/staff/",
			"/staff-booking-history/",
			"/staff-profile/",
			"/staff-task-assignment/",
			"/staff-event-details/floral-styling-review/",
		)

		self.client.force_login(customer)
		self.assertEqual(self.client.get("/customer_dashboard/").status_code, 200)
		for path in staff_paths:
			with self.subTest(account="customer", path=path):
				self.assertEqual(self.client.get(path).status_code, 403)

		self.client.force_login(staff)
		self.assertEqual(self.client.get("/customer_dashboard/").status_code, 403)
		for path in staff_paths:
			with self.subTest(account="staff", path=path):
				self.assertEqual(self.client.get(path).status_code, 200)

	def test_superuser_is_separate_from_customer_and_staff_portals(self):
		superuser = get_user_model().objects.create_superuser(
			username="portal-admin",
			email="portal-admin@example.com",
			password="C0mpl3x+event-planning-2026!",
		)
		self.client.force_login(superuser)

		for path in (
			"/customer_dashboard/",
			"/staff/",
			"/staff-booking-history/",
			"/staff-profile/",
			"/staff-task-assignment/",
			"/staff-event-details/floral-styling-review/",
		):
			with self.subTest(path=path):
				self.assertEqual(self.client.get(path).status_code, 403)


class AccountPasswordTests(TestCase):
	password = "C0mpl3x+event-planning-2026!"
	new_password = "An0ther+strong-password-2026!"

	def create_account(self, **kwargs):
		return get_user_model().objects.create_user(
			username=kwargs.pop("username", "password-user"),
			email=kwargs.pop("email", "password@example.com"),
			password=self.password,
			**kwargs,
		)

	def test_logout_requires_post_and_clears_authenticated_session(self):
		user = self.create_account()
		self.client.force_login(user)

		get_response = self.client.get(reverse("authentication:logout"))
		self.assertEqual(get_response.status_code, 405)
		self.assertIn("_auth_user_id", self.client.session)

		post_response = self.client.post(reverse("authentication:logout"))
		self.assertRedirects(post_response, reverse("authentication:login"))
		self.assertNotIn("_auth_user_id", self.client.session)

	def test_authenticated_user_can_change_password_without_losing_session(self):
		user = self.create_account()
		self.client.force_login(user)

		response = self.client.post(
			reverse("authentication:password_change"),
			{
				"old_password": self.password,
				"new_password1": self.new_password,
				"new_password2": self.new_password,
			},
		)

		self.assertRedirects(
			response,
			reverse("authentication:password_change_done"),
		)
		user.refresh_from_db()
		self.assertTrue(user.check_password(self.new_password))
		self.assertEqual(
			self.client.get(reverse("authentication:password_change_done")).status_code,
			200,
		)

	@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
	def test_password_reset_is_case_insensitive_and_preserves_staff_identity(self):
		staff = self.create_account(
			username="assigned-staff",
			email="Assigned.Staff@example.com",
			account_type="staff",
		)
		original_email = staff.email

		response = self.client.post(
			reverse("authentication:password_reset"),
			{"email": "ASSIGNED.STAFF@EXAMPLE.COM"},
		)
		self.assertRedirects(response, reverse("authentication:password_reset_done"))
		self.assertEqual(len(mail.outbox), 1)
		self.assertIn(original_email, mail.outbox[0].to)

		reset_match = re.search(
			r"http://testserver(/authentication/password/reset/[^\s]+)",
			mail.outbox[0].body,
		)
		self.assertIsNotNone(reset_match)
		reset_path = reset_match.group(1)
		confirm_response = self.client.get(reset_path, follow=True)
		self.assertTrue(confirm_response.context["validlink"])
		confirm_path = confirm_response.request["PATH_INFO"]
		confirm_response = self.client.post(
			confirm_path,
			{
				"new_password1": self.new_password,
				"new_password2": self.new_password,
			},
		)

		self.assertRedirects(
			confirm_response,
			reverse("authentication:password_reset_complete"),
		)
		staff.refresh_from_db()
		self.assertTrue(staff.check_password(self.new_password))
		self.assertEqual(staff.email, original_email)
		self.assertEqual(staff.account_type, "staff")
		self.assertIsNotNone(staff.password_reset_at)
		self.assertEqual(len(mail.outbox), 2)
		self.assertIn(original_email, mail.outbox[1].to)
		expired_response = self.client.get(reset_path, follow=True)
		self.assertFalse(expired_response.context["validlink"])

	@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
	def test_password_reset_response_does_not_reveal_unknown_email(self):
		response = self.client.post(
			reverse("authentication:password_reset"),
			{"email": "not-registered@example.com"},
		)

		self.assertRedirects(response, reverse("authentication:password_reset_done"))
		self.assertEqual(len(mail.outbox), 0)

	@override_settings(
		DEBUG=True,
		EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
	)
	def test_customer_password_reset_link_opens_password_form(self):
		customer = self.create_account(
			username="reset-customer",
			email="reset-customer@example.com",
			account_type="customer",
		)

		with self.assertLogs("authentication.forms", level="WARNING") as logs:
			response = self.client.post(
				reverse("authentication:password_reset"),
				{"email": customer.email},
			)
		self.assertRedirects(response, reverse("authentication:password_reset_done"))
		self.assertEqual(len(mail.outbox), 1)
		self.assertIn("token_length=39", logs.output[0])

		reset_match = re.search(
			r"http://testserver(/authentication/password/reset/[^\s]+)",
			mail.outbox[0].body,
		)
		self.assertIsNotNone(reset_match)
		confirm_response = self.client.get(reset_match.group(1), follow=True)

		self.assertTrue(confirm_response.context["validlink"])
		self.assertContains(confirm_response, "choose a new password")
