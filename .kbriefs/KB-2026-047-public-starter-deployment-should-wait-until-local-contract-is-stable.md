---
id: KB-2026-047
type: standard
status: published
created: 2026-04-30
updated: 2026-04-30
tags: [starters, deployment, cloud-run, cloudflare-pages, local-first, kbpd]
related:
  - KB-2026-045-public-starter-service-should-launch-with-a-hosted-derivative.md
  - KB-2026-046-public-starter-downloads-should-come-from-released-snapshots.md
  - KB-2026-029-free-local-baseline-vs-robust-remote-control-plane.md
---

# Public Starter Deployment Should Wait Until Local Contract Is Stable

## Context

The starter generator now has a local website, a hardened public-safe API
surface, released catalog snapshots, and downloadable zip artifacts. The next
question was what must be configured so GitHub Actions can deploy that system
to Cloud Run and Cloudflare Pages.

That setup is feasible now, but the product surface is still being refined
locally. The main KBPD question is not whether deployment is possible. It is
whether deployment should happen before the hosted contract stops changing
rapidly.

## Decision

Defer public deployment for now.

Continue refining the hosted derivative contract through the local site first,
then set up cloud deployment once the API, artifact model, and release flow are
stable enough that infrastructure work will not be churn-heavy.

When deployment does begin, use this split model:

1. `Cloud Run` for the Python starter API
2. `Cloudflare Pages` Direct Upload for the static site
3. `GitHub Actions -> Google Cloud` through Workload Identity Federation
4. `GitHub Actions -> Cloudflare Pages` through a scoped API token

## Why This Is The Right Standard Now

- it preserves momentum on the actual starter product instead of shifting early
  effort into cloud plumbing
- it avoids reworking CI/CD and secrets every time the public contract changes
- it keeps the local-first proof path strong while the hosted surface is still
  evolving
- it still leaves a clear, low-ambiguity deployment path ready for later

## Required Setup For Later Deployment

### Google Cloud Run

When deployment begins, GitHub Actions should authenticate to Google Cloud with
OIDC and Workload Identity Federation rather than a stored JSON service account
key.

Required Google Cloud setup:

- a Google Cloud project for the hosted API
- enabled APIs:
  - IAM
  - Resource Manager
  - Service Account Credentials
  - Security Token Service
  - Cloud Run
  - Artifact Registry
  - Cloud Build if source/buildpack deployment is ever used
- an Artifact Registry repository for the API image
- a dedicated service account for GitHub Actions deployments
- a Workload Identity Pool and Provider that trust this GitHub repository
- attribute conditions that restrict which repository, branch, or environment
  may deploy

Minimum IAM roles for the deployer service account:

- `roles/run.admin`
- `roles/iam.serviceAccountUser`
- `roles/artifactregistry.writer` if GitHub Actions pushes container images
- `roles/artifactregistry.reader` to deploy images from Artifact Registry

Required GitHub-side workflow permissions:

- `contents: read`
- `id-token: write`

Recommended GitHub environment variables or non-secret configuration:

- `GCP_PROJECT_ID`
- `GCP_REGION`
- `GCP_WIF_PROVIDER`
- `GCP_SERVICE_ACCOUNT`
- `GAR_LOCATION`
- `GAR_REPOSITORY`
- `CLOUD_RUN_SERVICE`

### Cloudflare Pages

Use `Direct Upload`, not Pages Git integration, so GitHub Actions remains the
authoritative build and deploy surface for the static UI.

Required Cloudflare setup:

- a Cloudflare Pages project created as a Direct Upload project
- a scoped Cloudflare API token with account-level `Pages Write`
- the Cloudflare account ID

Required GitHub secrets:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

Recommended GitHub environment variables or non-secret configuration:

- `CLOUDFLARE_PAGES_PROJECT`
- optional branch/environment mapping values if preview and production deploys
  are split

## Recommended GitHub Deployment Structure

When deployment begins, split the hosted deployment into two jobs:

1. `deploy-api`
2. `deploy-ui`

The `deploy-api` job should:

- authenticate to Google Cloud with `google-github-actions/auth`
- build and push a container image to Artifact Registry
- deploy the image to Cloud Run

The `deploy-ui` job should:

- build the static frontend
- deploy static assets with `wrangler pages deploy`

Use GitHub Environments such as `staging` and `production` so:

- production secrets are isolated
- branch restrictions are explicit
- reviewer gates can be added later without changing the workflow shape

## Evidence

- the local starter site now exposes a public-safe API from
  `scripts/starter_site.py`
- released snapshot and artifact generation are implemented in
  `scripts/starter_catalog.py`
- the public API contract is proven by
  `scripts/validate_public_starter_api.py`
- Google Cloud documentation recommends Workload Identity Federation for
  deployment pipelines instead of long-lived service account keys
- Cloudflare Pages CI guidance for Direct Upload uses `CLOUDFLARE_ACCOUNT_ID`
  and `CLOUDFLARE_API_TOKEN`

## Applicability

### This Standard Applies To

- deciding when to start hosted deployment work for the starter generator
- preparing GitHub CI/CD for future Cloud Run and Cloudflare Pages deployment

### This Standard Does Not Mean

- public deployment is blocked by a technical impossibility
- local refinement should continue indefinitely without a convergence point
- the eventual target architecture has changed

## Practical Next Step

Before setting up cloud deployment, continue refining:

- the local public API surface
- the release snapshot flow
- the downloadable artifact contract
- the minimal static UI

Once those stop changing rapidly, add:

- deployment docs
- GitHub deployment workflows
- cloud resource scaffolding
- environment-specific secret inventories
