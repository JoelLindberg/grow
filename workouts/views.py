import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models, transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import UserProfile
from workouts.forms import (
    WorkoutExerciseForm,
    WorkoutForm,
    WorkoutLogForm,
    WorkoutScheduleForm,
)
from workouts.models import Exercise, Workout, WorkoutExercise, WorkoutLog, WorkoutSchedule


DAY_CHOICES = [
    (0, "Mon"),
    (1, "Tue"),
    (2, "Wed"),
    (3, "Thu"),
    (4, "Fri"),
    (5, "Sat"),
    (6, "Sun"),
]

DAY_NAME_MAP = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}


# -----------------------------------------------------------------------------
# Helper Utilities
# -----------------------------------------------------------------------------


def get_schedule_for_week(user):
    """
    Assembles a full week calendar data structure for the user,
    respecting their preferred week_start_day (Monday vs Sunday).
    Only complete Workouts are scheduled (never individual exercises).
    """
    profile, _ = UserProfile.objects.get_or_create(user=user)
    ordered_weekdays = profile.get_ordered_weekdays()

    today = timezone.localdate()
    today_weekday = today.weekday()

    if profile.week_start_day == "sunday":
        days_since_sunday = (today_weekday + 1) % 7
        week_start_date = today - datetime.timedelta(days=days_since_sunday)
    else:
        week_start_date = today - datetime.timedelta(days=today_weekday)

    workouts = list(
        Workout.objects.filter(user=user)
        .prefetch_related("workout_exercises__exercise")
        .order_by("name")
    )

    schedules = list(
        WorkoutSchedule.objects.filter(user=user, is_active=True)
        .select_related("workout")
        .prefetch_related("workout__workout_exercises__exercise")
    )

    week_days_data = []
    for day_offset, (day_idx, day_name, day_abbr) in enumerate(ordered_weekdays):
        day_date = week_start_date + datetime.timedelta(days=day_offset)
        is_today = day_date == today

        day_workouts = {}

        # 1. Workouts scheduled via Workout.scheduled_days
        for w in workouts:
            if w.is_scheduled_on(day_idx):
                exercises = list(w.workout_exercises.all())
                day_workouts[w.id] = {
                    "workout": w,
                    "plan": w,  # template compatibility
                    "recurrence": "Weekly",
                    "exercises": exercises,
                    "categories": w.category_summary,
                    "total_sets": w.total_sets,
                    "total_reps": w.total_reps,
                }

        # 2. Workouts scheduled via recurring WorkoutSchedule rules
        for ws in schedules:
            matches_schedule = (
                ws.recurrence == "daily"
                or (ws.recurrence == "weekly" and ws.day_of_week == day_idx)
                or (ws.recurrence == "monthly" and day_date.day == ws.created_at.day)
            )
            if matches_schedule and ws.workout_id not in day_workouts:
                w = ws.workout
                exercises = list(w.workout_exercises.all())
                day_workouts[w.id] = {
                    "workout": w,
                    "plan": w,  # template compatibility
                    "recurrence": ws.get_recurrence_display(),
                    "exercises": exercises,
                    "categories": w.category_summary,
                    "total_sets": w.total_sets,
                    "total_reps": w.total_reps,
                }

        workouts_list = list(day_workouts.values())
        total_exercises = 0
        total_sets = 0
        total_reps = 0
        for dw in workouts_list:
            total_exercises += len(dw["exercises"])
            total_sets += dw["total_sets"]
            total_reps += dw["total_reps"]

        week_days_data.append(
            {
                "day_index": day_idx,
                "day_name": day_name,
                "day_abbr": day_abbr,
                "date": day_date,
                "is_today": is_today,
                "workouts": workouts_list,
                "plans": workouts_list,  # template compatibility
                "workout_count": len(workouts_list),
                "total_exercises": total_exercises,
                "total_sets": total_sets,
                "total_reps": total_reps,
                "has_workouts": len(workouts_list) > 0,
            }
        )

    return profile, week_days_data


