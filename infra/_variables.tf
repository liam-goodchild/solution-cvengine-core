variable "location" {
  description = "Resource location for Azure resources."
  type        = string
}

variable "environment" {
  description = "Name of Azure environment (dev/prd)."
  type        = string
}

variable "project" {
  description = "Project/organization code prefix for resource naming."
  type        = string
}

variable "solution" {
  description = "Solution name for resource naming."
  type        = string
}

variable "service" {
  description = "Service short name for resource naming."
  type        = string
}

variable "dns_zone_name" {
  description = "Name of the existing DNS zone."
  type        = string
}

variable "dns_zone_resource_group" {
  description = "Resource group containing the DNS zone."
  type        = string
}

variable "subdomain" {
  description = "Subdomain for the portfolio site (e.g., 'portfolio')."
  type        = string
}

variable "cosmosdb_free_tier" {
  description = "Enable Cosmos DB free tier."
  type        = bool
  default     = true
}
