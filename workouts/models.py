from django.conf import settings
from django.db import models
from django.utils import timezone


class Exercise(models.Model):
    """
    Catalog of gym exercises categorized by target muscle group.
    Curated by admins and referenced by workout routines and sessions.
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


class Workout(models.Model):
    """
    User-defined workout blueprint (e.g. 'Push Day', 'Legs & Core').
    Defines target exercises, sets, reps, weight, and the days of the week
    the entire workout is scheduled on.
    """

    DAY_NAMES = {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday",
    }
    DAY_ABBR = {
        0: "Mon",
        1: "Tue",
        2: "Wed",
        3: "Thu",
        4: "Fri",
        5: "Sat",
        6: "Sun",
    }

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workouts",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    scheduled_days = models.JSONField(
        default=list,
        blank=True,
        help_text="Days of the week this workout is scheduled (0=Monday, 6=Sunday).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Workout"
        verbose_name_plural = "Workouts"

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    @property
    def exercise_count(self):
        return self.workout_exercises.count()

    @property
    def total_sets(self):
        total = 0
        for we in self.workout_exercises.all():
            total += we.target_sets
        return total

    @property
    def total_reps(self):
        total = 0
        for we in self.workout_exercises.all():
            total += we.target_sets * we.target_reps
        return total

    @property
    def muscle_groups(self):
        """Returns sorted unique muscle groups targeted in this workout."""
        groups = set()
        for we in self.workout_exercises.select_related("exercise"):
            groups.add(we.exercise.muscle_group)
        return sorted(groups)

    @property
    def category_summary(self):
        """
        Returns a breakdown by exercise category (muscle group):
        - category: name of category (e.g., 'Legs', 'Arms', 'Chest')
        - count: number of exercises in this category
        - total_reps: total reps (sets * reps) for this category in the workout
        """
        categories = {}
        for we in self.workout_exercises.select_related("exercise"):
            cat = we.exercise.muscle_group
            if cat not in categories:
                categories[cat] = {
                    "category": cat,
                    "count": 0,
                    "total_reps": 0,
                }
            categories[cat]["count"] += 1
            categories[cat]["total_reps"] += we.target_sets * we.target_reps

        result = []
        for cat_name in sorted(categories.keys()):
            result.append(categories[cat_name])
        return result

    @property
    def estimated_duration_minutes(self):
        """
        Estimates total workout duration in minutes (~105s per set).
        """
        if self.exercise_count == 0:
            return 0
        total_seconds = self.total_sets * 105
        return max(15, round(total_seconds / 60))

    def is_scheduled_on(self, day_index):
        if not self.scheduled_days:
            return False
        return day_index in self.scheduled_days or str(day_index) in self.scheduled_days

    @property
    def scheduled_days_display(self):
        if not self.scheduled_days:
            return "Unscheduled"
        int_days = []
        for d in self.scheduled_days:
            if str(d).isdigit():
                val = int(d)
                if 0 <= val <= 6 and val not in int_days:
                    int_days.append(val)
        int_days.sort()
        if len(int_days) == 7:
            return "Daily"
        labels = []
        for d in int_days:
            if d in self.DAY_ABBR:
                labels.append(self.DAY_ABBR[d])
        return ", ".join(labels)

    @property
    def scheduled_day_indices(self):
        indices = []
        if not self.scheduled_days:
            return indices
        for d in self.scheduled_days:
            if str(d).isdigit():
                val = int(d)
                if 0 <= val <= 6 and val not in indices:
                    indices.append(val)
        indices.sort()
        return indices

    @property
    def plan_exercises(self):
        """Backward-compatibility alias."""
        return self.workout_exercises


class WorkoutExercise(models.Model):
    """
    An exercise assigned to a workout with prescription parameters:
    target sets, target reps, and weight (optional / bodyweight).
    """

    workout = models.ForeignKey(
        Workout,
        on_delete=models.CASCADE,
        related_name="workout_exercises",
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="workout_exercises",
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
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Workout Exercise"
        verbose_name_plural = "Workout Exercises"

    @property
    def is_bodyweight(self):
        return self.target_weight_kg is None or self.target_weight_kg <= 0

    @property
    def weight_display(self):
        if not self.is_bodyweight:
            val = f"{self.target_weight_kg:.2f}".rstrip("0").rstrip(".")
            return f"{val} kg"
        return "Bodyweight"

    @property
    def plan(self):
        """Backward-compatibility alias."""
        return self.workout

    @plan.setter
    def plan(self, value):
        self.workout = value

    def __str__(self):
        weight_str = f" @ {self.weight_display}"
        return f"{self.workout.name} - {self.exercise.name} ({self.target_sets}x{self.target_reps}{weight_str})"


class WorkoutSchedule(models.Model):
    """
    Assigns workouts to recurring intervals (daily, weekly, monthly)
    or to specific days of the week.
    """

    RECURRENCE_CHOICES = [
        ("weekly", "Weekly"),
        ("daily", "Daily"),
        ("monthly", "Monthly"),
    ]

    DAY_CHOICES = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workout_schedules",
    )
    workout = models.ForeignKey(
        Workout,
        on_delete=models.CASCADE,
        related_name="schedules",
    )
    day_of_week = models.PositiveSmallIntegerField(
        choices=DAY_CHOICES,
        default=0,
        help_text="Day of the week (0=Monday, 6=Sunday).",
    )
    recurrence = models.CharField(
        max_length=20,
        choices=RECURRENCE_CHOICES,
        default="weekly",
        help_text="Recurring interval: daily, weekly, or monthly.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["day_of_week", "workout__name"]
        verbose_name = "Workout Schedule"
        verbose_name_plural = "Workout Schedules"

    @property
    def plan(self):
        """Backward-compatibility alias."""
        return self.workout

    @plan.setter
    def plan(self, value):
        self.workout = value

    def __str__(self):
        day_str = dict(self.DAY_CHOICES).get(self.day_of_week, str(self.day_of_week))
        return f"{self.user.username} - {self.workout.name} ({self.get_recurrence_display()} on {day_str})"


class WorkoutLog(models.Model):
    """
    Workout result tracking:
    - Tracks results of workouts (all goals completed or not)
    - Well rested or not (helps guide user to implement more rest days)
    - Any notes the user wants to add
    - Snapshot of exercises, sets, reps, and weights
    """

    STATUS_CHOICES = [
        ("completed", "Completed"),
        ("skipped", "Skipped"),
        ("postponed", "Postponed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workout_logs",
    )
    workout = models.ForeignKey(
        Workout,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs",
    )
    workout_name = models.CharField(max_length=100)
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="completed")
    all_goals_completed = models.BooleanField(
        default=False,
        help_text="Tracks whether all exercise goals were completed.",
    )
    well_rested = models.BooleanField(
        default=True,
        help_text="Tracks whether the user felt well-rested before/during workout.",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="User notes and reflections on the workout.",
    )
    exercise_data = models.JSONField(
        default=list,
        blank=True,
        help_text="Snapshot of exercises, targets, completed sets/reps.",
    )
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-completed_at"]
        verbose_name = "Workout Log"
        verbose_name_plural = "Workout Logs"

    def __str__(self):
        return f"{self.workout_name} on {self.date} ({self.status}) - {self.user.username}"


# Backward compatibility aliases
WorkoutPlan = Workout
PlanExercise = WorkoutExercise
