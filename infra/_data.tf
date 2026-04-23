data "cloudflare_zones" "main" {
  account = {
    id = var.cloudflare_account_id
  }

  name   = var.dns_zone_name
  status = "active"
}