def _filter_uncompleted_today_workouts(user, scheduled_workouts, today):
    """
    Filter out workouts scheduled for today that have already been marked as completed today.
    Returns (uncompleted_workouts, all_today_completed).
    """
    if not scheduled_workouts:
        return [], False

    completed_logs = WorkoutLog.objects.filter(
        user=user,
        date=today,
        status="completed",
    )
    completed_ids = set(
        completed_logs.exclude(workout__isnull=True).values_list("workout_id", flat=True)
    )
    completed_names = set(
        completed_logs.filter(workout__isnull=True).values_list("workout_name", flat=True)
    )

    uncompleted = []
    for dw in scheduled_workouts:
        workout_obj = dw["workout"]
        if workout_obj.id not in completed_ids and workout_obj.name not in completed_names:
            uncompleted.append(dw)

    all_today_completed = len(scheduled_workouts) > 0 and len(uncompleted) == 0
    return uncompleted, all_today_completed


# -----------------------------------------------------------------------------
# Dashboard View
# -----------------------------------------------------------------------------


@login_required
def dashboard_view(request):
    """
    Main member dashboard (User Flows: Dashboard):
    - Workouts widget: Today's uncompleted Workouts with 'Start Workout' next to each scheduled workout,
      'All workouts completed for today' if all scheduled workouts for today are completed,
      or 'No workouts scheduled for today' if none are scheduled, plus 'Edit Workouts' link.
    - Meals widget: Today's Meals & Edit Meals (blank placeholder for now).
    - Weekly Schedule widget: Compact overview showing days with scheduled Workouts and count, plus 'Edit Schedule' link.
    - Workout History widget: Completed workouts count and completion rate percentage.
    """
    workouts = Workout.objects.filter(user=request.user).prefetch_related("workout_exercises__exercise")
    today = timezone.localdate()
    today_weekday = today.weekday()

    profile, week_data = get_schedule_for_week(request.user)
    today_day_data = None
    for d in week_data:
        if d["day_index"] == today_weekday:
            today_day_data = d
            break

    scheduled_today_workouts = today_day_data["workouts"] if today_day_data else []
    today_workouts, all_today_completed = _filter_uncompleted_today_workouts(
        request.user, scheduled_today_workouts, today
    )

    today_exercises = []
    if today_workouts:
        primary_workout = today_workouts[0]
        today_workout_title = primary_workout["workout"].name
        for w in today_workouts:
            for we in w["exercises"]:
                today_exercises.append(
                    {
                        "id": we.id,
                        "name": we.exercise.name,
                        "muscle_group": we.exercise.muscle_group,
                        "completed_sets": 0,
                        "target_sets": we.target_sets,
                        "sets": we.target_sets,
                        "reps": we.target_reps,
                        "weight": float(we.target_weight_kg) if we.target_weight_kg else 0,
                        "completed": False,
                    }
                )
    elif all_today_completed:
        today_workout_title = "All workouts completed for today"
    else:
        today_workout_title = "No workouts scheduled for today"

    scheduled_week_days = [d for d in week_data if d["has_workouts"]]

    all_logs = WorkoutLog.objects.filter(user=request.user)
    total_logs_count = all_logs.count()
    total_completed_count = all_logs.filter(status="completed").count()
    if total_logs_count > 0:
        completion_rate = round((total_completed_count / total_logs_count) * 100)
    else:
        completion_rate = 0

    recent_logs = all_logs.order_by("-date", "-completed_at")[:5]

    return render(
        request,
        "dashboard.html",
        {
            "profile": profile,
            "workouts": workouts,
            "workout_plans": workouts,  # compatibility
            "has_workouts": workouts.exists(),
            "has_plans": workouts.exists(),
            "today_day_name": DAY_NAME_MAP.get(today_weekday, "Today"),
            "today_date": today,
            "today_workouts": today_workouts,
            "today_workout_title": today_workout_title,
            "today_exercises": today_exercises,
            "today_has_workouts": len(today_workouts) > 0,
            "all_today_completed": all_today_completed,
            "today_day_data": today_day_data,
            "week_data": week_data,
            "week_days_data": week_data,
            "scheduled_week_days": scheduled_week_days,
            "total_completed": total_completed_count,
            "total_logs": total_logs_count,
            "completion_rate": completion_rate,
            "recent_logs": recent_logs,
        },
    )


# -----------------------------------------------------------------------------
# Workout Management Views (User Flows & PRD: Workouts)
# -----------------------------------------------------------------------------


@login_required
def workout_list_view(request):
    """
    Display all workouts belonging to the authenticated user.
    Provides entry point for creating new workouts or editing existing ones.
    """
    workouts = (
        Workout.objects.filter(user=request.user)
        .prefetch_related("workout_exercises__exercise")
        .order_by("-updated_at")
    )
    return render(
        request,
        "workouts/workout_list.html",
        {
            "workouts": workouts,
            "plans": workouts,  # compatibility
        },
    )


