from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm

from custom_user_app.models import CustomUser
from custom_user_app.forms import CustomUserCreationForm



@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    # Поля, отображаемые в списке пользователей
    list_display = (
        'username',
        'email',
        'is_staff',
        'is_active',
        'is_superuser',
        'has_recent_activity',
        'created_at',
        'updated_at'
    )

    # Поля для фильтрации
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        'created_at'
    )

    # Поиск по полям
    search_fields = ('username', 'email')

    # Порядок сортировки по умолчанию
    ordering = ('-created_at',)

    # Группировка полей в форме редактирования
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Личная информация', {
            'fields': ('email',)
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)  # Свёрнутая группа
        }),
    )

    # Поля при создании нового пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    # Только для чтения (не редактируются в админке)
    readonly_fields = ('created_at', 'updated_at')

    def has_recent_activity(self, obj):
        from django.utils import timezone
        from datetime import timedelta
        return obj.updated_at > timezone.now() - timedelta(days=30)

    has_recent_activity.boolean = True
    has_recent_activity.short_description = 'Недавняя активность'



    # Экспорт данных
    actions = ['export_as_csv']

    def export_as_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users.csv"'

        writer = csv.writer(response)
        writer.writerow(['Username', 'Email', 'Is Staff', 'Is Active', 'Created At'])

        for user in queryset:
            writer.writerow([
                user.username,
                user.email,
                user.is_staff,
                user.is_active,
                user.created_at
            ])

        return response

    export_as_csv.short_description = "Экспорт выбранных пользователей в CSV"


    class Meta:
        model = CustomUser
        fields = ('username', 'email')