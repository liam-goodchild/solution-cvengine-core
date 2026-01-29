resource "azurerm_dns_cname_record" "swa" {
  name                = var.environment == "prd" ? var.subdomain : "${var.subdomain}.dev"
  zone_name           = data.azurerm_dns_zone.main.name
  resource_group_name = var.dns_zone_resource_group
  ttl                 = 3600
  record              = azurerm_static_web_app.main.default_host_name
}
