from django.contrib.auth.hashers import make_password
from django.db import models
from django.contrib.auth.models import (
    AbstractUser,
    BaseUserManager,
)


class CustomUserManager(BaseUserManager):
    """
    Кастомный менеджер пользователей.
    Расширяет BaseUserManager для создания пользователей и суперпользователей
    с дополнительной валидацией обязательных полей и настройкой прав доступа.
    """

    def create_user(
        self,
        username,
        email,
        password=None,
        **extra_fields,
    ):
        """
        Создаёт и сохраняет обычного пользователя с username, email и паролем.

        Args:
            username (str): Имя пользователя. Должно быть уникальным.
            email (str): Электронная почта пользователя. Должна быть уникальной.
            password (str, optional): Пароль пользователя (может быть None).
            **extra_fields: Дополнительные поля пользователя.

        Returns:
            CustomUser: Экземпляр созданного пользователя.

        Raises:
            ValueError: Если username или email не указаны.
        """
        if not username:
            raise ValueError(
                "Имя пользователя (username) обязательно для заполнения"  # Проверка наличия username
            )
        if not email:
            raise ValueError(
                "Электронная почта (email) обязательна для заполнения"  # Проверка наличия email
            )

        email = self.normalize_email(email)  # Нормализация email (приведение к нижнему регистру)
        user = self.model(username=username, email=email, **extra_fields)  # Создание экземпляра модели пользователя

        user.password = make_password(password)  # Хеширование пароля перед сохранением
        user.save(using=self._db)  # Сохранение пользователя в базе данных
        return user

    def create_superuser(
        self,
        username,
        email,
        password=None,
        **extra_fields,
    ):
        """
        Создаёт суперпользователя с правами администратора.
        Устанавливает дополнительные флаги is_staff, is_superuser и is_active в True,
        затем вызывает метод create_user для создания пользователя.

        Args:
            username (str): Имя пользователя.
            email (str): Электронная почта пользователя.
            password (str, optional): Пароль пользователя.
            **extra_fields: Дополнительные поля пользователя.

        Returns:
            CustomUser: Экземпляр созданного суперпользователя.
        """
        # Установка прав доступа для суперпользователя
        extra_fields.setdefault("is_staff", True)  # Доступ к админ‑панели
        extra_fields.setdefault("is_superuser", True)  # Полные права администратора
        extra_fields.setdefault("is_active", True)  # Аккаунт активен

        return self.create_user(username, email, password, **extra_fields)  # Создание суперпользователя через create_user



class CustomUser(AbstractUser):
    """
    Кастомная модель пользователя.
    Расширяет AbstractUser, заменяя стандартную модель Django.
    Добавляет временные метки создания и обновления, настраивает обязательные поля.
    """

    """Поле имени пользователя: уникальное, максимум 70 символов."""
    username = models.CharField(
        max_length=70,
        unique=True,
        verbose_name="Имя пользователя.",
    )

    """Поле электронной почты: уникальное, валидируется как email."""
    email = models.EmailField(unique=True, verbose_name="Электронная почта")

    """Дата и время создания записи (устанавливается один раз при создании)."""
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Создано"
    )

    """Дата и время последнего обновления записи (автоматически обновляется при сохранении)."""
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Изменено")

    USERNAME_FIELD = "username"  # Поле, используемое для аутентификации (вместо email)
    REQUIRED_FIELDS = ["email"]  # Список полей, запрашиваемых при создании пользователя через createsuperuser

    objects = CustomUserManager()  # Использование кастомного менеджера пользователей

    def __str__(self):
        """
        Возвращает строковое представление объекта пользователя.
        Используется в админ‑панели и при выводе объектов в шаблонах.

        Returns:
            str: Электронная почта пользователя (как идентификатор).
        """
        return self.email  # Строковое представление — email пользователя