@login_required
def workout_create_view(request):
    """
    Create a new workout and immediately launch the workout editor.
    """
    if request.method == "POST":
        form = WorkoutForm(request.POST)
        if form.is_valid():
            workout = form.save(commit=False)
            workout.user = request.user
            workout.save()
            messages.success(request, f"Created workout '{workout.name}'. Now add your exercises!")
            return redirect("workouts:workout_edit", workout_id=workout.id)
    else:
        form = WorkoutForm()

    return render(
        request,
        "workouts/workout_create.html",
        {
            "form": form,
        },
    )


@login_required
def workout_edit_view(request, workout_id):
    """
    Full-featured workout editor (as specified in User Flows 'Workouts view'):
    - Update workout name, description, and scheduled days of the week.
    - Add, edit, remove, and reorder exercises (sets, reps, weight).
    """
    workout = get_object_or_404(Workout, id=workout_id, user=request.user)

    if request.method == "POST":
        post_data = request.POST.copy()
        if not post_data.get("name"):
            post_data["name"] = workout.name
        if "description" not in post_data:
            post_data["description"] = workout.description

        workout_form = WorkoutForm(post_data, instance=workout)
        if workout_form.is_valid():
            workout_form.save()
            messages.success(request, f"Saved workout '{workout.name}'.")
            if request.headers.get("HX-Request"):
                return HttpResponse(
                    '<span id="save-status" class="text-xs font-semibold text-[var(--status-success)]">✓ Workout Saved</span>'
                )
            return redirect("workouts:workout_edit", workout_id=workout.id)
    else:
        workout_form = WorkoutForm(instance=workout)

    exercise_form = WorkoutExerciseForm()
    exercises = workout.workout_exercises.select_related("exercise").order_by("order", "id")
    available_exercises = Exercise.objects.all().order_by("muscle_group", "name")

    return render(
        request,
        "workouts/workout_editor.html",
        {
            "workout": workout,
            "plan": workout,  # compatibility
            "workout_form": workout_form,
            "plan_form": workout_form,  # compatibility
            "exercise_form": exercise_form,
            "exercises": exercises,
            "available_exercises": available_exercises,
            "day_choices": DAY_CHOICES,
        },
    )


@login_required
@require_POST
def workout_delete_view(request, workout_id):
    """
    Delete a user's workout and its configured exercises.
    """
    workout = get_object_or_404(Workout, id=workout_id, user=request.user)
    name = workout.name
    workout.delete()
    messages.success(request, f"Workout '{name}' has been deleted.")
    return redirect("workouts:workout_list")


@login_required
@require_POST
def workout_duplicate_view(request, workout_id):
    """
    Duplicate an existing workout with all its exercises as a template.
    """
    source_workout = get_object_or_404(Workout, id=workout_id, user=request.user)

    with transaction.atomic():
        new_workout = Workout.objects.create(
            user=request.user,
            name=f"{source_workout.name} (Copy)",
            description=source_workout.description,
            scheduled_days=list(source_workout.scheduled_days or []),
        )
        for we in source_workout.workout_exercises.all():
            WorkoutExercise.objects.create(
                workout=new_workout,
                exercise=we.exercise,
                target_sets=we.target_sets,
                target_reps=we.target_reps,
                target_weight_kg=we.target_weight_kg,
                order=we.order,
            )

    messages.success(request, f"Duplicated '{source_workout.name}' into '{new_workout.name}'.")
    return redirect("workouts:workout_edit", workout_id=new_workout.id)


# -----------------------------------------------------------------------------
# Workout Exercise Interactive Actions (HTMX + standard fallback)
# -----------------------------------------------------------------------------


def _render_exercise_list(request, workout):
    """Helper to render the partial exercise list for HTMX swaps."""
    exercises = workout.workout_exercises.select_related("exercise").order_by("order", "id")
    return render(
        request,
        "workouts/partials/exercise_list.html",
        {
            "workout": workout,
            "plan": workout,  # compatibility
            "exercises": exercises,
        },
    )


