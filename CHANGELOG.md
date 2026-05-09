0.1.0 (2026-05-09)
---------------------
### New Feature — Initial course release (chap01–chap06)
* Added   - `chap01/`: Skeleton — Django + Celery + Redis wiring, no custom app
* Added   - `chap02/`: Basics — `Message` model, `@shared_task`, `.delay()`, result stored in DB
* Added   - `chap03/`: Standalone Worker — independent `worker01/` image, volume mount, `PYTHONPATH`
* Added   - `chap04/`: Task Routing — `send_transactional` / `send_newsletter`, two queues, two workers
* Added   - `chap05/`: Priority Queues — `worker_urgent` + `worker_default`, `apply_async(priority=X)`
* Added   - `chap06/`: Async HTTP Request — `post_to_httpbin` task, response stored in DB, auto-refresh list
* Added   - `CLAUDE.md`: codebase guidance for Claude Code including Git commit workflow
* Added   - `README.md`: course overview, learning path, chapter table, Git workflow documentation
* Added   - `assets/tools/x_setup.sh`, `x_destroy.sh`: shared Docker Compose helpers
