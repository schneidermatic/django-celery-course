# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Chapter-based tutorial repository for Django + Celery integration. Each `chapXX/` is a self-contained Docker project. Chapters build on each other using the same **Notification Dispatcher** domain (recipient / subject / message / status).

| Chapter | Topic |
|---|---|
| `chap01` | Skeleton — bare Django + Celery + Redis, no custom app |
| `chap02` | Basics — Form → `@shared_task` → Redis → Worker → DB |
| `chap03` | Standalone Worker — independent `worker01/` service |
| `chap04` | Task Routing — two queues, two workers |
| `chap05` | Priority Queues + Dedicated Workers — routing by urgency level |

There are no automated tests in this repository; it is a hands-on tutorial meant to be run interactively.

---

## Running a Chapter

```bash
cd chapXX
. .xrc          # loads shell helpers into current session
x_setup         # docker compose up -d --build
x_destroy       # docker compose down --remove-orphans --volumes --rmi local
x_logs          # docker compose logs -f
x_rmpyc         # remove all __pycache__ directories (run from chapter root)
x_ls            # list all available x_ helpers
```

After `x_setup`, the app is at **http://localhost:8000** and Flower (Celery monitor) at **http://localhost:5555**.

### Useful one-liners (any chapter)

```bash
docker exec -it django python manage.py migrate
docker exec -it django python manage.py shell
docker exec -it django pip freeze > app/requirements.txt
```

---

## Directory Layouts

```
chapXX/
├── docker-compose.yml
├── .xrc                        # shell helpers; source with: . .xrc
├── app/                        # Django project root
│   ├── Dockerfile              # python:3.11-slim + entrypoint.sh
│   ├── entrypoint.sh           # runs migrate, then exec "$@"
│   ├── requirements.txt
│   ├── app/                    # Django project package (settings, urls, celery)
│   └── message/                # Django app — Message domain
│       ├── models.py           # Message(recipient, subject, body, status[, priority], created_at)
│       ├── tasks.py            # chap02/03/05: send_message · chap04: send_transactional + send_newsletter
│       ├── views.py            # index (GET/POST form), results (list)
│       └── templates/message/
└── worker01/                   # chap03/04/05 — standalone Celery service
    ├── Dockerfile
    ├── celeryconfig.py         # broker_url / result_backend from env vars
    └── celerytask.py           # own Celery() instance, django.setup(), autodiscover_tasks(['message'])
```

**chap01:** No `message` app exists — the sole purpose is verifying that Django, Celery, and Redis can see each other.

**chap02:** Has a committed `.venv` directory inside `app/`. This is an artifact and is ignored by Docker (the Dockerfile installs from `requirements.txt`).

**chap04:** `docker-compose.yml` defines `worker_fast` (`-Q fast`) and `worker_bulk` (`-Q bulk`) — both built from the same `./worker01` image. `CELERY_TASK_ROUTES` in `settings.py` routes each task to its queue automatically; the view just calls `.delay()`.

**chap05:** Two workers — `worker_urgent` (`-Q urgent`) and `worker_default` (`-Q default`). The Flower service is built from `./worker01` (not `./app` as in chap01–04) because it needs `celerytask.py` to connect to the broker.

---

## Celery Configuration Pattern

All chapters use the namespace pattern so every `CELERY_*` Django setting maps directly to a Celery key:

```python
# app/app/celery.py
app.config_from_object("django.conf:settings", namespace="CELERY")
# CELERY_BROKER_URL  → broker_url
# CELERY_RESULT_BACKEND → result_backend
```

`app/app/__init__.py` must import `celery_app` so Django loads Celery on startup:

```python
from .celery import app as celery_app
__all__ = ("celery_app",)
```

Tasks use `@shared_task` (not `@app.task`) so they work with any Celery app instance — this matters in chap03+ where `worker01` has its own `Celery()` object.

---

## Standalone Worker Pattern (chap03+)

`worker01` mounts the Django project as a volume and adds it to `PYTHONPATH` so it can import models without being part of the Django image:

```yaml
# docker-compose.yml
celeryworker:
  volumes:
    - ./app:/usr/src/app/
    - ./worker01:/usr/src/worker01/
  working_dir: /usr/src/worker01
  environment:
    - PYTHONPATH=/usr/src/app
    - DJANGO_SETTINGS_MODULE=app.settings
```

```python
# worker01/celerytask.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()                      # ORM only, no web server — must run before Celery import
app = Celery('worker01')            # independent instance
app.config_from_object('celeryconfig')
app.autodiscover_tasks(['message'])
```

`django.setup()` must be called before the `Celery` import because `autodiscover_tasks` immediately imports `tasks.py`, which imports `models.py`, which requires the ORM to be ready.

---

## Priority Queue Gotcha (chap05)

`CELERY_BROKER_TRANSPORT_OPTIONS` must be set **identically** in both `app/app/settings.py` (dispatcher) and `worker01/celeryconfig.py` (consumer). When a task is dispatched with `apply_async(queue='default', priority=5)`, Celery writes to the Redis key `default:5`. If the worker lacks matching `broker_transport_options`, it polls the bare `default` key — which stays empty — and tasks remain `pending` forever.

---

## Environment Variables

Passed directly in `docker-compose.yml`; no `.env` file used.

| Variable | Value |
|---|---|
| `SECRET_KEY` | hardcoded dev string |
| `DEBUG` | `1` |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` |
| `CELERY_BROKER` | `redis://redis:6379/0` |
| `CELERY_BACKEND` | `redis://redis:6379/0` |

`worker01` additionally receives `PYTHONPATH` and `DJANGO_SETTINGS_MODULE`.

---

## Shared Tools

`assets/tools/x_setup.sh` and `assets/tools/x_destroy.sh` accept an optional directory argument and are called by each chapter's `.xrc`:

```bash
x_setup()   { "$TOOLS_DIR/x_setup.sh"   "$CWD"; }
x_destroy() { "$TOOLS_DIR/x_destroy.sh" "$CWD"; }
```

---

## Git Commit Workflow

Follow these steps in order every time changes are committed and released.

### 1. Update CHANGELOG.md

Add an entry at the top of `CHANGELOG.md` using this format:

```
0.2.0 (2026-05-09)
---------------------
### New Feature — <short title>
* Added   - `path/to/file.py`: description of what was added
* Changed - `path/to/file.py`: description of what changed
* Fixed   - `path/to/file.py`: description of what was fixed
```

### 2. Stage all changes

```bash
git add .
```

### 3. Commit with a message

```bash
git commit -m "short imperative description of the change"
```

### 4. Push to remote

```bash
git push
```

### 5. Create an annotated tag

Tags follow the `MAJOR.MINOR.PATCH` format (no `v` prefix on the tag name).
The annotation message always references `CHANGELOG.md`:

```bash
git tag -a 0.1.0 -m "Release v0.1.0 — Details are listed in 'CHANGELOG.md'"
```

### 6. Push the tag to remote

```bash
git push origin 0.1.0
```
