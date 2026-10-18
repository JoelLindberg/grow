from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models, transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from workouts.forms import PlanExerciseForm, WorkoutPlanForm
from workouts.models import Exercise, PlanExercise, WorkoutPlan


@login_required
def dashboard_view(request):
    """
    Main member dashboard: displays today's scheduled workout,
    plant-based nutrition tracker, and recovery status.
    Protected by authentication.
    """
    plans = WorkoutPlan.objects.filter(user=request.user)
    return render(
        request,
        "dashboard.html",
        {
            "workout_plans": plans,
            "has_plans": plans.exists(),
        },
    )


# -----------------------------------------------------------------------------
# Workout Plan Views
# -----------------------------------------------------------------------------


@login_required
def plan_list_view(request):
    """
    Display all workout plans belonging to the authenticated user.
    Provides entry point for creating new plans or editing existing ones.
    """
    plans = (
        WorkoutPlan.objects.filter(user=request.user)
        .prefetch_related("plan_exercises__exercise")
        .order_by("-updated_at")
    )
    return render(
        request,
        "workouts/plan_list.html",
        {
            "plans": plans,
        },
    )


@login_required
def plan_create_view(request):
    """
    Create a new workout plan and immediately launch the editor.
    """
    if request.method == "POST":
        form = WorkoutPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.user = request.user
            plan.save()
            messages.success(request, f"Created workout plan '{plan.name}'. Now add your exercises!")
            return redirect("workouts:plan_edit", plan_id=plan.id)
    else:
        form = WorkoutPlanForm()

    return render(
        request,
        "workouts/plan_create.html",
        {
            "form": form,
        },
    )


@login_required
def plan_edit_view(request, plan_id):
    """
    Full-featured workout plan editor:
    - Update plan name and description.
    - Add, edit, remove, and reorder exercises.
    - Tune set/rep/weight/rest targets.
    """
    plan = get_object_or_404(WorkoutPlan, id=plan_id, user=request.user)

    if request.method == "POST":
        plan_form = WorkoutPlanForm(request.POST, instance=plan)
        if plan_form.is_valid():
            plan_form.save()
            messages.success(request, f"Saved workout plan '{plan.name}'.")
            if request.headers.get("HX-Request"):
                return HttpResponse(
                    f'<span id="save-status" class="text-xs font-semibold text-emerald-400 animate-pulse">✓ Saved</span>'
                )
            return redirect("workouts:plan_edit", plan_id=plan.id)
    else:
        plan_form = WorkoutPlanForm(instance=plan)

    exercise_form = PlanExerciseForm()
    exercises = plan.plan_exercises.select_related("exercise").order_by("order", "id")
    available_exercises = Exercise.objects.all().order_by("muscle_group", "name")

    return render(
        request,
        "workouts/plan_editor.html",
        {
            "plan": plan,
            "plan_form": plan_form,
            "exercise_form": exercise_form,
            "exercises": exercises,
            "available_exercises": available_exercises,
        },
    )


@login_required
@require_POST
def plan_delete_view(request, plan_id):
    """
    Delete a user's workout plan and its configured exercises.
    """
    plan = get_object_or_404(WorkoutPlan, id=plan_id, user=request.user)
    name = plan.name
    plan.delete()
    messages.success(request, f"Workout plan '{name}' has been deleted.")
    return redirect("workouts:plan_list")


@login_required
@require_POST
def plan_duplicate_view(request, plan_id):
    """
    Duplicate an existing workout plan with all its exercises as a template.
    """
    source_plan = get_object_or_404(WorkoutPlan, id=plan_id, user=request.user)

    with transaction.atomic():
        new_plan = WorkoutPlan.objects.create(
            user=request.user,
            name=f"{source_plan.name} (Copy)",
            description=source_plan.description,
        )
        for pe in source_plan.plan_exercises.all():
            PlanExercise.objects.create(
                plan=new_plan,
                exercise=pe.exercise,
                target_sets=pe.target_sets,
                target_reps=pe.target_reps,
                target_weight_kg=pe.target_weight_kg,
                rest_seconds=pe.rest_seconds,
                order=pe.order,
            )

    messages.success(request, f"Duplicated '{source_plan.name}' into '{new_plan.name}'.")
    return redirect("workouts:plan_edit", plan_id=new_plan.id)


# -----------------------------------------------------------------------------
# Plan Exercise Interactive Actions (HTMX + standard fallback)
# -----------------------------------------------------------------------------


def _render_exercise_list(request, plan):
    """Helper to render the partial exercise list for HTMX swaps."""
    exercises = plan.plan_exercises.select_related("exercise").order_by("order", "id")
    return render(
        request,
        "workouts/partials/exercise_list.html",
        {
            "plan": plan,
            "exercises": exercises,
        },
    )


