from django.urls import path
from workouts import views

app_name = "workouts"

urlpatterns = [
    # Workout Plan Management
    path("plans/", views.plan_list_view, name="plan_list"),
    path("plans/create/", views.plan_create_view, name="plan_create"),
    path("plans/<int:plan_id>/edit/", views.plan_edit_view, name="plan_edit"),
    path("plans/<int:plan_id>/delete/", views.plan_delete_view, name="plan_delete"),
    path("plans/<int:plan_id>/duplicate/", views.plan_duplicate_view, name="plan_duplicate"),
    # Interactive Plan Exercise Operations (HTMX / Form)
    path("plans/<int:plan_id>/exercises/add/", views.plan_exercise_add_view, name="plan_exercise_add"),
    path("plans/<int:plan_id>/exercises/<int:exercise_id>/edit/", views.plan_exercise_edit_view, name="plan_exercise_edit"),
    path("plans/<int:plan_id>/exercises/<int:exercise_id>/delete/", views.plan_exercise_delete_view, name="plan_exercise_delete"),
    path("plans/<int:plan_id>/exercises/<int:exercise_id>/move/<str:direction>/", views.plan_exercise_move_view, name="plan_exercise_move"),
]
