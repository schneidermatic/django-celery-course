# chap06 — Async HTTP Request with Result Storage

## What this chapter demonstrates

This chapter extends the standalone-worker pattern from **chap03** to show a
complete async round-trip with a real external HTTP service:

```
Browser → Django (save + dispatch) → Redis → Worker → httpbin.org
                                                  ↓
Browser ← Django (read result)    ← SQLite ← Worker (save response)
```

1. The user submits a form with a **label** and a **payload** text.
2. Django saves a `Payload` record immediately with `status = pending`.
3. Django dispatches the Celery task `post_to_httpbin` to Redis and redirects
   to the results list — without waiting for the task to finish.
4. The standalone worker picks up the task, POSTs the payload as JSON to
   `https://httpbin.org/post`, and writes the response back to the database
   (`status = done`, HTTP status code, full response body).
5. The results list page auto-refreshes every 3 seconds while any record is
   still `pending`. Once the task completes, the status badge turns green and
   a **View response** link appears.
6. The detail view shows the full JSON response from httpbin.org, including
   the echoed payload, request headers, origin IP, and more.

---

## Services

| Service | URL | Description |
|---|---|---|
| Django (web) | http://localhost:8000 | Submit form, view results |
| Flower | http://localhost:5555 | Celery task monitor |

---

## Running

```bash
cd chap06
. .xrc
x_setup          # builds images and starts all 4 services
```

Stop and clean up:

```bash
x_destroy        # stops containers, removes volumes and local images
```

---

## What to enter in the form

**Label** — a short identifier for this request. Used to tag the payload sent
to httpbin.org so you can recognise it in the response. Examples:

```
test-1
hello-world
my-first-async-request
```

**Data** — the payload text that gets POSTed to httpbin.org. This can be any
free-form text. httpbin.org echoes it back verbatim under the `"json"` key of
its response, so you can use it to verify the round-trip. Examples:

```
Hello from chap06
{"message": "async works!"}
temperature=22.5&unit=celsius
```

> The data field accepts plain text — no special formatting required.
> httpbin.org will echo back exactly what you send.

---

## What the httpbin.org response looks like

After the task completes, click **View response** to see the full JSON
returned by httpbin.org. It looks like this:

```json
{
  "args": {},
  "data": "{\"label\": \"test-1\", \"data\": \"Hello from chap06\"}",
  "files": {},
  "form": {},
  "headers": {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
    "Content-Length": "49",
    "Content-Type": "application/json",
    "Host": "httpbin.org",
    "User-Agent": "python-requests/2.32.3"
  },
  "json": {
    "data": "Hello from chap06",
    "label": "test-1"
  },
  "origin": "...",
  "url": "https://httpbin.org/post"
}
```

The `"json"` key contains your original label and data — confirming the
payload made it through Django → Redis → Worker → httpbin.org and back.

---

## Worker internals — step by step

### 1. How the worker process starts

When `docker compose up` starts the `worker01` container, it runs:

```
celery -A celerytask worker -l INFO -E
```

`celerytask.py` is the entry point. It runs the following steps **in this exact
order** before Celery is even imported:

```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()   # initialises the ORM — must happen first
from celery import Celery
```

`django.setup()` must come before the Celery import because `autodiscover_tasks`
immediately imports `payload/tasks.py`, which in turn imports
`payload/models.py`. The ORM must be ready before any model class is loaded.
Without this order the worker would crash with an `AppRegistryNotReady`
exception.

After `django.setup()`, Celery creates its own independent application
instance (`Celery('worker01')`), reads the broker and backend URLs from
`celeryconfig.py`, and scans the `payload` package for a `tasks.py` file.
The worker is now connected to Redis and listening for messages.

---

### 2. How Django hands off the task

Back in the web container, when the user submits the form, `views.py` runs:

```python
p = Payload.objects.create(label=..., data=...)   # 1. write to DB immediately
post_to_httpbin.delay(p.id)                        # 2. write task message to Redis
return redirect('list')                            # 3. return HTTP response at once
```

`.delay(p.id)` serialises the task name and the integer primary key to JSON
and writes them to a Redis list. The web process does not wait — it returns
the redirect response to the browser within milliseconds, while the database
record still has `status = pending`.

Only the **primary key** is passed to the task, not the model instance itself.
Model instances cannot be serialised to JSON reliably; passing an integer ID
and re-fetching the record inside the task is the standard Celery pattern.

---

### 3. What the worker executes — `post_to_httpbin`

The full task function in `payload/tasks.py`:

