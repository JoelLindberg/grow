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


def get_filtered_exercises(user, filter_mode="latest"):
    """
    Returns exercises ordered by the requested filter mode:
    - 'latest': latest added exercises
    - 'oldest': oldest exercises
    - 'least_scheduled': exercises scheduled fewest times across user's workouts
    - 'most_scheduled': exercises scheduled most times across user's workouts
    """
    wes = WorkoutExercise.objects.filter(workout__user=user)
    schedule_counts = {}
    for we in wes:
        count = len(we.scheduled_days) if we.scheduled_days else 1
        schedule_counts[we.exercise_id] = schedule_counts.get(we.exercise_id, 0) + count

    for ws in WorkoutSchedule.objects.filter(user=user, is_active=True):
        for we in ws.workout.workout_exercises.all():
            schedule_counts[we.exercise_id] = schedule_counts.get(we.exercise_id, 0) + 1

    all_exercises = list(Exercise.objects.all())
    for ex in all_exercises:
        ex.schedule_count = schedule_counts.get(ex.id, 0)

    if filter_mode == "latest":
        return sorted(all_exercises, key=lambda e: (e.created_at, e.id), reverse=True)
    elif filter_mode == "oldest":
        return sorted(all_exercises, key=lambda e: (e.created_at, e.id))
    elif filter_mode == "least_scheduled":
        return sorted(all_exercises, key=lambda e: (e.schedule_count, e.name))
    elif filter_mode == "most_scheduled":
        return sorted(all_exercises, key=lambda e: (-e.schedule_count, e.name))
    else:
        return sorted(all_exercises, key=lambda e: (e.muscle_group, e.name))


