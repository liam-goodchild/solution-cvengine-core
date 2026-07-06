# AGENTS.md

This file provides guidance to Codex CLI and other AI coding agents when working with code in this repository.

## Project Overview

CVEngine is a serverless portfolio site hosted on Azure. Three components:

- **frontend/** - Static HTML/CSS/JS portfolio site (vanilla CSS, no framework, no build step). Space Grotesk + JetBrains Mono fonts, Font Awesome 6.3.0, AOS scroll animations.
- **functions/** - Node.js 18.x Azure Function (`UpdateVisitorCount`, GET/POST) tracking visitors in Cosmos DB. Runtime v2.0. Cosmos connection via `COSMOSDB_CONNECTION_STRING`.
- **infra/** - Terraform IaC: Resource Group, Static Web App + custom domain, Cosmos DB (SQL API, free tier), DNS CNAME on existing zone.

## Common Commands

### Azure Functions

```bash
cd functions
npm ci              # CI uses `npm ci` - requires package-lock.json
npm run build --if-present
```

### Terraform

State lives in a platform storage account; backend is configured at init time:

```bash
cd infra
terraform init \
  -backend-config="resource_group_name=rg-platform-<env>-uks-01" \
  -backend-config="storage_account_name=stplatform<env>uks02" \
  -backend-config="container_name=<repo-name>" \
  -backend-config="key=terraform.tfstate"
terraform validate
terraform plan  -var-file="vars/prd.tfvars"
terraform apply -var-file="vars/prd.tfvars"
```

## Architecture

### Request Flow

Browser → Azure Static Web App (frontend/) → Azure Function API (`/api/UpdateVisitorCount`) → Cosmos DB (`visitorDatabase.visitorContainer`).

### Naming Convention

`${project}-${solution}-${environment}-${location}-${service}-<type>-01` - e.g. `sh-app-prd-uks-cve-rg-01`.

### Terraform Variables

- `infra/vars/dev.tfvars` - dev
- `infra/vars/prd.tfvars` - prd

Terraform: `1.15.3` (CI pins `1.15.3`). Providers: `azurerm >= 4.0 < 5.0`, `azuread >= 3.0 < 4.0`.

### CI/CD (GitHub Actions)

Workflows in `.github/workflows/`:

- **terraform.yml** - Push to `major/**`, `minor/**`, `patch/**` under `infra/**`, or `workflow_dispatch` (env: dev/prd, action: plan/apply/destroy). Uses OIDC (`ARM_USE_OIDC=true`) via federated creds; no client secret. Composite action `./.github/actions/ensure-tfstate-container` bootstraps the backend container.
- **swa.yml** - Push to `major/**` / `minor/**` / `patch/**` under `frontend/**` or `functions/**`. Logs into Azure via OIDC, fetches the SWA deployment token at runtime with `az staticwebapp secrets list`, then runs `azure/static-web-apps-deploy`. `app_location: frontend`, `api_location: functions`.
- **linting.yml** - Super-Linter (Biome disabled).
- **zizmor.yml** - GitHub Actions workflow security scanner.
- **tag.yml** - Git version tagging.

Linter configs in `.github/linters/` (Prettier, TFLint, Checkov).

Environment **variables** required (`dev` / `prd`): `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `AZURE_PLATFORM_SUBSCRIPTION_ID` (set by `infra-landingzone-platform/scripts/bootstrap-platform.sh`). Sensitive values are fetched from the platform Key Vault (`kv-platform-<env>-uks-02`) after OIDC login.

Branch naming drives CI: only `major/**`, `minor/**`, `patch/**` branches trigger deploy workflows on push.

### Pipeline Hardening Conventions

Workflows follow zizmor/Checkov findings baked into CI:

- `persist-credentials: false` on every `actions/checkout`.
- Third-party actions pinned to commit SHA with a trailing `# vX.Y.Z` comment (e.g. `azure/login@a457da9...`). First-party `actions/*` may use `@vN`.
- Least-privilege `permissions:` block per workflow; `id-token: write` only where OIDC is needed.

Keep these when editing or adding workflows.
