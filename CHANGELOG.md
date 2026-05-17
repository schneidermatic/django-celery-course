0.2.1 (2026-05-17)
---------------------
### Changed — Update README.md references from chap to lab
* Changed - `README.md`: replaced all chapXX directory references with labXX

0.2.0 (2026-05-17)
---------------------
### Changed — Rename chapter directories to lab directories
* Changed - `chap01/` → `lab01/`: directory renamed
* Changed - `chap02/` → `lab02/`: directory renamed
* Changed - `chap03/` → `lab03/`: directory renamed
* Changed - `chap04/` → `lab04/`: directory renamed
* Changed - `chap05/` → `lab05/`: directory renamed
* Changed - `chap06/` → `lab06/`: directory renamed

0.1.1 (2026-05-09)
---------------------
### Changed — README cleanup
* Changed - `README.md`: removed Git Workflow section (workflow is documented in CLAUDE.md only)

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
