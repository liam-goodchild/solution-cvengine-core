# CVEngine

## Purpose

This repository defines the infrastructure and application code for CVEngine, a serverless portfolio and CV platform.
The goal is to provide a modern, scalable, and cost-effective online presence using Azure cloud services.

This solution:

- Deploys a serverless portfolio website using Azure Static Web Apps
- Implements visitor tracking via Azure Functions and Cosmos DB
- Automates infrastructure provisioning using Terraform and Azure DevOps
- Maintains security and compliance through automated linting and validation
- Provides a custom domain experience with DNS integration

---

## Architecture

CVEngine uses a serverless architecture built entirely on Azure Platform-as-a-Service offerings.

**Frontend**: Azure Static Web Apps hosts the portfolio website with global CDN distribution and custom domain support.

**Backend**: Azure Functions provides serverless API endpoints for visitor count tracking, connected to Cosmos DB for data persistence.

**Infrastructure**: Terraform manages all Azure resources, with state stored remotely in Azure Storage. Azure DevOps pipelines handle CI/CD workflows.

---

## Repository Structure

```
solution-cvengine-core/
├── .azuredevops/          # Pipeline definitions and linting configuration
├── frontend/              # Static website HTML, CSS, and JavaScript
├── functions/             # Azure Functions API code
└── infra/                 # Terraform infrastructure as code
    ├── vars/              # Environment-specific variable files
    └── *.tf               # Terraform resource definitions
```

---

## Deployment

### Prerequisites

- Azure subscription with appropriate permissions
- Terraform >= 1.0
- Azure CLI >= 2.0
- Configured Azure DevOps service connection

### Automated Deployment

1. Create a feature branch and make changes
2. Push changes and open a pull request to `main`
3. CI pipeline validates Terraform and runs linting
4. Merge to `main` triggers production deployment via CD pipeline

### Manual Deployment

```bash
cd infra
terraform init \
  -backend-config="resource_group_name=<backend-rg>" \
  -backend-config="storage_account_name=<backend-sa>" \
  -backend-config="container_name=solution-cvengine-core"

terraform plan \
  -var-file="vars/globals.tfvars" \
  -var-file="vars/uks/dev.tfvars"

terraform apply \
  -var-file="vars/globals.tfvars" \
  -var-file="vars/uks/dev.tfvars"
```

---

## Terraform Documentation

<!-- prettier-ignore-start -->
<!-- textlint-disable -->
<!-- BEGIN_TF_DOCS -->
<!-- END_TF_DOCS -->
<!-- textlint-enable -->
<!-- prettier-ignore-end -->

---

## Summary

CVEngine provides a complete serverless portfolio solution using Azure Static Web Apps, Functions, and Cosmos DB. All infrastructure is defined as code using Terraform, with automated CI/CD pipelines ensuring quality and security through linting and validation. The solution leverages free-tier Azure services to minimize costs while maintaining professional functionality.
