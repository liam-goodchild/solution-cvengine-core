resource "cloudflare_record" "swa_cname" {
  zone_id = data.cloudflare_zone.main.id
  type    = "CNAME"
  name    = "@"
  content = azurerm_static_web_app.main.default_host_name
  proxied = true
  ttl     = 1
}

resource "cloudflare_record" "swa_txt" {
  zone_id = data.cloudflare_zone.main.id
  type    = "TXT"
  name    = "@"
  content = azurerm_static_web_app_custom_domain.main.validation_token
  ttl     = 3600
}
