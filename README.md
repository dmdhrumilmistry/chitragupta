# Chitragupta Backend

Chitragupta is a powerful vulnerability management and analysis tool designed to help organizations secure their codebases. It currently focuses on secret scanning and repository management, with an architecture built for scalability and future extensibility.

## Features

- **GitHub Organization Sync**: Automatically synchronizes users and repositories from connected GitHub organizations.
- **Secret Scanning**: Integrates with **Trufflehog** to scan repositories for secrets and sensitive information.
- **Vulnerability Tracking**: Stores and manages scan results, allowing for tracking of verified and unverified secrets.
- **Scalable Architecture**: Built with Django, Celery, and Redis to handle large-scale scanning tasks asynchronously.

## Tech Stack

- **Framework**: Django 5.2
- **Database**: MongoDB (via `django-mongodb-backend`)
- **Task Queue**: Celery
- **Broker/Cache**: Redis
- **Containerization**: Docker & Docker Compose
- **Package Management**: UV

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose
- [UV](https://github.com/astral-sh/uv) (optional, for local python management)

### Installation & Running

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd chitragupta/backend
   ```

2. **Environment Configuration:**
   Copy the sample environment file and configure your secrets.
   ```bash
   cp .env.sample .env.dev
   ```
   *Note: Ensure you set your `GITHUB_APP_ID`, `GITHUB_PRIVATE_KEY`, and other GitHub App credentials in `.env.dev`.*

3. **Start the Application:**
   Use Docker Compose to build and start all services (Backend, Mongo, Redis, Celery Worker, Celery Beat, Flower).
   ```bash
   docker compose up -d --build
   ```

4. **Access the Application:**
   - **Backend API**: `http://localhost:8000`
   - **Flower (Celery Monitoring)**: `http://localhost:5555`

### Development Commands

- **Run Migrations:**
  ```bash
  docker compose exec backend uv run python manage.py migrate
  ```

- **Create Superuser:**
  ```bash
  docker compose exec backend uv run python manage.py createsuperuser
  ```

- **Open Python Shell:**
  ```bash
  docker compose exec -it backend uv run python manage.py shell -i ipython
  ```

## Future Roadmap

We are actively working on expanding Chitragupta's capabilities. Planned features include:

- **Integration with additional Security Tools**: Support for SAST (Static Application Security Testing) and DAST (Dynamic Application Security Testing) tools.
- **Enhanced Reporting**: Comprehensive dashboards and reporting for security posture.
- **Alerting**: Real-time notifications for critical vulnerabilities.