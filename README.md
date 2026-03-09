# Gluko Backend

Django REST API backend for **Gluko** — an AI-powered diabetes assistant that helps users estimate carbohydrates, calculate insulin bolus doses, log health data, and interact with an AI tutor.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Prerequisites](#3-prerequisites)
4. [First-Time Setup](#4-first-time-setup)
5. [Environment Variables](#5-environment-variables)
6. [Accessing Each Service](#6-accessing-each-service)
7. [Creating a Django Superuser](#7-creating-a-django-superuser)
8. [Common Commands](#8-common-commands)
9. [Troubleshooting](#9-troubleshooting)
10. [API Endpoints Reference](#10-api-endpoints-reference)
11. [Project Structure](#11-project-structure)
12. [Branch Protection Rules](#12-branch-protection-rules)
13. [Team Onboarding](#13-team-onboarding)

---

## 1. Project Overview

Gluko is an AI-powered web application designed to help people with diabetes manage their condition. The backend is built with Django 5 and Django REST Framework, exposing a JSON API consumed by the Next.js frontend.

**Core capabilities (by sprint):**

| Sprint | Feature |
|--------|---------|
| 1 | Auth (JWT), diabetes profile, carb estimator (text), bolus calculator |
| 2 | Image-based carb estimator (AWS S3), AWS deployment, CI/CD |
| 3 | Audio input, AI Tutor (orchestrator + agents), A1C estimator |

**Tech Stack:**
- Python 3.12 / Django 5.0.3
- Django REST Framework 3.15.1
- PostgreSQL 16
- JWT authentication via `djangorestframework-simplejwt`
- CORS support via `django-cors-headers`
- Containerised with Docker and Docker Compose

---

## 2. Architecture

```
 Developer Machine
 +---------------------------------------------------------------+
 |                                                               |
 |  Console 1 (Docker)            Console 2 (local)             |
 |  +--------------------------+  +---------------------------+  |
 |  |   gluko_backend          |  |   gluko-frontend          |  |
 |  |   Django 5 + DRF         |  |   Next.js 14              |  |
 |  |   localhost:8000         |<-+   localhost:3000          |  |
 |  |   docker compose up      |  |   npm run dev             |  |
 |  +-----------+--------------+  +---------------------------+  |
 |              |                                                 |
 |          psycopg2                                              |
 |              |                                                 |
 |    +---------v----------+                                      |
 |    |   Supabase         |                                      |
 |    |   PostgreSQL       |  <-- cloud, no local container       |
 |    |   (hosted)         |                                      |
 |    +--------------------+                                      |
 |                                                               |
 +---------------------------------------------------------------+

 Request flow:
   Browser --> Next.js (SSR/CSR) --> Django REST API --> Supabase (PostgreSQL)
                                          |
                                     (Sprint 2+)
                                          |
                                      AWS S3
                                 (food images, audio)
```

---

## 3. Prerequisites

| Tool | Minimum Version | Check Command |
|------|----------------|---------------|
| Docker Desktop | 24.x | `docker --version` |
| Docker Compose | v2.x (bundled with Docker Desktop) | `docker compose version` |
| Git | 2.x | `git --version` |
| SSH key registered on GitHub | -- | `ssh -T git@github-uts` |

> **Note:** Docker Compose v2 is invoked as `docker compose` (no hyphen). If your system only has v1, use `docker-compose` instead. All examples below use v2 syntax.

The frontend runs independently — see `gluko-frontend/README.md` for its own setup.

---

## 4. First-Time Setup

Follow every step in order. Do not skip steps.

### Step 1 - Clone the repository

```bash
git clone git@github-uts:AI-Studio-Temporary/gluko-backend.git
cd gluko-backend
```

### Step 2 - Set up the environment file

```bash
cp .env.example .env
```

Open `.env` and set your `DATABASE_URL` to the Supabase Session Pooler connection string:

```
DATABASE_URL=postgresql://postgres.xvgydqzkfyirprsgdfee:[YOUR-PASSWORD]@aws-0-ap-southeast-2.pooler.supabase.com:5432/postgres
```

Get this from: **Supabase Dashboard → Connect → Connection String → Session pooler**

> **Security:** `.env` is git-ignored. Never commit it. Never share it in chat.

### Step 3 - Build and start the backend

```bash
# From inside gluko-backend/
docker compose up --build
```

The first run takes 2-3 minutes while Docker pulls `python:3.12-slim` and installs packages. On subsequent runs startup takes about 10 seconds.

Django will automatically run `migrate` on startup, creating all tables in Supabase.

### Step 4 - Verify the backend is running

| Service | URL | Expected result |
|---------|-----|-----------------|
| Django admin | http://localhost:8000/admin/ | Login page |
| JWT endpoint | http://localhost:8000/api/token/ | JSON response |

### Step 5 - Create your superuser (first time only)

```bash
docker compose exec backend python manage.py createsuperuser
```

Follow the prompts. You can then log in at http://localhost:8000/admin/.

### Step 6 - Start the frontend (separate console)

The frontend runs independently. See `gluko-frontend/README.md` for setup instructions. In short:

```bash
cd ../gluko-frontend
npm install
npm run dev
# Next.js at http://localhost:3000
```

---

## 5. Environment Variables

All variables are loaded from `.env` in the `gluko-backend/` directory. Docker Compose passes them to both the `backend` and `frontend` services via `env_file: .env`.

### Django

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `True` | Set to `False` in production. When `True`, Django shows detailed error pages. |
| `SECRET_KEY` | `gluko-dev-secret-key-...` | Cryptographic key used for signing cookies and tokens. Must be long, random, and unique per environment. Change before any production deployment. |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated list of hostnames Django will serve. Add your EC2 public IP or domain for production. |

### PostgreSQL

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `gluko_db` | Name of the database created inside the container. |
| `POSTGRES_USER` | `gluko_user` | PostgreSQL superuser for this database. |
| `POSTGRES_PASSWORD` | `gluko_password` | Password for `POSTGRES_USER`. Change in production. |
| `POSTGRES_HOST` | `db` | Docker service name used as the hostname inside the Docker network. Do **not** change this for local development. |
| `POSTGRES_PORT` | `5432` | Standard PostgreSQL port. |

### JWT

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | `60` | How long an access token is valid before the client must refresh. Lower values are more secure. |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | `7` | How long a refresh token is valid. After this period the user must log in again. |

### AWS S3 (Sprint 2+)

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_ACCESS_KEY_ID` | _(empty)_ | IAM access key. Leave empty during Sprint 1. |
| `AWS_SECRET_ACCESS_KEY` | _(empty)_ | IAM secret key. Leave empty during Sprint 1. |
| `AWS_STORAGE_BUCKET_NAME` | _(empty)_ | S3 bucket for food images and audio files. |
| `AWS_S3_REGION_NAME` | `ap-southeast-2` | AWS region (Sydney). |

### Next.js

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api` | Base URL the browser uses to reach the Django API. The `NEXT_PUBLIC_` prefix makes it available client-side. |

---

## 6. Accessing Each Service

### Django Admin

- URL: http://localhost:8000/admin/
- Credentials: the superuser you create in Step 5 above
- Use it to: inspect database records, manage users, register new models

### Django REST API

- Base URL: http://localhost:8000/api/
- Authentication: JWT Bearer token (obtain via `/api/token/`)
- Test with curl:

```bash
# Obtain a token pair
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "yourpassword"}'

# Use the access token
curl http://localhost:8000/api/some-endpoint/ \
  -H "Authorization: Bearer <access_token>"
```

### PostgreSQL (direct access)

- Host: `localhost`
- Port: `5432`
- Database: `gluko_db`
- Username: `gluko_user`
- Password: `gluko_password`

Connect with psql:
```bash
docker compose exec db psql -U gluko_user -d gluko_db
```

Or use a GUI client such as TablePlus, DBeaver, or pgAdmin with the connection details above.

### Next.js Frontend

- URL: http://localhost:3000
- Hot-reload is enabled: changes to files in `gluko-frontend/src/` are reflected immediately without rebuilding the container.

---

## 7. Creating a Django Superuser

```bash
# While containers are running:
docker compose exec backend python manage.py createsuperuser
```

You will be prompted for:
- **Username** - choose anything (e.g., `admin`)
- **Email** - can be left blank during development
- **Password** - must pass Django's validators (min 8 chars, not too common)

Once created, log in at http://localhost:8000/admin/.

To reset a password later:

```bash
docker compose exec backend python manage.py changepassword <username>
```

---

## 8. Common Commands

All commands are run from the `gluko-backend/` directory unless otherwise noted.

### Starting and stopping

```bash
# Start all services in foreground (shows logs)
docker compose up

# Start all services in background (detached)
docker compose up -d

# Stop all services (preserves volumes)
docker compose down

# Stop all services AND delete the database volume (full reset)
docker compose down -v
```

### Building

```bash
# Rebuild all images (required after changes to Dockerfile or requirements.txt)
docker compose up --build

# Rebuild a single service
docker compose build backend
docker compose build frontend
```

### Django management commands

```bash
# Run database migrations
docker compose exec backend python manage.py migrate

# Create a new migration after changing a model
docker compose exec backend python manage.py makemigrations

# Open Django shell (Python REPL with Django context)
docker compose exec backend python manage.py shell

# Collect static files
docker compose exec backend python manage.py collectstatic --no-input

# Create superuser
docker compose exec backend python manage.py createsuperuser
```

### Viewing logs

```bash
# All services
docker compose logs -f

# Single service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

### Running tests

```bash
docker compose exec backend python manage.py test
```

### Accessing a running container shell

```bash
docker compose exec backend sh
docker compose exec frontend sh
docker compose exec db bash
```

### Checking container status

```bash
docker compose ps
```

---

## 9. Troubleshooting

### Port already in use

**Error:**
```
Error response from daemon: Ports are not available: exposing port TCP 0.0.0.0:5432 -> 0.0.0.0:0: listen tcp 0.0.0.0:5432: bind: address already in use
```

**Cause:** You have a local PostgreSQL, Django devserver, or Next.js running on the same ports.

**Fix:**
```bash
# Find what is using port 5432
lsof -i :5432

# Kill it (macOS/Linux)
kill -9 <PID>

# Or stop local postgres service
brew services stop postgresql@16
```

Repeat for ports 8000 and 3000 as needed.

---

### Backend cannot connect to database

**Error in logs:**
```
django.db.utils.OperationalError: could not connect to server: Connection refused
```

**Cause:** The backend started before the database was healthy. The `depends_on: condition: service_healthy` should prevent this, but on slow machines the healthcheck may time out.

**Fix:**
```bash
# Restart only the backend
docker compose restart backend

# Or bring everything down and up again
docker compose down && docker compose up
```

---

### Database migration errors

**Error:**
```
django.db.utils.ProgrammingError: relation "..." does not exist
```

**Cause:** Migrations have not been applied, or a model change requires a new migration.

**Fix:**
```bash
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
```

---

### Frontend: module not found / package errors

**Error:**
```
Module not found: Can't resolve '...'
```

**Cause:** `node_modules` inside the container is out of sync with `package.json`.

**Fix:**
```bash
# Force rebuild the frontend image
docker compose build --no-cache frontend
docker compose up
```

---

### Permission denied on manage.py

**Error:**
```
bash: ./manage.py: Permission denied
```

**Fix:**
```bash
chmod +x manage.py
```

---

### Volume permission errors on Linux

**Error:**
```
PermissionError: [Errno 13] Permission denied: '/app/...'
```

**Cause:** Docker on Linux runs containers as root, which can conflict with host file permissions.

**Fix:** Add your user to the `docker` group:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

---

### .env not found

**Error:**
```
open .env: no such file or directory
```

**Fix:**
```bash
cp .env.example .env
```

---

### Fresh start (nuclear option)

If everything is broken and you want a clean slate:

```bash
docker compose down -v          # Remove containers and volumes
docker system prune -af         # Remove all unused images and build cache
docker compose up --build       # Rebuild from scratch
```

> Warning: `docker compose down -v` deletes the database volume. All data will be lost. You will need to re-run migrations and recreate your superuser.

---

## 10. API Endpoints Reference

### Authentication

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/api/token/` | No | Obtain JWT access + refresh tokens |
| POST | `/api/token/refresh/` | No | Obtain a new access token using a refresh token |

**POST /api/token/**

Request body:
```json
{
  "username": "admin",
  "password": "yourpassword"
}
```

Response:
```json
{
  "access": "<jwt_access_token>",
  "refresh": "<jwt_refresh_token>"
}
```

**POST /api/token/refresh/**

Request body:
```json
{
  "refresh": "<jwt_refresh_token>"
}
```

Response:
```json
{
  "access": "<new_jwt_access_token>"
}
```

### Admin

| Endpoint | Description |
|----------|-------------|
| `/admin/` | Django admin panel (browser-based, not REST) |

### Planned endpoints (Sprint 1+)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Create a new user account |
| GET/PUT | `/api/profile/` | Get or update diabetes profile (ICR, ISF, etc.) |
| POST | `/api/carbs/estimate/` | Estimate carbs from text description |
| POST | `/api/bolus/calculate/` | Calculate insulin bolus dose |
| GET/POST | `/api/logs/glucose/` | Glucose log entries |
| GET/POST | `/api/logs/insulin/` | Insulin log entries |
| GET/POST | `/api/logs/meals/` | Meal log entries |
| GET/POST | `/api/logs/activity/` | Sport activity log entries |

---

## 11. Project Structure

```
gluko-backend/
|
+-- gluko/                      # Django project package
|   +-- __init__.py
|   +-- asgi.py                 # ASGI entry point (async servers)
|   +-- settings.py             # All configuration (reads from env vars)
|   +-- urls.py                 # Root URL configuration
|   +-- wsgi.py                 # WSGI entry point (gunicorn)
|
+-- data/                       # Datasets and raw data (not deployed)
+-- docs/                       # Architecture notes and documentation
+-- notebooks/                  # Jupyter notebooks for ML exploration
|
+-- manage.py                   # Django CLI entry point
+-- requirements.txt            # Python dependencies (pinned versions)
|
+-- Dockerfile                  # Backend container definition
+-- docker-compose.yml          # Orchestrates all three services
+-- .dockerignore               # Files excluded from Docker build context
|
+-- .env                        # Local environment variables (git-ignored)
+-- .env.example                # Template -- safe to commit
|
+-- README.md                   # This file
```

As the project grows, Django apps will be added as top-level directories alongside `gluko/`:

```
gluko-backend/
+-- gluko/          # project config
+-- users/          # custom user model + auth
+-- profiles/       # diabetes profile
+-- carbs/          # carb estimation
+-- bolus/          # bolus calculator
+-- logs/           # glucose, insulin, meal, activity logs
+-- tutor/          # AI tutor (Sprint 3)
```

---

## 12. Branch Protection Rules

To maintain code quality across the team the following rules apply to the `main` branch on both repositories.

**Protected branch: `main`**

| Rule | Setting |
|------|---------|
| Require pull request before merging | Yes |
| Required approvals | 1 (from a team member other than the author) |
| Dismiss stale reviews on new push | Yes |
| Require status checks to pass | Yes (GitHub Actions CI) |
| Require branches to be up to date | Yes |
| Allow force push | No |
| Allow deletions | No |

**Workflow for every change:**

```bash
# 1. Create a feature branch from main
git checkout -b feat/your-feature-name

# 2. Make your changes and commit
git add <files>
git commit -m "feat: describe what you did"

# 3. Push and open a pull request
git push -u origin feat/your-feature-name
# Open PR on GitHub, request review from a teammate

# 4. After approval, merge via GitHub UI (squash merge preferred)

# 5. Delete the branch after merging
```

**Commit message convention** (Conventional Commits):

| Prefix | Use for |
|--------|---------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `refactor:` | Code change with no feature or fix |
| `test:` | Adding or fixing tests |
| `chore:` | Build config, CI, dependency updates |

---

## 13. Team Onboarding

Every team member must complete the following steps to contribute to Gluko.

### Step 1 - SSH access

Ensure your SSH key is added to GitHub under the `github-uts` SSH host alias. Check your `~/.ssh/config` for an entry similar to:

```
Host github-uts
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_uts
```

Test it:
```bash
ssh -T git@github-uts
# Expected: Hi <username>! You've successfully authenticated...
```

### Step 2 - Clone both repos as siblings

```bash
mkdir -p ~/projects/gluko
cd ~/projects/gluko
git clone git@github-uts:AI-Studio-Temporary/gluko-backend.git
git clone git@github-uts:AI-Studio-Temporary/gluko-frontend.git
```

The repos **must** be siblings. The `docker-compose.yml` in `gluko-backend/` references the frontend with `../gluko-frontend`. If the directory names differ or they are not at the same level, Docker Compose will fail to find the frontend build context.

### Step 3 - Set up your environment

```bash
cd gluko-backend
cp .env.example .env
# No changes needed for local development
```

### Step 4 - Build and start

```bash
docker compose up --build
```

### Step 5 - Create your superuser

```bash
docker compose exec backend python manage.py createsuperuser
```

### Step 6 - Verify

| URL | Expected |
|-----|----------|
| http://localhost:8000/admin/ | Django admin login |
| http://localhost:3000 | Gluko landing page |

### Recommended tools

| Tool | Purpose |
|------|---------|
| VS Code with Python extension | Backend development |
| VS Code with ESLint + Prettier | Frontend development |
| TablePlus or DBeaver | Database inspection |
| Postman or Insomnia | API testing |
| Docker Desktop | Container management GUI |
