# chap04 — Task Routing

## What You Will Learn

How to route different types of tasks to dedicated Celery workers using named
queues. Transactional notifications (time-sensitive) go to the `fast` queue;
newsletter notifications (bulk, lower priority) go to the `bulk` queue. Each
queue has its own worker process.

```
Browser → Django View → Redis ─┬─ fast queue → worker_fast → SQLite DB
                                └─ bulk queue → worker_bulk → SQLite DB
```

### How This Differs from chap03

| | chap03 | chap04 |
|---|---|---|
| Tasks | One task: `send_message` | Two tasks: `send_transactional`, `send_newsletter` |
| Workers | One worker processes all tasks | Two workers, each listening on one queue |
| Queues | Default queue | `fast` (transactional) and `bulk` (newsletter) |
| Routing | None | `CELERY_TASK_ROUTES` in `settings.py` |
| Task speed | `time.sleep(2)` | Transactional: 1 s · Newsletter: 5 s |

The `worker_fast` and `worker_bulk` containers are built from the same
`worker01` image — they differ only in the `-Q` flag passed to Celery.

---

## Prerequisites

- Docker and Docker Compose installed
- Port `8000` available on your machine

---

## Step 1 — Start the Project

From the `chap04/` directory, source the helper file and run the setup command:

```bash
. .xrc
x_setup
```

This builds the images and starts four containers:

| Container | Role |
|---|---|
| `redis` | Message broker |
| `django` | Django dev server — dispatches tasks to the correct queue |
| `worker_fast` | Celery worker listening on the `fast` queue |
| `worker_bulk` | Celery worker listening on the `bulk` queue |

Verify all containers are running:

```bash
docker compose ps
```

---

## Step 2 — Open the Application

