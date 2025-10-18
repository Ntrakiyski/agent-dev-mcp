# Chrome MCP Server - Complete Tools Documentation

This document provides comprehensive documentation for all tools available in the Chrome MCP Server.

## Table of Contents

- [Screenshot Tools](#screenshot-tools)
- [Codegen Agent Tools](#codegen-agent-tools)
- [GitHub API Tools](#github-api-tools)
- [Coolify API Tools](#coolify-api-tools)

---

## Screenshot Tools

### 1. `take_screenshot`

**Description**: Take a screenshot of a web page and upload to ImgBB cloud storage.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | ✅ Yes | - | The URL to capture (e.g., "https://producthunt.com") |
| `full_page` | boolean | ❌ No | `true` | If True, captures entire scrollable page |
| `viewport_width` | integer | ❌ No | `1920` | Browser viewport width in pixels |
| `viewport_height` | integer | ❌ No | `1080` | Browser viewport height in pixels |
| `timeout` | integer | ❌ No | `30000` | Page load timeout in milliseconds |
| `delay` | integer | ❌ No | `0` | Additional delay in ms after page loads |
| `upload_to_cloud` | boolean | ❌ No | `true` | If True, uploads to ImgBB. If False, returns base64 |

**Output Schema**:

```json
{
  "success": true,
  "message": "Screenshot uploaded successfully",
  "public_url": "https://i.ibb.co/xxxxx/image.png"
}
```

Or when `upload_to_cloud=False`:

```json
{
  "success": true,
  "message": "Screenshot captured successfully",
  "screenshot_base64": "data:image/png;base64,..."
}
```

**Examples**:

```python
# Basic screenshot with cloud upload
take_screenshot("https://producthunt.com")

# Screenshot without cloud upload (returns base64)
take_screenshot("https://example.com", upload_to_cloud=False)

# Mobile viewport screenshot
take_screenshot("https://example.com", viewport_width=390, viewport_height=844)

# Screenshot with delay for animations
take_screenshot("https://example.com", delay=2000)
```

---

### 2. `get_page_title`

**Description**: Get the title of a web page.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | ✅ Yes | - | The URL to get the title from |
| `timeout` | integer | ❌ No | `30000` | Page load timeout in milliseconds |

**Output Schema**:

```json
"Product Hunt – The best new products in tech."
```

**Examples**:

```python
get_page_title("https://producthunt.com")
```

---

### 3. `health_check`

**Description**: Check server health and configuration.

**Input Parameters**: None

**Output Schema**:

```json
{
  "status": "healthy",
  "browser_connected": true,
  "imgbb_configured": true,
  "message": "Server is fully operational"
}
```

**Examples**:

```python
health_check()
```

---

## Codegen Agent Tools

### 1. `codegen_create_agent_run`

**Description**: Create a new Codegen agent run with a given prompt.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt` | string | ✅ Yes | - | The instruction for the Codegen agent to execute |
| `org_id` | string | ❌ No | env:`CODEGEN_ORG_ID` | Organization ID |
| `api_token` | string | ❌ No | env:`CODEGEN_API_TOKEN` | API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Agent run created successfully",
  "agent_run_id": "123456",
  "status": "pending",
  "web_url": "https://codegen.com/...",
  "result": null
}
```

**Examples**:

```python
# Create agent run with environment credentials
codegen_create_agent_run("Review PR #123")

# Override credentials
codegen_create_agent_run("Fix the bug in auth.py", org_id="123", api_token="token")
```

---

### 2. `codegen_get_agent_run`

**Description**: Get the status and details of a specific Codegen agent run.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `agent_run_id` | string | ✅ Yes | - | ID of the agent run to retrieve |
| `org_id` | string | ❌ No | env:`CODEGEN_ORG_ID` | Organization ID |
| `api_token` | string | ❌ No | env:`CODEGEN_API_TOKEN` | API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Agent run retrieved successfully",
  "agent_run_id": "123456",
  "status": "completed",
  "web_url": "https://codegen.com/...",
  "result": {...}
}
```

**Status Values**: `pending`, `running`, `completed`, `failed`

**Examples**:

```python
codegen_get_agent_run("123456")
```

---

### 3. `codegen_reply_to_agent_run`

**Description**: Reply to an existing Codegen agent run with additional instructions or feedback.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `agent_run_id` | string | ✅ Yes | - | ID of the agent run to reply to |
| `message` | string | ✅ Yes | - | Your reply message to the agent |
| `org_id` | string | ❌ No | env:`CODEGEN_ORG_ID` | Organization ID |
| `api_token` | string | ❌ No | env:`CODEGEN_API_TOKEN` | API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Reply sent successfully",
  "agent_run_id": "123456",
  "status": "processing"
}
```

**Examples**:

```python
codegen_reply_to_agent_run("123456", "Please also add unit tests")
```

---

### 4. `codegen_list_agent_runs`

**Description**: List all Codegen agent runs for an organization.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | ❌ No | `10` | Maximum number of runs to return |
| `offset` | integer | ❌ No | `0` | Number of runs to skip |
| `status` | string | ❌ No | `null` | Filter by status |
| `org_id` | string | ❌ No | env:`CODEGEN_ORG_ID` | Organization ID |
| `api_token` | string | ❌ No | env:`CODEGEN_API_TOKEN` | API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Retrieved 5 agent runs",
  "runs": [
    {
      "id": "123456",
      "status": "completed",
      "prompt": "Review PR #123",
      ...
    }
  ],
  "total": 5
}
```

**Examples**:

```python
# List all agent runs
codegen_list_agent_runs()

# List completed runs only
codegen_list_agent_runs(limit=20, status="completed")
```

---

### 5. `codegen_cancel_agent_run`

**Description**: Cancel a running Codegen agent run.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `agent_run_id` | string | ✅ Yes | - | ID of the agent run to cancel |
| `org_id` | string | ❌ No | env:`CODEGEN_ORG_ID` | Organization ID |
| `api_token` | string | ❌ No | env:`CODEGEN_API_TOKEN` | API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Agent run cancelled successfully",
  "agent_run_id": "123456",
  "status": "cancelled"
}
```

**Examples**:

```python
codegen_cancel_agent_run("123456")
```

---

## GitHub API Tools

### 1. `github_create_repo`

**Description**: Create a new GitHub repository.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | string | ✅ Yes | - | Repository name |
| `description` | string | ❌ No | `null` | Repository description |
| `private` | boolean | ❌ No | `true` | Whether repo should be private |
| `api_token` | string | ❌ No | env:`GITHUB_API_TOKEN` | GitHub API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Repository created successfully",
  "repo_name": "username/my-new-repo",
  "repo_url": "https://github.com/username/my-new-repo",
  "clone_url": "https://github.com/username/my-new-repo.git",
  "ssh_url": "git@github.com:username/my-new-repo.git"
}
```

**Examples**:

```python
# Create private repo with description
github_create_repo("my-new-repo", "A cool project")

# Create public repo
github_create_repo("test-repo", private=False)
```

---

### 2. `github_list_repos`

**Description**: List all GitHub repositories for the authenticated user.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `per_page` | integer | ❌ No | `100` | Number of repos per page (max: 100) |
| `page` | integer | ❌ No | `1` | Page number |
| `api_token` | string | ❌ No | env:`GITHUB_API_TOKEN` | GitHub API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Retrieved 25 repositories",
  "repos": [
    {
      "name": "repo-name",
      "full_name": "username/repo-name",
      "url": "https://github.com/username/repo-name",
      "private": true
    }
  ],
  "total": 25
}
```

**Examples**:

```python
# List all repos
github_list_repos()

# Paginated results
github_list_repos(per_page=50, page=2)
```

---

### 3. `github_search_repo`

**Description**: Search for a specific GitHub repository.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ Yes | - | Search query |
| `username` | string | ❌ No | `null` | Filter by username |
| `api_token` | string | ❌ No | env:`GITHUB_API_TOKEN` | GitHub API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Found 3 repositories",
  "repos": [
    {
      "name": "forest-app",
      "full_name": "username/forest-app",
      "url": "https://github.com/username/forest-app",
      "description": "A productivity app"
    }
  ],
  "total_count": 3
}
```

**Examples**:

```python
# Search all repos
github_search_repo("forest")

