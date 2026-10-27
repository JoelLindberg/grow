# Generated for GROW: Initial clean migration defining all workout and scheduling models

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Exercise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('muscle_group', models.CharField(choices=[('Chest', 'Chest'), ('Back', 'Back'), ('Legs', 'Legs'), ('Shoulders', 'Shoulders'), ('Arms', 'Arms'), ('Core', 'Core'), ('Full Body', 'Full Body')], db_index=True, max_length=50)),
                ('description', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Exercise',
                'verbose_name_plural': 'Exercises',
                'ordering': ['muscle_group', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Workout',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workouts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Workout',
                'verbose_name_plural': 'Workouts',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='WorkoutExercise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('target_sets', models.PositiveIntegerField(default=3)),
                ('target_reps', models.PositiveIntegerField(default=10)),
                ('target_weight_kg', models.DecimalField(blank=True, decimal_places=2, help_text='Target weight in kg (optional; bodyweight if blank or 0).', max_digits=5, null=True)),
                ('rest_seconds', models.PositiveIntegerField(default=60, help_text='Rest time in seconds between sets (default: 60s).')),
                ('scheduled_days', models.JSONField(blank=True, default=list, help_text='Days of the week this exercise is scheduled (0=Monday, 6=Sunday).')),
                ('order', models.PositiveIntegerField(default=0)),
                ('exercise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workout_exercises', to='workouts.exercise')),
                ('workout', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workout_exercises', to='workouts.workout')),
            ],
            options={
                'verbose_name': 'Workout Exercise',
                'verbose_name_plural': 'Workout Exercises',
                'ordering': ['order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='WorkoutSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day_of_week', models.PositiveSmallIntegerField(choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')], default=0, help_text='Day of the week (0=Monday, 6=Sunday).')),
                ('recurrence', models.CharField(choices=[('weekly', 'Weekly'), ('daily', 'Daily'), ('monthly', 'Monthly')], default='weekly', help_text='Recurring interval: daily, weekly, or monthly.', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workout_schedules', to=settings.AUTH_USER_MODEL)),
                ('workout', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedules', to='workouts.workout')),
            ],
            options={
                'verbose_name': 'Workout Schedule',
                'verbose_name_plural': 'Workout Schedules',
                'ordering': ['day_of_week', 'workout__name'],
            },
        ),
        migrations.CreateModel(
            name='WorkoutLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('workout_name', models.CharField(max_length=100)),
                ('date', models.DateField(default=django.utils.timezone.localdate)),
                ('status', models.CharField(choices=[('completed', 'Completed'), ('skipped', 'Skipped'), ('postponed', 'Postponed')], default='completed', max_length=20)),
                ('all_goals_completed', models.BooleanField(default=False, help_text='Tracks whether all exercise goals were completed.')),
                ('well_rested', models.BooleanField(default=True, help_text='Tracks whether the user felt well-rested before/during workout.')),
                ('notes', models.TextField(blank=True, default='', help_text='User notes and reflections on the workout.')),
                ('exercise_data', models.JSONField(blank=True, default=list, help_text='Snapshot of exercises, targets, completed sets/reps.')),
                ('completed_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workout_logs', to=settings.AUTH_USER_MODEL)),
                ('workout', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='logs', to='workouts.workout')),
            ],
            options={
                'verbose_name': 'Workout Log',
                'verbose_name_plural': 'Workout Logs',
                'ordering': ['-date', '-completed_at'],
            },
        ),
    ]
