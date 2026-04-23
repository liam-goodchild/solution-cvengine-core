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
  description = "Name of the existing DNS zone."
  type        = string
  default     = "skyhaven.ltd"
}

variable "dns_zone_resource_group" {
  description = "Resource group containing the DNS zone."
  type        = string
}

variable "cosmosdb_free_tier" {
  description = "Enable Cosmos DB free tier."
  type        = bool
  default     = true
}
