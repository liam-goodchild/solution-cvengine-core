resource "azurerm_dns_a_record" "swa" {
  provider            = azurerm.dns
  name                = "@"
  zone_name           = data.azurerm_dns_zone.main.name
  resource_group_name = data.azurerm_dns_zone.main.resource_group_name
  ttl                 = 3600
  target_resource_id  = azurerm_static_web_app.main.id
  tags                = local.tags
}

resource "azurerm_dns_txt_record" "swa" {
  provider            = azurerm.dns
  name                = "@"
  zone_name           = data.azurerm_dns_zone.main.name
  resource_group_name = data.azurerm_dns_zone.main.resource_group_name
  ttl                 = 3600
  tags                = local.tags

  record {
    value = azurerm_static_web_app_custom_domain.main.validation_token
  }
}
