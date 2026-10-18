from django.conf import settings
from django.db import models


class Exercise(models.Model):
    """
    Catalog of gym exercises categorized by target muscle group.
    Curated by admins and referenced by workout plans and sessions.
    """

    MUSCLE_GROUP_CHOICES = [
        ("Chest", "Chest"),
        ("Back", "Back"),
        ("Legs", "Legs"),
        ("Shoulders", "Shoulders"),
        ("Arms", "Arms"),
        ("Core", "Core"),
        ("Full Body", "Full Body"),
    ]

    name = models.CharField(max_length=100, unique=True)
    muscle_group = models.CharField(max_length=50, choices=MUSCLE_GROUP_CHOICES, db_index=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["muscle_group", "name"]
        verbose_name = "Exercise"
        verbose_name_plural = "Exercises"

    def __str__(self):
        return f"{self.name} ({self.muscle_group})"


class WorkoutPlan(models.Model):
    """
    User-defined workout plan blueprint (e.g. 'Push Day', 'Legs & Core').
    Defines target exercises, sets, reps, weight, and rest intervals.
    Serves as the reusable building block for daily schedules.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workout_plans",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Workout Plan"
        verbose_name_plural = "Workout Plans"

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    @property
    def exercise_count(self):
        return self.plan_exercises.count()

    @property
    def total_sets(self):
        return sum(pe.target_sets for pe in self.plan_exercises.all())

    @property
    def muscle_groups(self):
        """Returns sorted unique muscle groups targeted in this plan."""
        groups = set(pe.exercise.muscle_group for pe in self.plan_exercises.select_related("exercise"))
        return sorted(groups)

    @property
    def estimated_duration_minutes(self):
        """
        Estimates total workout duration in minutes:
        Each set ~ 45s of execution + rest time between sets.
        """
        total_seconds = 0
        for pe in self.plan_exercises.all():
            set_execution_seconds = pe.target_sets * 45
            rest_seconds = max(0, pe.target_sets - 1) * pe.rest_seconds
            total_seconds += (set_execution_seconds + rest_seconds)
        return max(15, round(total_seconds / 60)) if self.exercise_count > 0 else 0


class PlanExercise(models.Model):
    """
    An exercise assigned to a workout plan with prescription parameters:
    target sets, target reps, weight (optional / bodyweight), and rest time between sets.
    """

    plan = models.ForeignKey(
        WorkoutPlan,
        on_delete=models.CASCADE,
        related_name="plan_exercises",
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="plan_exercises",
    )
    target_sets = models.PositiveIntegerField(default=3)
    target_reps = models.PositiveIntegerField(default=10)
    target_weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Target weight in kg (optional; bodyweight if blank or 0).",
    )
    rest_seconds = models.PositiveIntegerField(
        default=60,
        help_text="Rest time in seconds between sets (default: 60s).",
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Plan Exercise"
        verbose_name_plural = "Plan Exercises"

    @property
    def is_bodyweight(self):
        return self.target_weight_kg is None or self.target_weight_kg <= 0

    @property
    def weight_display(self):
        if not self.is_bodyweight:
            val = f"{self.target_weight_kg:.2f}".rstrip("0").rstrip(".")
            return f"{val} kg"
        return "Bodyweight"

    def __str__(self):
        weight_str = f" @ {self.weight_display}"
        return f"{self.plan.name} - {self.exercise.name} ({self.target_sets}x{self.target_reps}{weight_str})"
