# UX workflows
    
## Workout
Intended usage workflow for performing a workout:

1. Login
2. You will see a dashboard with widgets for workouts, meals, and progress
3. Pressing a widget will take you to the corresponding view
4. The workout view shows the workouts scheduled for today
5. You will have the options:
    * Start workout
    * Postpone workout for the next day
    * Mark as skipped
6. Starting the workout will show you a list of the exercises in the workout.
7. Next to each exercise in the list there will pre-filled counters for sets and reps to complete. There will also be + and - buttons next to the counters to increment/decrement reps and sets. 
8. A checkbox to marke each exercise as completed. When checked, the exercise will be marked as completed.
9. When the user has completed all exercises, the workout will be marked as completed.
10. The user can then click a button to save the workout and it will be added to the workout history.

## Workout editor

Intended usage workflow for editing a workout:
1. Login
2. Navigate to the **Workouts** view
3. Click on create `Workout` or Select an existing `Workout` (if any) to edit
4. Edit the `Workout`
    * Add exercises
        * Select an exercise from the exercise database
        * Set the number of sets
        * Set the number of reps per set
        * Set the rest time between sets (optional) default 60 seconds
        * Set the weight (optional) if not set, then the exercise is bodyweight
        * Click on add exercise
        * Select days of the week for the exercise to be scheduled on (this will update the calendar view). It should be a multi select. It should allow multiple exercises on a single day so that morning and evening splits are possible. A user could for example select Monday for "Bench Press" and also Monday for "Squat" resulting in two exercises on Monday.
    * Remove exercises
        * Click on remove exercise
    * Edit exercises
        * Click on edit exercise
        * Change the number of sets
        * Change the number of reps per set
        * Change the rest time between sets
        * Change the weight
        * Change the days of the week for the exercise to be scheduled on (this will update the calendar view). Exactly the same ui as when adding an exercise.
        * Click on save exercise
5. Save the `Workout`

## Workout Schedule

1. Login
2. Click on the Schedule link in the navbar
3. You will see a calendar view of your workouts for the week. The title of the workout should be visible in the calendar view for each day. In finer text also display the exercises that make up the `Workout`. Also show the number of sets, reps and weight for each exercise.
4. You can click on one of the days to edit the schedule for that day.
5. You should be presented with a drop down which allows you to select to filter on: the latest added exercises, the oldest exercises, the least scheduled exercises (because either it's an exercises that you need to implement more often or it should be removed) and the most scheduled exercises (to be able to find your favorites).
6. You will then be able to select one or more of the exercises and click add, which will add them to the current schedule for the selected day.



## User Invitation & Onboarding (Invite-Only)
Intended workflow for inviting a new member:

1. **Admin generates invitation**:
   * Admin navigates to the Admin Panel / Invitation Manager.
   * Admin enters the recipient's email address and clicks "Send Invitation".
   * System generates a secure, cryptographically random single-use token with a finite lifespan (e.g., 72 hours).
   * System sends an email with the link: `https://grow.app/register/<token>/`.
2. **Invitee registers**:
   * Invitee clicks the link in their email.
   * System validates:
     - Does the token exist in the database?
     - Has the token already been used?
     - Has the token expired (exceeded TTL)?
   * If valid:
     - Invitee is presented with the Registration form (email is pre-filled and locked).
     - Invitee chooses a username and strong password.
     - Upon submission, user account is created, the invite token is marked as accepted/invalidated, and the user is logged in.
   * If invalid/expired:
     - Invitee is presented with a clear message explaining that the invite link is invalid or expired, with instructions to request a fresh invite from the admin.