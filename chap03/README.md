# chap03 — Standalone Celery Worker

## What You Will Learn

How to run a Celery worker as a completely independent service — separate image,
separate process, separate Celery app instance — while still sharing the same
Redis broker and Django models.

```
Browser → Django View → Redis (broker) → worker01 (standalone) → SQLite DB
```

### How This Differs from chap02

| | chap02 | chap03 |
|---|---|---|
| Worker image | Built from `./app` (Django image) | Built from `./worker01` (own image) |
| Worker command | `celery --app=app worker` | `celery -A celerytask worker` |
| Celery app instance | Django's `app/app/celery.py` | `worker01/celerytask.py` (own instance) |
| Django coupling | Worker is part of the Django project | Worker bootstraps Django only for ORM access |

Django and `worker01` share **only** the Redis broker. Neither service knows
how the other is deployed.

---

## Prerequisites

- Docker and Docker Compose installed
- Port `8000` available on your machine

---

## Step 1 — Start the Project

From the `chap03/` directory, source the helper file and run the setup command:

```bash
. .xrc
x_setup
```

This builds the Docker images and starts three containers:

| Container | Role |
|---|---|
| `redis` | Message broker |
| `django` | Django dev server — serves the UI and dispatches tasks |
| `worker01` | Standalone Celery worker — own image, own Celery app instance |

Verify all containers are running:

```bash
docker compose ps
```

---

## Step 2 — Open the Application