@login_required
@require_POST
def plan_exercise_add_view(request, plan_id):
    """
    Add an exercise to the workout plan.
    Supports HTMX swap for zero-reload list update.
    """
    plan = get_object_or_404(WorkoutPlan, id=plan_id, user=request.user)
    form = PlanExerciseForm(request.POST)

    if form.is_valid():
        pe = form.save(commit=False)
        pe.plan = plan
        max_order = plan.plan_exercises.aggregate(models.Max("order"))["order__max"] or 0
        pe.order = max_order + 1
        pe.save()
        plan.save()  # update timestamp

        if request.headers.get("HX-Request"):
            return _render_exercise_list(request, plan)
        messages.success(request, f"Added {pe.exercise.name} to plan.")
    else:
        if request.headers.get("HX-Request"):
            return HttpResponse(
                f'<div class="p-3 bg-red-950/40 text-red-300 text-xs rounded-lg">Error adding exercise: {form.errors}</div>',
                status=400,
            )
        messages.error(request, "Could not add exercise. Please check input values.")

    return redirect("workouts:plan_edit", plan_id=plan.id)


@login_required
def plan_exercise_edit_view(request, plan_id, exercise_id):
    """
    Edit prescription (sets, reps, weight, rest) of an exercise in a plan.
    GET: returns editable row / form partial.
    POST: updates exercise and returns refreshed exercise list.
    """
    plan = get_object_or_404(WorkoutPlan, id=plan_id, user=request.user)
    plan_exercise = get_object_or_404(PlanExercise, id=exercise_id, plan=plan)

    if request.method == "POST":
        form = PlanExerciseForm(request.POST, instance=plan_exercise)
        if form.is_valid():
            pe = form.save()
            plan.save()  # update timestamp
            if request.headers.get("HX-Request"):
                return _render_exercise_list(request, plan)
            messages.success(request, f"Updated {pe.exercise.name}.")
            return redirect("workouts:plan_edit", plan_id=plan.id)
    else:
        form = PlanExerciseForm(instance=plan_exercise)

    if request.headers.get("HX-Request"):
        return render(
            request,
            "workouts/partials/exercise_edit_row.html",
            {
                "plan": plan,
                "plan_exercise": plan_exercise,
                "form": form,
            },
        )
    return redirect("workouts:plan_edit", plan_id=plan.id)


@login_required
@require_POST
def plan_exercise_delete_view(request, plan_id, exercise_id):
    """
    Remove an exercise from a workout plan.
    """
    plan = get_object_or_404(WorkoutPlan, id=plan_id, user=request.user)
    plan_exercise = get_object_or_404(PlanExercise, id=exercise_id, plan=plan)
    exercise_name = plan_exercise.exercise.name
    plan_exercise.delete()
    plan.save()  # update timestamp

    if request.headers.get("HX-Request"):
        return _render_exercise_list(request, plan)

    messages.success(request, f"Removed {exercise_name} from plan.")
    return redirect("workouts:plan_edit", plan_id=plan.id)


@login_required
@require_POST
def plan_exercise_move_view(request, plan_id, exercise_id, direction):
    """
    Reorder exercises up or down in the workout plan.
    """
    plan = get_object_or_404(WorkoutPlan, id=plan_id, user=request.user)
    exercises = list(plan.plan_exercises.all().order_by("order", "id"))

    target_idx = None
    for idx, item in enumerate(exercises):
        if item.id == exercise_id:
            target_idx = idx
            break

    if target_idx is not None:
        if direction == "up" and target_idx > 0:
            swap_idx = target_idx - 1
            exercises[target_idx].order, exercises[swap_idx].order = (
                exercises[swap_idx].order,
                exercises[target_idx].order,
            )
            # Ensure strictly ordered values if identical
            if exercises[target_idx].order == exercises[swap_idx].order:
                exercises[swap_idx].order = target_idx - 1
                exercises[target_idx].order = target_idx
            exercises[target_idx].save()
            exercises[swap_idx].save()
        elif direction == "down" and target_idx < len(exercises) - 1:
            swap_idx = target_idx + 1
            exercises[target_idx].order, exercises[swap_idx].order = (
                exercises[swap_idx].order,
                exercises[target_idx].order,
            )
            if exercises[target_idx].order == exercises[swap_idx].order:
                exercises[target_idx].order = target_idx + 1
                exercises[swap_idx].order = target_idx
            exercises[target_idx].save()
            exercises[swap_idx].save()
        plan.save()

    if request.headers.get("HX-Request"):
        return _render_exercise_list(request, plan)

    return redirect("workouts:plan_edit", plan_id=plan.id)
