# Copilot Instructions for MoneyFlow Mirror

## Project Overview

- **Stack:** Django 4, Gunicorn, PostgreSQL, Cloudflare R2 (via `django-storages`), Docker
- **Main Apps:** `gastos` (expenses), `ingresos` (income), `usuarios` (users)
- **Purpose:** Personal finance management—track, categorize, and visualize income/expenses.

## Architecture & Patterns

- **App Structure:** Each domain (`gastos`, `ingresos`, `usuarios`) is a Django app with its own models, views, templates, and tests.
- **Settings:** Environment-driven via `.env` (use `python-dotenv`). Production settings (Koyeb) use PostgreSQL and R2; local defaults to SQLite and local media.
- **Static/Media:** Static files are served via WhiteNoise in production. Media files use Cloudflare R2 in production, local filesystem in dev.
- **API:** REST endpoints via `djangorestframework` (see `api_views.py` in each app).
- **Forms:** User profile image uploads are handled via forms and tested for R2 integration (`test_app_features.py`).

## Developer Workflows

- **Local Dev:**  
  - Create and activate a virtualenv:  
    `python3 -m venv .venv; .\.venv\Scripts\activate`
  - Install dependencies:  
    `pip install -r requirements.txt`
  - Set up `.env` from `.env.local.example`
  - Run migrations:  
    `python manage.py migrate`
  - Start server:  
    `python manage.py runserver`
- **Testing R2 Integration:**  
  - Run `test_app_features.py` to verify image upload and CSRF protection.
- **Docker/Koyeb Deployment:**  
  - Build via Dockerfile; entrypoint runs migrations, collects static, starts Gunicorn.
  - Use `deploy-koyeb.sh` for scripted deployment (requires Koyeb CLI).
  - Environment variables are set via Koyeb dashboard or secrets.

## Conventions

- **Environment Variables:**  
  - All secrets/configs are loaded from `.env` (never commit real credentials).
  - Key variables: `SECRET_KEY`, `DEBUG`, `DATABASE_URL`, `ALLOWED_HOSTS`, R2 keys.
- **Static/Media:**  
  - Use `/static/` and `/media/` URLs; in production, media is served from R2.
- **Security:**  
  - CSRF trusted origins set per environment.
  - Production enables secure cookies and XSS protection.

## Integration Points

- **Cloudflare R2:**  
  - Configured via `django-storages` in `settings.py`.
  - Bucket, keys, and endpoint set via env vars.
- **Koyeb:**  
  - Auto-builds from GitHub using Dockerfile.
  - PostgreSQL provisioned via Koyeb CLI or dashboard.

## Key Files

- `billetera/settings.py`: All environment/config logic.
- `Dockerfile`, `entrypoint.sh`: Container build/run steps.
- `requirements.txt`: All dependencies.
- `test_app_features.py`: Example integration test for R2.
- `deploy-koyeb.sh`: Automated deployment script.

## Example Patterns

- **Adding a new model:**  
  - Place in the relevant app (`gastos/models.py`), register in `admin.py`, create migrations.
- **API endpoint:**  
  - Add to `api_views.py` and `serializers.py` in the app.
- **Custom user logic:**  
  - Extend in `usuarios/models.py` and `signals.py`.

---

Please review and let me know if any section is unclear or missing details about your workflows, conventions, or architecture. I can iterate further based on your feedback!
