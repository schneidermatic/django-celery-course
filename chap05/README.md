# chap05 — Priority Queues + Dedicated Workers

## What You Will Learn

How to combine queue routing with task prioritisation: urgent tasks are isolated
in their own queue with a dedicated worker so they are never delayed by a backlog
of lower-priority work. Normal and low-priority tasks share a second queue, where
priority ordering ensures that normal tasks are processed before low ones.

```
                           ┌─ urgent queue ──► worker_urgent
Browser → Django View → Redis
                           └─ default queue ──► worker_default
                                (normal priority 5, low priority 9)
```

### How This Differs from chap04

| | chap04 | chap05 |
|---|---|---|
| Routing basis | Task type (transactional vs. newsletter) | Priority level (urgent vs. everything else) |
| Queue names | `fast`, `bulk` | `urgent`, `default` |
| Workers | `worker_fast`, `worker_bulk` | `worker_urgent`, `worker_default` |
| Dispatch call | `.delay(n.id)` | `apply_async(queue=..., priority=...)` |
| Priority ordering | None | Within `default` queue: normal (5) before low (9) |

chap04 separates by **what** the task is. chap05 separates by **how urgent** it is.

---

## Prerequisites

- Docker and Docker Compose installed
- Port `8000` available on your machine

---

## Step 1 — Start the Project

From the `chap05/` directory, source the helper file and run the setup command:

```bash
. .xrc
x_setup
```

This builds the images and starts four containers:

| Container | Queue | Role |
|---|---|---|
| `redis` | — | Message broker |
| `django` | — | Django dev server — routes tasks to the correct queue |
| `worker_urgent` | `urgent` | Dedicated worker — never touches the default queue |
| `worker_default` | `default` | Processes normal and low tasks in priority order |

Verify all containers are running:

```bash
docker compose ps
```

---

## Step 2 — Open the Application

