locals {
  location_short = "uks"
  prefix         = "${var.project}-${var.solution}-${var.environment}-${local.location_short}-${var.service}"

  fqdn = var.environment == "prd" ? "${var.subdomain}.${var.dns_zone_name}" : "${var.subdomain}.dev.${var.dns_zone_name}"
}
