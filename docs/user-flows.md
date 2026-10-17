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