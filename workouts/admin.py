from django.contrib import admin
from workouts.models import Exercise, PlanExercise, WorkoutPlan


class PlanExerciseInline(admin.TabularInline):
    model = PlanExercise
    extra = 1
    fields = ("order", "exercise", "target_sets", "target_reps", "target_weight_kg", "rest_seconds")
    ordering = ("order",)


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("name", "muscle_group", "created_at")
    list_filter = ("muscle_group",)
    search_fields = ("name", "description")


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "exercise_count", "total_sets", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("name", "description", "user__username")
    inlines = [PlanExerciseInline]


@admin.register(PlanExercise)
class PlanExerciseAdmin(admin.ModelAdmin):
    list_display = ("plan", "exercise", "target_sets", "target_reps", "target_weight_kg", "rest_seconds", "order")
    list_filter = ("plan",)
    search_fields = ("plan__name", "exercise__name")
