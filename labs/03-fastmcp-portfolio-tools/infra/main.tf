terraform {
  required_version = ">= 1.7"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.110"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.11"
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

# User-assigned identity so AcrPull can be granted before the container app is created,
# avoiding the race condition where SystemAssigned identity's role hasn't propagated
# by the time ACA tries its first image pull.
resource "azurerm_user_assigned_identity" "acr_pull" {
  name                = "mi-fastmcp-portfolio-tools-dev"
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = local.tags
}

resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.this.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.acr_pull.principal_id
}

# Role assignments can take up to a few minutes to propagate in Azure AD.
# Waiting here ensures ACA can pull from ACR on first provisioning.
resource "time_sleep" "wait_for_role" {
  depends_on      = [azurerm_role_assignment.acr_pull]
  create_duration = "90s"
}

data "azurerm_container_app_environment" "this" {
  name                = var.environment_name
  resource_group_name = var.resource_group_name
}

resource "azurerm_container_app" "this" {
  depends_on                   = [time_sleep.wait_for_role]
  name                         = var.container_app_name
  container_app_environment_id = data.azurerm_container_app_environment.this.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  tags                         = local.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.acr_pull.id]
  }

  registry {
    server   = azurerm_container_registry.this.login_server
    identity = azurerm_user_assigned_identity.acr_pull.id
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

output "fqdn" {
  value = azurerm_container_app.this.ingress[0].fqdn
}

output "acr_login_server" {
  value = azurerm_container_registry.this.login_server
}
