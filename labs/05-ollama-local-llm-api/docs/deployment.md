# Lab 05: Deployment Guide

## Prerequisites

- Azure CLI authenticated (`az login`)
- Terraform >= 1.7 installed
- A running Azure Container Apps Environment (shared with other labs: `cae-ai-ml-production-labs-dev`)
- A GitHub PAT with `read:packages` scope for GHCR image pull
- A reachable Ollama instance and its URL (see note below)

## Ollama availability in Azure

The Container App runs only the FastAPI wrapper. Ollama itself is not deployed to Azure. The
`OLLAMA_BASE_URL` variable must point to an Ollama instance reachable from the Container App:

- **Local testing**: the `GET /health` endpoint works without Ollama. `/summarize` requires Ollama.
- **Tunneling**: expose your local Ollama via `ngrok http 11434` and supply the tunnel URL.
- **Azure VM**: run Ollama on a VM in the same VNet and supply its private IP.

## Deploy

```bash
cd labs/05-ollama-local-llm-api/infra

cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with real values

terraform init
terraform plan
terraform apply
```

Terraform outputs the Container App FQDN on success:

```
Outputs:
fqdn = "ca-ollama-local-llm-api-dev.<region>.azurecontainerapps.io"
```

## Verify

```bash
export BASE_URL="https://$(terraform output -raw fqdn)"

# Health check (no Ollama required)
curl "$BASE_URL/health"

# Summarize (requires Ollama reachable at OLLAMA_BASE_URL)
curl -X POST "$BASE_URL/summarize" \
  -H "Content-Type: application/json" \
  -d '{"text": "Azure Container Apps is a serverless container hosting service.", "model": "tinyllama"}'
```

## Teardown

```bash
terraform destroy
```

## Environment variables

| Variable | Set via | Default |
|----------|---------|---------|
| `OLLAMA_BASE_URL` | `var.ollama_base_url` | (required) |
| `OLLAMA_DEFAULT_MODEL` | `var.ollama_default_model` | `phi3.5` |
| `ENVIRONMENT` | hardcoded in template | `production` |
| `LOG_LEVEL` | hardcoded in template | `INFO` |