```python
@shared_task
def post_to_httpbin(payload_id):
    from payload.models import Payload          # (A) deferred import

    p = Payload.objects.get(id=payload_id)      # (B) read record from DB

    try:
        response = requests.post(               # (C) HTTP POST to httpbin.org
            'https://httpbin.org/post',
            json={'label': p.label, 'data': p.data},
        )
        p.status          = 'done'              # (D) success path
        p.response_body   = response.text
        p.response_status = response.status_code
    except Exception as exc:
        p.status        = 'failed'              # (E) failure path
        p.response_body = str(exc)

    p.save()                                    # (F) write result back to DB
```

**Step A — deferred import:** The model import is inside the function body, not
at the top of the module. `tasks.py` is loaded once at worker startup during
`autodiscover_tasks`. At that moment Django's ORM is initialised but there is
a brief window where placing the import at module level can cause subtle issues
on first load. Deferring it to the function body is the safe, conventional
pattern for Celery tasks that use Django models.

**Step B — DB read:** The worker fetches the `Payload` row by its primary key.
The worker container has no web server, but it accesses the same SQLite file as
Django through the Docker volume mount (`./app:/usr/src/app/`). Both containers
read and write the same physical file.

**Step C — HTTP POST:** `requests.post(..., json=...)` sends a POST request to
`https://httpbin.org/post`. The `json=` keyword argument automatically:
- serialises the Python dict to a JSON string
- sets the `Content-Type: application/json` header

httpbin.org is a public echo service that reflects the request back as JSON.
No authentication or API key is needed.

**Step D — success path:** On a successful HTTP response (any status code,
including 4xx/5xx), the three fields are updated in memory:
- `status` is set to `'done'`
- `response_body` receives the full raw response text (a JSON string, ~500–800
  bytes for a typical httpbin.org reply)
- `response_status` receives the integer HTTP status code (normally `200`)

**Step E — failure path:** If `requests.post` raises an exception — for
example a `ConnectionError` when httpbin.org is unreachable, or a `Timeout` —
the except block catches it:
- `status` is set to `'failed'`
- `response_body` stores the human-readable exception message as plain text
- `response_status` is left `None` (the field is nullable) because no HTTP
  response was received

**Step F — DB write:** A single `p.save()` call at the end writes all changed
fields back to SQLite. Django generates an `UPDATE` statement for all fields on
the object, not just the changed ones. The write is synchronous — the task
completes once `save()` returns.

---

### 4. How the result reaches the browser

The browser is on the results list page (`/list/`), which contains:

```html
<meta http-equiv="refresh" content="3">
```

This tag is only rendered when at least one `Payload` row has `status =
pending`. It tells the browser to reload the page every 3 seconds. On each
reload, `views.py` queries the database:

```python
payloads = Payload.objects.all().order_by('-created_at')
has_pending = payloads.filter(status='pending').exists()
```

Once the worker has written `status = done` to SQLite, the next page reload
picks up the updated row. The status badge changes from orange `pending` to
green `done`, the **View response** link appears, and — because no rows are
`pending` anymore — the `<meta refresh>` tag is no longer emitted. The page
stops refreshing on its own.

---

### 5. How the detail view renders the stored response

`payload_detail` in `views.py` retrieves the raw string stored in
`response_body` and pretty-prints it:

```python
pretty_body = json.dumps(json.loads(p.response_body), indent=2)
```

`json.loads` parses the stored string back into a Python dict; `json.dumps`
re-serialises it with 2-space indentation. The result is passed to the
template and rendered inside a `<pre>` block. Django's template engine
auto-escapes the content, so any `<`, `>`, or `&` characters inside the JSON
are safe to display in HTML.

If `response_body` is not valid JSON (for example in a `failed` record where
it contains an exception message), the `json.JSONDecodeError` is caught and the
raw string is displayed as-is.

---

## Key files

| File | Purpose |
|---|---|
| `app/payload/models.py` | `Payload` model — stores label, data, status, response |
| `app/payload/tasks.py` | `post_to_httpbin` — the Celery task that calls httpbin.org |
| `app/payload/views.py` | `index`, `payload_list`, `payload_detail` |
| `app/payload/templates/payload/list.html` | Auto-refreshing results list |
| `worker01/celerytask.py` | Standalone worker entry point |

---

## Status values

| Status | Meaning |
|---|---|
| `pending` | Task dispatched, worker has not finished yet |
| `done` | httpbin.org responded successfully — response stored in DB |
| `failed` | Network error or unexpected exception — error message stored in DB |