@login_required
@require_POST
def workout_exercise_add_view(request, workout_id):
    """
    Add an exercise to the workout (sets, reps, optional weight).
    Supports HTMX swap for zero-reload list update.
    """
    workout = get_object_or_404(Workout, id=workout_id, user=request.user)
    form = WorkoutExerciseForm(request.POST)

    if form.is_valid():
        we = form.save(commit=False)
        we.workout = workout
        max_order = workout.workout_exercises.aggregate(models.Max("order"))["order__max"] or 0
        we.order = max_order + 1
        we.save()
        workout.save()  # update timestamp

        if request.headers.get("HX-Request"):
            return _render_exercise_list(request, workout)
        messages.success(request, f"Added {we.exercise.name} to workout.")
    else:
        if request.headers.get("HX-Request"):
            return HttpResponse(
                f'<div class="p-3 badge-danger text-xs rounded-lg">Error adding exercise: {form.errors}</div>',
                status=400,
            )
        messages.error(request, "Could not add exercise. Please check input values.")

    return redirect("workouts:workout_edit", workout_id=workout.id)


@login_required
def workout_exercise_edit_view(request, workout_id, exercise_id):
    """
    Edit prescription (sets, reps, weight) of an exercise in a workout.
    GET: returns editable row / form partial.
    POST: updates exercise and returns refreshed exercise list.
    """
    workout = get_object_or_404(Workout, id=workout_id, user=request.user)
    workout_exercise = get_object_or_404(WorkoutExercise, id=exercise_id, workout=workout)

    if request.method == "POST":
        form = WorkoutExerciseForm(request.POST, instance=workout_exercise)
        if form.is_valid():
            we = form.save()
            workout.save()  # update timestamp
            if request.headers.get("HX-Request"):
                return _render_exercise_list(request, workout)
            messages.success(request, f"Updated {we.exercise.name}.")
            return redirect("workouts:workout_edit", workout_id=workout.id)
    else:
        form = WorkoutExerciseForm(instance=workout_exercise)

    if request.headers.get("HX-Request"):
        return render(
            request,
            "workouts/partials/exercise_edit_row.html",
            {
                "workout": workout,
                "plan": workout,  # compatibility
                "workout_exercise": workout_exercise,
                "plan_exercise": workout_exercise,  # compatibility
                "form": form,
            },
        )
    return redirect("workouts:workout_edit", workout_id=workout.id)


@login_required
@require_POST
def workout_exercise_delete_view(request, workout_id, exercise_id):
    """
    Remove an exercise from a workout.
    """
    workout = get_object_or_404(Workout, id=workout_id, user=request.user)
    workout_exercise = get_object_or_404(WorkoutExercise, id=exercise_id, workout=workout)
    exercise_name = workout_exercise.exercise.name
    workout_exercise.delete()
    workout.save()  # update timestamp

    if request.headers.get("HX-Request"):
        return _render_exercise_list(request, workout)

    messages.success(request, f"Removed {exercise_name} from workout.")
    return redirect("workouts:workout_edit", workout_id=workout.id)


@login_required
@require_POST
def workout_exercise_move_view(request, workout_id, exercise_id, direction):
    """
    Reorder exercises up or down in the workout.
    """
    workout = get_object_or_404(Workout, id=workout_id, user=request.user)
    exercises = list(workout.workout_exercises.all().order_by("order", "id"))

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
        workout.save()

    if request.headers.get("HX-Request"):
        return _render_exercise_list(request, workout)

    return redirect("workouts:workout_edit", workout_id=workout.id)


# -----------------------------------------------------------------------------
# Workout Execution & Result Tracking (User Flows: Today's Workout Steps 1-10)
# -----------------------------------------------------------------------------


