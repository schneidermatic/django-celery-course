# chap02 — Django + Celery: Basics

## What You Will Learn

How to dispatch an asynchronous Celery task from a Django view, process it in a
background worker, and persist the result in a database.

```
Browser → Django View → Redis (broker) → Celery Worker → SQLite DB
```

---

## Prerequisites

- Docker and Docker Compose installed
- Port `8000` available on your machine

---

## Step 1 — Start the Project

From the `chap02/` directory, source the helper file and run the setup command:

```bash
. .xrc
x_setup
```

This builds the Docker images and starts three containers:

| Container | Role |
|---|---|
| `redis` | Message broker — relays tasks between Django and the worker |
| `django` | Django dev server — serves the web UI, dispatches tasks |
| `celery` | Celery worker — receives and executes tasks from Redis |

Verify all containers are running:

```bash
docker compose ps
```

---

## Step 2 — Open the Application

Navigate to [http://localhost:8000/](http://localhost:8000/) in your browser.

You will see a form with three fields:

- **Recipient** — who the message is for
- **Subject** — the message subject
- **Message** — the message body

---

## Step 3 — Send a Message

Fill in the form and click **Send**.

Django immediately creates a `Message` record in the database with
`status = pending` and dispatches the task to Redis. The browser redirects to
the results page.

---

## Step 4 — Observe Asynchronous Processing

On the results page you will see your message listed as **pending**.

The Celery worker picks up the task from Redis, waits 2 seconds (simulating
network latency), then sets `status = sent`.

Reload the page after a moment — the status changes to **sent**.

To watch the worker process tasks in real time:

```bash
x_logs
```

Look for lines like:

```
celery  | Task message.tasks.send_message[...] received
celery  | Task message.tasks.send_message[...] succeeded
```

---

## Step 5 — Stop and Clean Up

Stop all containers and remove images and volumes:

```bash
x_destroy
```

---

## Project Structure

```
chap02/
├── docker-compose.yml          # Defines redis, django, celery services
├── .xrc                        # Shell helpers (x_setup, x_destroy, x_logs ...)
└── app/
    ├── Dockerfile
    ├── entrypoint.sh           # Runs migrations, then starts the service command
    ├── requirements.txt
    ├── manage.py
    ├── app/                    # Django project package
    │   ├── celery.py           # Celery app instance
    │   └── settings.py        # CELERY_BROKER_URL / CELERY_RESULT_BACKEND
    └── message/                # Django app
        ├── models.py           # Message model (recipient, subject, body, status)
        ├── tasks.py            # send_message — the Celery task
        ├── views.py            # index (form) and results views
        └── templates/
            ├── index.html      # Message form
            └── result.html     # Results list
```

---

## Celery Integration: Source Code Changes

chap02 builds directly on the skeleton from chap01.  The three core wiring
files (`celery.py`, `__init__.py`, and the two `CELERY_*` settings) are
**unchanged**.  Every change in this chapter is about adding the first real
task and connecting it to the web layer.

---

### `app/app/settings.py` — registers the `message` app

**What was changed:** One line added to `INSTALLED_APPS`.

```python
INSTALLED_APPS = [
    ...
    'message',   # ← new
]
```

**Why this matters for Celery:**
`celery.py` calls `app.autodiscover_tasks()` with no arguments, which means it
scans every entry in `INSTALLED_APPS` for a `tasks.py` module.  If `message`
is not in this list, Celery will not discover `send_message` at startup.
The worker will start, but any message for `message.tasks.send_message`
will be rejected with a `NotRegistered` error.

---

### `app/message/models.py` — the `Message` model with a `status` field

**What was added:** Entirely new file.

```python
class Message(models.Model):
    recipient  = models.CharField(max_length=100)
    subject    = models.CharField(max_length=200)
    body       = models.TextField()
    status     = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
```

**Why the `status` field is the key Celery-related design decision:**
The model is created by the Django view immediately (synchronously) with
`status='pending'`.  The Celery worker updates it to `status='sent'`
asynchronously, after execution.  This two-phase write is the observable
evidence of async processing: the results page shows `pending` immediately
after submission and `sent` once the worker is done.

Without a persistent status field there would be no way to display progress
or results — the task execution happens in a separate process with no shared
memory with Django.

**Why the text field is named `body` and not `message`:**
The model class is already called `Message`.  Using `Message.message` for the
text field would be redundant and confusing.  `body` is the conventional name
for the content field of a message-like object (email body, SMS body, etc.).

---

### `app/message/tasks.py` — the `send_message` task

**What was added:** Entirely new file.

```python
from celery import shared_task

@shared_task
def send_message(message_id):
    from message.models import Message
    m = Message.objects.get(id=message_id)
    time.sleep(2)
    m.status = 'sent'
    m.save()
```

**Three Celery-specific decisions in this file:**

**1. `@shared_task` instead of `@app.task`**

`@app.task` requires a direct reference to the Celery app object, which would
mean importing `app` from `app/app/celery.py`.  That works in chap02 because
the worker uses the same Django image.  But from chap03 onward, the standalone
worker creates its own `Celery('worker01')` instance — importing the Django
app's object would break or cause the wrong instance to be used.

`@shared_task` binds *lazily* to whichever Celery app is active at call time.
The same task function works correctly with any Celery instance, making it
safe to reuse across all chapters without modification.

**2. `message_id` as the argument (not a model instance)**

Celery serialises task arguments to JSON before writing them to Redis.  A
Django model instance is not JSON-serialisable.  Passing the integer primary
key is the standard pattern: it is a single integer, always serialisable, and
the task can re-fetch the full record from the database when it executes.

**3. `from message.models import Message` inside the function body**

This file is imported by both the Django process and the Celery worker process
at startup — before any task is executed.  At that moment, `django.setup()` may
not yet have fully initialised the ORM (especially in the standalone worker
pattern from chap03+).  Placing the import inside the function body defers it
until the task actually runs, by which time the ORM is guaranteed to be ready.

---

### `app/message/views.py` — dispatching the task with `.delay()`

**What was added:** Entirely new file.  The Celery-specific part is this:

```python
m = Message.objects.create(
    recipient=request.POST['recipient'],
    subject=request.POST['subject'],
    body=request.POST['body'],
)
send_message.delay(m.id)   # ← async dispatch
return redirect('results')
```

**What `.delay()` does:**
1. Serialises the task name and argument to JSON:
   `{"task": "message.tasks.send_message", "args": [42], ...}`
2. Writes the message to the Redis broker.
3. Returns a task ID immediately — the web process does not wait.

The `redirect('results')` happens *before* the worker starts executing the
task.  This is the fundamental value of Celery: the view returns in
milliseconds regardless of how long the task takes.

**Why `.delay()` instead of a direct function call:**
Calling `send_message(m.id)` directly would execute the 2-second sleep in
the Django view, blocking the HTTP response.  `.delay()` moves that work to the
background worker; Django is free to handle the next request immediately.

---

## Key Concepts

**`@shared_task`**
Decorating a function with `@shared_task` registers it with Celery without
tying it to a specific Celery app instance. This keeps the task reusable across
different configurations.

**`.delay()`**
Calling `send_message.delay(m.id)` sends the task to Redis
asynchronously. Django does not wait for it to finish — the response is
returned to the browser immediately.

**Worker and Django share only the broker**
Django and the Celery worker run in separate containers. They do not share
memory or processes. Redis is the only communication channel between them.

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
