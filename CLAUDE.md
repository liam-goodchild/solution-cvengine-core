# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CVEngine Core is a serverless portfolio site hosted on Azure. It consists of three components:

- **frontend/** — Static HTML/CSS/JS portfolio site (vanilla CSS, no framework, no build step). Uses Space Grotesk + JetBrains Mono fonts, Font Awesome 6.3.0 icons, AOS scroll animations.
- **functions/** — Node.js Azure Function (`UpdateVisitorCount`) that tracks visitors via Cosmos DB
- **infra/** — Terraform IaC provisioning Azure Static Web App, Cosmos DB (SQL API, free tier), DNS CNAME

## Common Commands

### Azure Functions (backend)

```bash
cd functions
npm install
npm run build --if-present
```

### Terraform

```bash
cd infra
terraform init -backend-config="resource_group_name=<rg>" -backend-config="storage_account_name=<sa>" -backend-config="container_name=terraform" -backend-config="key=terraform.tfstate"
terraform validate
terraform plan -var-file="vars/globals.tfvars" -var-file="vars/uks/prd.tfvars"
terraform apply -var-file="vars/globals.tfvars" -var-file="vars/uks/prd.tfvars"
```

### Linting

Linting runs in CI via Super-Linter. Configs live in `.azuredevops/linters/`:

- **Prettier** (`.prettierrc.json`): YAML uses single quotes, JSON uses double quotes
- **TFLint** (`.tflint.hcl`): `terraform_unused_declarations` rule is disabled
- **Checkov** (`.checkov.yaml`): Several Azure checks skipped for free-tier compatibility

## Architecture

### Request Flow

Browser → Azure Static Web App (frontend/) → Azure Function API (`/api/UpdateVisitorCount`) → Cosmos DB (`visitorDatabase.visitorContainer`)

### Infrastructure Naming Convention

Resources follow: `${project}-${solution}-${environment}-${location}-${service}-<type>-01`
Example: `sh-app-prd-uks-cve-rg-01`

### Terraform Variable Structure

- `infra/vars/globals.tfvars` — Shared config (location, project, solution, DNS)
- `infra/vars/uks/dev.tfvars` — Dev environment
- `infra/vars/uks/prd.tfvars` — Production environment

### CI/CD (Azure DevOps)

Pipelines in `.azuredevops/`:

- **ci-terraform.yaml** — PR validation: lint, checkov, terraform plan
- **cd-terraform.yaml** — Main branch: plan → apply → deploy static web app → Git version tag
- **dev-terraform.yaml** — Manual trigger for dev infrastructure
- **destroy-terraform.yaml** — Requires typing "DESTROY" to confirm

Service connection: `sh-sc-cvengine`

### Functions Runtime

- Node.js 18.x, Azure Functions runtime v2.0
- Single function: `UpdateVisitorCount` (GET/POST)
- Cosmos DB connection via `COSMOSDB_CONNECTION_STRING` env var
