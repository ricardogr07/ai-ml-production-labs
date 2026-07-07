terraform {
  required_version = ">= 1.7"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.3"
    }
    azapi = {
      source  = "azure/azapi"
      version = "~> 2.0"
    }
  }
}

provider "azurerm" {
  features {}
  skip_provider_registration = true
}

provider "azapi" {}

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
  default     = "cosmos-vector-memory-dev"
  description = "CosmosDB account name (must be globally unique)."
}

variable "database_name" {
  type    = string
  default = "vector-memory"
}

variable "container_name" {
  type    = string
  default = "documents"
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

  capabilities {
    name = "EnableNoSQLVectorSearch"
  }

  tags = {
    lab         = "06"
    environment = "dev"
    project     = "ai-ml-production-labs"
  }
}

resource "azurerm_cosmosdb_sql_database" "this" {
  name                = var.database_name
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.this.name
}

# ponytail: azurerm has no schema for CosmosDB vector container policies
# (open upstream request: hashicorp/terraform-provider-azurerm#30520), so the
# container is managed via azapi against the real Microsoft.DocumentDB ARM API
# instead of azurerm_cosmosdb_sql_container.
resource "azapi_resource" "container" {
  type      = "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-11-15"
  name      = var.container_name
  parent_id = azurerm_cosmosdb_sql_database.this.id

  body = {
    properties = {
      resource = {
        id = var.container_name
        partitionKey = {
          paths = ["/id"]
          kind  = "Hash"
        }
        indexingPolicy = {
          indexingMode = "consistent"
          automatic    = true
          vectorIndexes = [
            {
              path = "/embedding"
              type = "diskANN"
            }
          ]
        }
        vectorEmbeddingPolicy = {
          vectorEmbeddings = [
            {
              path             = "/embedding"
              dataType         = "float32"
              dimensions       = 384
              distanceFunction = "cosine"
            }
          ]
        }
      }
    }
  }
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
