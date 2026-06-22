# Lab 01: Azure Deployment Guide

This document covers the one-time setup required to deploy lab 01 to Azure Container Apps using GHCR as the container registry and GitHub Actions for CI/CD.

---

## Prerequisites

- Azure CLI installed and authenticated (`az login`)
- Terraform >= 1.7 installed
- A GitHub PAT with `write:packages` scope (for GHCR push from GitHub Actions)
- An Azure subscription (free tier or pay-as-you-go)

---

## Infrastructure overview

All labs share a single resource group (`rg-ai-ml-production-labs-dev`). The bootstrap module creates the shared Container App Environment and Log Analytics workspace. Lab 01's Terraform module provisions only the Container App, reading the environment via a data source.

Resources are tagged so you can target a specific lab:

```bash
az resource list \
  --tag lab=01 \
  --resource-group rg-ai-ml-production-labs-dev \
  --output table
```

The container image is stored in GHCR (`ghcr.io/<username>/fastapi-azure-ml-service`), which is free for public repos and included in GitHub Free for private repos up to 500 MB.

---

## Step 1: Select your subscription

```bash
az login
az account list --output table
az account set --subscription "<your-subscription-id>"
```

---

## Step 2: Apply shared bootstrap infrastructure

The bootstrap module creates the resource group, Log Analytics workspace, Application Insights, and Container App Environment. Run this once for the entire monorepo.

```bash
cd infra/azure/bootstrap
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform apply
```

---

## Step 3: Set up GitHub OIDC authentication

This project uses a User-Assigned Managed Identity for OIDC: no stored credentials, short-lived tokens only.

```bash
# Create the managed identity in the shared resource group
az identity create \
  --name mi-ai-ml-production-labs \
  --resource-group rg-ai-ml-production-labs-dev

# From the output, note: clientId (AZURE_CLIENT_ID), tenantId (AZURE_TENANT_ID),
# principalId (needed for role assignment below)

# Grant Contributor on the resource group
# Note: if az role assignment create fails with MissingSubscription, use az rest instead:
az rest --method PUT \
  --url "https://management.azure.com/subscriptions/<subscription-id>/resourceGroups/rg-ai-ml-production-labs-dev/providers/Microsoft.Authorization/roleAssignments/<new-uuid>?api-version=2022-04-01" \
  --body '{
    "properties": {
      "roleDefinitionId": "/subscriptions/<subscription-id>/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c",
      "principalId": "<principalId>",
      "principalType": "ServicePrincipal"
    }
  }'

# Add the OIDC federated credential (replace <github-username> with your GitHub username/org)
az identity federated-credential create \
  --name github-actions-master \
  --identity-name mi-ai-ml-production-labs \
  --resource-group rg-ai-ml-production-labs-dev \
  --issuer https://token.actions.githubusercontent.com \
  --subject repo:<github-username>/ai-ml-production-labs:ref:refs/heads/master \
  --audiences api://AzureADTokenExchange
```

---

## Step 4: Set GitHub repository secrets

Go to **Settings > Secrets and variables > Actions** in the GitHub repo and add:

| Secret | Value |
|---|---|
| `AZURE_CLIENT_ID` | Managed identity `clientId` |
| `AZURE_TENANT_ID` | Azure tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |
| `AZURE_RESOURCE_GROUP` | `rg-ai-ml-production-labs-dev` |
| `GHCR_PAT` | GitHub classic PAT with `write:packages` scope |

Note: GHCR requires a **classic PAT**, not a fine-grained PAT. Fine-grained PATs do not support the `write:packages` scope.

---

## Step 5: Apply lab 01 Container App infrastructure (local)

```bash
cd labs/01-fastapi-azure-ml-service/infra
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and fill in real values for the sensitive fields:

```hcl
ghcr_username   = "<your-github-username>"
ghcr_pat        = "<your-github-classic-pat-with-read-packages>"
container_image = "ghcr.io/<your-github-username>/fastapi-azure-ml-service:<sha>"
```

Then apply:

```bash
terraform init
terraform apply
```

The `fqdn` output is the public URL for the Container App. Copy it.

---

## Step 6: Deploy via the integration pipeline (recommended)

Go to **Actions > Integration Test** and click **Run workflow**:

| Input | Value |
|---|---|
| `lab` | `01-fastapi-azure-ml-service` |
| `image_name` | `fastapi-azure-ml-service` |
| `hold_for_validation` | `true` to pause before teardown |

The pipeline: builds and pushes the image to GHCR, runs `terraform apply`, runs the smoke test, optionally holds for manual Postman validation, then runs `terraform destroy`. Total run time is roughly 5-10 minutes.

---

## Step 7: Verify the deployment

```bash
# Replace <fqdn> with the output from terraform apply or the pipeline logs
curl https://<fqdn>/health
# Expected: {"status":"ok","service":"fastapi-azure-ml-service","version":"0.1.0","timestamp_utc":"..."}

# Run the smoke test directly against the live endpoint
BASE_URL=https://<fqdn> python labs/01-fastapi-azure-ml-service/scripts/smoke_test.py

# Run the e2e test suite
LAB01_BASE_URL=https://<fqdn> uv run pytest labs/01-fastapi-azure-ml-service/tests/e2e -v
```

---

## Step 8: Test with Postman

1. Open `postman/lab-01.postman_collection.json` in Postman.
2. Go to the **Variables** tab and update `base_url_azure` to `https://<fqdn>`.
3. Run all requests and confirm expected status codes.

---

## Rate limiting

`POST /predict` is limited to 10 requests per minute per IP address. Exceeding the limit returns:

```json
HTTP 429 Too Many Requests
{"error": "Rate limit exceeded: 10 per 1 minute"}
```

`GET /health` has no rate limit.

---

## Cost and resource management

| Resource | SKU | Monthly cost |
|---|---|---|
| Container App Environment | Consumption | Free (shared) |
| Container App | Consumption, min 0 replicas | ~$0 when idle |
| Log Analytics | PerGB2018, 30-day retention | Free up to 5 GB/month |
| Application Insights | Workspace-based | Free up to 5 GB/month |
| GHCR | Free for public repos | $0 |

Scale-to-zero (`min_replicas = 0`) means the Container App incurs no compute cost between requests. Cold starts take approximately 2-5 seconds.

---

## Teardown

To remove only lab 01 resources:

```bash
cd labs/01-fastapi-azure-ml-service/infra

# On networks where the listSecrets endpoint is blocked (e.g., corporate proxies),
# add -refresh=false to skip state refresh:
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
