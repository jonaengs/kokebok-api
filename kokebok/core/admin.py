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
    model = CustomUser  # type: ignore
    list_display = ["username", "is_staff", "last_login"]
    list_filter = []  # type: ignore # -- type signture for these lists is horrible. Skip it.
    search_fields = []  # type: ignore


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.unregister(Group)
