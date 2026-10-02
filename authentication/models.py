from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
	class AccountType(models.TextChoices):
		CUSTOMER = "customer", "Customer"
		STAFF = "staff", "Staff"

	class Gender(models.TextChoices):
		FEMALE = "female", "Female"
		MALE = "male", "Male"
		NON_BINARY = "non_binary", "Non-binary"
		PREFER_NOT_TO_SAY = "prefer_not_to_say", "Prefer not to say"

	email = models.EmailField(unique=True)
	account_type = models.CharField(
		max_length=10,
		choices=AccountType.choices,
		default=AccountType.CUSTOMER,
	)
	phone = models.CharField(max_length=32, blank=True)
	date_of_birth = models.DateField(null=True, blank=True)
	gender = models.CharField(max_length=24, choices=Gender.choices, blank=True)
	address = models.CharField(max_length=255, blank=True)
	city = models.CharField(max_length=100, blank=True)
	postal_code = models.CharField(max_length=20, blank=True)

	REQUIRED_FIELDS = ["email"]
