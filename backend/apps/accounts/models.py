from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
import uuid

class UserManager(models.Manager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email address is required.")

        email = email.lower().strip()

        user = self.model(
            email=email,
            **extra_fields,
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(
            email=email,
            password=password,
            **extra_fields,
        )

    def get_by_natural_key(self, email):
        return self.get(email__iexact=email)

class User(AbstractBaseUser, PermissionsMixin):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    email = models.EmailField(
        unique=True,
        db_index=True,
    )

    first_name = models.CharField(
        max_length=100,
    )

    last_name = models.CharField(
        max_length=100,
    )

    is_active = models.BooleanField(
        default=True,
    )

    is_staff = models.BooleanField(
        default=False,
    )

    password_reset_required = models.BooleanField(
        default=False,
    )

    date_joined = models.DateTimeField(
        auto_now_add=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"

    def __str__(self):
        return self.email