from django.contrib.auth.models import AbstractUser
from django.db import models

from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    @property
    def is_source_system(self):
        return hasattr(self, "source_system")

    @property
    def is_end_user(self):
        return not hasattr(self, "source_system")


class PhoneNumber(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="phone_numbers")
    phone_number = PhoneNumberField()

    def __repr__(self):
        return f"<PhoneNumber: id {self.pk} for {self.user}>"

    def __str__(self):
        return f"PhoneNumber {self.phone_number} for {self.user}"
