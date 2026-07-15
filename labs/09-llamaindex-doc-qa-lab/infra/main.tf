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
  default = "ca-llamaindex-doc-qa-lab-dev"
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

variable "llm_provider" {
  type    = string
  default = "ollama"
}

variable "ollama_model" {
  type    = string
  default = "llama3.2"
}

variable "anthropic_model" {
  type    = string
  default = "claude-opus-4-8"
}

variable "anthropic_api_key" {
  type        = string
  sensitive   = true
  default     = ""
  description = "Anthropic API key injected into the app container (optional tier)."
}

variable "ollama_dns_label" {
  type        = string
  default     = "ollama-lab09-dev"
  description = "DNS name label for the Ollama container group (region unique)."
}

variable "qdrant_dns_label" {
  type        = string
  default     = "qdrant-lab09-dev"
  description = "DNS name label for the Qdrant container group (region unique)."
}

data "azurerm_container_app_environment" "this" {
  name                = var.environment_name
  resource_group_name = var.resource_group_name
}

# Ollama server for the default generation tier: public so the app tier and
# CI can both reach it. Destroyed at the end of every integration-test run.
resource "azurerm_container_group" "ollama" {
  name                = "aci-ollama-lab09-dev"
  location            = var.location
  resource_group_name = var.resource_group_name
  os_type             = "Linux"
  restart_policy      = "Always"
  ip_address_type     = "Public"
  dns_name_label      = var.ollama_dns_label

  container {
    name   = "ollama"
    image  = "ollama/ollama:latest"
    cpu    = 2
    memory = 8

    ports {
      port     = 11434
      protocol = "TCP"
    }
  }

  exposed_port {
    port     = 11434
    protocol = "TCP"
  }

  tags = {
    lab         = "09"
    environment = "dev"
    project     = "ai-ml-production-labs"
  }
}

# Qdrant vector store: public and unauthenticated for the run's duration,
# same tradeoff as the Ollama endpoint above but also writable (seed_data.py
# upserts into it) - see README for the production note on API-key auth.
resource "azurerm_container_group" "qdrant" {
  name                = "aci-qdrant-lab09-dev"
  location            = var.location
  resource_group_name = var.resource_group_name
  os_type             = "Linux"
  restart_policy      = "Always"
  ip_address_type     = "Public"
  dns_name_label      = var.qdrant_dns_label

  container {
    name   = "qdrant"
    image  = "qdrant/qdrant:latest"
    cpu    = 1
    memory = 2

    ports {
      port     = 6333
      protocol = "TCP"
    }
  }

  exposed_port {
    port     = 6333
    protocol = "TCP"
  }

  tags = {
    lab         = "09"
    environment = "dev"
    project     = "ai-ml-production-labs"
  }
}

resource "azurerm_container_app" "this" {
  name                         = var.container_app_name
  container_app_environment_id = data.azurerm_container_app_environment.this.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  tags = {
    lab         = "09"
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

  secret {
    name  = "anthropic-api-key"
    value = var.anthropic_api_key # pragma: allowlist secret # ggignore
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
      cpu    = 1
      memory = "2Gi"

      env {
        name  = "LLM_PROVIDER"
        value = var.llm_provider
      }
      env {
        name  = "OLLAMA_BASE_URL"
        value = "http://${azurerm_container_group.ollama.fqdn}:11434"
      }
      env {
        name  = "OLLAMA_MODEL"
        value = var.ollama_model
      }
      env {
        name  = "QDRANT_URL"
        value = "http://${azurerm_container_group.qdrant.fqdn}:6333"
      }
      env {
        name  = "ANTHROPIC_MODEL"
        value = var.anthropic_model
      }
      env {
        name        = "ANTHROPIC_API_KEY"
        secret_name = "anthropic-api-key"
      }
    }
    min_replicas = 0
    max_replicas = 2
  }
}

output "fqdn" {
  description = "Public FQDN of the app Container App."
  value       = azurerm_container_app.this.ingress[0].fqdn
}

output "ollama_fqdn" {
  description = "Public FQDN of the Ollama container group."
  value       = azurerm_container_group.ollama.fqdn
}

output "qdrant_fqdn" {
  description = "Public FQDN of the Qdrant container group."
  value       = azurerm_container_group.qdrant.fqdn
}
