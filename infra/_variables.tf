variable "location" {
  description = "Resource location for Azure resources."
  type        = string
  default     = "uksouth"
}

variable "location_short" {
  description = "Short region token for resource naming."
  type        = string
  default     = "uks"
}

variable "environment" {
  description = "Name of Azure environment (dev/prd)."
  type        = string
}

variable "workload" {
  description = "Workload name for resource naming."
  type        = string
  default     = "cvengine"
}

variable "instance" {
  description = "Two-digit resource instance identifier."
  type        = string
  default     = "01"
}

variable "dns_zone_name" {
  description = "Domain name for the public DNS zone."
  type        = string
}

variable "platform_subscription_id" {
  description = "Subscription ID for the platform subscription that contains legacy Azure DNS records in state."
  type        = string
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token with Zone and DNS edit permissions."
  type        = string
  sensitive   = true
}

variable "cloudflare_account_id" {
  description = "Cloudflare account ID."
  type        = string
}

variable "cosmosdb_free_tier" {
  description = "Enable Cosmos DB free tier."
  type        = bool
  default     = true
}
