# UX workflows

## Dashboard

1. Login
2. You will see a dashboard with widgets:
    - Workouts
      - Today's Workouts
        - A "Start Workout" button is displayed next to each scheduled workout
        - If there are no workouts scheduled for today, the user will see a message saying "No workouts scheduled for today"
        - If all `Workouts` have been marked as completed for the given day the widget should display "All workouts completed for today"
      - Edit Workouts
        - Takes you to the full `Workouts` view where you can edit, create or delete workouts
    - Meals
      - Today's Meals
      - Edit Meals
        - Leave this blank for now.
    - Weekly Schedule
      - A very compact overview of your workouts for the week.
        - Show the days that have scheduled `Workouts`
        - Show the `Workouts` count for the scheduled days
      - Edit Schedule
        - Takes you to the full `Schedule` view where you can add, remove and clear all workouts from the weekly schedule.
    - Workout History
      - How many workouts have been completed and what the completion rate is (percentage)
3. If you decide not to click on any of the above widgets you can also navigate to the full `Workouts`, `Meals`, `Weekly Schedule` and `Workout History` views using the navigation menu.


## Today's Workout
Intended usage workflow for performing a Workout:

1. Login
2. You will see the Dashboard with Today's Workout widget
4. The `Workout` widget shows the `Workouts` scheduled for today
    - Scheduled `Workouts` that have been marked as completed should not be shown
5. You will have the options:
    * Start workout
    * Postpone workout for the next day
    * Mark as skipped
6. Starting the workout will take you to the `Workout Perform view` where you will see your `Workout` (list of exercises, sets, reps and weight)
7. Next to each exercise in the list there will pre-filled counters
    - Sets should display 0 / TOTAL SETS set in the `Workout` for the given exercise.
    - Reps should display the reps for the current set. The user should still be able to increment/decrement reps with + and - buttons in case they want to do more/less reps than what is set in the `Workout`.
    - Weights should display the weight for the current set. The user should still be able to increment/decrement weights with + and - buttons in case they want to do more/less weight than what is set in the `Workout`.
    - It's important to save any increments/decrements of any of the above parameters to the cache/storage so that the user doesn't lose their progress if they close the app or the page.
8. A checkbox to mark each exercise as completed. When checked, the exercise will be marked as completed.
    - It's important to save the status of the checkbox (checked/unchecked) to the cache/storage so that the user doesn't lose their progress if they close the app or the page.
9. When the user has completed all exercises, the workout will be marked as completed.
10. The user can then click a button to save the workout and it will be added to the workout history.
    - This will save and mark the `Workout` as completed permanently in the database.


## Workouts view

Intended usage workflow for adding, removing and editing a Workout:
1. Login
2. Navigate to the **Workouts** view via the Dashboard or the Menu
3. Click on create `Workout` or Select an existing `Workout` (if any) to edit
4. Edit the `Workout`
    * Add exercises
        * Select an exercise from the exercise database
        * Set the number of sets
        * Set the number of reps per set
        * Set the weight (optional) if not set, then the exercise is bodyweight
        * Click on add exercise
    * Remove exercises
        * Click on remove exercise
    * Edit exercises
        * Click on edit exercise
        * Change the number of sets
        * Change the number of reps per set
        * Change the weight
        * Click on save exercise
5. Give the user the option to select which days of the week the Workout should be scheduled on.
6. Save the `Workout`


## Weekly Schedule

1. Login
2. Navigate to the Weekly Schedule by clicking on the in either in the Widget or the Menu.
3. You will see a calendar view of your `Workouts` for the week.
    - The title of the `Workout` should be visible in the calendar view for each day.
    - In finer text also display a count of the category (e.g Legs, Arms, Chest etc.) that make up the `Workout`.
    - Also show the number of total reps for the Workout for each category.
    - If a day is empty the option to "Add Workout" is displayed.
      - The schedule is updated/saved after adding a `Workout`.
4. You can click on one of the days to edit the schedule for that day.
    - You will be able to add and remove `Workouts` for that day.
      - The schedule is updated/saved after adding a `Workout`.


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