@login_required
def workout_today_view(request):
    """
    Workout Perform view for performing today's scheduled workout (User Flows: Today's Workout Steps 6-10):
    - Shows uncompleted workouts scheduled for today (or a specific workout if ?workout=<id> is passed).
    - Options to Start workout, Postpone for next day, or Mark as skipped.
    - Exercise list with pre-filled counters:
      - Sets: 0 / TOTAL SETS set in the Workout for the given exercise (+ / - buttons).
      - Reps: reps for the current set (+ / - buttons).
      - Weight: weight for the current set (+ / - buttons).
      - Checkbox to mark each exercise as completed.
    - Saves progress in client cache/storage until the user clicks Save Workout, which marks it
      completed permanently in the database.
    """
    today = timezone.localdate()
    today_weekday = today.weekday()

    _, week_data = get_schedule_for_week(request.user)
    today_day_data = None
    for d in week_data:
        if d["day_index"] == today_weekday:
            today_day_data = d
            break

    scheduled_today_workouts = today_day_data["workouts"] if today_day_data else []
    today_workouts, all_today_completed = _filter_uncompleted_today_workouts(
        request.user, scheduled_today_workouts, today
    )

    selected_workout_id = request.GET.get("workout")
    if selected_workout_id and str(selected_workout_id).isdigit():
        target_id = int(selected_workout_id)
        filtered = []
        for dw in today_workouts:
            if dw["workout"].id == target_id:
                filtered.append(dw)
        if filtered:
            today_workouts = filtered

    today_exercises = []
    primary_workout = None

    if today_workouts:
        active_workout_entry = today_workouts[0]
        primary_workout = active_workout_entry["workout"]
        for we in active_workout_entry["exercises"]:
            today_exercises.append(
                {
                    "id": we.id,
                    "name": we.exercise.name,
                    "muscle_group": we.exercise.muscle_group,
                    "completed_sets": 0,
                    "target_sets": we.target_sets,
                    "sets": we.target_sets,
                    "reps": we.target_reps,
                    "target_reps": we.target_reps,
                    "weight": float(we.target_weight_kg) if we.target_weight_kg else 0,
                    "target_weight": float(we.target_weight_kg) if we.target_weight_kg else 0,
                    "completed": False,
                }
            )

    log_form = WorkoutLogForm()

    return render(
        request,
        "workouts/workout_today.html",
        {
            "today_day_name": DAY_NAME_MAP.get(today_weekday, "Today"),
            "today_date": today,
            "today_workouts": today_workouts,
            "primary_workout": primary_workout,
            "today_exercises": today_exercises,
            "has_workouts": len(today_workouts) > 0,
            "all_today_completed": all_today_completed,
            "log_form": log_form,
        },
    )


@login_required
@require_POST
def workout_postpone_view(request):
    """
    Postpone today's workout for the next day (User Flows Step 5).
    Moves the scheduled Workout from today_weekday to tomorrow_weekday.
    """
    today = timezone.localdate()
    today_weekday = today.weekday()
    tomorrow_weekday = (today_weekday + 1) % 7

    _, week_data = get_schedule_for_week(request.user)
    today_day_data = None
    for d in week_data:
        if d["day_index"] == today_weekday:
            today_day_data = d
            break

    scheduled_today_workouts = today_day_data["workouts"] if today_day_data else []
    uncompleted_workouts, _ = _filter_uncompleted_today_workouts(
        request.user, scheduled_today_workouts, today
    )

    workout_id_raw = request.POST.get("workout_id")
    if workout_id_raw and str(workout_id_raw).isdigit():
        target_id = int(workout_id_raw)
        uncompleted_workouts = [dw for dw in uncompleted_workouts if dw["workout"].id == target_id]

    if uncompleted_workouts:
        with transaction.atomic():
            for dw in uncompleted_workouts:
                workout = dw["workout"]
                days = set(workout.scheduled_day_indices)
                days.discard(today_weekday)
                days.add(tomorrow_weekday)
                workout.scheduled_days = sorted(list(days))
                workout.save()

                # Also update any weekly WorkoutSchedule rules for this workout on today_weekday
                WorkoutSchedule.objects.filter(
                    user=request.user,
                    workout=workout,
                    day_of_week=today_weekday,
                    recurrence="weekly",
                ).update(day_of_week=tomorrow_weekday)

            WorkoutLog.objects.create(
                user=request.user,
                workout=uncompleted_workouts[0]["workout"],
                workout_name=uncompleted_workouts[0]["workout"].name,
                date=today,
                status="postponed",
                notes="Postponed to tomorrow.",
            )

        messages.success(request, f"Workout postponed to {DAY_NAME_MAP[tomorrow_weekday]}!")
    else:
        messages.info(request, "No workout scheduled for today to postpone.")

    return redirect("workouts:workout_today")


@login_required
@require_POST
def workout_skip_view(request):
    """
    Mark today's workout as skipped (User Flows Step 5).
    """
    today = timezone.localdate()
    today_weekday = today.weekday()

    _, week_data = get_schedule_for_week(request.user)
    today_day_data = None
    for d in week_data:
        if d["day_index"] == today_weekday:
            today_day_data = d
            break

    scheduled_today_workouts = today_day_data["workouts"] if today_day_data else []
    uncompleted_workouts, _ = _filter_uncompleted_today_workouts(
        request.user, scheduled_today_workouts, today
    )

    workout_obj = None
    workout_name = "Daily Workout"
    workout_id_raw = request.POST.get("workout_id")
    if workout_id_raw and str(workout_id_raw).isdigit():
        target_id = int(workout_id_raw)
        for dw in uncompleted_workouts:
            if dw["workout"].id == target_id:
                workout_obj = dw["workout"]
                workout_name = workout_obj.name
                break
    elif uncompleted_workouts:
        workout_obj = uncompleted_workouts[0]["workout"]
        workout_name = workout_obj.name

    WorkoutLog.objects.create(
        user=request.user,
        workout=workout_obj,
        workout_name=workout_name,
        date=today,
        status="skipped",
        all_goals_completed=False,
        notes=request.POST.get("notes", "Marked as skipped."),
    )

    messages.info(request, f"Workout '{workout_name}' marked as skipped.")
    return redirect("workouts:workout_today")


