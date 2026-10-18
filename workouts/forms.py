from django import forms
from workouts.models import Exercise, PlanExercise, WorkoutPlan


class WorkoutPlanForm(forms.ModelForm):
    """
    Form for creating and editing a workout plan's title and description.
    """

    class Meta:
        model = WorkoutPlan
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "input-gym",
                    "placeholder": "e.g., Upper Body Push & Core",
                    "autocomplete": "off",
                    "required": True,
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "input-gym resize-none",
                    "rows": 2,
                    "placeholder": "Brief notes, intensity, or focus areas (optional)...",
                }
            ),
        }


class PlanExerciseForm(forms.ModelForm):
    """
    Form for adding or editing an exercise within a workout plan.
    Provides touch-friendly controls for sets, reps, weight (optional/bodyweight),
    and rest intervals (default 60s).
    """

    class Meta:
        model = PlanExercise
        fields = [
            "exercise",
            "target_sets",
            "target_reps",
            "target_weight_kg",
            "rest_seconds",
        ]
        widgets = {
            "exercise": forms.Select(
                attrs={
                    "class": "input-gym cursor-pointer",
                    "id": "id_exercise",
                }
            ),
            "target_sets": forms.NumberInput(
                attrs={
                    "class": "input-gym text-center font-bold text-lg",
                    "min": 1,
                    "max": 30,
                    "id": "id_target_sets",
                }
            ),
            "target_reps": forms.NumberInput(
                attrs={
                    "class": "input-gym text-center font-bold text-lg",
                    "min": 1,
                    "max": 200,
                    "id": "id_target_reps",
                }
            ),
            "target_weight_kg": forms.NumberInput(
                attrs={
                    "class": "input-gym text-center font-bold text-lg",
                    "min": 0,
                    "max": 500,
                    "step": "0.5",
                    "placeholder": "Bodyweight",
                    "id": "id_target_weight_kg",
                }
            ),
            "rest_seconds": forms.NumberInput(
                attrs={
                    "class": "input-gym text-center font-bold text-lg",
                    "min": 0,
                    "max": 600,
                    "step": 5,
                    "id": "id_rest_seconds",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Group exercises alphabetically by muscle group for clear selection
        self.fields["exercise"].queryset = Exercise.objects.all().order_by("muscle_group", "name")
        self.fields["rest_seconds"].initial = 60
        self.fields["target_weight_kg"].required = False

    def clean_target_weight_kg(self):
        val = self.cleaned_data.get("target_weight_kg")
        if val is None or val == 0:
            return None
        return val
