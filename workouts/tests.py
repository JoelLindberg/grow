from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from accounts.models import UserProfile
from workouts.models import (
    Exercise,
    PlanExercise,
    Workout,
    WorkoutExercise,
    WorkoutLog,
    WorkoutPlan,
    WorkoutSchedule,
)

User = get_user_model()


class IndexPageTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_index_page_renders_with_autumn_theme(self):
        """Verify the index page renders with 200 status code and autumn theme content."""
        request = self.factory.get("/")
        view = TemplateView.as_view(template_name="index.html")
        response = view(request)
        response.render()

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()

        self.assertIn("If you are strong, you have to be", content)
        self.assertIn("theme.css", content)
        self.assertIn("grow_season", content)
        self.assertIn("Alpha", content)
        self.assertIn("v0.1-alpha", content)


class HomeExerciseDatabaseTests(TestCase):
    """
    Verify the initial database includes exercises focused on home workouts
    using dumbbells, bodyweight, and the ab wheel on the ground.
    """

    def test_home_exercise_variations_exist(self):
        # Push-up variations (normal, narrow, wide, decline)
        self.assertTrue(Exercise.objects.filter(name="Push-Up (Normal)").exists())
        self.assertTrue(Exercise.objects.filter(name="Push-Up (Narrow / Diamond)").exists())
        self.assertTrue(Exercise.objects.filter(name="Push-Up (Wide)").exists())
        self.assertTrue(Exercise.objects.filter(name="Decline Push-Up").exists())

        # Squat variations (normal, wide / sumo)
        self.assertTrue(Exercise.objects.filter(name="Bodyweight Squat (Normal)").exists())
        self.assertTrue(Exercise.objects.filter(name="Bodyweight Squat (Wide / Sumo)").exists())

        # Calf raise variations (standing, single-leg)
        self.assertTrue(Exercise.objects.filter(name="Standing Calf Raise").exists())
        self.assertTrue(Exercise.objects.filter(name="Single-Leg Calf Raise").exists())

        # Dumbbell raise on the floor above head for chest (Floor Dumbbell Pullover)
        self.assertTrue(Exercise.objects.filter(name="Floor Dumbbell Pullover").exists())

        # Ab wheel core training
        self.assertTrue(Exercise.objects.filter(name="Ab Wheel Rollout (Kneeling)").exists())


class WorkoutModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="gym_rat", password="StrongPassword123!")
        self.pushup_normal = Exercise.objects.get_or_create(
            name="Push-Up (Normal)",
            defaults={"muscle_group": "Chest", "description": "Pushup"},
        )[0]
        self.pullover = Exercise.objects.get_or_create(
            name="Floor Dumbbell Pullover",
            defaults={"muscle_group": "Chest", "description": "Floor pullover"},
        )[0]
        self.wheel = Exercise.objects.get_or_create(
            name="Ab Wheel Rollout (Kneeling)",
            defaults={"muscle_group": "Core", "description": "Ab wheel"},
        )[0]

    def test_workout_creation_and_properties(self):
        workout = Workout.objects.create(
            user=self.user,
            name="Home Push & Core",
            description="Pushups and ab wheel",
        )
        self.assertEqual(str(workout), "Home Push & Core (gym_rat)")
        self.assertEqual(workout.exercise_count, 0)
        self.assertEqual(workout.total_sets, 0)
        self.assertEqual(workout.muscle_groups, [])
        self.assertEqual(workout.estimated_duration_minutes, 0)

        # Exercise 1: Bodyweight pushups (no weight set)
        we1 = WorkoutExercise.objects.create(
            workout=workout,
            exercise=self.pushup_normal,
            target_sets=4,
            target_reps=15,
            target_weight_kg=None,
            rest_seconds=60,
            order=1,
        )
        self.assertTrue(we1.is_bodyweight)
        self.assertEqual(we1.weight_display, "Bodyweight")
        self.assertEqual(we1.rest_seconds, 60)

        # Exercise 2: Weighted pullover
        we2 = WorkoutExercise.objects.create(
            workout=workout,
            exercise=self.pullover,
            target_sets=3,
            target_reps=10,
            target_weight_kg=Decimal("12.50"),
            rest_seconds=60,
            order=2,
        )
        self.assertFalse(we2.is_bodyweight)
        self.assertEqual(we2.weight_display, "12.5 kg")
        self.assertIn("@ 12.5 kg", str(we2))

        self.assertEqual(workout.exercise_count, 2)
        self.assertEqual(workout.total_sets, 7)
        self.assertTrue(workout.estimated_duration_minutes > 0)

    def test_backward_compatibility_aliases(self):
        """Verify WorkoutPlan and PlanExercise aliases work seamlessly."""
        self.assertEqual(WorkoutPlan, Workout)
        self.assertEqual(PlanExercise, WorkoutExercise)

        plan = WorkoutPlan.objects.create(user=self.user, name="Alias Workout")
        pe = PlanExercise.objects.create(
            plan=plan,
            exercise=self.pushup_normal,
            target_sets=3,
            target_reps=10,
        )
        self.assertEqual(pe.workout, plan)
        self.assertEqual(plan.workout_exercises.count(), 1)
        self.assertEqual(plan.plan_exercises.count(), 1)


class WorkoutWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="member_one", password="StrongPassword123!")
        self.other_user = User.objects.create_user(username="member_two", password="StrongPassword123!")
        self.client.force_login(self.user)

        self.pushup_normal = Exercise.objects.get_or_create(
            name="Push-Up (Normal)",
            defaults={"muscle_group": "Chest", "description": "Pushup"},
        )[0]
        self.pullover = Exercise.objects.get_or_create(
            name="Floor Dumbbell Pullover",
            defaults={"muscle_group": "Chest", "description": "Floor pullover"},
        )[0]
        self.wheel = Exercise.objects.get_or_create(
            name="Ab Wheel Rollout (Kneeling)",
            defaults={"muscle_group": "Core", "description": "Wheel"},
        )[0]

    def test_unauthenticated_access_redirects_to_login(self):
        self.client.logout()
        url = reverse("workouts:workout_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_workout_list_view_empty_state_and_populated(self):
        response = self.client.get(reverse("workouts:workout_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No Workouts Created Yet")

        workout = Workout.objects.create(user=self.user, name="Home Strength")
        response = self.client.get(reverse("workouts:workout_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Home Strength")

    def test_workout_create_workflow(self):
        url = reverse("workouts:workout_create")
        post_data = {
            "name": "Home Dumbbell & Core",
            "description": "Dumbbells and wheel",
        }
        response = self.client.post(url, post_data)
        workout = Workout.objects.get(name="Home Dumbbell & Core", user=self.user)
        self.assertRedirects(response, reverse("workouts:workout_edit", kwargs={"workout_id": workout.id}))

    def test_workout_user_isolation(self):
        secret_workout = Workout.objects.create(user=self.other_user, name="Secret Workout")
        edit_url = reverse("workouts:workout_edit", kwargs={"workout_id": secret_workout.id})
        self.assertEqual(self.client.get(edit_url).status_code, 404)

        delete_url = reverse("workouts:workout_delete", kwargs={"workout_id": secret_workout.id})
        self.assertEqual(self.client.post(delete_url).status_code, 404)
        self.assertTrue(Workout.objects.filter(id=secret_workout.id).exists())

    def test_add_exercise_bodyweight_and_weighted(self):
        workout = Workout.objects.create(user=self.user, name="Push Workout")
        add_url = reverse("workouts:workout_exercise_add", kwargs={"workout_id": workout.id})

        # 1. Add bodyweight exercise (no weight specified)
        bw_data = {
            "exercise": self.pushup_normal.id,
            "target_sets": 4,
            "target_reps": 12,
            "target_weight_kg": "",
            "rest_seconds": 60,
        }
        response = self.client.post(add_url, bw_data)
        self.assertRedirects(response, reverse("workouts:workout_edit", kwargs={"workout_id": workout.id}))

        we1 = WorkoutExercise.objects.get(workout=workout, exercise=self.pushup_normal)
        self.assertIsNone(we1.target_weight_kg)
        self.assertTrue(we1.is_bodyweight)
        self.assertEqual(we1.weight_display, "Bodyweight")

        # 2. Add weighted exercise with HTMX
        weighted_data = {
            "exercise": self.pullover.id,
            "target_sets": 3,
            "target_reps": 10,
            "target_weight_kg": "14.5",
            "rest_seconds": 60,
        }
        htmx_response = self.client.post(add_url, weighted_data, HTTP_HX_REQUEST="true")
        self.assertEqual(htmx_response.status_code, 200)
        self.assertContains(htmx_response, "Floor Dumbbell Pullover")
        self.assertContains(htmx_response, "14.5 kg")

        we2 = WorkoutExercise.objects.get(workout=workout, exercise=self.pullover)
        self.assertEqual(we2.target_weight_kg, Decimal("14.50"))
        self.assertFalse(we2.is_bodyweight)

    def test_edit_exercise_weight_and_prescription(self):
        workout = Workout.objects.create(user=self.user, name="Home Workout")
        we = WorkoutExercise.objects.create(
            workout=workout,
            exercise=self.pullover,
            target_sets=3,
            target_reps=10,
            target_weight_kg=Decimal("10.00"),
            rest_seconds=60,
        )

        edit_ex_url = reverse(
            "workouts:workout_exercise_edit",
            kwargs={"workout_id": workout.id, "exercise_id": we.id},
        )

        # Update weight to 16 kg
        update_data = {
            "exercise": self.pullover.id,
            "target_sets": 4,
            "target_reps": 8,
            "target_weight_kg": "16",
            "rest_seconds": 60,
        }
        post_response = self.client.post(edit_ex_url, update_data, HTTP_HX_REQUEST="true")
        self.assertEqual(post_response.status_code, 200)
        self.assertContains(post_response, "16 kg")

        we.refresh_from_db()
        self.assertEqual(we.target_weight_kg, Decimal("16.00"))
        self.assertEqual(we.target_sets, 4)

        # Update back to bodyweight by clearing weight
        bw_update_data = {
            "exercise": self.pullover.id,
            "target_sets": 4,
            "target_reps": 8,
            "target_weight_kg": "",
            "rest_seconds": 60,
        }
        self.client.post(edit_ex_url, bw_update_data, HTTP_HX_REQUEST="true")
        we.refresh_from_db()
        self.assertIsNone(we.target_weight_kg)
        self.assertTrue(we.is_bodyweight)

    def test_duplicate_workout_preserves_weights(self):
        workout = Workout.objects.create(user=self.user, name="Push Workout")
        WorkoutExercise.objects.create(
            workout=workout,
            exercise=self.pushup_normal,
            target_sets=3,
            target_reps=15,
            target_weight_kg=None,
            order=1,
        )
        WorkoutExercise.objects.create(
            workout=workout,
            exercise=self.pullover,
            target_sets=3,
            target_reps=10,
            target_weight_kg=Decimal("15.00"),
            order=2,
        )

        dup_url = reverse("workouts:workout_duplicate", kwargs={"workout_id": workout.id})
        self.client.post(dup_url)

        cloned = Workout.objects.get(name="Push Workout (Copy)", user=self.user)
        self.assertEqual(cloned.exercise_count, 2)
        cloned_we2 = cloned.workout_exercises.get(exercise=self.pullover)
        self.assertEqual(cloned_we2.target_weight_kg, Decimal("15.00"))


class WorkoutScheduleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="scheduler_user", password="StrongPassword123!")
        self.client.force_login(self.user)
        self.pushup = Exercise.objects.get_or_create(
            name="Push-Up (Normal)",
            defaults={"muscle_group": "Chest", "description": "Pushup"},
        )[0]
        self.squat = Exercise.objects.get_or_create(
            name="Bodyweight Squat (Normal)",
            defaults={"muscle_group": "Legs", "description": "Squat"},
        )[0]
        self.wheel = Exercise.objects.get_or_create(
            name="Ab Wheel Rollout (Kneeling)",
            defaults={"muscle_group": "Core", "description": "Ab wheel"},
        )[0]

    def test_user_profile_week_start_preference(self):
        """Verify week start preference default is Monday, and can be changed to Sunday."""
        profile = self.user.profile
        self.assertEqual(profile.week_start_day, "monday")

        ordered_mon = profile.get_ordered_weekdays()
        self.assertEqual(ordered_mon[0][0], 0)
        self.assertEqual(ordered_mon[0][1], "Monday")
        self.assertEqual(ordered_mon[-1][0], 6)
        self.assertEqual(ordered_mon[-1][1], "Sunday")

        profile.week_start_day = "sunday"
        profile.save()
        ordered_sun = profile.get_ordered_weekdays()
        self.assertEqual(ordered_sun[0][0], 6)
        self.assertEqual(ordered_sun[0][1], "Sunday")
        self.assertEqual(ordered_sun[1][0], 0)
        self.assertEqual(ordered_sun[1][1], "Monday")

    def test_workout_exercise_scheduled_days_functionality(self):
        """Verify WorkoutExercise stores days and provides query helpers."""
        workout = Workout.objects.create(user=self.user, name="Split Workout")
        we = WorkoutExercise.objects.create(
            workout=workout,
            exercise=self.pushup,
            target_sets=3,
            target_reps=12,
            scheduled_days=[0, 2, 4],  # Mon, Wed, Fri
        )
        self.assertTrue(we.is_scheduled_on(0))
        self.assertFalse(we.is_scheduled_on(1))
        self.assertTrue(we.is_scheduled_on(2))
        self.assertEqual(we.scheduled_days_display, "Mon, Wed, Fri")
        self.assertEqual(we.scheduled_day_indices, [0, 2, 4])

        self.assertIn(we, workout.exercises_for_day(0))
        self.assertEqual(workout.exercises_for_day(1), [])

    def test_add_and_edit_exercise_with_scheduled_days_in_editor(self):
        """Verify editor form posts save days of the week for splits."""
        workout = Workout.objects.create(user=self.user, name="Push Workout")

        add_url = reverse("workouts:workout_exercise_add", kwargs={"workout_id": workout.id})
        data = {
            "exercise": self.pushup.id,
            "target_sets": 4,
            "target_reps": 12,
            "target_weight_kg": "",
            "rest_seconds": 60,
            "days": ["0", "3"],
        }
        res = self.client.post(add_url, data, HTTP_HX_REQUEST="true")
        self.assertEqual(res.status_code, 200)

        we = WorkoutExercise.objects.get(workout=workout, exercise=self.pushup)
        self.assertEqual(we.scheduled_days, [0, 3])

        edit_url = reverse(
            "workouts:workout_exercise_edit",
            kwargs={"workout_id": workout.id, "exercise_id": we.id},
        )
        edit_data = {
            "exercise": self.pushup.id,
            "target_sets": 4,
            "target_reps": 15,
            "target_weight_kg": "",
            "rest_seconds": 60,
            "days": ["1", "4"],
        }
        edit_res = self.client.post(edit_url, edit_data, HTTP_HX_REQUEST="true")
        self.assertEqual(edit_res.status_code, 200)

        we.refresh_from_db()
        self.assertEqual(we.scheduled_days, [1, 4])

    def test_schedule_week_view(self):
        """Verify weekly calendar renders with days, workouts, and exercises."""
        workout = Workout.objects.create(user=self.user, name="Upper Split")
        WorkoutExercise.objects.create(
            workout=workout,
            exercise=self.pushup,
            target_sets=3,
            target_reps=10,
            scheduled_days=[0],  # Monday
        )

        schedule_url = reverse("workouts:schedule")
        res = self.client.get(schedule_url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Weekly Workout Schedule")
        self.assertContains(res, "Upper Split")
        self.assertContains(res, "Push-Up (Normal)")
        self.assertContains(res, "Monday")

    def test_schedule_week_start_preference_toggle_view(self):
        """Verify switching between Monday and Sunday week start via POST."""
        toggle_url = reverse("workouts:schedule_week_start")
        res = self.client.post(toggle_url, {"week_start_day": "sunday"}, HTTP_HX_REQUEST="true")
        self.assertEqual(res.status_code, 200)

        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.week_start_day, "sunday")

    def test_schedule_day_view_and_filter_dropdown(self):
        """Verify clicking on a day opens the day editor and exercises filter dropdown works."""
        day_url = reverse("workouts:schedule_day", kwargs={"day_index": 0})  # Monday
        res = self.client.get(day_url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Monday Schedule")
        self.assertContains(res, "Latest added exercises")
        self.assertContains(res, "Least scheduled exercises")
        self.assertContains(res, "Most scheduled exercises")

        filter_url = reverse("workouts:schedule_filtered_exercises", kwargs={"day_index": 0})
        res_least = self.client.get(f"{filter_url}?filter=least_scheduled", HTTP_HX_REQUEST="true")
        self.assertEqual(res_least.status_code, 200)
        self.assertContains(res_least, "Scheduled: 0x")

        res_most = self.client.get(f"{filter_url}?filter=most_scheduled", HTTP_HX_REQUEST="true")
        self.assertEqual(res_most.status_code, 200)

    def test_schedule_day_add_and_remove_exercises(self):
        """Verify selecting exercises from day editor adds them to the schedule, and remove works."""
        workout = Workout.objects.create(user=self.user, name="Monday Routine")
        add_url = reverse("workouts:schedule_day_exercise_add", kwargs={"day_index": 0})

        post_data = {
            "selected_exercises": [self.squat.id, self.wheel.id],
            "workout_id": workout.id,
            "target_sets": 3,
            "target_reps": 12,
            "target_weight_kg": "",
            "rest_seconds": 60,
        }
        res = self.client.post(add_url, post_data)
        self.assertEqual(res.status_code, 302)

        we_squat = WorkoutExercise.objects.get(workout=workout, exercise=self.squat)
        self.assertIn(0, we_squat.scheduled_days)

        # Remove squat from Monday
        remove_url = reverse(
            "workouts:schedule_day_exercise_remove",
            kwargs={"day_index": 0, "workout_exercise_id": we_squat.id},
        )
        rem_res = self.client.post(remove_url)
        self.assertEqual(rem_res.status_code, 302)

        we_squat.refresh_from_db()
        self.assertNotIn(0, we_squat.scheduled_days)

    def test_assign_workout_recurring(self):
        """Verify assigning a workout at recurring intervals (daily, weekly, monthly)."""
        workout = Workout.objects.create(user=self.user, name="Leg Day")
        assign_url = reverse("workouts:schedule_workout_assign")

        # Assign Leg Day weekly on Wednesday (2)
        data = {
            "workout": workout.id,
            "day_of_week": 2,
            "recurrence": "weekly",
        }
        res = self.client.post(assign_url, data)
        self.assertEqual(res.status_code, 302)

        ws = WorkoutSchedule.objects.get(user=self.user, workout=workout)
        self.assertEqual(ws.day_of_week, 2)
        self.assertEqual(ws.recurrence, "weekly")

        # Delete recurring assignment
        del_url = reverse("workouts:schedule_assignment_delete", kwargs={"schedule_id": ws.id})
        del_res = self.client.post(del_url)
        self.assertEqual(del_res.status_code, 302)
        self.assertFalse(WorkoutSchedule.objects.filter(id=ws.id).exists())


class WorkoutExecutionAndResultTrackingTests(TestCase):
    """
    Test the User Flows Workout Steps 1-10 and PRD Workout Result Tracking:
    - View workouts scheduled for today
    - Start workout, Postpone, Skip options
    - Interactive counters and goal completion
    - Result tracking: well-rested status, notes, history
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="gym_warrior", password="StrongPassword123!")
        self.client.force_login(self.user)

        self.pushup = Exercise.objects.get_or_create(
            name="Push-Up (Normal)",
            defaults={"muscle_group": "Chest", "description": "Pushup"},
        )[0]
        self.wheel = Exercise.objects.get_or_create(
            name="Ab Wheel Rollout (Kneeling)",
            defaults={"muscle_group": "Core", "description": "Ab wheel"},
        )[0]

        # Create workout scheduled for today
        self.today_weekday = timezone.localdate().weekday()
        self.workout = Workout.objects.create(user=self.user, name="Daily Power Routine")
        self.we1 = WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.pushup,
            target_sets=3,
            target_reps=10,
            target_weight_kg=None,
            scheduled_days=[self.today_weekday],
        )

    def test_workout_today_view_renders_scheduled_workout(self):
        """Verify /workouts/today/ displays today's workout with Start/Postpone/Skip actions."""
        res = self.client.get(reverse("workouts:workout_today"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Daily Power Routine")
        self.assertContains(res, "Start Workout")
        self.assertContains(res, "Postpone for Next Day")
        self.assertContains(res, "Mark as Skipped")
        self.assertContains(res, "Push-Up (Normal)")

    def test_workout_postpone_action(self):
        """Verify postponing today's workout moves scheduled exercises to tomorrow."""
        tomorrow_weekday = (self.today_weekday + 1) % 7
        res = self.client.post(reverse("workouts:workout_postpone"))
        self.assertEqual(res.status_code, 302)

        self.we1.refresh_from_db()
        self.assertIn(tomorrow_weekday, self.we1.scheduled_days)
        self.assertNotIn(self.today_weekday, self.we1.scheduled_days)

        log = WorkoutLog.objects.filter(user=self.user, status="postponed").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.workout, self.workout)

    def test_workout_skip_action(self):
        """Verify marking today's workout as skipped logs a skipped record in WorkoutLog."""
        res = self.client.post(reverse("workouts:workout_skip"), {"notes": "Feeling sick today"})
        self.assertEqual(res.status_code, 302)

        log = WorkoutLog.objects.filter(user=self.user, status="skipped").first()
        self.assertIsNotNone(log)
        self.assertFalse(log.all_goals_completed)
        self.assertIn("Feeling sick today", log.notes)

    def test_workout_save_session_with_result_tracking(self):
        """
        Verify saving workout session creates a completed log with:
        - all_goals_completed (True or False)
        - well_rested (True or False to guide recovery)
        - notes
        - snapshot of exercises
        """
        save_url = reverse("workouts:workout_save_session")
        post_data = {
            "workout_id": self.workout.id,
            "workout_name": self.workout.name,
            "well_rested": "0",  # User reported feeling fatigued
            "all_goals_completed": "1",
            "notes": "Good pump, but muscles felt tight and tired. Need more rest.",
            "exercise_id": [self.we1.id],
            "exercise_name": [self.pushup.name],
            "exercise_sets": ["3"],
            "exercise_reps": ["10"],
            "exercise_weight": ["0"],
            "exercise_completed": [str(self.we1.id)],
        }
        res = self.client.post(save_url, post_data)
        self.assertRedirects(res, reverse("workouts:workout_history"))

        log = WorkoutLog.objects.filter(user=self.user, status="completed").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.workout, self.workout)
        self.assertTrue(log.all_goals_completed)
        self.assertFalse(log.well_rested)  # Correctly captured fatigued flag
        self.assertIn("Need more rest", log.notes)
        self.assertEqual(len(log.exercise_data), 1)
        self.assertTrue(log.exercise_data[0]["completed"])

    def test_workout_history_view(self):
        """Verify workout history displays logged records and rest stats."""
        WorkoutLog.objects.create(
            user=self.user,
            workout=self.workout,
            workout_name="Heavy Legs",
            status="completed",
            all_goals_completed=True,
            well_rested=False,
            notes="Tired hamstrings",
        )
        res = self.client.get(reverse("workouts:workout_history"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Heavy Legs")
        self.assertContains(res, "Fatigue Logged")
        self.assertContains(res, "All Goals Completed")
        self.assertContains(res, "Tired hamstrings")
