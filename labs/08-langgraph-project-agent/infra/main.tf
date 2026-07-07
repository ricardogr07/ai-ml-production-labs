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

variable "container_image" {
  type        = string
  description = "Fully qualified agent image reference on GHCR (set by CI)."
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

variable "anthropic_api_key" {
  type        = string
  sensitive   = true
  description = "Anthropic API key injected into the agent container."
}

variable "anthropic_model" {
  type    = string
  default = "claude-opus-4-8"
}

variable "ollama_dns_label" {
  type        = string
  default     = "ollama-lab08-dev"
  description = "DNS name label for the Ollama container group (region unique)."
}

# One-shot agent run: executes the graph once against the Anthropic API,
# writes the scorecard to stdout, and terminates. CI asserts on the logs.
resource "azurerm_container_group" "agent" {
  name                = "aci-langgraph-agent-dev"
  location            = var.location
  resource_group_name = var.resource_group_name
  os_type             = "Linux"
  restart_policy      = "Never"
  ip_address_type     = "None"

  image_registry_credential {
    server   = "ghcr.io"
    username = var.ghcr_username
    password = var.ghcr_pat
  }

  container {
    name   = "agent"
    image  = var.container_image
    cpu    = 1
    memory = 2

    environment_variables = {
      LLM_PROVIDER    = "anthropic"
      ANTHROPIC_MODEL = var.anthropic_model
    }

    secure_environment_variables = {
      ANTHROPIC_API_KEY = var.anthropic_api_key
    }
  }

  tags = {
    lab         = "08"
    environment = "dev"
    project     = "ai-ml-production-labs"
  }
}

# Ollama server for the ollama tier: CI pulls a model through its API and
# runs the lab integration tests against the public endpoint, then destroys.
resource "azurerm_container_group" "ollama" {
  name                = "aci-ollama-lab08-dev"
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
    lab         = "08"
    environment = "dev"
    project     = "ai-ml-production-labs"
  }
}

output "fqdn" {
  description = "Public FQDN of the Ollama container group."
  value       = azurerm_container_group.ollama.fqdn
}

output "agent_container_group" {
  description = "Name of the one-shot agent container group (for log retrieval)."
  value       = azurerm_container_group.agent.name
}
