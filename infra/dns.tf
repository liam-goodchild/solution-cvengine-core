resource "cloudflare_dns_record" "swa_cname" {
  zone_id = local.cloudflare_zone_id
  type    = "CNAME"
  name    = var.dns_zone_name
  content = azurerm_static_web_app.main.default_host_name
  proxied = true
  ttl     = 1
}

resource "cloudflare_dns_record" "swa_txt" {
  zone_id = local.cloudflare_zone_id
  type    = "TXT"
  name    = var.dns_zone_name
  content = azurerm_static_web_app_custom_domain.main.validation_token
  ttl     = 3600
}
