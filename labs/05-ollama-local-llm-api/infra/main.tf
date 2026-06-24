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

variable "container_app_name" {
  type    = string
  default = "ca-ollama-local-llm-api-dev"
}

variable "container_image" {
  type = string
}

variable "environment_name" {
  type    = string
  default = "cae-ai-ml-production-labs-dev"
}

variable "ghcr_username" {
  type        = string
  description = "GitHub username for GHCR pull authentication."
}

variable "ghcr_pat" {
  type        = string
  sensitive   = true
  description = "GitHub PAT with read:packages scope for GHCR pull."
}

variable "ollama_base_url" {
  type        = string
  description = "URL of a running Ollama instance reachable from the Container App."
}

variable "ollama_default_model" {
  type    = string
  default = "phi3.5"
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

  tags = {
    lab         = "05"
    environment = "dev"
    project     = "ai-ml-production-labs"
  }

  registry {
    server               = "ghcr.io"
    username             = var.ghcr_username
    password_secret_name = "ghcr-pat"
  }

  secret {
    name  = "ghcr-pat"
    value = var.ghcr_pat # pragma: allowlist secret
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
      env {
        name  = "OLLAMA_BASE_URL"
        value = var.ollama_base_url
      }
      env {
        name  = "OLLAMA_DEFAULT_MODEL"
        value = var.ollama_default_model
      }
    }
    min_replicas = 0
    max_replicas = 2
  }
}

output "fqdn" {
  value = azurerm_container_app.this.ingress[0].fqdn
}