@login_required
@require_POST
def workout_save_session_view(request):
    """
    Save completed workout session to workout history (User Flows Steps 9-10 & PRD):
    - Saves all_goals_completed (True if all checked or user confirms)
    - Saves well_rested flag (helps guide user to implement more rest days)
    - Saves user notes
    - Stores snapshot of completed exercises
    """
    today = timezone.localdate()

    workout_id = request.POST.get("workout_id")
    workout_name = request.POST.get("workout_name", "Workout Session")
    workout = None
    if workout_id and workout_id.isdigit():
        workout = Workout.objects.filter(id=int(workout_id), user=request.user).first()
        if workout:
            workout_name = workout.name

    well_rested_val = request.POST.get("well_rested")
    well_rested = well_rested_val in ["1", "true", "True", "on"]

    all_goals_completed_val = request.POST.get("all_goals_completed")
    all_goals_completed = all_goals_completed_val in ["1", "true", "True", "on"]

    notes = request.POST.get("notes", "").strip()

    # Parse exercise snapshot data if provided
    exercise_ids = request.POST.getlist("exercise_id")
    exercise_names = request.POST.getlist("exercise_name")
    exercise_sets = request.POST.getlist("exercise_sets")
    exercise_reps = request.POST.getlist("exercise_reps")
    exercise_weights = request.POST.getlist("exercise_weight")
    exercise_completed = request.POST.getlist("exercise_completed")

    snapshot = []
    for idx in range(len(exercise_names)):
        ex_completed = (
            str(exercise_ids[idx]) in exercise_completed
            or f"completed_{exercise_ids[idx]}" in request.POST
        )
        snapshot.append(
            {
                "id": exercise_ids[idx] if idx < len(exercise_ids) else None,
                "name": exercise_names[idx],
                "sets": int(exercise_sets[idx]) if idx < len(exercise_sets) and exercise_sets[idx].isdigit() else 3,
                "reps": int(exercise_reps[idx]) if idx < len(exercise_reps) and exercise_reps[idx].isdigit() else 10,
                "weight": float(exercise_weights[idx]) if idx < len(exercise_weights) and exercise_weights[idx] else 0,
                "completed": ex_completed,
            }
        )

    if snapshot and all(item["completed"] for item in snapshot):
        all_goals_completed = True

    log = WorkoutLog.objects.create(
        user=request.user,
        workout=workout,
        workout_name=workout_name,
        date=today,
        status="completed",
        all_goals_completed=all_goals_completed,
        well_rested=well_rested,
        notes=notes,
        exercise_data=snapshot,
    )

    if not well_rested:
        messages.warning(
            request,
            f"Saved '{log.workout_name}' to history. You noted feeling less rested — consider scheduling an extra recovery day soon to maintain balance!",
        )
    else:
        messages.success(
            request,
            f"Great job! Saved '{log.workout_name}' to your workout history.",
        )

    return redirect("workouts:workout_history")


@login_required
def workout_history_view(request):
    """
    Displays workout history: logged sessions, completion rate, rest reflections, and notes.
    """
    logs = WorkoutLog.objects.filter(user=request.user).order_by("-date", "-completed_at")
    total_logs = logs.count()
    total_completed = logs.filter(status="completed").count()
    if total_logs > 0:
        completion_rate = round((total_completed / total_logs) * 100)
    else:
        completion_rate = 0
    well_rested_count = logs.filter(status="completed", well_rested=True).count()
    needs_rest_count = logs.filter(status="completed", well_rested=False).count()

    return render(
        request,
        "workouts/workout_history.html",
        {
            "logs": logs,
            "total_logs": total_logs,
            "total_completed": total_completed,
            "completion_rate": completion_rate,
            "well_rested_count": well_rested_count,
            "needs_rest_count": needs_rest_count,
        },
    )


