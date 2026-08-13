Both celery codebases (celery-workers and celery-beat-producers), plus the
`run_celery.py` startup wrapper, live in the registry-platform base image
`registry-platform/celery`. This registry's `docker/celery/Dockerfile` only
extends that base with the Disability Registry domain model — it does not
install celery itself.

Because both codebases are present in the base, which application runs is
selected at startup via environment variables. `run_celery.py` (inherited from
the base) reads them:

1. Run as a Worker (default):

   ```
   CELERY_APP: openg2p_registry_celery_workers.main.celery_app
   CELERY_OPTS: worker --loglevel=info
   ```

2. Run as a Beat producer:

   ```
   CELERY_APP: openg2p_registry_celery_beat_producers.main.celery_app
   CELERY_OPTS: worker --beat --loglevel=info --schedule=/tmp/celery-beat-schedule.db
   ```

These are set per-deployment in the Helm values (`celeryWorker` / `celeryBeat`).

## What the worker does for THIS registry

Two things, both of which are invisible until the worker is running:

* **Section completion scores.** `load_sample_data.py` and every change-request
  approval enqueue rows into `g2p_completion_score_computation_queue`; the worker
  drains it. Without a worker the queue simply grows and the completion
  percentages in the staff portal stay empty.
* **The `SUPPORT_NEED` score.** Computed by
  `score_compute/services/support_need.py` in this repo's extension, which is
  installed into this image. The seed loader writes an initial value so the demo
  dashboards are not blank, but the worker is what keeps it current as support
  rows change.
