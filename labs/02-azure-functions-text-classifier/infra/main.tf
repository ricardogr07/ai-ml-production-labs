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
  type        = string
  default     = "rg-ai-ml-production-labs-dev"
  description = "Shared resource group created by the bootstrap module."
}

variable "location" {
  type        = string
  default     = "eastus"
  description = "Azure region for all resources."
}

variable "function_app_name" {
  type        = string
  default     = "func-text-classifier-dev"
  description = "Name of the Linux Function App. Must be globally unique."
}

variable "storage_account_name" {
  type        = string
  default     = "stfunctxtcls02dev"
  description = "Storage account name (3-24 chars, lowercase alphanumeric, globally unique)."
}

variable "app_insights_connection_string" {
  type        = string
  sensitive   = true
  default     = ""
  description = "Application Insights connection string from bootstrap output (terraform output -raw app_insights_connection_string)."
}

variable "existing_service_plan_name" {
  type        = string
  default     = ""
  description = "Name of an existing Consumption App Service Plan to reuse. When set, no new plan is created. Use this when the subscription's 'Total VMs' quota in Microsoft.Web is 0."
}

locals {
  tags = {
    lab         = "02"
    environment = "dev"
    project     = "ai-ml-production-labs"
  }
  service_plan_id = var.existing_service_plan_name != "" ? data.azurerm_service_plan.existing[0].id : azurerm_service_plan.new[0].id
}

data "azurerm_service_plan" "existing" {
  count               = var.existing_service_plan_name != "" ? 1 : 0
  name                = var.existing_service_plan_name
  resource_group_name = var.resource_group_name
}

resource "azurerm_service_plan" "new" {
  count               = var.existing_service_plan_name == "" ? 1 : 0
  name                = "${var.function_app_name}-plan"
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = "Linux"
  sku_name            = "Y1"
  tags                = local.tags
}

resource "azurerm_storage_account" "this" {
  name                     = var.storage_account_name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  tags                     = local.tags
}

resource "azurerm_linux_function_app" "this" {
  name                       = var.function_app_name
  resource_group_name        = var.resource_group_name
  location                   = var.location
  service_plan_id            = local.service_plan_id
  storage_account_name       = azurerm_storage_account.this.name
  storage_account_access_key = azurerm_storage_account.this.primary_access_key
  tags                       = local.tags

  site_config {
    application_stack {
      python_version = "3.12"
    }
  }

  app_settings = {
    FUNCTIONS_WORKER_RUNTIME              = "python"
    APPLICATIONINSIGHTS_CONNECTION_STRING = var.app_insights_connection_string
    ENVIRONMENT                           = "production"
    LOG_LEVEL                             = "INFO"
  }
}

output "function_app_hostname" {
  description = "Default hostname of the deployed Function App."
  value       = azurerm_linux_function_app.this.default_hostname
}

output "function_app_name" {
  description = "Function App name, used with 'func azure functionapp publish'."
  value       = azurerm_linux_function_app.this.name
}
