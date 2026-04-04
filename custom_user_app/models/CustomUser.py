from django.contrib.auth.hashers import make_password
from django.db import models
from django.contrib.auth.models import (
    AbstractUser,
    BaseUserManager,
)


class CustomUserManager(BaseUserManager):
    def create_user(
        self,
        username,
        email,
        password=None,
        **extra_fields,
    ):

        if not username:
            raise ValueError(
                "Имя пользователя (username) обязательно для заполнения"
            )
        if not email:
            raise ValueError(
                "Электронная почта (email) обязательна для заполнения"
            )

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)

        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        username,
        email,
        password=None,
        **extra_fields,
    ):

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(username, email, password, **extra_fields)


class CustomUser(AbstractUser):

    username = models.CharField(
        max_length=70,
        unique=True,
        verbose_name="Имя пользователя.",
    )
    email = models.EmailField(unique=True, verbose_name="Электронная почта")

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Создано"
    )

    updated_at = models.DateTimeField(auto_now=True, verbose_name="Изменено")
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email
