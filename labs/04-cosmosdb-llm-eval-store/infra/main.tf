terraform {
  required_version = ">= 1.7"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.110"
    }
  }
}

provider "azurerm" {
  features {}
  skip_provider_registration = true
}

variable "resource_group_name" {
  type    = string
  default = "rg-ai-ml-production-labs-dev"
}

variable "location" {
  type    = string
  default = "eastus"
}

variable "account_name" {
  type        = string
  default     = "cosmos-llm-eval-store-dev"
  description = "CosmosDB account name (must be globally unique)."
}

variable "database_name" {
  type    = string
  default = "llm-eval-store"
}

variable "container_name" {
  type    = string
  default = "evaluations"
}

resource "azurerm_cosmosdb_account" "this" {
  name                = var.account_name
  location            = var.location
  resource_group_name = var.resource_group_name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = var.location
    failover_priority = 0
  }

  capabilities {
    name = "EnableServerless"
  }

  tags = {
    lab         = "04"
    environment = "dev"
    project     = "ai-ml-production-labs"
  }
}

resource "azurerm_cosmosdb_sql_database" "this" {
  name                = var.database_name
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.this.name
}

resource "azurerm_cosmosdb_sql_container" "this" {
  name                = var.container_name
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.this.name
  database_name       = azurerm_cosmosdb_sql_database.this.name
  partition_key_paths = ["/experiment_id"]
}

output "endpoint" {
  description = "CosmosDB account endpoint — set as COSMOS_URL in .env."
  value       = azurerm_cosmosdb_account.this.endpoint
}

output "primary_key" {
  description = "CosmosDB primary key — set as COSMOS_KEY in .env."
  value       = azurerm_cosmosdb_account.this.primary_key
  sensitive   = true
}