# Search by specific user
github_search_repo("react", username="facebook")
```

---

## Coolify API Tools

**Note**: The following hardcoded values are used by default:
- **Project UUID**: `j0ck0c4kckgw0gosksosogog`
- **Server UUID**: `qk48swgog4kok0og8848wwg8`

### 1. `coolify_list_applications`

**Description**: List all Coolify applications.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_token` | string | ❌ No | env:`COOLIFY_API_TOKEN` | Coolify API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Retrieved 5 applications",
  "applications": [
    {
      "uuid": "app-uuid",
      "name": "my-app",
      "status": "running",
      ...
    }
  ],
  "total": 5
}
```

**Examples**:

```python
coolify_list_applications()
```

---

### 2. `coolify_list_servers`

**Description**: List all Coolify servers.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_token` | string | ❌ No | env:`COOLIFY_API_TOKEN` | Coolify API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Retrieved 2 servers",
  "servers": [
    {
      "uuid": "server-uuid",
      "name": "production-server",
      "ip": "192.168.1.1",
      ...
    }
  ],
  "total": 2
}
```

**Examples**:

```python
coolify_list_servers()
```

---

### 3. `coolify_get_server_details`

**Description**: Get details of a specific Coolify server.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `server_uuid` | string | ❌ No | `qk48swgog4kok0og8848wwg8` | Server UUID (defaults to hardcoded value) |
| `api_token` | string | ❌ No | env:`COOLIFY_API_TOKEN` | Coolify API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Server details retrieved successfully",
  "server": {
    "uuid": "qk48swgog4kok0og8848wwg8",
    "name": "production-server",
    "ip": "192.168.1.1",
    "port": 22,
    ...
  }
}
```

