resource "azurerm_resource_group" "main" {
  name     = "${local.prefix}-rg-01"
  location = var.location
}

resource "azurerm_static_web_app" "main" {
  name                = "${local.prefix}-stapp-01"
  resource_group_name = azurerm_resource_group.main.name
  location            = "westeurope"
  sku_tier            = "Free"
  sku_size            = "Free"

  app_settings = {
    "CosmosDBConnectionString" = azurerm_cosmosdb_account.main.primary_sql_connection_string
  }
}

resource "azurerm_static_web_app_custom_domain" "main" {
  static_web_app_id = azurerm_static_web_app.main.id
  domain_name       = local.fqdn
  validation_type   = "cname-delegation"

  depends_on = [azurerm_dns_cname_record.swa]
}
