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

variable "acr_name" {
  type        = string
  default     = "acraimlprodlabsdev"
  description = "Azure Container Registry name (must be globally unique, alphanumeric only)."
}

variable "container_app_name" {
  type    = string
  default = "ca-fastmcp-portfolio-tools-dev"
}

variable "environment_name" {
  type    = string
  default = "cae-ai-ml-production-labs-dev"
}

variable "container_image" {
  type        = string
  default     = ""
  description = "Full image reference, e.g. acraimlprodlabsdev.azurecr.io/fastmcp-portfolio-tools:<sha>"
}

variable "mcp_auth_token" {
  type        = string
  sensitive   = true
  description = "Pre-shared Bearer token required by the MCP server."
}

locals {
  tags = {
    lab         = "03"
    environment = "dev"
    project     = "ai-ml-production-labs"
  }
}

resource "azurerm_container_registry" "this" {
  name                = var.acr_name
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "Basic"
  admin_enabled       = false
  tags                = local.tags
}

data "azurerm_container_app_environment" "this" {
  name                = var.environment_name
  resource_group_name = var.resource_group_name
}

resource "azurerm_container_app" "this" {
  name                         = var.container_app_name
  container_app_environment_id = data.azurerm_container_app_environment.this.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  tags                         = local.tags

  identity {
    type = "SystemAssigned"
  }

  registry {
    server   = azurerm_container_registry.this.login_server
    identity = "system"
  }

  secret {
    name  = "mcp-auth-token"
    value = var.mcp_auth_token # pragma: allowlist secret
  }

  ingress {
    external_enabled = true
    target_port      = 8080
    transport        = "auto"
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    container {
      name   = var.container_app_name
      image  = var.container_image
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
      env {
        name  = "LOG_LEVEL"
        value = "INFO"
      }
      env {
        name        = "MCP_AUTH_TOKEN"
        secret_name = "mcp-auth-token"
      }
    }
    min_replicas = 0
    max_replicas = 2
  }
}

resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.this.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_container_app.this.identity[0].principal_id
}

output "fqdn" {
  value = azurerm_container_app.this.ingress[0].fqdn
}

output "acr_login_server" {
  value = azurerm_container_registry.this.login_server
}
