from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm

from custom_user_app.models import CustomUser
from custom_user_app.forms import CustomUserCreationForm



@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Кастомная админ‑панель для модели CustomUser.
    Расширяет стандартную UserAdmin, добавляя:
    - кастомную форму создания пользователя;
    - дополнительные поля в списке отображения;
    - фильтрацию и поиск;
    - свёрнутую группу полей с датами;
    - действие экспорта в CSV;
    - индикатор недавней активности пользователя.
    """

    add_form = CustomUserCreationForm  # Форма для создания нового пользователя в админке

    """Поля, отображаемые в списке пользователей в админ‑панели."""
    list_display = (
        'username',  # Отображение имени пользователя
        'email',  # Отображение электронной почты
        'is_staff',  # Статус сотрудника (доступ к админке)
        'is_active',  # Активность аккаунта
        'is_superuser',  # Статус суперпользователя
        'has_recent_activity',  # Индикатор недавней активности (метод ниже)
        'created_at',  # Дата создания аккаунта
        'updated_at'  # Дата последнего обновления аккаунта
    )

    """Фильтры, доступные в правой колонке списка пользователей."""
    list_filter = (
        'is_staff',  # Фильтр по статусу сотрудника
        'is_superuser',  # Фильтр по статусу суперпользователя
        'is_active',  # Фильтр по активности аккаунта
        'created_at'  # Фильтр по дате создания аккаунта
    )

    """Поля, по которым можно искать пользователей в админке."""
    search_fields = ('username', 'email')  # Поля для поиска пользователей

    """Сортировка списка пользователей по дате создания (от новых к старым)."""
    ordering = ('-created_at',)  # Сортировка по дате создания (новые сверху)

    """Разбиение полей на логические группы с разной видимостью в форме редактирования."""
    fieldsets = (
        (None, {
            'fields': ('username', 'password')  # Базовые поля: имя и пароль
        }),
        ('Личная информация', {
            'fields': ('email',)  # Личная информация: email
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser')  # Настройки прав доступа
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)  # Группа полей с датами отображается свёрнутой по умолчанию
        }),
    )

    """Настройка формы создания нового пользователя (отличается от формы редактирования)."""
    add_fieldsets = (
        (None, {
            'classes': ('wide',),  # Широкая форма для удобства заполнения
            'fields': ('username', 'email', 'password1', 'password2'),  # Поля при создании нового пользователя
        }),
    )

    """Поля, которые нельзя редактировать в админ‑панели (автоматически обновляются)."""
    readonly_fields = ('created_at', 'updated_at')  # Поля, доступные только для чтения

    def has_recent_activity(self, obj):
        """
        Определяет, был ли пользователь активен за последние 30 дней.

        Args:
            obj (CustomUser): Экземпляр пользователя.

        Returns:
            bool: True, если пользователь обновлял данные за последние 30 дней, иначе False.
        """
        from django.utils import timezone
        from datetime import timedelta
        return obj.updated_at > timezone.now() - timedelta(days=30)

    has_recent_activity.boolean = True  # Отображать результат как иконку (галочка/крестик)
    has_recent_activity.short_description = 'Недавняя активность'  # Заголовок столбца в списке

    """Список доступных групповых обработок в админ‑панели."""
    actions = ['export_as_csv']  # Доступные массовые действия над пользователями

    def export_as_csv(self, request, queryset):
        """
        Экспортирует выбранных пользователей в CSV‑файл.
        Создаёт HTTP‑ответ с CSV‑файлом, содержащим данные выбранных пользователей.

        Args:
            request (HttpRequest): HTTP‑запрос от клиента.
            queryset (QuerySet): Набор выбранных пользователей для экспорта.

        Returns:
            HttpResponse: Ответ с CSV‑файлом для скачивания.
        """
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users.csv"'  # Заголовки для скачивания файла

        writer = csv.writer(response)
        writer.writerow(['Username', 'Email', 'Is Staff', 'Is Active', 'Created At'])  # Заголовки столбцов CSV

        for user in queryset:
            writer.writerow([
                user.username,  # Имя пользователя
                user.email,  # Электронная почта
                user.is_staff,  # Статус сотрудника
                user.is_active,  # Активность аккаунта
                user.created_at  # Дата создания аккаунта
            ])

        return response

    export_as_csv.short_description = "Экспорт выбранных пользователей в CSV"  # Описание действия для отображения в админке

    class Meta:
        """Метаданные для админ‑панели."""
        model = CustomUser  # Модель, к которой применяется админ‑панель
        fields = ('username', 'email')  # Поля модели, используемые в админке