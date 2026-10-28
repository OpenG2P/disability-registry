# Disability Registry — Celery image (workers + beat).
#
# Thin extension of the registry-platform celery base image (see
# docker/staff-api/Dockerfile for the full rationale). Adds only the domain
# model; both celery packages, the run_celery.py wrapper, the CELERY_* ENV
# defaults and the CMD are inherited from the base. A single image runs as
# worker or beat, selected at runtime via CELERY_APP.
#
# This image runs the SUPPORT_NEED score computation, so score_compute/ has to
# be present here as well as in the APIs — which it is, since the whole
# extension package is installed.
#
# Build context = repo root (so disability-extension/ is reachable).
ARG RP_VERSION=0.0.0-develop.625
FROM openg2p/openg2p-registry-celery:${RP_VERSION}

ENV REGISTRY_EXTENSION_MODULE=openg2p_registry_disability_extension

COPY disability-extension/ /app/disability-extension/
RUN pip install --no-cache-dir /app/disability-extension
