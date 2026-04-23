resource "azurerm_dns_a_record" "swa" {
  name                = "@"
  zone_name           = data.azurerm_dns_zone.main.name
  resource_group_name = var.dns_zone_resource_group
  ttl                 = 3600
  target_resource_id  = azurerm_static_web_app.main.id
  tags                = local.tags
}

resource "azurerm_dns_txt_record" "swa" {
  name                = "@"
  zone_name           = data.azurerm_dns_zone.main.name
  resource_group_name = var.dns_zone_resource_group
  ttl                 = 3600
  tags                = local.tags

  record {
    value = azurerm_static_web_app_custom_domain.main.validation_token
  }
}
