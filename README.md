# Sports Schedule Aggregator

Backend-first Django project for storing and serving sports competition schedules scraped from official sport websites.

The first target is judo, using the IJF official website as the source. The code is structured so more sports and source organizations can be added later.

## Project Structure

```text
backend/
  manage.py
  config/
  apps/
    sports/
    events/
    scraping_logs/
scraper/
  scrapy.cfg
  sport_scraper/
    spiders/
      ijf.py
README.md
.env.example
requirements.txt
```

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your environment file:

```bash
copy .env.example .env
```

Set `DATABASE_URL` to your Neon PostgreSQL connection string. Keep `sslmode=require` in the URL when using Neon.

Run migrations:

```bash
cd backend
python manage.py migrate
```

Create an admin user:

```bash
python manage.py createsuperuser
```

Run the backend:

```bash
python manage.py runserver
```

API routes:

- `GET /health/`
- `GET /api/sports/`
- `GET /api/organizations/`
- `GET /api/events/`
- `GET /api/events/{id}/`

Event filters:

- `sport`
- `organization`
- `country`
- `status`
- `start_date_after`
- `start_date_before`
- `end_date_after`
- `end_date_before`

Examples:

```text
/api/events/?sport=judo&status=upcoming
/api/events/?organization=ijf&country=Georgia
/api/events/?start_date_after=2026-01-01&start_date_before=2026-12-31
```

## Running the Scraper

The scraper imports the Django project and writes through the Django ORM, so it
must use the same `DATABASE_URL` as the backend when seeding production data.

From the repository root, create a scraper env file if you want scraper-specific
local settings:

```bash
copy scraper\.env.example scraper\.env
```

For production, set environment variables in the host instead of committing
secrets. Required scraper environment variables:

```text
DATABASE_URL=<same Neon connection string used by the backend>
DJANGO_SETTINGS_MODULE=config.settings
SECRET_KEY=<any long Django secret>
DEBUG=False
DATABASE_CONN_MAX_AGE=600
```

Run the IJF scraper from the `scraper/` folder:

```bash
cd scraper
scrapy crawl ijf
```

The scraper is separate from the Django backend service, but it writes to the same database through Django's ORM. This keeps the first version simple and avoids creating private API authentication before it is needed. In deployment, run the backend and scraper as separate services using the same `DATABASE_URL`.

The IJF spider is intentionally conservative. It includes realistic parsing hooks and TODOs because the live IJF page structure can change. Prefer updating selectors after inspecting the current official page rather than guessing.

After the scraper runs against the production Neon database, verify that data is
visible through the deployed API:

```text
https://sports-schedule-backend.onrender.com/api/sports/
https://sports-schedule-backend.onrender.com/api/organizations/
https://sports-schedule-backend.onrender.com/api/events/
```

## Render + Neon Deployment

The backend is ready to deploy as a single Render Web Service using Neon PostgreSQL. No Docker, Celery, Redis, or background workers are required.

### 1. Create a Neon database

1. Create a Neon project and database.
2. Copy the PostgreSQL connection string.
3. Use the pooled Neon connection string if you enable Neon's pooler. Keep `sslmode=require` in the URL.

Example:

```text
postgres://user:password@ep-example-pooler.us-east-2.aws.neon.tech/dbname?sslmode=require
```

### 2. Publish the repo to GitHub

Render deploys from a Git provider, so push this project to GitHub before creating the Render service.

### 3. Create the Render Web Service

In Render:

1. Create a new Web Service.
2. Connect the GitHub repo.
3. Use the repository root as the root directory.
4. Set the build command:

```bash
pip install -r requirements.txt && cd backend && python manage.py collectstatic --noinput
```

5. Set the start command:

```bash
cd backend && python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

The included `render.yaml` contains the same configuration if you prefer Render Blueprint deployment.

### 4. Set Render environment variables

Required:

```text
DATABASE_URL=<your Neon connection string>
SECRET_KEY=<long random Django secret>
DEBUG=False
ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
DATABASE_CONN_MAX_AGE=600
```

Do not enable wildcard CORS in production. Add only the frontend origins that should call the API.

### 5. Verify deployment

After Render finishes the deploy, open:

```text
https://your-render-service.onrender.com/health/
```

Expected response:

```json
{
  "status": "ok"
}
```

Then verify:

- `GET /api/sports/`
- `GET /api/organizations/`
- `GET /api/events/`

### 6. Create a superuser manually

Open the Render shell for the web service and run:

```bash
cd backend
python manage.py createsuperuser
```

Migrations are run by the Render start command. If you prefer to run them manually from the Render shell:

```bash
cd backend
python manage.py migrate
```

Backend service notes:

- Static files are served with WhiteNoise.
- `DATABASE_URL` is read from environment variables.
- Persistent Django database connections are enabled with `DATABASE_CONN_MAX_AGE`.
- HTTPS security settings are enabled when `DEBUG=False`.
- CORS is restricted to `CORS_ALLOWED_ORIGINS`.

### 7. Create a Render Cron Job for the scraper

Create a separate Render Cron Job from the same GitHub repository:

1. In Render, create **New +** -> **Cron Job**.
2. Connect `DarkLordGeo/sportschedulegeobackend`.
3. Use the repository root as the root directory.
4. Set the build command:

```bash
pip install -r requirements.txt
```

5. Set the command:

```bash
cd scraper && scrapy crawl ijf
```

6. Set the schedule you want, for example daily:

```text
0 3 * * *
```

7. Set environment variables:

```text
DATABASE_URL=<same Neon connection string used by the backend>
DJANGO_SETTINGS_MODULE=config.settings
SECRET_KEY=<any long Django secret>
DEBUG=False
DATABASE_CONN_MAX_AGE=600
```

Do not use SQLite in production. The scraper has a production guard and will
fail loudly when `DEBUG=False` and `DATABASE_URL` is missing.

The scraper creates a `ScrapeRun` when it starts, updates totals as records are
created or updated, logs invalid skipped records, and marks the run as
`success`, `partial`, or `failed` when it ends.

No frontend or custom authentication system is included yet. Admin-only management is handled by Django admin.
