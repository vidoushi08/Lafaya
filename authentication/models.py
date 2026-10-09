from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower


class User(AbstractUser):
	class AccountType(models.TextChoices):
		CUSTOMER = "customer", "Customer"
		STAFF = "staff", "Staff"

	class Gender(models.TextChoices):
		FEMALE = "female", "Female"
		MALE = "male", "Male"

	email = models.EmailField(blank=False)
	account_type = models.CharField(
		max_length=10,
		choices=AccountType.choices,
		default=AccountType.CUSTOMER,
		blank=True,
	)
	phone = models.CharField(max_length=32, blank=True)
	date_of_birth = models.DateField(null=True, blank=True)
	gender = models.CharField(max_length=24, choices=Gender.choices)
	address = models.CharField(max_length=255, blank=True)
	city = models.CharField(max_length=100, blank=True)
	postal_code = models.CharField(max_length=20, blank=True)
	password_reset_at = models.DateTimeField(null=True, blank=True)

	REQUIRED_FIELDS = ["email"]

	class Meta(AbstractUser.Meta):
		constraints = [
			models.UniqueConstraint(
				Lower("email"),
				name="user_email_case_insensitive_unique",
			),
			models.CheckConstraint(
				condition=(
					Q(is_superuser=True, account_type="")
					| Q(
						is_superuser=False,
						account_type__in=["customer", "staff"],
					)
				),
				name="user_account_type_matches_superuser",
			),
		]

	def save(self, *args, **kwargs):
		if self.is_superuser:
			self.account_type = ""
		elif not self.account_type:
			self.account_type = self.AccountType.CUSTOMER
		super().save(*args, **kwargs)
