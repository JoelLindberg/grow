from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.views.generic import TemplateView

from workouts.models import Exercise, PlanExercise, WorkoutPlan

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
        self.assertIn("Autumn Palette: Oak, Maple &amp; Pumpkin", content)


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

    def test_workout_plan_creation_and_properties(self):
        plan = WorkoutPlan.objects.create(
            user=self.user,
            name="Home Push & Core",
            description="Pushups and ab wheel",
        )
        self.assertEqual(str(plan), "Home Push & Core (gym_rat)")
        self.assertEqual(plan.exercise_count, 0)
        self.assertEqual(plan.total_sets, 0)
        self.assertEqual(plan.muscle_groups, [])
        self.assertEqual(plan.estimated_duration_minutes, 0)

        # Exercise 1: Bodyweight pushups (no weight set)
        pe1 = PlanExercise.objects.create(
            plan=plan,
            exercise=self.pushup_normal,
            target_sets=4,
            target_reps=15,
            target_weight_kg=None,
            rest_seconds=60,
            order=1,
        )
        self.assertTrue(pe1.is_bodyweight)
        self.assertEqual(pe1.weight_display, "Bodyweight")
        self.assertEqual(pe1.rest_seconds, 60)

        # Exercise 2: Weighted pullover
        pe2 = PlanExercise.objects.create(
            plan=plan,
            exercise=self.pullover,
            target_sets=3,
            target_reps=10,
            target_weight_kg=Decimal("12.50"),
            rest_seconds=60,
            order=2,
        )
        self.assertFalse(pe2.is_bodyweight)
        self.assertEqual(pe2.weight_display, "12.5 kg")
        self.assertIn("@ 12.5 kg", str(pe2))

        self.assertEqual(plan.exercise_count, 2)
        self.assertEqual(plan.total_sets, 7)
        self.assertTrue(plan.estimated_duration_minutes > 0)


class WorkoutPlanWorkflowTests(TestCase):
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
        url = reverse("workouts:plan_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_plan_list_view_empty_state_and_populated(self):
        response = self.client.get(reverse("workouts:plan_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No workout plans yet")

        plan = WorkoutPlan.objects.create(user=self.user, name="Home Strength")
        response = self.client.get(reverse("workouts:plan_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Home Strength")

    def test_plan_create_workflow(self):
        url = reverse("workouts:plan_create")
        post_data = {
            "name": "Home Dumbbell & Core",
            "description": "Dumbbells and wheel",
        }
        response = self.client.post(url, post_data)
        plan = WorkoutPlan.objects.get(name="Home Dumbbell & Core", user=self.user)
        self.assertRedirects(response, reverse("workouts:plan_edit", kwargs={"plan_id": plan.id}))

    def test_plan_user_isolation(self):
        secret_plan = WorkoutPlan.objects.create(user=self.other_user, name="Secret Plan")
        edit_url = reverse("workouts:plan_edit", kwargs={"plan_id": secret_plan.id})
        self.assertEqual(self.client.get(edit_url).status_code, 404)

        delete_url = reverse("workouts:plan_delete", kwargs={"plan_id": secret_plan.id})
        self.assertEqual(self.client.post(delete_url).status_code, 404)
        self.assertTrue(WorkoutPlan.objects.filter(id=secret_plan.id).exists())

    def test_add_exercise_bodyweight_and_weighted(self):
        plan = WorkoutPlan.objects.create(user=self.user, name="Push Plan")
        add_url = reverse("workouts:plan_exercise_add", kwargs={"plan_id": plan.id})

        # 1. Add bodyweight exercise (no weight specified)
        bw_data = {
            "exercise": self.pushup_normal.id,
            "target_sets": 4,
            "target_reps": 12,
            "target_weight_kg": "",
            "rest_seconds": 60,
        }
        response = self.client.post(add_url, bw_data)
        self.assertRedirects(response, reverse("workouts:plan_edit", kwargs={"plan_id": plan.id}))

        pe1 = PlanExercise.objects.get(plan=plan, exercise=self.pushup_normal)
        self.assertIsNone(pe1.target_weight_kg)
        self.assertTrue(pe1.is_bodyweight)
        self.assertEqual(pe1.weight_display, "Bodyweight")

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

        pe2 = PlanExercise.objects.get(plan=plan, exercise=self.pullover)
        self.assertEqual(pe2.target_weight_kg, Decimal("14.50"))
        self.assertFalse(pe2.is_bodyweight)

    def test_edit_exercise_weight_and_prescription(self):
        plan = WorkoutPlan.objects.create(user=self.user, name="Home Workout")
        pe = PlanExercise.objects.create(
            plan=plan,
            exercise=self.pullover,
            target_sets=3,
            target_reps=10,
            target_weight_kg=Decimal("10.00"),
            rest_seconds=60,
        )

        edit_ex_url = reverse("workouts:plan_exercise_edit", kwargs={"plan_id": plan.id, "exercise_id": pe.id})

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

        pe.refresh_from_db()
        self.assertEqual(pe.target_weight_kg, Decimal("16.00"))
        self.assertEqual(pe.target_sets, 4)

        # Update back to bodyweight by clearing weight
        bw_update_data = {
            "exercise": self.pullover.id,
            "target_sets": 4,
            "target_reps": 8,
            "target_weight_kg": "",
            "rest_seconds": 60,
        }
        self.client.post(edit_ex_url, bw_update_data, HTTP_HX_REQUEST="true")
        pe.refresh_from_db()
        self.assertIsNone(pe.target_weight_kg)
        self.assertTrue(pe.is_bodyweight)

    def test_duplicate_plan_preserves_weights(self):
        plan = WorkoutPlan.objects.create(user=self.user, name="Push Plan")
        PlanExercise.objects.create(
            plan=plan,
            exercise=self.pushup_normal,
            target_sets=3,
            target_reps=15,
            target_weight_kg=None,
            order=1,
        )
        PlanExercise.objects.create(
            plan=plan,
            exercise=self.pullover,
            target_sets=3,
            target_reps=10,
            target_weight_kg=Decimal("15.00"),
            order=2,
        )

        dup_url = reverse("workouts:plan_duplicate", kwargs={"plan_id": plan.id})
        self.client.post(dup_url)

        cloned_plan = WorkoutPlan.objects.get(name="Push Plan (Copy)", user=self.user)
        self.assertEqual(cloned_plan.exercise_count, 2)
        cloned_pe2 = cloned_plan.plan_exercises.get(exercise=self.pullover)
        self.assertEqual(cloned_pe2.target_weight_kg, Decimal("15.00"))