def get_schedule_for_week(user):
    """
    Assembles a full week calendar data structure for the user,
    respecting their preferred week_start_day (Monday vs Sunday).
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
        WorkoutSchedule.objects.filter(user=user, is_active=True).select_related("workout")
    )

    week_days_data = []
    for day_offset, (day_idx, day_name, day_abbr) in enumerate(ordered_weekdays):
        day_date = week_start_date + datetime.timedelta(days=day_offset)
        is_today = day_date == today

        day_workouts = {}
        for ws in schedules:
            matches_schedule = (
                ws.recurrence == "daily"
                or (ws.recurrence == "weekly" and ws.day_of_week == day_idx)
                or (ws.recurrence == "monthly" and day_date.day == ws.created_at.day)
            )
            if matches_schedule:
                if ws.workout_id not in day_workouts:
                    day_workouts[ws.workout_id] = {
                        "workout": ws.workout,
                        "plan": ws.workout,  # template compatibility
                        "recurrence": ws.get_recurrence_display(),
                        "exercises": list(ws.workout.workout_exercises.all()),
                    }

        for w in workouts:
            matching_exercises = [we for we in w.workout_exercises.all() if we.is_scheduled_on(day_idx)]
            if matching_exercises:
                if w.id in day_workouts:
                    existing_ex_ids = {we.id for we in day_workouts[w.id]["exercises"]}
                    for me in matching_exercises:
                        if me.id not in existing_ex_ids:
                            day_workouts[w.id]["exercises"].append(me)
                else:
                    day_workouts[w.id] = {
                        "workout": w,
                        "plan": w,  # template compatibility
                        "recurrence": "Weekly Split",
                        "exercises": matching_exercises,
                    }

        workouts_list = list(day_workouts.values())
        total_exercises = sum(len(dw["exercises"]) for dw in workouts_list)
        total_sets = sum(sum(we.target_sets for we in dw["exercises"]) for dw in workouts_list)

        week_days_data.append(
            {
                "day_index": day_idx,
                "day_name": day_name,
                "day_abbr": day_abbr,
                "date": day_date,
                "is_today": is_today,
                "workouts": workouts_list,
                "plans": workouts_list,  # template compatibility
                "total_exercises": total_exercises,
                "total_sets": total_sets,
                "has_workouts": total_exercises > 0,
            }
        )

    return profile, week_days_data


# -----------------------------------------------------------------------------
# Dashboard View
# -----------------------------------------------------------------------------


@login_required
def dashboard_view(request):
    """
    Main member dashboard: displays today's scheduled workout,
    plant-based nutrition tracker, and recovery status.
    Widgets link directly to their corresponding views as per User Flows.
    """
    workouts = Workout.objects.filter(user=request.user)
    today = timezone.localdate()
    today_weekday = today.weekday()

    _, week_data = get_schedule_for_week(request.user)
    today_day_data = next((d for d in week_data if d["day_index"] == today_weekday), None)

    today_workouts = today_day_data["workouts"] if today_day_data else []
    today_exercises = []
    today_workout_title = "Rest Day"

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
                        "sets": we.target_sets,
                        "reps": we.target_reps,
                        "weight": float(we.target_weight_kg) if we.target_weight_kg else 0,
                        "rest_seconds": we.rest_seconds,
                        "completed": False,
                    }
                )

    recent_logs = WorkoutLog.objects.filter(user=request.user).order_by("-date", "-completed_at")[:5]

    return render(
        request,
        "dashboard.html",
        {
            "workouts": workouts,
            "workout_plans": workouts,  # compatibility
            "has_workouts": workouts.exists(),
            "has_plans": workouts.exists(),
            "today_day_name": DAY_NAME_MAP.get(today_weekday, "Today"),
            "today_date": today,
            "today_workout_title": today_workout_title,
            "today_exercises": today_exercises,
            "today_has_workouts": len(today_exercises) > 0,
            "today_day_data": today_day_data,
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
    Full-featured workout editor (as specified in User Flows 'Workout editor'):
    - Update workout name and description.
    - Add, edit, remove, and reorder exercises.
    - Set sets, reps, weight, rest time, and scheduled days of week.
    """
    workout = get_object_or_404(Workout, id=workout_id, user=request.user)

    if request.method == "POST":
        workout_form = WorkoutForm(request.POST, instance=workout)
        if workout_form.is_valid():
            workout_form.save()
            messages.success(request, f"Saved workout '{workout.name}'.")
            if request.headers.get("HX-Request"):
                return HttpResponse(
                    '<span id="save-status" class="text-xs font-semibold text-emerald-400 animate-pulse">✓ Saved</span>'
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
        )
        for we in source_workout.workout_exercises.all():
            WorkoutExercise.objects.create(
                workout=new_workout,
                exercise=we.exercise,
                target_sets=we.target_sets,
                target_reps=we.target_reps,
                target_weight_kg=we.target_weight_kg,
                rest_seconds=we.rest_seconds,
                scheduled_days=list(we.scheduled_days),
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
            "day_choices": DAY_CHOICES,
        },
    )


@login_required
@require_POST
def workout_exercise_add_view(request, workout_id):
    """
    Add an exercise to the workout with scheduled days of the week.
    Supports HTMX swap for zero-reload list update.
    """
    workout = get_object_or_404(Workout, id=workout_id, user=request.user)
    form = WorkoutExerciseForm(request.POST)

    if form.is_valid():
        we = form.save(commit=False)
        we.workout = workout
        days = request.POST.getlist("days")
        we.scheduled_days = [int(d) for d in days if str(d).isdigit() and 0 <= int(d) <= 6]
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
                f'<div class="p-3 bg-red-950/40 text-red-300 text-xs rounded-lg">Error adding exercise: {form.errors}</div>',
                status=400,
            )
        messages.error(request, "Could not add exercise. Please check input values.")

    return redirect("workouts:workout_edit", workout_id=workout.id)


