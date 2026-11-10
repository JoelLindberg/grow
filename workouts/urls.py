from django.urls import path
from workouts import views

app_name = "workouts"

urlpatterns = [
    # Workout Management (PRD: Workouts)
    path("", views.workout_list_view, name="workout_list"),
    path("create/", views.workout_create_view, name="workout_create"),
    path("<int:workout_id>/edit/", views.workout_edit_view, name="workout_edit"),
    path("<int:workout_id>/delete/", views.workout_delete_view, name="workout_delete"),
    path("<int:workout_id>/duplicate/", views.workout_duplicate_view, name="workout_duplicate"),

    # Interactive Workout Exercise Operations (HTMX / Form)
    path("<int:workout_id>/exercises/add/", views.workout_exercise_add_view, name="workout_exercise_add"),
    path("<int:workout_id>/exercises/<int:exercise_id>/edit/", views.workout_exercise_edit_view, name="workout_exercise_edit"),
    path("<int:workout_id>/exercises/<int:exercise_id>/delete/", views.workout_exercise_delete_view, name="workout_exercise_delete"),
    path("<int:workout_id>/exercises/<int:exercise_id>/move/<str:direction>/", views.workout_exercise_move_view, name="workout_exercise_move"),

    # Workout Session Execution & Result Tracking (User Flows 4-10 & PRD)
    path("today/", views.workout_today_view, name="workout_today"),
    path("today/postpone/", views.workout_postpone_view, name="workout_postpone"),
    path("today/skip/", views.workout_skip_view, name="workout_skip"),
    path("today/save/", views.workout_save_session_view, name="workout_save_session"),
    path("history/", views.workout_history_view, name="workout_history"),

    # Workout Schedule & Weekly Calendar (PRD & User Flows — Workouts are scheduled, not exercises)
    path("schedule/", views.schedule_week_view, name="schedule"),
    path("schedule/settings/week-start/", views.schedule_week_start_preference_view, name="schedule_week_start"),
    path("schedule/clear/", views.schedule_clear_all_view, name="schedule_clear_all"),
    path("schedule/<int:day_index>/", views.schedule_day_view, name="schedule_day"),
    path("schedule/<int:day_index>/workouts/add/", views.schedule_day_workout_add_view, name="schedule_day_workout_add"),
    path("schedule/<int:day_index>/workouts/<int:workout_id>/remove/", views.schedule_day_workout_remove_view, name="schedule_day_workout_remove"),
    path("schedule/assign-workout/", views.schedule_workout_assign_view, name="schedule_workout_assign"),
    path("schedule/assignment/<int:schedule_id>/delete/", views.schedule_assignment_delete_view, name="schedule_assignment_delete"),

    # Backward Compatibility Aliases for Plans
    path("plans/", views.workout_list_view, name="plan_list"),
    path("plans/create/", views.workout_create_view, name="plan_create"),
    path("plans/<int:workout_id>/edit/", views.workout_edit_view, name="plan_edit"),
    path("plans/<int:workout_id>/delete/", views.workout_delete_view, name="plan_delete"),
    path("plans/<int:workout_id>/duplicate/", views.workout_duplicate_view, name="plan_duplicate"),
    path("plans/<int:workout_id>/exercises/add/", views.workout_exercise_add_view, name="plan_exercise_add"),
    path("plans/<int:workout_id>/exercises/<int:exercise_id>/edit/", views.workout_exercise_edit_view, name="plan_exercise_edit"),
    path("plans/<int:workout_id>/exercises/<int:exercise_id>/delete/", views.workout_exercise_delete_view, name="plan_exercise_delete"),
    path("plans/<int:workout_id>/exercises/<int:exercise_id>/move/<str:direction>/", views.workout_exercise_move_view, name="plan_exercise_move"),
    path("schedule/assign-plan/", views.schedule_workout_assign_view, name="schedule_plan_assign"),
]
