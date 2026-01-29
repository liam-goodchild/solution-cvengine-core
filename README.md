# CVEngine

## Purpose

This repository defines the infrastructure and application code for CVEngine, a serverless portfolio and CV platform.
The goal is to provide a modern, scalable, and cost-effective online presence using Azure cloud services.

This solution:

- Deploys a serverless portfolio site using Azure Static Web Apps
- Implements visitor tracking via Azure Functions and Cosmos DB
- Automates infrastructure provisioning using Terraform and Azure DevOps
- Maintains security and compliance through automated linting and validation
- Provides a custom domain experience with DNS integration

---

## Architecture

CVEngine uses a serverless architecture built entirely on Azure Platform-as-a-Service offerings.

**Frontend**: Azure Static Web Apps hosts the portfolio site with global CDN distribution and custom domain support.

**Backend**: Azure Functions provides serverless API endpoints for visitor count tracking, connected to Cosmos DB for data persistence.

**Infrastructure**: Terraform manages all Azure resources, with state stored remotely in Azure Storage. Azure DevOps pipelines handle CI/CD workflows.

---

## Repository Structure

```
solution-cvengine-core/
├── .azuredevops/          # Pipeline definitions and linting configuration
├── frontend/              # Static site HTML, CSS, and JavaScript
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
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.0, < 2.0 |
| <a name="requirement_azuread"></a> [azuread](#requirement\_azuread) | >= 3.0, < 4.0 |
| <a name="requirement_azurerm"></a> [azurerm](#requirement\_azurerm) | >= 4.0, < 5.0 |

## Resources

| Name | Type |
|------|------|
| [azurerm_cosmosdb_account.main](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/cosmosdb_account) | resource |
| [azurerm_cosmosdb_sql_container.visitor](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/cosmosdb_sql_container) | resource |
| [azurerm_cosmosdb_sql_database.visitor](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/cosmosdb_sql_database) | resource |
| [azurerm_dns_cname_record.swa](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/dns_cname_record) | resource |
| [azurerm_resource_group.main](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/resource_group) | resource |
| [azurerm_static_web_app.main](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/static_web_app) | resource |
| [azurerm_static_web_app_custom_domain.main](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/static_web_app_custom_domain) | resource |
| [azurerm_client_config.current](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/data-sources/client_config) | data source |
| [azurerm_dns_zone.main](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/data-sources/dns_zone) | data source |

## Modules

No modules.

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_dns_zone_name"></a> [dns\_zone\_name](#input\_dns\_zone\_name) | Name of the existing DNS zone. | `string` | n/a | yes |
| <a name="input_dns_zone_resource_group"></a> [dns\_zone\_resource\_group](#input\_dns\_zone\_resource\_group) | Resource group containing the DNS zone. | `string` | n/a | yes |
| <a name="input_environment"></a> [environment](#input\_environment) | Name of Azure environment (dev/prd). | `string` | n/a | yes |
| <a name="input_location"></a> [location](#input\_location) | Resource location for Azure resources. | `string` | n/a | yes |
| <a name="input_project"></a> [project](#input\_project) | Project/organization code prefix for resource naming. | `string` | n/a | yes |
| <a name="input_service"></a> [service](#input\_service) | Service short name for resource naming. | `string` | n/a | yes |
| <a name="input_solution"></a> [solution](#input\_solution) | Solution name for resource naming. | `string` | n/a | yes |
| <a name="input_subdomain"></a> [subdomain](#input\_subdomain) | Subdomain for the portfolio site (e.g., 'portfolio'). | `string` | n/a | yes |
| <a name="input_cosmosdb_free_tier"></a> [cosmosdb\_free\_tier](#input\_cosmosdb\_free\_tier) | Enable Cosmos DB free tier. | `bool` | `true` | no |

## Outputs

No outputs.
<!-- END_TF_DOCS -->
<!-- textlint-enable -->
<!-- prettier-ignore-end -->

---

## Summary

CVEngine provides a complete serverless portfolio solution using Azure Static Web Apps, Functions, and Cosmos DB. All infrastructure is defined as code using Terraform, with automated CI/CD pipelines ensuring quality and security through linting and validation. The solution leverages free-tier Azure services to minimize costs while maintaining professional functionality.