@login_required
def workout_exercise_edit_view(request, workout_id, exercise_id):
    """
    Edit prescription (sets, reps, weight, rest, days) of an exercise in a workout.
    GET: returns editable row / form partial.
    POST: updates exercise and returns refreshed exercise list.
    """
    workout = get_object_or_404(Workout, id=workout_id, user=request.user)
    workout_exercise = get_object_or_404(WorkoutExercise, id=exercise_id, workout=workout)

    if request.method == "POST":
        form = WorkoutExerciseForm(request.POST, instance=workout_exercise)
        if form.is_valid():
            we = form.save(commit=False)
            days = request.POST.getlist("days")
            we.scheduled_days = [int(d) for d in days if str(d).isdigit() and 0 <= int(d) <= 6]
            we.save()
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
                "day_choices": DAY_CHOICES,
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
# Workout Execution & Result Tracking (User Flows: Workout Steps 1-10 & PRD)
# -----------------------------------------------------------------------------


@login_required
def workout_today_view(request):
    """
    Dedicated view for performing today's scheduled workout:
    - Step 4: Shows workouts scheduled for today.
    - Step 5: Options to Start workout, Postpone for next day, or Mark as skipped.
    - Step 6-8: Exercise list with pre-filled counters for sets and reps,
      + and - buttons to increment/decrement reps and sets, and checkboxes to mark complete.
    - Step 9-10: When completed, save workout session to workout history.
    - Result tracking: well-rested status and reflections/notes.
    """
    today = timezone.localdate()
    today_weekday = today.weekday()

    _, week_data = get_schedule_for_week(request.user)
    today_day_data = next((d for d in week_data if d["day_index"] == today_weekday), None)

    today_workouts = today_day_data["workouts"] if today_day_data else []
    today_exercises = []
    primary_workout = None

    if today_workouts:
        primary_workout = today_workouts[0]["workout"]
        for w in today_workouts:
            for we in w["exercises"]:
                today_exercises.append(
                    {
                        "id": we.id,
                        "name": we.exercise.name,
                        "muscle_group": we.exercise.muscle_group,
                        "sets": we.target_sets,
                        "reps": we.target_reps,
                        "weight": float(we.target_weight_kg) if we.target_weight_kg else 0,
                        "rest_seconds": we.rest_seconds,
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
            "has_workouts": len(today_exercises) > 0,
            "log_form": log_form,
        },
    )