Navigate to [http://localhost:8000/](http://localhost:8000/) in your browser.

The form and behaviour are identical to chap02. Fill in **Recipient**, **Subject**
and **Message**, then click **Send**.

---

## Step 3 — Observe the Standalone Worker

After submitting the form, watch `worker01` pick up and process the task:

```bash
x_logs
```

Key log lines to look for:

```
worker01  | celery@worker01 ready.
worker01  | Task message.tasks.send_message[...] received
worker01  | Task message.tasks.send_message[...] succeeded
```

Notice that the task is logged by `worker01`, **not** by `django`. Django only
dispatches — it never executes.

Reload the results page after a moment to see the status change from
**pending** to **sent**.

---

## Step 4 — Understand the Architecture

Open `worker01/celerytask.py`. This file is the heart of the standalone worker:

```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()                          # bootstraps Django for ORM access only

from celery import Celery

app = Celery('worker01')                # own Celery app — independent of Django's
app.config_from_object('celeryconfig')
app.autodiscover_tasks(['message'])     # discovers message/tasks.py
```

`worker01` has no knowledge of the Django web server. The only shared resource
is the Redis broker address, configured via the `CELERY_BROKER` environment
variable in `docker-compose.yml`.

---

## Step 5 — Stop and Clean Up

```bash
x_destroy
```

---

## Project Structure

```
chap03/
├── docker-compose.yml          # 3 services: redis, django, worker01
├── .xrc                        # Shell helpers
├── app/                        # Django project (identical to chap02)
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   ├── manage.py
│   ├── app/                    # Django project package
│   │   ├── celery.py           # Django's Celery app (used for dispatching only)
│   │   └── settings.py
│   └── message/                # Django app — Message domain
│       ├── models.py           # Message model
│       ├── tasks.py            # send_message task
│       ├── views.py
│       └── templates/message/
└── worker01/                   # Standalone Celery worker
    ├── Dockerfile              # python:3.11-slim — no Django project structure
    ├── requirements.txt        # celery + redis + Django (ORM only)
    ├── celeryconfig.py         # broker_url and result_backend
    └── celerytask.py           # standalone Celery app instance
```

---

## Celery Integration: Source Code Changes

chap03 introduces the standalone worker pattern.  The Django application files
(`app/`) are **identical to chap02** — no changes to `celery.py`, `__init__.py`,
`settings.py`, `models.py`, `tasks.py`, or `views.py`.  All Celery-related
changes are in the new `worker01/` directory and in `docker-compose.yml`.

---

### `worker01/celeryconfig.py` — the worker's own Celery configuration

**What was added:** Entirely new file.

```python
import os

broker_url     = os.environ.get('CELERY_BROKER', 'redis://redis:6379/0')
result_backend = os.environ.get('CELERY_BACKEND', 'redis://redis:6379/0')
```

**Why a separate config file and not Django settings?**
The standalone worker reads `settings.py` only to bootstrap the Django ORM —
it uses `DJANGO_SETTINGS_MODULE` + `django.setup()` for that.  Using a
dedicated `celeryconfig.py` for Celery's own connection settings keeps the
worker self-contained: its Celery configuration does not depend on the Django
settings namespace convention (`CELERY_*` prefix + `config_from_object`).  Both
approaches are equivalent; this one makes the worker easier to understand and
operate in isolation.

---

### `worker01/celerytask.py` — the standalone Celery application instance

**What was added:** Entirely new file.  This is the heart of the standalone
worker pattern.

```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from celery import Celery

app = Celery('worker01')
app.config_from_object('celeryconfig')
app.autodiscover_tasks(['message'])
```

**Why each line is required — and why the order matters:**

| Line | Why it cannot be omitted or reordered |
|---|---|
| `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')` | `django.setup()` needs to know which settings file to load.  The `DJANGO_SETTINGS_MODULE` env var is set in `docker-compose.yml`, but the `setdefault` call ensures the file also works when run manually outside Docker. |
| `django.setup()` | Initialises Django's ORM so the task can call `Message.objects.get()`.  Without this call, any ORM access raises `Apps aren't loaded yet`. |
| `from celery import Celery` **after** `django.setup()` | If Celery were imported before `django.setup()`, the `autodiscover_tasks` call would scan `tasks.py`, which imports `models.py`, before the ORM is ready — causing the same `Apps aren't loaded yet` error. |
| `app = Celery('worker01')` | Creates an independent Celery instance separate from Django's `Celery('app')`.  Both instances point to the same Redis broker, so tasks dispatched by Django are visible to this worker.  Naming it `'worker01'` gives it a distinct identity in Flower and logs. |
| `app.config_from_object('celeryconfig')` | Loads `broker_url` and `result_backend` from the local `celeryconfig.py` module. |
| `app.autodiscover_tasks(['message'])` | Explicit package list required because there is no `INSTALLED_APPS` registry in the worker.  Without this list, `send_message` would not be registered and all messages would be rejected. |

---

### `docker-compose.yml` — three changes enable the standalone pattern

The `worker01` service replaces the `celery` service from chap02.

```yaml
worker01:
  build:
    context: ./worker01          # own Dockerfile — not the Django image
  volumes:
    - ./app:/usr/src/app/        # mounts the Django source code
    - ./worker01:/usr/src/worker01/
  working_dir: /usr/src/worker01
  environment:
    - PYTHONPATH=/usr/src/app    # makes `import message` resolve correctly
    - DJANGO_SETTINGS_MODULE=app.settings
```

**Why each change is necessary:**

| Change | Why it is needed |
|---|---|
| `context: ./worker01` | The worker uses its own minimal Docker image (Python + Celery + Redis client; no Django web server, no static files, no `manage.py`).  Using the Django image would work but couples the two services unnecessarily. |
| Volume mount `./app:/usr/src/app/` | The worker needs access to `message/tasks.py` and `message/models.py`.  Mounting the directory at runtime means both services always use the same version of the code — no copying, no synchronisation problem. |
| `PYTHONPATH=/usr/src/app` | Without this, `import message` inside the worker container raises `ModuleNotFoundError`.  Adding `/usr/src/app` to `PYTHONPATH` tells Python to look for packages there, making the Django app tree visible as if it were installed. |
| `DJANGO_SETTINGS_MODULE=app.settings` | Required for `django.setup()` in `celerytask.py` to find the correct settings file.  The path `app.settings` corresponds to `app/app/settings.py` relative to the mounted volume. |

**What did NOT change in `docker-compose.yml`:**
The `django` service is identical to chap02 — it still dispatches tasks with
`.delay()`, still uses Redis as the broker, and is completely unaware that the
worker is now a separate service with a separate image.

---

## Key Concepts

**Separate Celery app instance**
`worker01` creates its own `Celery('worker01')` instance in `celerytask.py`,
independent of the `Celery('app')` instance in `app/app/celery.py`. Both
instances point to the same Redis broker, so tasks dispatched by Django are
visible to `worker01`.

**`django.setup()`**
The standalone worker calls `django.setup()` before importing any models. This
initialises the Django ORM without starting a web server. `worker01` needs this
only to read and write `Message` records.

**Volume mount as code sharing**
`docker-compose.yml` mounts `./app` into `worker01` at `/usr/src/app/` and
sets `PYTHONPATH=/usr/src/app`. This gives `worker01` access to the Django
models without copying the code into its image.

**Task name as the contract**
Django dispatches the task by name (`message.tasks.send_message`).
`worker01` autodiscovers the same name via `app.autodiscover_tasks(['message'])`.
The two services are decoupled — changing one does not require rebuilding the other.

---

## Available Shell Commands

After sourcing `.xrc`:

| Command | Description |
|---|---|
| `x_setup` | Build images and start all containers |
| `x_destroy` | Stop containers and remove images and volumes |
| `x_logs` | Stream logs from all containers |
| `x_rmpyc` | Remove all `__pycache__` directories |
| `x_ls` | List all available commands |
