# GROW - Strength and Kindness

**The stronger you get, the kinder you become**

## Ownership of Body and Mind

"Cultivating a strong body and mind creates the foundation necessary to be kind. When you are physically resilient and mentally balanced, you manage stress better, allowing you to extend genuine empathy and compassion to others without depleting your own energy."

This app will help you plan your workouts and plant based meals. It will be built as a PWA with offline-first capabilities to ensure it can be used in any environment.

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| Backend | Django 5.x (Python 3.12+) |
| Frontend | Django Templates + Tailwind CSS |
| Interactivity | HTMX (server sync) + Alpine.js (client state) |
| Database | MariaDB 11.4 (prod & local Docker) / SQLite (optional fallback) |
| Deployment | PWA with Service Worker |

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical design and [docs/PRD.md](docs/PRD.md) for the product spec.

## Development Setup

### Prerequisites

- **Python 3.12+**
- **Docker & Docker Compose** (e.g., Colima + `docker-cli` on macOS)

### Getting Started

1. **Create and activate a virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure environment variables**:
    ```bash
    cp .env.example .env
    ```

4. **Start local MariaDB 11.4 container**:
    ```bash
    colima start   # if using Colima on macOS and not already running
    docker compose up -d
    ```

5. **Run database migrations**:
    ```bash
    python manage.py migrate
    ```

6. **Create a superuser** (for Django Admin access):
    ```bash
    python manage.py createsuperuser
    ```

7. **Start the development server**:
    ```bash
    python manage.py runserver
    ```

8. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser. The admin panel is at [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/).


**Optional - Run tests**

1. `python manage.py test`
