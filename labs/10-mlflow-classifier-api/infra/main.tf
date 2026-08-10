terraform {
  required_version = ">= 1.7"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.3"
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

variable "container_app_name" {
  type    = string
  default = "ca-mlflow-classifier-api-dev"
}

variable "container_image" {
  type        = string
  description = "Fully qualified app image reference on GHCR (set by CI)."
}

variable "environment_name" {
  type    = string
  default = "cae-ai-ml-production-labs-dev"
}

variable "ghcr_username" {
  type        = string
  description = "GitHub username for GHCR image pull."
}

variable "ghcr_pat" {
  type        = string
  sensitive   = true
  description = "GitHub PAT with read:packages scope for GHCR image pull."
}

# The environment is shared across labs and created outside this config, so it
# is read, never managed here. A destroy of this lab must not take the
# environment (and every other lab's app) with it.
data "azurerm_container_app_environment" "this" {
  name                = var.environment_name
  resource_group_name = var.resource_group_name
}

resource "azurerm_container_app" "this" {
  name                         = var.container_app_name
  container_app_environment_id = data.azurerm_container_app_environment.this.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  tags = {
    lab         = "10"
    environment = "dev"
    project     = "ai-ml-production-labs"
  }

  registry {
    server               = "ghcr.io"
    username             = var.ghcr_username
    password_secret_name = "ghcr-pat" # ggignore
  }

  secret {
    name  = "ghcr-pat"
    value = var.ghcr_pat # pragma: allowlist secret # ggignore
  }

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
      # No MLFLOW_TRACKING_URI override: the image bakes a trained model at the
      # default relative store, and Container Apps has no persistent volume to
      # point elsewhere at. Overriding it here would resolve to an empty path
      # in a fresh replica and serve 503.
    }
    # Scale to zero: the lab costs nothing between demos, at the price of a
    # cold start on the first request after idle. The model loads lazily and
    # per process, so a cold replica pays one artifact load too. Wrong trade
    # for a latency-sensitive service, right for a portfolio lab.
    min_replicas = 0
    max_replicas = 2
  }
}

output "fqdn" {
  value = azurerm_container_app.this.ingress[0].fqdn
}
