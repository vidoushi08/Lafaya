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
		self.assertContains(response, 'name="gender" autocomplete="sex" required')
		self.assertNotContains(response, "select gender")
		for value, label in get_user_model().Gender.choices:
			self.assertContains(response, f'<option value="{value}">{label}</option>')