**Examples**:

```python
# Use default hardcoded server UUID
coolify_get_server_details()

# Use custom server UUID
coolify_get_server_details(server_uuid="custom-uuid")
```

---

### 4. `coolify_create_application`

**Description**: Create a new public application in Coolify.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `git_repository` | string | ✅ Yes | - | Git repository URL (e.g., "https://github.com/user/repo.git") |
| `name` | string | ✅ Yes | - | Application name |
| `git_branch` | string | ❌ No | `"main"` | Git branch to deploy |
| `build_pack` | string | ❌ No | `"dockercompose"` | Build pack type |
| `docker_compose_location` | string | ❌ No | `"docker-compose.yml"` | Path to docker-compose file |
| `instant_deploy` | boolean | ❌ No | `true` | Whether to deploy immediately |
| `environment_name` | string | ❌ No | `"production"` | Environment name |
| `project_uuid` | string | ❌ No | `j0ck0c4kckgw0gosksosogog` | Project UUID |
| `server_uuid` | string | ❌ No | `qk48swgog4kok0og8848wwg8` | Server UUID |
| `api_token` | string | ❌ No | env:`COOLIFY_API_TOKEN` | Coolify API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Application created successfully",
  "application_uuid": "new-app-uuid",
  "application": {
    "uuid": "new-app-uuid",
    "name": "my-app",
    "git_repository": "https://github.com/user/repo.git",
    ...
  }
}
```

**Examples**:

```python
# Create app with default settings
coolify_create_application("https://github.com/user/repo.git", "my-app")

# Create app with custom branch
coolify_create_application(
    "https://github.com/user/repo.git", 
    "test-app", 
    git_branch="develop"
)

# Full customization
coolify_create_application(
    git_repository="https://github.com/user/repo.git",
    name="production-app",
    git_branch="main",
    environment_name="production",
    instant_deploy=True
)
```

---

### 5. `coolify_restart_application`

**Description**: Restart a Coolify application.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `app_uuid` | string | ✅ Yes | - | Application UUID |
| `api_token` | string | ❌ No | env:`COOLIFY_API_TOKEN` | Coolify API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Application restarted successfully"
}
```

**Examples**:

```python
coolify_restart_application("app-uuid-here")
```

---

### 6. `coolify_stop_application`

**Description**: Stop a Coolify application.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `app_uuid` | string | ✅ Yes | - | Application UUID |
| `api_token` | string | ❌ No | env:`COOLIFY_API_TOKEN` | Coolify API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Application stopped successfully"
}
```

**Examples**:

```python
coolify_stop_application("app-uuid-here")
```

---

## Environment Variables

All tools support environment variable configuration. Create a `.env` file with:

```bash
# ImgBB Configuration
IMGBB_API_KEY=your_imgbb_api_key_here

# Codegen Configuration
CODEGEN_ORG_ID=your_org_id_here
CODEGEN_API_TOKEN=your_api_token_here

# GitHub Configuration
GITHUB_API_TOKEN=your_github_token_here

# Coolify Configuration
COOLIFY_API_TOKEN=your_coolify_token_here
COOLIFY_API_BASE_URL=https://worfklow.org/api/v1  # Optional
```

## Error Handling

All tools return a consistent error response format:

```json
{
  "success": false,
  "message": "Detailed error message explaining what went wrong"
}
```

## Common Response Patterns

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  ...additional fields...
}
```

### Error Response
```json
{
  "success": false,
  "message": "Error description"
}
```

## Rate Limiting

- **GitHub API**: 5,000 requests per hour for authenticated requests
- **Coolify API**: Varies by instance configuration
- **ImgBB API**: Varies by plan (free tier available)
- **Codegen API**: Contact Codegen for rate limits

## Support

For issues or questions:
- GitHub Issues: [Create an issue](https://github.com/Ntrakiyski/chrome-mcp/issues)
- Email: support@your-domain.com

## License

This project is licensed under the MIT License.

