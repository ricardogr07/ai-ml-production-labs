# Lab 02: Azure Deployment Guide

This document covers deploying lab 02 to Azure Functions (Consumption plan, Python 3.12) using Terraform and Azure Functions Core Tools.

---

## Prerequisites

- Azure CLI installed and authenticated (`az login`)
- Terraform >= 1.7 installed
- Azure Functions Core Tools v4 (`npm install -g azure-functions-core-tools@4`)
- An Azure subscription with at least 1 "Y1 VMs" quota in Microsoft.Web (East US). Check via Azure Portal: Subscription > Settings > Usage + quotas, filter "Microsoft.Web". Request an increase if the limit is 0.
- GitHub OIDC and repository secrets configured: see [infra/azure/README.md](../../../../infra/azure/README.md)

---

## Infrastructure overview

All labs share a single resource group (`rg-ai-ml-production-labs-dev`). The bootstrap module creates the shared Log Analytics workspace and Application Insights instance. Lab 02's Terraform module adds three resources, all tagged `lab=02`:

| Resource | Name | SKU |
|---|---|---|
| Storage Account | `stfunctxtcls02dev` | Standard LRS |
| Service Plan | `func-text-classifier-dev-plan` | Y1 (Consumption, Linux) |
| Linux Function App | `func-text-classifier-dev` | Python 3.12, Functions v4 |

The function code is deployed as a ZIP package via Azure Functions Core Tools or the CI pipeline. The Docker image from stage 2 is for local development only.

To list lab 02 resources at any time:

```bash
az resource list \
  --tag lab=02 \
  --resource-group rg-ai-ml-production-labs-dev \
  --output table
```

---

## Step 1: Select your subscription

```bash
az login
az account list --output table
az account set --subscription "<your-subscription-id>"
```

---

## Step 2: Apply shared bootstrap infrastructure

The bootstrap module creates the resource group, Log Analytics workspace, and Application Insights. Run this once for the entire monorepo (skip if already done for lab 01).

```bash
cd infra/azure/bootstrap
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform apply
```

Note the connection string for step 3:

```bash
terraform output -raw app_insights_connection_string
```

---

## Step 3: Apply lab 02 infrastructure

```bash
cd labs/02-azure-functions-text-classifier/infra
cp terraform.tfvars.example terraform.tfvars
```

Fill in `app_insights_connection_string` from step 2. Then apply:

```bash
terraform init
terraform plan   # verify 3 resources to add
terraform apply
```

Record the outputs:

```bash
terraform output function_app_hostname  # live endpoint base URL
terraform output function_app_name      # used in step 4
```

---

## Step 4: Deploy the function code

From the lab root, publish the function code to the provisioned app:

```bash
cd labs/02-azure-functions-text-classifier
func azure functionapp publish <function_app_name> --python
```

Replace `<function_app_name>` with the value from `terraform output function_app_name` (default: `func-text-classifier-dev`).

---

## Step 5: Verify the deployment

```bash
# Replace <hostname> with the value from terraform output function_app_hostname

curl -s -X POST "https://<hostname>/api/classify" \
  -H "Content-Type: application/json" \
  -d '{"text":"Service crashed in production."}' | python -m json.tool
# Expected: {"label":"incident","confidence":0.85,"model_version":"rules-v0.1.0"}

curl -s -X POST "https://<hostname>/api/classify" \
  -H "Content-Type: application/json" \
  -d '{"text":"New release deployed to staging."}' | python -m json.tool
# Expected: {"label":"deployment","confidence":0.75,"model_version":"rules-v0.1.0"}

curl -s -X POST "https://<hostname>/api/classify" \
  -H "Content-Type: application/json" \
  -d '{"text":""}' | python -m json.tool
# Expected: HTTP 422 with Pydantic validation detail
```

Or run the smoke test script directly against the live endpoint:

```bash
BASE_URL=https://<hostname> uv run python labs/02-azure-functions-text-classifier/scripts/smoke_test.py
```

---

## Cost and resource management

| Resource | SKU | Monthly cost |
|---|---|---|
| Function App (Consumption) | Y1 | First 1M executions free, then ~$0.20/million |
| Storage Account | Standard LRS | ~$0.02/GB stored |
| Log Analytics | PerGB2018, 30-day retention | Free up to 5 GB/month |
| Application Insights | Workspace-based | Free up to 5 GB/month |

The Consumption plan scales to zero automatically: no executions means no compute cost. Cold starts take approximately 500ms to 2s for a Python function.

---

## Teardown

To remove only lab 02 resources:

```bash
cd labs/02-azure-functions-text-classifier/infra

# On networks where the listSecrets endpoint is blocked (e.g., corporate proxies):
terraform destroy -refresh=false -auto-approve

# On unrestricted networks (including GitHub Actions runners):
terraform destroy -auto-approve
```

To remove all shared infrastructure (affects all labs):

```bash
cd infra/azure/bootstrap
terraform destroy
# or delete the resource group directly:
az group delete --name rg-ai-ml-production-labs-dev --yes
```