# -----------------------------------------------------------------------------
# Workout Schedule Views (User Flows: Weekly Schedule)
# -----------------------------------------------------------------------------


@login_required
def schedule_week_view(request):
    """
    Calendar view of Workouts for the week (User Flows: Weekly Schedule):
    - Displays Workout title for each day.
    - Displays count of each category (e.g. Legs, Arms, Chest) and total reps per category.
    - If a day is empty, displays option to 'Add Workout'.
    - Clicking a day opens the day schedule editor to add/remove Workouts for that day.
    """
    profile, week_days_data = get_schedule_for_week(request.user)
    user_workouts = (
        Workout.objects.filter(user=request.user)
        .prefetch_related("workout_exercises__exercise")
        .order_by("name")
    )

    context = {
        "profile": profile,
        "week_days_data": week_days_data,
        "user_workouts": user_workouts,
        "user_plans": user_workouts,  # compatibility
    }

    if request.headers.get("HX-Request") and request.GET.get("partial") == "week_overview":
        return render(request, "workouts/partials/schedule_week_overview.html", context)

    return render(request, "workouts/schedule_week.html", context)


@login_required
@require_POST
def schedule_week_start_preference_view(request):
    """
    Change user's preferred start of the week (e.g. Monday - Sunday or Sunday - Saturday).
    Swaps the weekly calendar view via HTMX or redirects.
    """
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    new_pref = request.POST.get("week_start_day")

    if new_pref in ["monday", "sunday"]:
        profile.week_start_day = new_pref
        profile.save()
        messages.success(request, f"Week start updated to {profile.get_week_start_day_display()}.")

    if request.headers.get("HX-Request"):
        profile, week_days_data = get_schedule_for_week(request.user)
        user_workouts = (
            Workout.objects.filter(user=request.user)
            .prefetch_related("workout_exercises__exercise")
            .order_by("name")
        )
        return render(
            request,
            "workouts/partials/schedule_week_overview.html",
            {
                "profile": profile,
                "week_days_data": week_days_data,
                "user_workouts": user_workouts,
            },
        )

    return redirect("workouts:schedule")


@login_required
def schedule_day_view(request, day_index):
    """
    Edit the schedule for a specific day (User Flows: Weekly Schedule Step 4):
    - Lists Workouts currently scheduled on that day.
    - Allows adding and removing Workouts for that day.
    - Schedule is updated/saved immediately after adding or removing a Workout.
    """
    if day_index < 0 or day_index > 6:
        return HttpResponseBadRequest("Invalid day of week")

    profile, week_days_data = get_schedule_for_week(request.user)
    day_data = None
    for d in week_days_data:
        if d["day_index"] == day_index:
            day_data = d
            break

    user_workouts = (
        Workout.objects.filter(user=request.user)
        .prefetch_related("workout_exercises__exercise")
        .order_by("name")
    )

    scheduled_workout_ids = set()
    if day_data:
        for dw in day_data["workouts"]:
            scheduled_workout_ids.add(dw["workout"].id)

    available_workouts = []
    for w in user_workouts:
        if w.id not in scheduled_workout_ids:
            available_workouts.append(w)

    return render(
        request,
        "workouts/schedule_day.html",
        {
            "profile": profile,
            "day_index": day_index,
            "day_name": DAY_NAME_MAP[day_index],
            "day_data": day_data,
            "user_workouts": user_workouts,
            "available_workouts": available_workouts,
            "scheduled_workout_ids": scheduled_workout_ids,
        },
    )


@login_required
@require_POST
def schedule_day_workout_add_view(request, day_index):
    """
    Add one or more Workouts to the schedule for a specific day (User Flows: Weekly Schedule Steps 3 & 4).
    Immediately updates and saves the Workout's scheduled_days.
    """
    if day_index < 0 or day_index > 6:
        return HttpResponseBadRequest("Invalid day of week")

    workout_ids = request.POST.getlist("workout_id")
    if not workout_ids:
        single_id = request.POST.get("workout")
        if single_id:
            workout_ids = [single_id]

    if not workout_ids:
        messages.error(request, "Please select a workout to add.")
        return redirect("workouts:schedule_day", day_index=day_index)

    added_names = []
    with transaction.atomic():
        for wid in workout_ids:
            if not str(wid).isdigit():
                continue
            workout = get_object_or_404(Workout, id=int(wid), user=request.user)
            days = set(workout.scheduled_day_indices)
            days.add(day_index)
            workout.scheduled_days = sorted(list(days))
            workout.save()
            added_names.append(workout.name)

    if added_names:
        names_str = ", ".join(added_names)
        messages.success(request, f"Added '{names_str}' to {DAY_NAME_MAP[day_index]}.")

    if request.POST.get("next") == "schedule":
        return redirect("workouts:schedule")
    return redirect("workouts:schedule_day", day_index=day_index)


