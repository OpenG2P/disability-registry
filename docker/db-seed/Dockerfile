# Disability Registry — DB-seed image.
#
# Thin extension of the registry-platform db-seed base image. The base ships the
# seeding machinery (entrypoint.sh, the shared openg2p-data clone, geo loader,
# code-list loader, geo-widget sync, template uploader) plus the reference
# registry's seed content. This image replaces the seed content with ours, and
# adds the two loaders that are NOT domain-agnostic.
#
# WHICH LOADERS ARE DOMAIN-SPECIFIC
#   The base image's load_sample_data.py and upload_images.py are written against
#   the REFERENCE registry's schema — they INSERT into g2p_register_individuals /
#   g2p_register_households and read that registry's seed JSON. This registry has
#   neither (it has g2p_register_persons_with_disability plus the DO.DR.04-10
#   sub-tables), so inheriting them makes the Job crash-loop the moment
#   LOAD_SAMPLE_DATA=true. We therefore ship our own, copied over the inherited
#   ones below.
#
#   Genuinely generic and inherited unchanged: entrypoint.sh, load_geo_data.py,
#   load_attributes_from_mds.py, sync_geo_widgets.py, upload_templates.py,
#   requirements.txt.
#
# The entrypoint (inherited) reads /seed/* at container-run time; behaviour is
# toggled entirely via env from the Helm Job.
#
# Build context = repo root (so disability-extension/ and docker/db-seed/ are
# both reachable).
ARG RP_VERSION=0.0.0-develop.383
FROM registry.gitlab.com/openg2p/registry/registry-platform/db-seed:${RP_VERSION}

# The base image ships the reference registry's seed; clear it so only this
# registry's seed is applied. Without this the reference registry's register
# definitions are inserted alongside ours and the staff portal shows both.
RUN rm -rf /seed/meta_data/* /seed/awe_meta_data/* /seed/templates/* /seed/seed-data/*

COPY disability-extension/src/openg2p_registry_disability_extension/meta_data/     /seed/meta_data/
COPY disability-extension/src/openg2p_registry_disability_extension/awe_meta_data/ /seed/awe_meta_data/
COPY disability-extension/src/openg2p_registry_disability_extension/templates/     /seed/templates/
COPY docker/db-seed/seed-data/                                                     /seed/seed-data/

# This registry's domain-specific loaders, overriding the base image's
# reference-shaped ones.
COPY docker/db-seed/load_sample_data.py /seed/load_sample_data.py
COPY docker/db-seed/upload_images.py    /seed/upload_images.py

# The reporting layer. These views are this registry's own schema and ship with
# this image; reporting.yaml carries what the platform's generator cannot infer.
COPY docker/db-seed/reporting_views.sql /seed/reporting_views.sql
COPY docker/db-seed/reporting.yaml      /seed/reporting.yaml

RUN chmod +x /seed/load_sample_data.py /seed/upload_images.py