Navigate to [http://localhost:8000/](http://localhost:8000/) in your browser.

The **Priority** dropdown shows where each choice is routed:

| Selection | Queue | Worker | Priority value |
|---|---|---|---|
| Urgent | `urgent` | `worker_urgent` | — (isolated, no ordering needed) |
| Normal | `default` | `worker_default` | 5 |
| Low | `default` | `worker_default` | 9 |

---

## Step 3 — Observe the Two Workers

**Test isolation:** submit one urgent and one normal notification. Watch the logs:

```bash
x_logs
```

```
worker_urgent   | Task message.tasks.send_message[...] received   ← urgent
worker_default  | Task message.tasks.send_message[...] received   ← normal
```

Each worker only ever picks up messages from its own queue.

**Test priority ordering within `default`:** submit several low-priority
notifications in quick succession, then immediately one normal-priority
notification. The `worker_default` will process the normal one before the
remaining low ones:

```
worker_default  | Task ... received   ← low
worker_default  | Task ... succeeded  ← low
worker_default  | Task ... received   ← normal (processed next, ahead of remaining low)
worker_default  | Task ... succeeded  ← normal
worker_default  | Task ... received   ← low (remaining)
```

Reload the results page to see the `[urgent]` / `[normal]` / `[low]` labels
and the updated status for each entry.

---

## Step 4 — Understand the Dispatch Logic

Open `app/message/views.py`:

```python
PRIORITY_MAP = {'normal': 5, 'low': 9}

if priority == 'urgent':
    send_message.apply_async(args=[m.id], queue='urgent')
else:
    send_message.apply_async(
        args=[m.id],
        queue='default',
        priority=PRIORITY_MAP[priority],
    )
```

Urgent tasks are placed directly in the `urgent` queue — no priority number
is needed because the queue is already exclusive to them. Normal and low tasks
go to `default` with a numeric priority so that `worker_default` processes them
in the right order.

Open `app/app/settings.py` to see the priority queue configuration:

```python
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'priority_steps': list(range(10)),
    'sep': ':',
    'queue_order_strategy': 'priority',
}
```

This setting affects the `default` queue only — it tells Redis to maintain
10 priority buckets and to serve higher-priority messages first.

Open `docker-compose.yml` to see how the two workers are differentiated:

```yaml
worker_urgent:
  command: celery -A celerytask worker -l INFO -Q urgent -E

worker_default:
  command: celery -A celerytask worker -l INFO -Q default -E
```

Both services are built from the same `./worker01` image. The `-Q` flag is
the only difference — exactly the same pattern as chap04.

---

## Step 5 — What Happens Under the Hood for Each Priority Level

### Urgent

**You select:** Priority → Urgent

**In `views.py`:**
```python
send_message.apply_async(args=[m.id], queue='urgent')
```

**What Celery does:**
1. Serialises the task call (`message.tasks.send_message`, args `[m.id]`) to JSON.
2. Writes the message to the Redis list key `urgent` (a plain FIFO list, no sub-keys).
3. Returns immediately — the view redirects to the results page.

**In Redis:**
```
LPUSH urgent  {"task": "message.tasks.send_message", "args": [42], ...}
```

**In `worker_urgent`:**
- The worker is started with `-Q urgent`, so it polls only the `urgent` key.
- It dequeues the message, calls `send_message(42)`, sleeps 2 seconds,
  sets `status='sent'`, and saves.
- `worker_default` never sees this message — it subscribes only to `default`.

**Why this is the fast lane:**
`worker_urgent` has zero competition.  No matter how many normal or low tasks
are queued in `default`, they cannot block `worker_urgent` — it does not even
look at that queue.

---

### Normal

**You select:** Priority → Normal

**In `views.py`:**
```python
PRIORITY_MAP = {'normal': 5, 'low': 9}

send_message.apply_async(args=[m.id], queue='default', priority=5)
```

**What Celery does:**
1. Serialises the task call to JSON.
2. Applies `broker_transport_options`: queue `default` + sep `:` + priority `5`
   → writes the message to the Redis list key `default:5`.
3. Returns immediately.

**In Redis:**
```
LPUSH default:5  {"task": "message.tasks.send_message", "args": [43], ...}
```

**In `worker_default`:**
- The worker is started with `-Q default`.  Because `broker_transport_options`
  is set in `celeryconfig.py`, Celery expands `default` into all 10 sub-keys:
  `default:0`, `default:1`, … `default:9`.
- It polls them in priority order (lowest number first).  When a `default:5`
  message exists it is always dequeued ahead of any `default:9` message.
- Once dequeued, the task runs identically to the urgent case: 2-second sleep,
  status → 'sent'.

**Priority 5 in context:**
The scale runs 0 (highest) to 9 (lowest).  Choosing 5 for "normal" leaves
four levels of headroom above (0–4) for future higher-urgency categories, and
three levels below (6–8) between normal and the lowest tier.

---

### Low

**You select:** Priority → Low

**In `views.py`:**
```python
send_message.apply_async(args=[m.id], queue='default', priority=9)
```

**What Celery does:**
Same as normal, but the message lands in `default:9` — the lowest-priority
bucket in the scale.

**In Redis:**
```
LPUSH default:9  {"task": "message.tasks.send_message", "args": [44], ...}
```

**In `worker_default`:**
- `default:9` is the last bucket checked.  The worker processes every message
  in `default:0` through `default:8` before touching `default:9`.
- If you submit a low task and then immediately a normal task, the normal task
  will be processed first — even though the low task arrived earlier.

**Why this is the correct model for bulk background work:**
Low-priority tasks never delay each other (they are still processed in order
within their own bucket), but any higher-priority work submitted later will
jump ahead of them.  This is ideal for tasks like nightly batch jobs or
background cleanup that should yield CPU time to anything more urgent.

---

### Summary: the two control levers

| Lever | Mechanism | Effect |
|---|---|---|
| **Queue routing** (`queue='urgent'` vs `queue='default'`) | Separate Redis lists, separate workers | Complete isolation — urgent tasks have their own dedicated worker |
| **Priority ordering** (`priority=5` vs `priority=9`) | Redis sub-keys within `default:*` | Relative ordering — normal is processed before low when both are waiting |

The two levers are independent.  Routing determines *which worker* picks up
the task.  Priority determines the *order* in which that worker processes
the tasks already in its queue.

---

## Step 6 — Stop and Clean Up

```bash
x_destroy
```

---

## Project Structure

```
chap05/
├── docker-compose.yml          # 4 services: redis, django, worker_urgent, worker_default
├── .xrc                        # Shell helpers
├── app/                        # Django project
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   ├── manage.py
│   ├── app/                    # Django project package
│   │   ├── celery.py
│   │   └── settings.py         # CELERY_BROKER_TRANSPORT_OPTIONS defined here
│   └── message/                # Django app — Message domain
│       ├── models.py           # Message (priority field: urgent/normal/low)
│       ├── tasks.py            # send_message — single task
│       ├── views.py            # routes to urgent or default queue; PRIORITY_MAP for default
│       └── templates/message/
└── worker01/                   # Standalone Celery worker (same as chap03/04)
    ├── Dockerfile
    ├── requirements.txt
    ├── celeryconfig.py
    └── celerytask.py
```

---

## Celery Integration: Source Code Changes

chap05 combines queue routing (from chap04) with Redis priority ordering (new).
Changes touch both the Django application (`app/`) and the standalone worker
configuration (`worker01/`).  Compared to chap04, `worker01/celerytask.py` is
**unchanged**; all other Celery-related files have been modified.

---

### `app/app/settings.py` — adds `CELERY_BROKER_TRANSPORT_OPTIONS`

**What was added:** A new dictionary at the bottom of `settings.py`.

```python
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'priority_steps': list(range(10)),
    'sep': ':',
    'queue_order_strategy': 'priority',
}
```

**What each key does:**

| Key | Value | Effect |
|---|---|---|
| `priority_steps` | `[0, 1, 2, …, 9]` | Declares 10 priority buckets.  Lower number = higher urgency.  0 is the highest priority; 9 is the lowest. |
| `sep` | `':'` | The separator inserted between the queue name and the priority number when forming the Redis key.  Queue `default` + sep `:` + priority `5` → Redis key `default:5`. |
| `queue_order_strategy` | `'priority'` | Tells the Celery worker to always consume from the lowest-numbered non-empty bucket first, rather than cycling through buckets in round-robin order. |

**What happens without this setting:**
The `priority=` argument to `apply_async()` is accepted without error but
silently ignored — all messages go to the bare `default` Redis key and are
processed in arrival order.  Tasks are still dispatched and executed correctly;
they simply are not ordered by priority.

**Critical: this setting must also exist in `worker01/celeryconfig.py`.**
See that section below for details.

---

### `app/message/models.py` — adds the `priority` field

**What was changed:** One new field added to the `Message` model.

```python
priority = models.CharField(max_length=10, default='normal')
```

**Why this field is needed:**
The form lets the user select 'urgent', 'normal', or 'low'.  Storing the choice
in the database makes the routing decision visible in the results list —
`[urgent]`, `[normal]`, and `[low]` labels appear next to each row.  Without
this field, there would be no persistent record of which queue handled the task.

---

### `app/message/tasks.py` — reverts to a single task function

**What was changed:** The two task functions from chap04 (`send_transactional`
and `send_newsletter`) are replaced by a single `send_message` function.

```python
@shared_task
def send_message(message_id):
    from message.models import Message
    m = Message.objects.get(id=message_id)
    time.sleep(2)
    m.status = 'sent'
    m.save()
```

**Why one function is sufficient in chap05:**
In chap04, routing was based on the task *name* via `CELERY_TASK_ROUTES`.  Two
names were needed so the routing table could map them to different queues.

In chap05, routing is based on the `queue=` argument passed directly to
`apply_async()` in the view — no routing table is involved.  The same task
function can be sent to any queue by changing the `queue=` argument at call
time.  One function is therefore sufficient for all three priority levels.

**How `send_message` reaches the worker — the `@shared_task` mechanism:**
`send_message` is decorated with `@shared_task`, not `@app.task`.  The
difference matters because chap05 has two independent Celery instances:

| Instance | File | Role |
|---|---|---|
| `Celery('app')` | `app/app/celery.py` | Django process — dispatches tasks |
| `Celery('worker01')` | `worker01/celerytask.py` | Worker process — executes tasks |

`@app.task` would bind the function to exactly one of those instances at
definition time.  `@shared_task` keeps the binding lazy — the function
attaches itself to whichever Celery instance is active in the current process.

When `worker_urgent` or `worker_default` starts, `celerytask.py` runs
`app.autodiscover_tasks(['message'])`.  This imports `message/tasks.py` and
registers `send_message` under the name `message.tasks.send_message` with
the worker's own `Celery('worker01')` instance.  From that point on, every
message the worker dequeues that references `message.tasks.send_message` is
dispatched to this function and executed inside the worker container.

The Django process never executes `send_message` — it only serialises the call
to JSON and writes it to Redis.  Execution always happens inside one of the two
worker containers.

---

### `app/message/views.py` — `PRIORITY_MAP` and `apply_async()`

**What was changed:** The dispatch logic is completely rewritten.

```python
PRIORITY_MAP = {'normal': 5, 'low': 9}

if priority == 'urgent':
    send_message.apply_async(args=[m.id], queue='urgent')
else:
    send_message.apply_async(
        args=[m.id],
        queue='default',
        priority=PRIORITY_MAP[priority],
    )
```

**Why `apply_async()` and not `.delay()`:**
`.delay()` only accepts positional arguments that map to the task's parameters.
It does not accept keyword arguments like `queue=` or `priority=`.
`apply_async()` is the full form that supports all dispatch options.
`.delay(m.id)` is exactly equivalent to `.apply_async(args=[m.id])` — when
you need more than the task arguments, you must use `apply_async()`.

**Why urgent tasks have no `priority=` argument:**
The `urgent` queue has only one subscriber (`worker_urgent`) and receives only
urgent tasks.  There is no ordering decision to make — every message is equally
urgent and processed FIFO.  Adding `priority=0` would technically work but
would add `broker_transport_options` as a requirement for the `urgent` queue
as well, which is unnecessary.

**Why the `PRIORITY_MAP` values are 5 and 9:**
The valid range is 0 (highest) to 9 (lowest).  Using 5 and 9 leaves four
priority levels (0–4) available above `normal` for future categories without
requiring any changes to `PRIORITY_MAP` or the model.  Using the full extremes
(0 and 9) would leave no room for additional tiers.

**What `PRIORITY_MAP` produces in Redis:**

| Form selection | `apply_async()` call | Redis key |
|---|---|---|
| Urgent | `queue='urgent'` | `urgent` (plain FIFO list) |
| Normal | `queue='default', priority=5` | `default:5` |
| Low | `queue='default', priority=9` | `default:9` |

---

### `worker01/celeryconfig.py` — adds `broker_transport_options`

**What was added:** A new dictionary at the bottom of `celeryconfig.py`.

```python
broker_transport_options = {
    'priority_steps': list(range(10)),
    'sep': ':',
    'queue_order_strategy': 'priority',
}
```

**This is the most critical change in chap05 and the easiest to miss.**

Both the dispatcher (Django) and the consumer (the Celery worker) must have
identical `broker_transport_options`.

**What happens if this setting is missing from the worker:**
- Django's `settings.py` has `CELERY_BROKER_TRANSPORT_OPTIONS`.
- Celery on the Django side writes messages to `default:5` and `default:9`.
- The worker reads its config from `celeryconfig.py` (no `broker_transport_options`).
- Without this setting, the worker subscribes to the plain `default` Redis key.
- `default` is always empty — all messages went to `default:5` and `default:9`.
- Result: every 'normal' and 'low' task stays **pending forever**.

The fix is exactly what is in this file: `broker_transport_options` must be a
byte-for-byte copy of `CELERY_BROKER_TRANSPORT_OPTIONS` from `settings.py`.
There is no automatic synchronisation — both sides must be kept in sync manually.

---

## Key Concepts

**Routing by priority level**
In chap04, routing separates tasks by type. Here, routing separates tasks by
urgency. The `urgent` queue acts as a fast lane: its worker is never blocked
by a backlog of low-priority work because it simply does not subscribe to
the `default` queue.

**Priority ordering within a shared queue**
The `default` queue still uses Redis priority buckets so that normal tasks
(priority 5) are processed ahead of low tasks (priority 9) when both are
waiting. This is chap05's original concept, now scoped to the non-urgent tier.

**`apply_async(queue=..., priority=...)`**
The two arguments are independent. `queue` controls which worker sees the
message. `priority` controls the order in which that worker processes messages
already in its queue. For the `urgent` queue, only one priority level ever
arrives, so the `priority` argument is omitted.

**When to combine routing and prioritisation**
Use routing when different tasks have genuinely different latency requirements
and must not compete for the same worker pool. Use prioritisation when tasks
of the same class have different urgency levels. Combining both gives you SLA
tiers: an urgent tier with guaranteed capacity and a default tier with
best-effort ordering.

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
