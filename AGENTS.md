# GROW — AI Agent Instructions & Project Manifest

## Project Overview
GROW is a mobile-first Progressive Web App (PWA) for workout logging and plant-based meal planning.
- **Product Spec & Features**: See [docs/PRD.md](docs/PRD.md)
- **Technical Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **user flows and intended usage**: See [docs/USER-FLOWS.md](docs/USER-FLOWS.md)

## Hard Technical Guardrails
1. **Resource Constraints**: Target host has 1 vCPU and 1GB RAM. Keep backend code lean, avoid heavy background processes or memory-heavy libraries. WSGI only (no ASGI/websockets required).
2. **Interactivity Boundary**:
   - **Alpine.js**: Zero-latency client UI state only (e.g., set/rep counters, countdown timers, stopwatch, local persistence).
   - **HTMX**: Server communication and partial HTML swaps (saving sets, completing workouts, dashboard widgets).
   - Do NOT introduce React/Vue/SPA frameworks.
3. **Offline Resilience**: Workout logging must work in poor gym connectivity (cache shell + localStorage sync).
4. **Design Philosophy**: Mobile-first, high-contrast dark mode, large touch targets (minimum 44x44px for gym usability).

## Coding Conventions
* Try not to write *clever* Pythonista-style code. Write boring, explicit code instead.
* Avoid language features that were introduced to Python but aren't that common in other C family languages, with the only exceptions being if it would make sense in terms of performance or if it is required to use this feature in Django.
* Write code that is easy to understand and maintain.
* The style of the code should respect how it must be written in Python for performance reasons.

## Python venv

For development, always use a python virtual environment. Don't use the system python.
* Activate the virtual environment with: `source ./venv/bin/activate`
* Expect it to already be available. You do not need to create it.
* Do not run `pip install` or any other pip command without activating the virtual environment.

## Command Cheatsheet

```bash
# Start / stop local MariaDB 11.4 container (via Colima / Docker Compose)
docker compose up -d
docker compose down

# Start development server
python manage.py runserver

# Create / apply database migrations
python manage.py makemigrations
python manage.py migrate

# Create admin superuser
python manage.py createsuperuser

# Run Django system checks
python manage.py check

# Open Django shell
python manage.py shell
```

## Testing

```bash
# Run all tests
python manage.py test

# Run tests for a specific app
python manage.py test accounts
python manage.py test workouts
python manage.py test nutrition
```
