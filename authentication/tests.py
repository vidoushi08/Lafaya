from datetime import date

from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase


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
			password="A-strong-test-password-42",
		)

		with self.assertRaises(IntegrityError):
			with transaction.atomic():
				get_user_model().objects.filter(pk=user.pk).update(
					account_type="customer",
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

	def test_registration_creates_a_customer_with_a_hashed_password(self):
		response = self.client.post(
			"/authentication/register/",
			self.registration_data(
				email="Customer@Example.com",
				account_type="staff",
			),
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.redirect_chain, [("/authentication/", 302)])
		user = get_user_model().objects.get(username="new-customer")
		self.assertEqual(user.email, "customer@example.com")
		self.assertEqual(user.account_type, "customer")
		self.assertEqual(user.postal_code, "11302")
		self.assertTrue(user.check_password("C0mpl3x+event-planning-2026!"))
		self.assertNotEqual(user.password, "C0mpl3x+event-planning-2026!")
		self.assertContains(response, "Your customer account has been created.")

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
				"email": "CUSTOMER@example.com",
				"password": "C0mpl3x+event-planning-2026!",
			},
		)

		self.assertRedirects(response, "/customer_dashboard/")
		self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

	def test_staff_login_redirects_to_staff_dashboard(self):
		self.create_account(
			account_type="staff",
			email="assigned-staff@example.com",
		)

		response = self.client.post(
			"/authentication/",
			{
				"email": "assigned-staff@example.com",
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
				"email": "admin@example.com",
				"password": "C0mpl3x+event-planning-2026!",
			},
		)

		self.assertRedirects(response, "/admin/")

	def test_invalid_credentials_show_generic_error_and_do_not_log_in(self):
		self.create_account()

		response = self.client.post(
			"/authentication/",
			{"email": "customer@example.com", "password": "incorrect-password"},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Invalid email address or password.")
		self.assertNotIn("_auth_user_id", self.client.session)

	def test_unknown_email_uses_the_same_generic_error(self):
		response = self.client.post(
			"/authentication/",
			{"email": "unknown@example.com", "password": "incorrect-password"},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Invalid email address or password.")
		self.assertNotIn("_auth_user_id", self.client.session)

	def test_safe_next_url_is_honored_and_external_next_is_ignored(self):
		self.create_account()
		credentials = {
			"email": "customer@example.com",
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
				"email": "customer@example.com",
				"password": "C0mpl3x+event-planning-2026!",
			},
		)

		self.assertTrue(self.client.session.get_expire_at_browser_close())

	def test_checked_remember_me_uses_default_session_expiry(self):
		self.create_account()

		self.client.post(
			"/authentication/",
			{
				"email": "customer@example.com",
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

	def test_superadmin_can_create_a_staff_account_without_admin_site_access(self):
		superadmin = get_user_model().objects.create_superuser(
			username="lafaya-admin",
			email="admin@example.com",
			password="C0mpl3x+event-planning-2026!",
		)
		self.client.force_login(superadmin)

		response = self.client.post(
			"/admin/authentication/user/add/",
			{
				"username": "assigned-staff",
				"email": "assigned-staff@example.com",
				"account_type": "staff",
				"password1": "C0mpl3x+staff-password-2026!",
				"password2": "C0mpl3x+staff-password-2026!",
			},
		)

		self.assertEqual(response.status_code, 302)
		staff = get_user_model().objects.get(username="assigned-staff")
		self.assertEqual(staff.account_type, "staff")
		self.assertFalse(staff.is_staff)
		self.assertFalse(staff.is_superuser)
		self.assertTrue(staff.check_password("C0mpl3x+staff-password-2026!"))

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
