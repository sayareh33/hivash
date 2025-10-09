from django.contrib import admin

from .models import CustomUser, UserProfile


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        "phone",
        "email",
        "is_active",
        "is_staff",
        "is_superuser",
        "is_phone_verified",
    )
    list_filter = ("is_active", "is_staff", "is_superuser", "is_phone_verified")
    search_fields = ("phone", "email")
    readonly_fields = (
        "date_joined",
        "last_login",
        "otp_code",
        "otp_created_at",
        "locked_until",
    )
    fieldsets = (
        ("Credentials", {"fields": ("phone", "password")}),
        (
            "Contact",
            {"fields": ("email", "is_phone_verified", "new_phone")},
        ),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (
            "Security",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                    "otp_code",
                    "otp_created_at",
                    "otp_attempts",
                    "login_attempts",
                    "locked_until",
                )
            },
        ),
    )
    filter_horizontal = ("groups", "user_permissions")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "first_name", "last_name", "national_code")
    search_fields = ("user__phone", "first_name", "last_name", "national_code")
    autocomplete_fields = ("user",)
