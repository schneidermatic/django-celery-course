# Django + Celery — Practical Course

<p align="left">
  <img src="assets/img/logo01.png" alt="Django + Celery course logo" width="200">
</p>

A hands-on, six-chapter course that teaches you how to integrate Celery into a
Django application — from the minimal wiring all the way to task routing,
priority queues, and real external HTTP calls — using Docker Compose throughout.

---

## Course Objectives

By the end of this course you will be able to:

- Wire Celery into a Django project and verify the broker connection
- Dispatch asynchronous tasks from a Django view with `@shared_task` and `.delay()`
- Run a Celery worker as a fully independent service, separate from the Django image
- Route different task types to dedicated queues and dedicated worker processes
- Combine routing and prioritisation: isolate urgent tasks in a dedicated queue and worker while ordering the remaining tasks by priority
- Monitor workers, queues, and task history in real time with Flower
- Dispatch an async task that makes a real external HTTP call, stores the full response in the database, and surfaces it back to the browser without blocking the web process

---

## What You Will Build

Every chapter uses the same **Notification Dispatcher** — a small Django web app
where a user fills in a form (recipient, subject, message) and submits it. Django
stores the record in a database, dispatches a Celery task, and immediately
redirects to a results page. The worker picks up the task in the background,
processes it, and updates the record status from `pending` to `sent`.

```
Browser ──► Django View ──► Redis (broker) ──► Celery Worker ──► SQLite DB
```

Using one consistent domain across all chapters means every change you make from
chapter to chapter is purely architectural — you are never distracted by a new
business problem.

---

## Learning Path

The chapters build on each other in a deliberate sequence:

**lab01 → Verify the pipeline.** Connect Django, Celery, and Redis in Docker
Compose. No custom tasks yet — just confirm the three services can see each other.

**lab02 → First real task.** Add the `Message` model and `send_message`
task. Learn the basic async pattern: `@shared_task`, `.delay()`, result in DB.

**lab03 → Architectural independence.** Move the worker into its own image with
its own Celery app instance. Django and the worker share only the broker — neither
knows how the other is built or deployed.

**lab04 → Operational control by type.** Introduce two task types
(transactional vs. newsletter), two named queues, and two dedicated workers.
Routing is declared once in `CELERY_TASK_ROUTES`; no changes to the task code.

**lab05 → Routing by urgency level.** Combine the two previous techniques:
urgent tasks get their own dedicated queue and worker so they are never delayed
by a backlog; normal and low tasks share a second queue where priority ordering
(`apply_async(queue=..., priority=X)`) still applies within that tier.

**lab06 → Async HTTP request with result storage.** Switch to a new domain —
the `Payload` model — and make the worker perform a real outbound HTTP call to
`httpbin.org`. The response body and status code are written back to the
database. The results list page auto-refreshes every three seconds while any
record is still `pending`, then stops once all tasks are complete. A detail view
pretty-prints the full JSON response.

---

## Chapter Overview

| Chapter | Title | New Concept | Key Files / Settings |
|---|---|---|---|
| [lab01](lab01/README.md) | Skeleton | `celery.py` wiring, `__init__.py` import, `CELERY_BROKER_URL` | no custom app, no tasks |
| [lab02](lab02/README.md) | Basics | `@shared_task`, `.delay()`, DB result | `message/tasks.py` — `send_message` |
| [lab03](lab03/README.md) | Standalone Worker | own image, `django.setup()`, volume + `PYTHONPATH` | `worker01/celerytask.py` |
| [lab04](lab04/README.md) | Task Routing | `CELERY_TASK_ROUTES`, named queues, `-Q` flag | `worker_fast` + `worker_bulk` containers |
| [lab05](lab05/README.md) | Priority Queues + Dedicated Workers | routing by urgency, `apply_async(queue=..., priority=X)` | `worker_urgent` + `worker_default` |
| [lab06](lab06/README.md) | Async HTTP Request + Result Storage | outbound HTTP in a task, response stored in DB, auto-refreshing list | `payload/tasks.py` — `post_to_httpbin` |

---

## Technology Stack

| Tool | Version | Role |
|---|---|---|
| Django | 5.2 | Web framework — models, views, forms |
| Celery | 5.4 | Task queue — dispatching and execution |
| Redis | 8 | Message broker and result backend |
| Docker Compose | — | Isolates every service; one command to start a chapter |
| Flower | 2.0.1 | Web UI to inspect workers, queues, and task history |

---

## Prerequisites

- Basic Python and Django knowledge (models, views, URLs) — no Celery experience needed
- Docker and Docker Compose installed on your machine
- A terminal (bash or zsh)

---

## How to Work Through the Course

Each chapter is a self-contained Docker project. Start from lab01 and work
forward. There is no shared state between chapters.

```bash
cd lab01          # or lab02 … lab06
. .xrc             # load shell helpers into the current session
x_setup            # build Docker images and start all containers
```

Open the application at **http://localhost:8000** and Flower (the Celery monitor)
at **http://localhost:5555**. A direct link to Flower is also on the app's form
page.

When you are done:

```bash
x_destroy          # stop containers, remove images and volumes
```

Each chapter's `README.md` contains a step-by-step walkthrough, log output to
expect, and an explanation of the key concepts introduced.

---

## Repository Layout

```
Celery/
├── README.md              ← you are here
├── CLAUDE.md              ← guidance for Claude Code
├── assets/
│   └── tools/             ← shared x_setup.sh and x_destroy.sh scripts
├── lab01/                ← Skeleton
├── lab02/                ← Basics
├── lab03/                ← Standalone Worker
├── lab04/                ← Task Routing
├── lab05/                ← Task Prioritisation
└── lab06/                ← Async HTTP Request + Result Storage
```

Every `labXX/` directory contains:

```
labXX/
├── docker-compose.yml     ← all services for this chapter
├── .xrc                   ← shell helpers (x_setup, x_destroy, x_logs, …)
├── README.md              ← chapter walkthrough
├── app/                   ← Django project
└── worker01/              ← standalone Celery worker (lab03–06 only)
```