@login_required
@require_POST
def schedule_day_workout_remove_view(request, day_index, workout_id):
    """
    Remove a Workout from a specific day's schedule (User Flows: Weekly Schedule Step 4).
    """
    if day_index < 0 or day_index > 6:
        return HttpResponseBadRequest("Invalid day of week")

    workout = get_object_or_404(Workout, id=workout_id, user=request.user)
    days = set(workout.scheduled_day_indices)
    days.discard(day_index)
    workout.scheduled_days = sorted(list(days))
    workout.save()

    # Also remove any WorkoutSchedule records for this workout on this day
    WorkoutSchedule.objects.filter(
        user=request.user,
        workout=workout,
        day_of_week=day_index,
    ).delete()

    messages.success(request, f"Removed '{workout.name}' from {DAY_NAME_MAP[day_index]}.")

    if request.POST.get("next") == "schedule":
        return redirect("workouts:schedule")
    return redirect("workouts:schedule_day", day_index=day_index)


@login_required
@require_POST
def schedule_clear_all_view(request):
    """
    Clear all workouts from the weekly schedule (User Flows: Dashboard / Weekly Schedule).
    """
    with transaction.atomic():
        for workout in Workout.objects.filter(user=request.user):
            if workout.scheduled_days:
                workout.scheduled_days = []
                workout.save()
        WorkoutSchedule.objects.filter(user=request.user).delete()

    messages.success(request, "Cleared all workouts from the weekly schedule.")
    return redirect("workouts:schedule")


@login_required
@require_POST
def schedule_workout_assign_view(request):
    """
    Assign a workout to a day of the week (or recurring interval).
    Updates Workout.scheduled_days for weekly assignments.
    """
    workout_id = request.POST.get("workout")
    day_idx_raw = request.POST.get("day_of_week")
    recurrence = request.POST.get("recurrence", "weekly")

    if workout_id and str(workout_id).isdigit() and day_idx_raw is not None and str(day_idx_raw).isdigit():
        workout = get_object_or_404(Workout, id=int(workout_id), user=request.user)
        day_idx = int(day_idx_raw)
        if 0 <= day_idx <= 6:
            if recurrence == "weekly":
                days = set(workout.scheduled_day_indices)
                days.add(day_idx)
                workout.scheduled_days = sorted(list(days))
                workout.save()
            elif recurrence == "daily":
                workout.scheduled_days = [0, 1, 2, 3, 4, 5, 6]
                workout.save()
            WorkoutSchedule.objects.update_or_create(
                user=request.user,
                workout=workout,
                day_of_week=day_idx,
                recurrence=recurrence,
                defaults={"is_active": True},
            )
            messages.success(
                request,
                f"Scheduled '{workout.name}' on {DAY_NAME_MAP.get(day_idx)}.",
            )
            if request.POST.get("next") == "schedule":
                return redirect("workouts:schedule")
            return redirect("workouts:schedule_day", day_index=day_idx)

    messages.error(request, "Could not assign workout. Please verify the selections.")
    return redirect("workouts:schedule")


@login_required
@require_POST
def schedule_assignment_delete_view(request, schedule_id):
    """
    Delete a recurring workout assignment.
    """
    ws = get_object_or_404(WorkoutSchedule, id=schedule_id, user=request.user)
    workout_name = ws.workout.name
    ws.delete()
    messages.success(request, f"Removed schedule for '{workout_name}'.")
    return redirect("workouts:schedule")


# -----------------------------------------------------------------------------
# Backward Compatibility View Aliases
# -----------------------------------------------------------------------------

plan_list_view = workout_list_view
plan_create_view = workout_create_view
plan_edit_view = workout_edit_view
plan_delete_view = workout_delete_view
plan_duplicate_view = workout_duplicate_view
plan_exercise_add_view = workout_exercise_add_view
plan_exercise_edit_view = workout_exercise_edit_view
plan_exercise_delete_view = workout_exercise_delete_view
plan_exercise_move_view = workout_exercise_move_view
schedule_plan_assign_view = schedule_workout_assign_view
