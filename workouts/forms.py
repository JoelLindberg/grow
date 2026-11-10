from django import forms
from workouts.models import Exercise, Workout, WorkoutExercise, WorkoutLog, WorkoutSchedule


class WorkoutForm(forms.ModelForm):
    """
    Form for creating and editing a workout's title, description,
    and scheduled days of the week.
    """

    DAY_CHOICES = [
        (0, "Mon"),
        (1, "Tue"),
        (2, "Wed"),
        (3, "Thu"),
        (4, "Fri"),
        (5, "Sat"),
        (6, "Sun"),
    ]

    days = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        help_text="Days of the week this workout is scheduled on.",
    )

    class Meta:
        model = Workout
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.scheduled_days:
            initial_days = []
            for d in self.instance.scheduled_days:
                initial_days.append(str(d))
            self.fields["days"].initial = initial_days

    def save(self, commit=True):
        instance = super().save(commit=False)
        selected_days = self.cleaned_data.get("days", [])
        parsed_days = []
        for d in selected_days:
            if str(d).isdigit():
                val = int(d)
                if 0 <= val <= 6 and val not in parsed_days:
                    parsed_days.append(val)
        parsed_days.sort()
        instance.scheduled_days = parsed_days
        if commit:
            instance.save()
        return instance


class WorkoutExerciseForm(forms.ModelForm):
    """
    Form for adding or editing an exercise within a workout.
    Provides touch-friendly controls for sets, reps, and weight (optional/bodyweight).
    """

    class Meta:
        model = WorkoutExercise
        fields = [
            "exercise",
            "target_sets",
            "target_reps",
            "target_weight_kg",
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["exercise"].queryset = Exercise.objects.all().order_by("muscle_group", "name")
        self.fields["target_weight_kg"].required = False

    def clean_target_weight_kg(self):
        val = self.cleaned_data.get("target_weight_kg")
        if val is None or val == 0:
            return None
        return val


class WorkoutScheduleForm(forms.ModelForm):
    """
    Form to assign a workout to recurring intervals (daily, weekly, monthly)
    or to specific days of the week.
    """

    class Meta:
        model = WorkoutSchedule
        fields = ["workout", "day_of_week", "recurrence"]
        widgets = {
            "workout": forms.Select(
                attrs={
                    "class": "input-gym cursor-pointer",
                    "required": True,
                }
            ),
            "day_of_week": forms.Select(
                attrs={
                    "class": "input-gym cursor-pointer",
                    "required": True,
                }
            ),
            "recurrence": forms.Select(
                attrs={
                    "class": "input-gym cursor-pointer",
                    "required": True,
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields["workout"].queryset = Workout.objects.filter(user=user).order_by("name")


class WorkoutLogForm(forms.ModelForm):
    """
    Form for recording workout session results:
    - All goals completed or not
    - Well rested or not
    - Notes
    """

    class Meta:
        model = WorkoutLog
        fields = ["all_goals_completed", "well_rested", "notes"]
        widgets = {
            "all_goals_completed": forms.CheckboxInput(
                attrs={"class": "accent-orange-500 w-5 h-5 rounded"}
            ),
            "well_rested": forms.CheckboxInput(
                attrs={"class": "accent-orange-500 w-5 h-5 rounded"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "input-gym resize-none",
                    "rows": 3,
                    "placeholder": "How did the workout feel? Any personal records or energy notes...",
                }
            ),
        }


# Backward compatibility aliases
WorkoutPlanForm = WorkoutForm
PlanExerciseForm = WorkoutExerciseForm
