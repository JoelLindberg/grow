from django.db import migrations


def seed_home_exercises(apps, schema_editor):
    Exercise = apps.get_model("workouts", "Exercise")

    home_exercises = [
        # Chest (Home variations: pushups narrow/normal/wide, floor pullover, floor press/fly)
        ("Push-Up (Normal)", "Chest", "Standard shoulder-width push-up on the floor targeting chest, triceps, and core."),
        ("Push-Up (Narrow / Diamond)", "Chest", "Hands close together forming a diamond or narrow base to emphasize triceps and inner chest."),
        ("Push-Up (Wide)", "Chest", "Wide hand placement on the floor maximizing pectoral stretch and outer chest engagement."),
        ("Decline Push-Up", "Chest", "Feet elevated on a chair, couch, or bed to target the upper clavicular pectorals."),
        ("Incline Push-Up", "Chest", "Hands elevated on a chair or couch for controlled tempo or warmups."),
        ("Floor Dumbbell Pullover", "Chest", "Lying on the floor, raising a dumbbell in a controlled overhead arc to stretch and load the chest and lats."),
        ("Floor Dumbbell Press", "Chest", "Lying on the floor, pressing dumbbells upward with safe floor-stopped elbow depth."),
        ("Floor Dumbbell Flyes", "Chest", "Lying on the floor, wide arc flyes isolating the pectorals with safe floor support."),

        # Legs (Home variations: squats normal/wide, calf raises standing/single-leg, dumbbells)
        ("Bodyweight Squat (Normal)", "Legs", "Shoulder-width stance bodyweight squat targeting quads, glutes, and core."),
        ("Bodyweight Squat (Wide / Sumo)", "Legs", "Wide-stance squat emphasizing adductors (inner thighs) and glute activation."),
        ("Dumbbell Goblet Squat", "Legs", "Holding a dumbbell vertically against chest in a standard stance."),
        ("Dumbbell Squat (Normal Stance)", "Legs", "Holding dumbbells at sides in a standard shoulder-width stance."),
        ("Dumbbell Squat (Wide / Sumo Stance)", "Legs", "Wide stance holding a dumbbell hanging between legs for inner thigh and glute load."),
        ("Bulgarian Split Squat (Bodyweight)", "Legs", "Unilateral leg exercise with rear foot elevated on a chair or couch."),
        ("Bulgarian Split Squat (Dumbbell)", "Legs", "Unilateral Bulgarian split squat holding dumbbells at sides for progression."),
        ("Standing Calf Raise", "Legs", "Two-legged calf raise on flat floor or step edge for gastrocnemius."),
        ("Single-Leg Calf Raise", "Legs", "Bodyweight unilateral calf raise on one leg for concentrated intensity."),
        ("Single-Leg Calf Raise (Dumbbell)", "Legs", "Holding a dumbbell in one hand while performing single-leg calf raises."),
        ("Walking Lunges", "Legs", "Dynamic forward lunges targeting quads, glutes, and balance."),

        # Core (Focus on the wheel on the ground + bodyweight)
        ("Ab Wheel Rollout (Kneeling)", "Core", "Kneeling on floor/mat, rolling the small ab wheel forward into extension and contracting back."),
        ("Ab Wheel Rollout (Isometric Pause)", "Core", "Rolling the ab wheel out and pausing for 2-3 seconds at peak extension."),
        ("Plank", "Core", "Isometric forearm hold on the floor for anti-extension core stability."),
        ("Side Plank", "Core", "Unilateral lateral core hold strengthening obliques and hips."),
        ("Lying Leg Raise", "Core", "Lying flat on the floor, raising straight legs toward ceiling for lower abdominal strength."),
        ("Mountain Climbers", "Core", "Dynamic alternating knee drives from push-up position on the floor."),

        # Back (Home dumbbells + bodyweight)
        ("Dumbbell Bent-Over Row", "Back", "Hinged at hips with dumbbells, rowing towards waist for lat and rhomboid thickness."),
        ("Single-Arm Dumbbell Row", "Back", "One-arm dumbbell row using a chair or couch for torso support."),
        ("Dumbbell Romanian Deadlift", "Back", "Hip-hinge movement holding dumbbells along shins for hamstrings, glutes, and lower back."),
        ("Floor Back Extension (Superman)", "Back", "Lying prone on the floor, simultaneously lifting arms, chest, and legs to strengthen the posterior chain."),

        # Shoulders (Dumbbells + bodyweight)
        ("Dumbbell Overhead Press", "Shoulders", "Seated or standing vertical dumbbell shoulder press."),
        ("Dumbbell Lateral Raise", "Shoulders", "Side raises with dumbbells targeting lateral deltoid width."),
        ("Dumbbell Front Raise", "Shoulders", "Front raises isolating the anterior deltoid."),
        ("Dumbbell Rear Delt Flye", "Shoulders", "Hinged forward with light dumbbells, flying outward to isolate rear deltoids."),
        ("Pike Push-Up", "Shoulders", "Bodyweight inverted push-up targeting vertical pressing power in the deltoids."),

        # Arms (Dumbbells + bodyweight)
        ("Dumbbell Bicep Curl", "Arms", "Classic standing or seated dumbbell bicep curl."),
        ("Dumbbell Hammer Curl", "Arms", "Neutral grip dumbbell curl emphasizing brachialis and forearms."),
        ("Dumbbell Concentration Curl", "Arms", "Seated curl with elbow braced against inner thigh for peak bicep isolation."),
        ("Chair Dips (Bodyweight)", "Arms", "Tricep dips using the edge of a sturdy chair, bench, or couch."),
        ("Overhead Dumbbell Tricep Extension", "Arms", "Holding a dumbbell overhead with both hands, lowering behind head and extending elbows."),
        ("Floor Dumbbell Skull Crushers", "Arms", "Lying flat on the floor, lowering dumbbells toward ears and pressing to lockout."),

        # Full Body
        ("Dumbbell Clean and Press", "Full Body", "Explosive movement bringing dumbbells from floor/hang to shoulders and pressing overhead."),
        ("Burpees", "Full Body", "Bodyweight floor chest-to-ground drop followed by jump for metabolic conditioning."),
    ]

    for name, muscle_group, description in home_exercises:
        Exercise.objects.update_or_create(
            name=name,
            defaults={"muscle_group": muscle_group, "description": description},
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("workouts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_home_exercises, noop),
    ]
