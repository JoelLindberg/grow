from django.db import migrations


def seed_exercises(apps, schema_editor):
    Exercise = apps.get_model("workouts", "Exercise")

    exercises = [
        # Chest (pushups, floor press/fly/pullover)
        ("Push-Up - Normal", "Chest", "Standard shoulder-width push-up on the floor targeting chest, triceps, and core."),
        ("Push-Up - Narrow / Diamond", "Chest", "Hands close together forming a diamond or narrow base to emphasize triceps and inner chest."),
        ("Push-Up - Wide", "Chest", "Wide hand placement on the floor maximizing pectoral stretch and outer chest engagement."),
        ("Push-Up - Decline", "Chest", "Feet elevated on a chair, couch, or bed to target the upper clavicular pectorals."),
        ("Push-Up - Incline", "Chest", "Hands elevated on a chair or couch for controlled tempo or warmups."),
        ("Chest Press - Dumbbell", "Chest", "Lying on the floor, pressing dumbbells upward with safe floor-stopped elbow depth."),
        ("Chest Fly - Dumbbell", "Chest", "Lying on the floor, wide arc flyes isolating the pectorals with safe floor support."),
        ("Chest Pullover - Dumbbell", "Chest", "Lying on the floor, raising a dumbbell in a controlled overhead arc to stretch and load the chest and lats."),

        # Legs (Squats, calf raises, lunges)
        ("Squat - Normal Stance", "Legs", "Standard shoulder-width stance squat targeting quads, glutes, and core."),
        ("Squat - Wide / Sumo Stance", "Legs", "Wide-stance squat emphasizing adductors (inner thighs) and glute activation."),
        ("Squat - Goblet", "Legs", "Holding a dumbbell vertically against chest in a standard stance."),
        ("Bulgarian Split Squat", "Legs", "Unilateral leg exercise with rear foot elevated on a chair, couch, or bench."),
        ("Calf Raise - Standing", "Legs", "Two-legged calf raise on flat floor or step edge for gastrocnemius."),
        ("Calf Raise - Single-Leg", "Legs", "Unilateral calf raise on one leg for concentrated intensity."),
        ("Lunge - Walking", "Legs", "Dynamic forward lunges targeting quads, glutes, and balance."),
        ("Lunge - Stationary", "Legs", "Forward lunges targeting quads and glutes."),
        ("Lunge - Reverse", "Legs", "Forward lunges targeting quads and glutes."),
        ("Lunge - Side", "Legs", "Forward lunges targeting quads and glutes."),
        ("Lunge - Curtsey", "Legs", "Forward lunges targeting quads and glutes."),

        # Core (ab wheel, planks, leg raises, twists)
        ("Ab Wheel Rollout - Kneeling", "Core", "Kneeling on floor/mat, rolling the small ab wheel forward into extension and contracting back."),
        ("Ab Wheel Rollout - Isometric Pause", "Core", "Rolling the ab wheel out and pausing for 2-3 seconds at peak extension."),
        ("Plank", "Core", "Isometric forearm hold on the floor for anti-extension core stability."),
        ("Plank - Side", "Core", "Unilateral lateral core hold strengthening obliques and hips."),
        ("Plank - Side with Leg Raise", "Core", "Side plank with alternating leg raises targeting hip abductors."),
        ("Leg Raise - Lying", "Core", "Lying flat on the floor, raising straight legs toward ceiling for lower abdominal strength."),
        ("Mountain Climber", "Core", "Dynamic alternating knee drives from push-up position on the floor."),
        ("Russian Twist", "Core", "Seated rotational exercise with feet on floor or elevated targeting the obliques."),
        ("Sit-Up", "Core", "Lying on floor with knees bent, curling the torso upward toward knees for upper abdominal and hip flexor strength."),

        # Back (Dumbbells + bodyweight)
        ("Bent-Over Row - Dumbbell", "Back", "Hinged at hips with dumbbells, rowing towards waist for lat and rhomboid thickness."),
        ("Single-Arm Row - Dumbbell", "Back", "One-arm dumbbell row using a chair or couch for torso support."),
        ("Romanian Deadlift - Dumbbell", "Back", "Hip-hinge movement holding dumbbells along shins for hamstrings, glutes, and lower back."),
        ("Back Extension - Floor (Superman)", "Back", "Lying prone on the floor, simultaneously lifting arms, chest, and legs to strengthen the posterior chain."),

        # Shoulders (Dumbbells + bodyweight)
        ("Overhead (Military) Press - Dumbbell", "Shoulders", "Seated or standing vertical dumbbell shoulder press."),
        ("Lateral Raise - Dumbbell", "Shoulders", "Side raises with dumbbells targeting lateral deltoid width."),
        ("Front Raise - Dumbbell", "Shoulders", "Front raises isolating the anterior deltoid."),
        ("Upright Row - Dumbbell", "Shoulders", "Standing dumbbell rows with elbows driving high and wide, targeting the lateral deltoids."),
        ("Rear Delt Fly - Dumbbell", "Shoulders", "Hinged forward with light dumbbells, flying outward to isolate rear deltoids."),
        ("Push-Up - Pike", "Shoulders", "Bodyweight inverted push-up targeting vertical pressing power in the deltoids."),
        
        # Arms (Dumbbells + bodyweight)
        ("Bicep Curl - Dumbbell", "Arms", "Classic standing or seated dumbbell bicep curl."),
        ("Bicep Curl - Reverse Grip, Dumbbell", "Arms", "Classic standing or seated dumbbell bicep curl with reverse grip."),
        ("Hammer Curl - Dumbbell", "Arms", "Neutral grip dumbbell curl emphasizing brachialis and forearms."),
        ("Concentration Curl - Dumbbell", "Arms", "Seated curl with elbow braced against inner thigh for peak bicep isolation."),
        ("Dip", "Arms", "Tricep dips using the edge of a sturdy chair, bench, or couch."),
        ("Overhead Tricep Extension - Dumbbell", "Arms", "Holding a dumbbell overhead with both hands, lowering behind head and extending elbows."),
        ("Skull Crusher - Floor Dumbbell", "Arms", "Lying flat on the floor, lowering dumbbells toward ears and pressing to lockout."),
        ("Wrist Curl - Dumbbell", "Arms", "Performing curls with the palms facing up or down to target the forearm flexors and extensors."),
        ("Wrist Curl - Reverse, Dumbbell", "Arms", "Performing curls with the palms facing up or down to target the forearm flexors and extensors."),

        # Full Body
        ("Clean and Press - Dumbbell", "Full Body", "Explosive movement bringing dumbbells from floor/hang to shoulders and pressing overhead."),
        ("Burpee", "Full Body", "Bodyweight floor chest-to-ground drop followed by jump for metabolic conditioning."),
    ]

    for name, muscle_group, description in exercises:
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
        migrations.RunPython(seed_exercises, noop),
    ]
