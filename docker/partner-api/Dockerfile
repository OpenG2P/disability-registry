# Disability Registry — Partner API image.
#
# Thin extension of the registry-platform base image (see
# docker/staff-api/Dockerfile for the full rationale). Adds only the domain
# model; ENV defaults and the migrate+gunicorn CMD are inherited.
#
# This is the image that answers DCI searches, so it is the one that renders
# dr_person_to_dci.json.j2 and enforces consent scopes against it.
#
# Build context = repo root (so disability-extension/ is reachable).
ARG RP_VERSION=0.0.0-develop.421
FROM openg2p/openg2p-registry-partner-api:${RP_VERSION}

ENV REGISTRY_EXTENSION_MODULE=openg2p_registry_disability_extension

COPY disability-extension/ /app/disability-extension/
RUN pip install --no-cache-dir /app/disability-extension
