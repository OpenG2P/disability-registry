# OpenG2P Disability Registry

A ready-to-install **Disability Registry** built on the OpenG2P registry
platform, modelled on the SPDCI Disability Registry data objects
(DO.DR.01 – DO.DR.10).

A single-register, individual-subject registry: one `PersonWithDisability`
register with eight detail tables — impairments, the five kinds of support
(human assistance, assistive technology, medical care, housing, animal),
related persons and programme enrolments. There is no household register.

This package is a thin overlay over the shared **openg2p-registry** chart: it
adds the domain via images built from this repository, and reuses the platform's
service templates, IAM/Keycloak wiring, db-seed machinery and sanity suite
unchanged. It adds only the analytics jobs that are genuinely its own — the
reporting views and the Superset dashboard import, both written against this
registry's schema.

- **Platform chart & images:** published by
  [registry-platform](https://gitlab.com/openg2p/registry/registry-platform);
  this chart pins a specific `openg2p-registry` version as a dependency.
- **What to set:** the ingress host (`global.registryHostname`) and, for a real
  environment, the shared commons endpoints (Postgres, Keycloak, Consent/Partner
  Management, AWE, Audit) via the inherited `global.*` values.
- **Geography and code lists:** come from the environment's Master Data Service
  (`geoSeed.countryPack` in the `openg2p-master-data` chart). Nothing in this
  chart names a country.

## The defaults are SANDBOX defaults

Out of the box this installs with demo data on and the sanity suite enabled.
For production, at minimum:

```yaml
registry:
  dbSeed:
    enabled: true          # required — the metadata IS the registry
    loadTemplates: true    # required — without the DCI templates every
                           #            partner search returns an empty 200
    loadSampleData: false
    loadImages: false
  sanity:
    enabled: false
    runE2e: false          # never true in production
analytics:
  reportingViews:
    enabled: true
global:
  partnerSignatureValidationEnabled: true
  consentEnforcementEnabled: true
```

Never promote a sandbox namespace to production — demo records cannot be cleanly
separated afterwards. Install fresh.

## Dashboards

`analytics.dashboards.enabled` defaults to **false**. The Superset bundle is
built rather than shipped; build it into `files/dr-dashboards.zip` with
`docker/dashboards/build_bundle.py` before turning this on.

See the deployment docs at [docs.openg2p.org](https://docs.openg2p.org).
