from django.contrib import admin
from workouts.models import Exercise, Workout, WorkoutExercise, WorkoutLog, WorkoutSchedule


class WorkoutExerciseInline(admin.TabularInline):
    model = WorkoutExercise
    extra = 1
    fields = ("order", "exercise", "target_sets", "target_reps", "target_weight_kg", "rest_seconds", "scheduled_days")
    ordering = ("order",)


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("name", "muscle_group", "created_at")
    list_filter = ("muscle_group",)
    search_fields = ("name", "description")


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "exercise_count", "total_sets", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("name", "description", "user__username")
    inlines = [WorkoutExerciseInline]


@admin.register(WorkoutExercise)
class WorkoutExerciseAdmin(admin.ModelAdmin):
    list_display = ("workout", "exercise", "target_sets", "target_reps", "target_weight_kg", "rest_seconds", "scheduled_days", "order")
    list_filter = ("workout",)
    search_fields = ("workout__name", "exercise__name")


@admin.register(WorkoutSchedule)
class WorkoutScheduleAdmin(admin.ModelAdmin):
    list_display = ("user", "workout", "day_of_week", "recurrence", "is_active", "created_at")
    list_filter = ("day_of_week", "recurrence", "is_active")
    search_fields = ("user__username", "workout__name")


@admin.register(WorkoutLog)
class WorkoutLogAdmin(admin.ModelAdmin):
    list_display = ("workout_name", "user", "date", "status", "all_goals_completed", "well_rested", "completed_at")
    list_filter = ("status", "all_goals_completed", "well_rested", "date")
    search_fields = ("workout_name", "user__username", "notes")

