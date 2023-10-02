from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

CustomUser = get_user_model()


class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            ("Permissions"),
            {
                "fields": (
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
            },
        ),
    )
    model = CustomUser
    list_display = ["username", "is_staff", "last_login"]
    list_filter: list[str] = []
    search_fields: list[str] = []


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.unregister(Group)
