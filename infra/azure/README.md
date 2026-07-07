# Shared Azure Infrastructure

This directory contains reusable Terraform modules and the one-time bootstrap for all labs in this monorepo. The setup in this file is done once: all lab-specific deployment guides reference this document rather than repeating these steps.

---

## Directory structure

| Module | Purpose |
|---|---|
| `bootstrap/` | Shared resource group, Log Analytics, Application Insights, Container App Environment |
| `container-apps/` | Reusable template for Azure Container Apps deployments (used by lab 01) |
| `functions/` | Reusable template for Azure Functions deployments (used by lab 02) |
| `cosmosdb/` | Reusable template for Cosmos DB |
| `monitoring/` | Standalone Log Analytics + Application Insights |

---

## One-time bootstrap

The bootstrap module creates shared infrastructure used by all labs. Run it once per Azure subscription.

```bash
cd infra/azure/bootstrap
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform apply
```

Save the sensitive output for use in lab-specific deployments:

```bash
terraform output -raw app_insights_connection_string
```

---

## One-time GitHub OIDC setup

This project uses a User-Assigned Managed Identity for OIDC authentication from GitHub Actions: no stored credentials, short-lived tokens only. Run these steps once for the entire repository.

### 1. Create the managed identity

```bash
az identity create \
  --name mi-gh-ai-ml-production-labs \
  --resource-group rg-ai-ml-production-labs-dev
```

From the output record:

| Field | Used as |
|---|---|
| `clientId` | `AZURE_CLIENT_ID` secret |
| `tenantId` | `AZURE_TENANT_ID` secret |
| `principalId` | Role assignment below |

### 2. Grant Contributor and User Access Administrator on the shared resource group

Contributor covers most labs. Lab 03 additionally creates a role assignment during apply, which requires User Access Administrator:

```bash
az role assignment create --assignee-object-id <principalId> --assignee-principal-type ServicePrincipal \
  --role Contributor --scope /subscriptions/<subscription-id>/resourceGroups/rg-ai-ml-production-labs-dev
az role assignment create --assignee-object-id <principalId> --assignee-principal-type ServicePrincipal \
  --role "User Access Administrator" --scope /subscriptions/<subscription-id>/resourceGroups/rg-ai-ml-production-labs-dev
```

Role assignments take a few minutes to propagate; a workflow dispatched immediately after granting may fail with "No subscriptions found".

If `az role assignment create` fails with a `MissingSubscription` error (common behind corporate proxies), use `az rest` directly:

```bash
az rest --method PUT \
  --url "https://management.azure.com/subscriptions/<subscription-id>/resourceGroups/rg-ai-ml-production-labs-dev/providers/Microsoft.Authorization/roleAssignments/<new-uuid>?api-version=2022-04-01" \
  --body '{
    "properties": {
      "roleDefinitionId": "/subscriptions/<subscription-id>/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c",
      "principalId": "<principalId>",
      "principalType": "ServicePrincipal"
    }
  }'
```

### 3. Add the OIDC federated credential

```bash
az identity federated-credential create \
  --name github-actions-master \
  --identity-name mi-gh-ai-ml-production-labs \
  --resource-group rg-ai-ml-production-labs-dev \
  --issuer https://token.actions.githubusercontent.com \
  --subject repo:<github-username>/ai-ml-production-labs:ref:refs/heads/master \
  --audiences api://AzureADTokenExchange
```

### 4. Set GitHub repository secrets

Go to **Settings > Secrets and variables > Actions** and add:

| Secret | Value |
|---|---|
| `AZURE_CLIENT_ID` | Managed identity `clientId` |
| `AZURE_TENANT_ID` | Azure tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |
| `AZURE_RESOURCE_GROUP` | `rg-ai-ml-production-labs-dev` |
| `GHCR_PAT` | GitHub classic PAT with `write:packages` scope (labs 01, 05, and 08) |
| `MCP_AUTH_TOKEN` | Bearer token for lab 03's MCP server smoke test |
| `ANTHROPIC_API_KEY` | Anthropic API key (lab 08 e2e job and one-shot agent container) |

Note: GHCR requires a classic PAT. Fine-grained PATs do not support the `write:packages` scope.
