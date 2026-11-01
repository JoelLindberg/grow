# Changelog

All notable changes to GROW will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to a simple Major.Minor versioning scheme.

---

## [0.1-alpha] - 2026-11-01

### Highlights
- Initial alpha deployment ready for early testing on MariaDB 11.4 with Phusion Passenger.

### Added
- **Authentication & Profiles**: Account registration, login, logout, and profile management (`accounts`).
- **Workout Logging & Scheduling**:
  - `Workout`, `WorkoutExercise`, `WorkoutSchedule`, and `WorkoutLog` models.
  - Interactive workout routine editor with Alpine.js set and rep counter.
  - Quick-logging interface at `/workouts/today/`.
  - Workout history log at `/workouts/history/`.
  - Weekly and daily split scheduling views.
- **Database Migrations (`workouts`)**:
  - `0001_initial`: Core tables for exercises, workouts, and schedules.
  - `0002_seed_home_exercises`: Seed library of bodyweight and kettlebell exercises.
- **Environment & Deployment**:
  - Production security defaults (fail-closed `DEBUG=False` and secret key validation).
  - Configurable `STATIC_ROOT`, `CSRF_TRUSTED_ORIGINS`, and `ENV_FILE`.
  - Local MariaDB 11.4 container with `docker-compose.yml`.

