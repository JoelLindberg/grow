from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    User preferences and profile settings.
    Stores calendar preferences like preferred start of the week.
    """

    WEEK_START_CHOICES = [
        ("monday", "Monday – Sunday"),
        ("sunday", "Sunday – Saturday"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    week_start_day = models.CharField(
        max_length=10,
        choices=WEEK_START_CHOICES,
        default="monday",
        help_text="Preferred start day of the week for schedule overview.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.username}'s Profile ({self.week_start_day})"

    def get_ordered_weekdays(self):
        """
        Returns an ordered list of tuples: (day_index, day_name, day_abbr)
        based on the user's preferred week_start_day.
        Python's date.weekday() uses 0=Monday .. 6=Sunday.
        """
        all_days = [
            (0, "Monday", "Mon"),
            (1, "Tuesday", "Tue"),
            (2, "Wednesday", "Wed"),
            (3, "Thursday", "Thu"),
            (4, "Friday", "Fri"),
            (5, "Saturday", "Sat"),
            (6, "Sunday", "Sun"),
        ]
        if self.week_start_day == "sunday":
            return [all_days[6]] + all_days[0:6]
        return all_days


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    """Ensure every user automatically has a UserProfile."""
    UserProfile.objects.get_or_create(user=instance)