@login_required
@require_POST
def workout_postpone_view(request):
    """
    Postpone today's workout for the next day (User Flows Step 5).
    """
    today = timezone.localdate()
    today_weekday = today.weekday()
    tomorrow_weekday = (today_weekday + 1) % 7

    _, week_data = get_schedule_for_week(request.user)
    today_day_data = next((d for d in week_data if d["day_index"] == today_weekday), None)

    if today_day_data and today_day_data["workouts"]:
        with transaction.atomic():
            for dw in today_day_data["workouts"]:
                for we in dw["exercises"]:
                    days = set(we.scheduled_days or [])
                    days.discard(today_weekday)
                    days.discard(str(today_weekday))
                    days.add(tomorrow_weekday)
                    we.scheduled_days = sorted(list(days))
                    we.save()

            WorkoutLog.objects.create(
                user=request.user,
                workout=today_day_data["workouts"][0]["workout"],
                workout_name=today_day_data["workouts"][0]["workout"].name,
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
    today_day_data = next((d for d in week_data if d["day_index"] == today_weekday), None)

    workout_obj = None
    workout_name = "Daily Workout"
    if today_day_data and today_day_data["workouts"]:
        workout_obj = today_day_data["workouts"][0]["workout"]
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
    today_weekday = today.weekday()

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
    Displays workout history: logged sessions, completed goals, rest reflections, and notes.
    """
    logs = WorkoutLog.objects.filter(user=request.user).order_by("-date", "-completed_at")
    total_completed = logs.filter(status="completed").count()
    well_rested_count = logs.filter(status="completed", well_rested=True).count()
    needs_rest_count = logs.filter(status="completed", well_rested=False).count()

    return render(
        request,
        "workouts/workout_history.html",
        {
            "logs": logs,
            "total_completed": total_completed,
            "well_rested_count": well_rested_count,
            "needs_rest_count": needs_rest_count,
        },
    )


# -----------------------------------------------------------------------------
# Workout Schedule Views (PRD & User Flows prioritized feature)
# -----------------------------------------------------------------------------


@login_required
def schedule_week_view(request):
    """
    Calendar view of workouts for the week (User Flows Step 3):
    - Vertical mobile-first layout.
    - Displays workout title and exercises with sets, reps, weight in finer text.
    - Allows switching week start preference (Monday vs Sunday).
    - Links to day schedule editor.
    """
    profile, week_days_data = get_schedule_for_week(request.user)
    recurring_schedules = (
        WorkoutSchedule.objects.filter(user=request.user)
        .select_related("workout")
        .order_by("day_of_week")
    )
    user_workouts = Workout.objects.filter(user=request.user).order_by("name")
    assign_form = WorkoutScheduleForm(user=request.user)

    context = {
        "profile": profile,
        "week_days_data": week_days_data,
        "recurring_schedules": recurring_schedules,
        "user_workouts": user_workouts,
        "user_plans": user_workouts,  # compatibility
        "assign_form": assign_form,
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
        return render(
            request,
            "workouts/partials/schedule_week_overview.html",
            {
                "profile": profile,
                "week_days_data": week_days_data,
            },
        )

    return redirect("workouts:schedule")


@login_required
def schedule_day_view(request, day_index):
    """
    Edit the schedule for a specific day (User Flows Workout Schedule Steps 4-6):
    - Lists workouts and exercises currently scheduled on that day.
    - Provides exercise selector dropdown filtered by:
      latest added, oldest, least scheduled, most scheduled.
    - Allows multi-select adding exercises to this day.
    """
    if day_index < 0 or day_index > 6:
        return HttpResponseBadRequest("Invalid day of week")

    profile, week_days_data = get_schedule_for_week(request.user)
    day_data = next((d for d in week_days_data if d["day_index"] == day_index), None)

    active_filter = request.GET.get("filter", "latest")
    filtered_exercises = get_filtered_exercises(request.user, active_filter)

    user_workouts = Workout.objects.filter(user=request.user).order_by("name")
    assign_form = WorkoutScheduleForm(
        initial={"day_of_week": day_index, "recurrence": "weekly"},
        user=request.user,
    )

    return render(
        request,
        "workouts/schedule_day.html",
        {
            "profile": profile,
            "day_index": day_index,
            "day_name": DAY_NAME_MAP[day_index],
            "day_data": day_data,
            "active_filter": active_filter,
            "filtered_exercises": filtered_exercises,
            "user_workouts": user_workouts,
            "user_plans": user_workouts,  # compatibility
            "assign_form": assign_form,
        },
    )


@login_required
def schedule_filtered_exercises_view(request, day_index):
    """
    HTMX partial endpoint to dynamically refresh the exercise filter dropdown results:
    - Latest added exercises
    - Oldest exercises
    - Least scheduled exercises
    - Most scheduled exercises
    """
    if day_index < 0 or day_index > 6:
        return HttpResponseBadRequest("Invalid day of week")

    active_filter = request.GET.get("filter", "latest")
    filtered_exercises = get_filtered_exercises(request.user, active_filter)
    user_workouts = Workout.objects.filter(user=request.user).order_by("name")

    return render(
        request,
        "workouts/partials/schedule_filtered_exercises.html",
        {
            "day_index": day_index,
            "day_name": DAY_NAME_MAP[day_index],
            "active_filter": active_filter,
            "filtered_exercises": filtered_exercises,
            "user_workouts": user_workouts,
            "user_plans": user_workouts,  # compatibility
        },
    )


@login_required
@require_POST
def schedule_day_exercise_add_view(request, day_index):
    """
    Add selected exercises to the schedule for the chosen day.
    Accepts one or more exercise IDs from checkboxes and attaches them
    to the selected or default workout with this day in scheduled_days.
    """
    if day_index < 0 or day_index > 6:
        return HttpResponseBadRequest("Invalid day of week")

    exercise_ids = request.POST.getlist("selected_exercises")
    if not exercise_ids:
        messages.error(request, "Please select at least one exercise to add.")
        return redirect("workouts:schedule_day", day_index=day_index)

    workout_id = request.POST.get("workout_id") or request.POST.get("plan_id")
    if workout_id:
        workout = get_object_or_404(Workout, id=workout_id, user=request.user)
    else:
        workout = Workout.objects.filter(user=request.user).first()
        if not workout:
            workout = Workout.objects.create(
                user=request.user,
                name=f"{DAY_NAME_MAP[day_index]} Routine",
                description="Custom scheduled workout",
            )

    target_sets = int(request.POST.get("target_sets", 3) or 3)
    target_reps = int(request.POST.get("target_reps", 10) or 10)
    target_weight_kg = request.POST.get("target_weight_kg")
    target_weight_kg = float(target_weight_kg) if target_weight_kg else None
    rest_seconds = int(request.POST.get("rest_seconds", 60) or 60)

    added_count = 0
    with transaction.atomic():
        for ex_id in exercise_ids:
            try:
                ex = Exercise.objects.get(id=ex_id)
            except Exercise.DoesNotExist:
                continue

            we = workout.workout_exercises.filter(exercise=ex).first()
            if we:
                days = set(we.scheduled_days or [])
                days.add(day_index)
                we.scheduled_days = sorted(list(days))
                we.save()
            else:
                max_order = workout.workout_exercises.aggregate(models.Max("order"))["order__max"] or 0
                WorkoutExercise.objects.create(
                    workout=workout,
                    exercise=ex,
                    target_sets=target_sets,
                    target_reps=target_reps,
                    target_weight_kg=target_weight_kg,
                    rest_seconds=rest_seconds,
                    scheduled_days=[day_index],
                    order=max_order + 1,
                )
            added_count += 1
        workout.save()

    messages.success(
        request,
        f"Added {added_count} exercise(s) to {DAY_NAME_MAP[day_index]}'s schedule under '{workout.name}'.",
    )
    return redirect("workouts:schedule_day", day_index=day_index)


@login_required
@require_POST
def schedule_day_exercise_remove_view(request, day_index, workout_exercise_id):
    """
    Remove an exercise from a specific day's schedule.
    Removes day_index from scheduled_days.
    """
    we = get_object_or_404(WorkoutExercise, id=workout_exercise_id, workout__user=request.user)
    exercise_name = we.exercise.name

    current_days = set(we.scheduled_days or [])
    if day_index in current_days or str(day_index) in current_days:
        current_days.discard(day_index)
        current_days.discard(str(day_index))
        we.scheduled_days = sorted(list(current_days))
        we.save()
        we.workout.save()

    messages.success(request, f"Removed {exercise_name} from {DAY_NAME_MAP.get(day_index, '')}'s schedule.")
    return redirect("workouts:schedule_day", day_index=day_index)


@login_required
@require_POST
def schedule_workout_assign_view(request):
    """
    Assign a workout to recurring intervals (daily, weekly, monthly)
    or to a specific day of the week.
    """
    form = WorkoutScheduleForm(request.POST, user=request.user)
    if form.is_valid():
        ws = form.save(commit=False)
        ws.user = request.user
        ws.save()
        messages.success(
            request,
            f"Scheduled '{ws.workout.name}' ({ws.get_recurrence_display()} on {DAY_NAME_MAP.get(ws.day_of_week)}).",
        )
    else:
        messages.error(request, "Could not assign workout. Please verify the selections.")

    day_idx = request.POST.get("day_of_week")
    if day_idx is not None and str(day_idx).isdigit():
        return redirect("workouts:schedule_day", day_index=int(day_idx))
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
    messages.success(request, f"Removed recurring schedule for '{workout_name}'.")
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