Navigate to [http://localhost:8000/](http://localhost:8000/) in your browser.

The form now includes a **Type** dropdown:

- **Transactional** — dispatched to the `fast` queue → `worker_fast`
- **Newsletter** — dispatched to the `bulk` queue → `worker_bulk`

Fill in **Recipient**, **Subject**, **Message** and select a type, then click **Send**.

---

## Step 3 — Observe the Workers

After submitting the form, watch which worker picks up the task:

```bash
x_logs
```

For a **Transactional** submission you should see:

```
worker_fast  | Task message.tasks.send_transactional[...] received
worker_fast  | Task message.tasks.send_transactional[...] succeeded
```

For a **Newsletter** submission:

```
worker_bulk  | Task message.tasks.send_newsletter[...] received
worker_bulk  | Task message.tasks.send_newsletter[...] succeeded
```

`worker_fast` **never** picks up newsletter tasks, and `worker_bulk` **never**
picks up transactional tasks. Submit one of each type and confirm this separation
in the logs.

Reload the results page to see the status change from **pending** to **sent**.
The `[transactional]` / `[newsletter]` label is shown next to each entry.

---

## Step 4 — Understand the Routing Configuration

Open `app/app/settings.py`. The routing table maps each task name to a queue:

```python
CELERY_TASK_ROUTES = {
    'message.tasks.send_transactional': {'queue': 'fast'},
    'message.tasks.send_newsletter':    {'queue': 'bulk'},
}
```

This is the only configuration change needed. Celery reads `CELERY_TASK_ROUTES`
at startup and routes every `.delay()` / `.apply_async()` call accordingly —
no changes are needed in the task functions themselves.

Open `docker-compose.yml` to see how the two workers are differentiated:

```yaml
worker_fast:
  command: celery -A celerytask worker -l INFO -Q fast

worker_bulk:
  command: celery -A celerytask worker -l INFO -Q bulk
```

Both services use the same `build: context: ./worker01`. The `-Q` flag is the
only difference.

---

## Step 5 — Stop and Clean Up

```bash
x_destroy
```

---

## Project Structure

```
chap04/
├── docker-compose.yml          # 4 services: redis, django, worker_fast, worker_bulk
├── .xrc                        # Shell helpers
├── app/                        # Django project
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   ├── manage.py
│   ├── app/                    # Django project package
│   │   ├── celery.py
│   │   └── settings.py         # CELERY_TASK_ROUTES defined here
│   └── message/                # Django app — Message domain
│       ├── models.py           # Message (+ message_type field)
│       ├── tasks.py            # send_transactional + send_newsletter
│       ├── views.py            # dispatches to correct task based on form input
│       └── templates/message/
└── worker01/                   # Standalone Celery worker (same as chap03)
    ├── Dockerfile
    ├── requirements.txt
    ├── celeryconfig.py
    └── celerytask.py
```

---

## Celery Integration: Source Code Changes

chap04 introduces task routing: different task types go to dedicated queues and
dedicated workers.  The `worker01/` files (`celerytask.py`, `celeryconfig.py`)
are **identical to chap03** — no changes to the standalone worker pattern.
All new Celery behaviour is in the Django application and `docker-compose.yml`.

---

### `app/app/settings.py` — adds `CELERY_TASK_ROUTES`

**What was added:** A new dictionary at the bottom of `settings.py`.

```python
CELERY_TASK_ROUTES = {
    'message.tasks.send_transactional': {'queue': 'fast'},
    'message.tasks.send_newsletter':    {'queue': 'bulk'},
}
```

**How it works:**
When the view calls `send_transactional.delay(m.id)`, Celery looks up the
task's fully-qualified name (`message.tasks.send_transactional`) in this
dictionary and writes the message to the `fast` Redis list.  The view does not
specify a queue — routing is handled transparently by Celery.

**Why configure routing in `settings.py` and not in the task file:**
The task function represents *what* to do; the queue represents *operational
policy* — where and how urgently to do it.  Keeping them separate means:
- The `tasks.py` file never needs to change if the routing policy changes.
- In a production system, routing can be reconfigured by a deployment engineer
  without the developer touching application code.
- The same task could theoretically be routed to different queues in different
  environments (staging vs production) using environment-specific settings.

---

### `app/message/models.py` — adds the `message_type` field

**What was changed:** One new field added to the `Message` model.

```python
message_type = models.CharField(max_length=20, default='transactional')
```

**Why this field is needed:**
The form lets the user select 'transactional' or 'newsletter'.  Without storing
this in the database, the results list would have no way to show which queue
(and therefore which worker) handled each message.  The `[transactional]`
and `[newsletter]` labels in the results list come from this field.

It also preserves the routing decision as a historical record — useful for
auditing which tasks were processed by which worker.

---

### `app/message/tasks.py` — two separate task functions

**What was changed:** `send_message` replaced by two functions.

```python
@shared_task
def send_transactional(message_id):
    ...
    time.sleep(1)   # simulates a fast delivery API
    m.status = 'sent'
    m.save()

@shared_task
def send_newsletter(message_id):
    ...
    time.sleep(5)   # simulates slow batch delivery
    m.status = 'sent'
    m.save()
```

**Why two functions are necessary:**
`CELERY_TASK_ROUTES` routes by fully-qualified task *name*.  If there were only
one function (`send_message`), both types would share the same name and
the routing table could not distinguish them — both would go to whichever queue
the single entry pointed to.

Having two functions gives Celery two distinct names to route:
- `message.tasks.send_transactional` → `fast`
- `message.tasks.send_newsletter`    → `bulk`

**Why the sleep durations differ (1 s vs 5 s):**
The exaggerated difference makes the isolation easy to observe in logs.
Submitting a newsletter (5 s) and then immediately a transactional notification
(1 s) shows that `worker_fast` processes the transactional task immediately —
it does not wait for `worker_bulk` to finish the newsletter.

---

### `app/message/views.py` — selects the correct task function

**What was changed:** The POST handler now reads `message_type` and
calls the corresponding task.

```python
message_type = request.POST.get('message_type', 'transactional')
m = Message.objects.create(..., message_type=message_type)

if message_type == 'newsletter':
    send_newsletter.delay(m.id)
else:
    send_transactional.delay(m.id)
```

**Why the routing logic is split across view and settings:**
- The *view* decides **which task function** to call based on the user's input.
- `CELERY_TASK_ROUTES` in settings decides **which queue** that task goes to.

These are separate concerns.  The view should not know about queue names; the
routing table should not know about form input parsing.  The division means
either can be changed independently.

---

### `docker-compose.yml` — two worker services instead of one

**What was changed:** `worker01` service replaced by `worker_fast` and `worker_bulk`.

```yaml
worker_fast:
  hostname: worker_fast
  command: celery -A celerytask worker -l INFO -Q fast -E

worker_bulk:
  hostname: worker_bulk
  command: celery -A celerytask worker -l INFO -Q bulk -E
```

Both are built from the same `./worker01` image.  The only differences:
- The `-Q` flag: `worker_fast` subscribes to `fast`; `worker_bulk` to `bulk`.
- The `hostname:` directive: sets the system hostname so Celery reports a
  readable worker name (`celery@worker_fast`) instead of a random container ID
  hash.  Without `hostname:`, Flower shows workers as `celery@a3f7d9c1e2b4`
  and the worker cannot be inspected by name.
- The `-E` flag: enables worker events.  Without this, Flower receives no
  event stream and cannot display task history or worker status.

A Celery worker started with `-Q fast` only polls the Redis list named `fast`.
It will never see a message posted to `bulk`, and vice versa — the queue
subscription is the enforcement mechanism for the routing isolation.

---

## Key Concepts

**`CELERY_TASK_ROUTES`**
A dictionary in Django settings that maps fully-qualified task names to queues.
Celery applies this routing automatically on every `.delay()` call — the calling
code does not need to specify a queue explicitly.

**Named queues**
Workers are started with `-Q <queue-name>` to subscribe to a specific queue.
A worker ignores all messages on queues it is not subscribed to. This is how
`worker_fast` stays focused on time-sensitive tasks while `worker_bulk` handles
the slower batch work.

**Same image, different behaviour**
Both `worker_fast` and `worker_bulk` are built from `./worker01`. The separation
of concerns is achieved entirely through the Compose command (`-Q fast` vs
`-Q bulk`) — no code duplication required.

**Two task functions**
`send_transactional` sleeps 1 second; `send_newsletter` sleeps 5 seconds. This
exaggerated difference makes it easy to observe in the logs that the two queues
process work independently — submitting a newsletter does not slow down a
subsequent transactional notification.

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
