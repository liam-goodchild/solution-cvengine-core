provider "azurerm" {
  features {}
}

provider "azurerm" {
  alias           = "dns"
  subscription_id = var.platform_subscription_id
  features {}
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}
