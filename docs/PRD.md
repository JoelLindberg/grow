# Product Requirements Document - GROW

## Vision
*If you are strong, you have to be kind.*  
*A strong body and mind to be kind.*
*Strong Body - Strong Mind*

**The stronger you get, the kinder you become**

"Cultivating a strong body and mind creates the foundation necessary to be kind. When you are physically resilient and mentally balanced, you manage stress better, allowing you to extend genuine empathy and compassion to others without depleting your own energy."

## MVP Features

### 1. Workout plans
* Defines structure of a workout
    - Exercise
            - Sets
            - Reps
            - Rest
    - A workout plan is defined by a name and the exercises that make up the workout plan.
    - There can be as many workout plans as the user wants.
    - Workout plans can be created, edited, and deleted by the user.
* Workout schedule **Prioritized feature**
    - Implements workout plans according to user selection
    - The user will be able to assign workout plans at recurring intervals (daily, weekly, monthly).
* Workout result tracking **Prioritized feature**
    - Tracks results of workouts
        - If all goals were completed or not
        - Well rested or not. This can help guiding the user to implement more rest days.
        - Any notes the user wants to add
* Plant based meal planning
    - Foods that (when combined) make up full amino acid chains
    - Protein calculation per meal
    - Protein calculation per day

### 2. User Access & Authentication (Invite-Only)
* **No Open Self-Service Registration**: To prevent platform abuse and eliminate spam management overhead, public registration is disabled initially.
* **Admin-Managed Invitations**:
    - Admins generate invitations from the admin panel by entering the invitee's email address.
    - An invitation email is sent containing a secure, unguessable registration link.
* **Token Protection & Expiration**:
    - High-entropy cryptographic token in the URL (`/register/<token>/`) to prevent brute-force guessing.
    - Time-limited validity (e.g., expires after 48–72 hours).
    - Single-use policy: token is invalidated immediately upon successful registration.
    - Bound to the invited email address.



