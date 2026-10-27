from django.contrib import admin
from accounts.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "week_start_day", "created_at"]
    list_filter = ["week_start_day"]
    search_fields = ["user__username", "user__email"]
