locals {
  resource_suffix      = "${var.workload}-${var.environment}-${var.location_short}-${var.instance}"
  resource_suffix_flat = "${var.workload}${var.environment}${var.location_short}${var.instance}"
  cloudflare_zone_id   = one(data.cloudflare_zones.main.result).id

  tags = {
    managed-by = "terraform"
  }
}
