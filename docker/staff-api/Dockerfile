# Disability Registry — Staff Portal API image.
#
# Under the inverted build model the registry-platform publishes the base image
# (platform code + fastapi-common/iam-core runtime + entrypoint/CMD/ENV). This
# image only adds the Disability Registry domain model on top: the
# disability-extension is pip-installed under its own import name
# (openg2p_registry_disability_extension) and selected at runtime by
# REGISTRY_EXTENSION_MODULE. ENV defaults, the non-root user and the
# migrate+gunicorn CMD are all inherited from the base.
#
# RP_VERSION pins the openg2p-registry base image tag. Keep it in lockstep with
# the openg2p-registry chart dependency pinned in
# helm/openg2p-disability-registry/Chart.yaml — test/test_rp_pin_lockstep.py
# fails the build if they ever split.
#
# Build context = repo root (so disability-extension/ is reachable).
ARG RP_VERSION=0.0.0-develop.621
FROM openg2p/openg2p-registry-staff-api:${RP_VERSION}

# Select this registry's domain model. It coexists with the base image's
# reference extension; the env picks ours, so nothing has to be uninstalled.
ENV REGISTRY_EXTENSION_MODULE=openg2p_registry_disability_extension

COPY disability-extension/ /app/disability-extension/
RUN pip install --no-cache-dir /app/disability-extension
