data "cloudflare_zone" "main" {
  name = var.dns_zone_name
}
