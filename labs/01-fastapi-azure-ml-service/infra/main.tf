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
}

variable "resource_group_name" {
  type = string
}

variable "location" {
  type    = string
  default = "eastus"
}

variable "container_app_name" {
  type    = string
  default = "ca-fastapi-azure-ml-service-dev"
}

variable "container_image" {
  type = string
}

variable "environment_name" {
  type    = string
  default = "cae-ai-ml-production-labs-dev"
}

variable "log_analytics_workspace_name" {
  type    = string
  default = "log-ai-ml-production-labs-dev"
}

data "azurerm_log_analytics_workspace" "this" {
  name                = var.log_analytics_workspace_name
  resource_group_name = var.resource_group_name
}

resource "azurerm_container_app_environment" "this" {
  name                       = var.environment_name
  location                   = var.location
  resource_group_name        = var.resource_group_name
  log_analytics_workspace_id = data.azurerm_log_analytics_workspace.this.id
}

resource "azurerm_container_app" "this" {
  name                         = var.container_app_name
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  ingress {
    external_enabled = true
    target_port      = 8000
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
    }
    min_replicas = 0
    max_replicas = 2
  }
}

output "fqdn" {
  value = azurerm_container_app.this.ingress[0].fqdn
}
