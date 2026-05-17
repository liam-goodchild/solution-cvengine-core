resource "azurerm_static_web_app" "main" {
  name                = "stapp-${local.resource_suffix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = "westeurope"
  sku_tier            = "Free"
  sku_size            = "Free"
  tags                = local.tags

  app_settings = {
    "CosmosDBConnectionString" = azurerm_cosmosdb_account.main.primary_sql_connection_string
    "CosmosDBDatabaseName"     = azurerm_cosmosdb_sql_database.visitor.name
    "CosmosDBContainerName"    = azurerm_cosmosdb_sql_container.visitor.name
  }

  lifecycle {
    ignore_changes = [
      app_settings["BLOG_NOTIFY_SECRET"],
      app_settings["BREVO_API_KEY"],
      app_settings["BREVO_LIST_ID"],
      app_settings["EMAIL_DAILY_LIMIT"],
      app_settings["EMAIL_FROM"],
      app_settings["EMAIL_FROM_NAME"],
      app_settings["EMAIL_REPLY_TO"],
      app_settings["PUBLIC_SITE_URL"],
      repository_url,
      repository_branch,
    ]
  }
}

resource "azurerm_static_web_app_custom_domain" "main" {
  static_web_app_id = azurerm_static_web_app.main.id
  domain_name       = var.dns_zone_name
  validation_type   = "dns-txt-token"
}
