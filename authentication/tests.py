from datetime import date

from django.contrib.auth import authenticate, get_user_model
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

	def test_customer_creation_hashes_password_and_sets_account_type(self):
		user = get_user_model().objects.create_user(
			username="customer-one",
			email="customer@example.com",
			password="A-strong-test-password-42",
		)

		self.assertEqual(user.account_type, "customer")
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
