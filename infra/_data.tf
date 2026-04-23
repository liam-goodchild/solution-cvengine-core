data "azurerm_dns_zone" "main" {
  provider            = azurerm.dns
  name                = var.dns_zone_name
  resource_group_name = var.dns_zone_resource_group
}
