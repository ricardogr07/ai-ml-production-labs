# MCP Client Setup: FastMCP Portfolio Tools

How to connect Claude Desktop, VSCode Copilot, and OpenAI Codex to the portfolio tools MCP server, running either locally via Docker or deployed on Azure Container Apps.

## Prerequisites

- The server is running and you have your `MCP_AUTH_TOKEN` value.
- For cloud: the ACA FQDN from `terraform output fqdn`.

## Endpoints

| Target | URL |
|---|---|
| Local Docker | `http://localhost:8080/mcp` |
| ACA cloud | `https://<fqdn>/mcp` |

## Claude Desktop

Config file location:

- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "portfolio-tools-local": {
      "type": "streamable-http",
      "url": "http://localhost:8080/mcp",
      "headers": {
        "Authorization": "Bearer changeme"
      }
    },
    "portfolio-tools-cloud": {
      "type": "streamable-http",
      "url": "https://<fqdn>/mcp",
      "headers": {
        "Authorization": "Bearer <your-token>"
      }
    }
  }
}
```

Restart Claude Desktop after editing. The tools `score_project`, `suggest_readme_sections`, and `generate_portfolio_summary` will appear in the tool picker.

## VSCode Copilot

Create `.vscode/mcp.json` in the workspace root:

```json
{
  "servers": {
    "portfolio-tools-local": {
      "type": "http",
      "url": "http://localhost:8080/mcp",
      "headers": {
        "Authorization": "Bearer changeme"
      }
    },
    "portfolio-tools-cloud": {
      "type": "http",
      "url": "https://<fqdn>/mcp",
      "headers": {
        "Authorization": "Bearer <your-token>"
      }
    }
  }
}
```

Reload the window. The tools will be available via Copilot Chat when agent mode is active.

## OpenAI Codex

Add to `~/.codex/config.json`:

```json
{
  "mcpServers": {
    "portfolio-tools": {
      "type": "http",
      "url": "https://<fqdn>/mcp",
      "headers": {
        "Authorization": "Bearer <your-token>"
      }
    }
  }
}
```

## Local Docker quickstart

```bash
# Start with auth enabled
docker compose up

# Or directly:
docker run --rm -p 8080:8080 \
  -e MCP_AUTH_TOKEN=changeme \
  -e LOG_LEVEL=INFO \
  -e ENVIRONMENT=local \
  lab-03:local
```

## Rate limiting

The server enforces 60 requests per IP per 60-second window. Exceeding this returns HTTP 429. The limit is configurable via `RATE_LIMIT_CALLS` and `RATE_LIMIT_PERIOD` environment variables.

## Verifying the connection

Run the smoke test against the server to confirm all three tools respond correctly:

```bash
# Against local Docker
MCP_AUTH_TOKEN=changeme uv run --package fastmcp-portfolio-tools \
  python labs/03-fastmcp-portfolio-tools/scripts/smoke_test.py http://localhost:8080

# Against ACA
MCP_AUTH_TOKEN=<your-token> uv run --package fastmcp-portfolio-tools \
  python labs/03-fastmcp-portfolio-tools/scripts/smoke_test.py https://<fqdn>
```
