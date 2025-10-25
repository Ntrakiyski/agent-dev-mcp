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

### 3. `ask_about_screenshot`

**Description**: Analyze a screenshot using OpenRouter's vision-capable LLM models. Perfect for extracting information from screenshots, describing UI elements, reading text from images, or any vision-based tasks.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt` | string | ✅ Yes | - | Your question or instruction about the image (e.g., "What's in this image?", "Describe the UI layout") |
| `image_url` | string | ✅ Yes | - | Public URL of the image to analyze (e.g., from ImgBB, or any accessible image URL) |
| `model` | string | ❌ No | `"qwen/qwen-2.5-vl-72b-instruct"` | OpenRouter model ID. Other vision models: "google/gemini-2.0-flash-001", "anthropic/claude-3.5-sonnet", etc. |
| `api_key` | string | ❌ No | env:`OPENROUTER_API_KEY` | OpenRouter API key (optional, uses OPENROUTER_API_KEY env var if not provided) |
| `max_tokens` | integer | ❌ No | model default | Maximum tokens in response |
| `temperature` | float | ❌ No | model default | Sampling temperature 0.0-1.0 for controlling randomness |

**Output Schema**:

```json
{
  "success": true,
  "message": "Image analyzed successfully",
  "response": "The image shows a modern web dashboard with...",
  "model": "qwen/qwen-2.5-vl-72b-instruct",
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 200,
    "total_tokens": 350
  }
}
```

**Examples**:

```python
# Basic screenshot analysis
ask_about_screenshot(
    "What's in this image?",
    "https://i.ibb.co/xxxxx/screenshot.png"
)

# UI layout analysis with specific model
ask_about_screenshot(
    "Describe the UI layout and list all visible buttons",
    "https://i.ibb.co/xxxxx/dashboard.png",
    model="google/gemini-2.0-flash-001"
)

# Text extraction with low temperature
ask_about_screenshot(
    "Extract all visible text from this image",
    "https://i.ibb.co/xxxxx/document.png",
    temperature=0.2
)

# Combined workflow: Screenshot + Analysis
screenshot = take_screenshot("https://example.com")
analysis = ask_about_screenshot(
    "Does this page have any visual bugs?",
    screenshot['public_url']
)
```

**Supported Vision Models**:

| Model | ID | Best For |
|-------|-----|----------|
| **Qwen 2.5-VL** (default) | `qwen/qwen-2.5-vl-72b-instruct` | General vision tasks, fast & affordable |
| **Gemini 2.0 Flash** | `google/gemini-2.0-flash-001` | Fast responses, good accuracy |
| **Claude 3.5 Sonnet** | `anthropic/claude-3.5-sonnet` | Complex analysis, detailed responses |
| **GPT-4 Vision** | `openai/gpt-4-vision-preview` | High accuracy, comprehensive |

See [OpenRouter Models](https://openrouter.ai/models) for the complete list of vision-capable models.

**Configuration**:

```bash
# .env file
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
```

Get your API key from: https://openrouter.ai/keys

**Use Cases**:

1. **Screenshot QA**: Capture and analyze web pages for bugs
2. **UI Documentation**: Generate descriptions of UI components
3. **Error Diagnosis**: Analyze error screenshots and get solutions
4. **Accessibility Audit**: Check for accessibility issues
5. **Text Extraction**: Extract text from images or screenshots
6. **Layout Analysis**: Understand page structure and design

---

### 4. `health_check`

**Description**: Check server health and configuration status.

**Input Parameters**: None

**Output Schema**:

```json
{
  "status": "healthy",
  "browser_connected": true,
  "imgbb_configured": true,
  "openrouter_configured": true,
  "message": "Server is fully operational"
}
```

Or when degraded:

```json
{
  "status": "degraded",
  "browser_connected": true,
  "imgbb_configured": true,
  "openrouter_configured": false,
  "message": "Warnings: OpenRouter API key not configured"
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

**Description**: Resume a paused Codegen agent run with additional instructions or feedback.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `agent_run_id` | integer | ✅ Yes | - | ID of the agent run to resume (must be an integer) |
| `prompt` | string | ✅ Yes | - | Your prompt/message to the agent |
| `images` | list[string] | ❌ No | `null` | Optional list of base64 encoded data URIs for images |
| `org_id` | string | ❌ No | env:`CODEGEN_ORG_ID` | Organization ID |
| `api_token` | string | ❌ No | env:`CODEGEN_API_TOKEN` | API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Agent run resumed successfully",
  "agent_run_id": 123456,
  "status": "processing",
  "result": {
    "id": 123456,
    "organization_id": 789,
    "status": "processing",
    "created_at": "2024-01-01T00:00:00Z",
    "web_url": "https://codegen.com/...",
    ...
  }
}
```

**Examples**:

```python
# Basic usage with integer ID
codegen_reply_to_agent_run(123456, "Please also add unit tests")

# With organization ID
codegen_reply_to_agent_run(123456, "Looks good, ship it!", org_id="123")

# With image attachment
codegen_reply_to_agent_run(123456, "Check this screenshot", images=["data:image/png;base64,..."])
```

---

### 4. `codegen_list_agent_runs`

**Description**: List Codegen agent runs for an organization with optional filtering and pagination.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | ❌ No | `10` | Maximum number of runs to return (range: 1-100) |
| `skip` | integer | ❌ No | `0` | Number of runs to skip for pagination (must be >= 0) |
| `user_id` | integer | ❌ No | `null` | Filter by user ID who initiated the agent runs |
| `source_type` | string | ❌ No | `null` | Filter by source type (e.g., 'LOCAL', 'SLACK', 'GITHUB', 'API', 'LINEAR') |
| `org_id` | string | ❌ No | env:`CODEGEN_ORG_ID` | Organization ID |
| `api_token` | string | ❌ No | env:`CODEGEN_API_TOKEN` | API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Retrieved 5 agent runs",
  "runs": [
    {
      "id": 123456,
      "organization_id": 789,
      "status": "completed",
      "created_at": "2024-01-01T00:00:00Z",
      "web_url": "https://codegen.com/...",
      "summary": "Review PR #123",
      "source_type": "GITHUB",
      "github_pull_requests": [...],
      "metadata": {}
    }
  ],
  "total": 5,
  "page": 1,
  "size": 5,
  "pages": 1
}
```

**Examples**:

```python
# List all agent runs with default pagination
codegen_list_agent_runs()

# List with custom pagination
codegen_list_agent_runs(limit=20, skip=10)

# Filter by user and source type
codegen_list_agent_runs(user_id=123, source_type="SLACK")

# Combine filters
codegen_list_agent_runs(limit=50, user_id=456, source_type="GITHUB")
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

### 4. `github_list_pull_requests`

**Description**: List pull requests in a GitHub repository with state filtering.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `owner` | string | ✅ Yes | - | Repository owner username (e.g., "Ntrakiyski") |
| `repo` | string | ✅ Yes | - | Repository name (e.g., "chrome-mcp") |
| `state` | string | ❌ No | `"open"` | PR state filter: "open", "closed", or "all" |
| `per_page` | integer | ❌ No | `30` | Number of PRs per page (max: 100) |
| `page` | integer | ❌ No | `1` | Page number |
| `api_token` | string | ❌ No | env:`GITHUB_API_TOKEN` | GitHub API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Retrieved 3 pull requests",
  "pull_requests": [
    {
      "number": 1,
      "title": "Add new feature",
      "state": "open",
      "user": "username",
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-02T12:00:00Z",
      "html_url": "https://github.com/owner/repo/pull/1",
      "head": "feature-branch",
      "base": "main",
      "mergeable": true,
      "draft": false
    }
  ],
  "count": 3
}
```

**Examples**:

```python
# List open PRs
github_list_pull_requests("Ntrakiyski", "chrome-mcp")

# List all PRs (open + closed)
github_list_pull_requests("Ntrakiyski", "chrome-mcp", state="all")

# List closed PRs with pagination
github_list_pull_requests("Ntrakiyski", "chrome-mcp", state="closed", per_page=50, page=1)
```

---

### 5. `github_get_pull_request`

**Description**: Get detailed information about a specific pull request including mergeable state, commit count, and file statistics.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `owner` | string | ✅ Yes | - | Repository owner username |
| `repo` | string | ✅ Yes | - | Repository name |
| `pull_number` | integer | ✅ Yes | - | Pull request number |
| `api_token` | string | ❌ No | env:`GITHUB_API_TOKEN` | GitHub API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Retrieved PR #1",
  "pull_request": {
    "number": 1,
    "title": "Add new feature",
    "body": "This PR adds...",
    "state": "open",
    "user": "username",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-02T12:00:00Z",
    "closed_at": null,
    "merged_at": null,
    "html_url": "https://github.com/owner/repo/pull/1",
    "head": "feature-branch",
    "base": "main",
    "mergeable": true,
    "mergeable_state": "clean",
    "merged": false,
    "draft": false,
    "commits": 5,
    "additions": 120,
    "deletions": 30,
    "changed_files": 8
  }
}
```

**Examples**:

```python
# Get PR details
github_get_pull_request("Ntrakiyski", "chrome-mcp", 1)

# Check if PR is mergeable
result = github_get_pull_request("Ntrakiyski", "chrome-mcp", 1)
if result["pull_request"]["mergeable"]:
    print("PR can be merged!")
```

---

### 6. `github_merge_pull_request`

**Description**: Merge a pull request using merge, squash, or rebase strategy.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `owner` | string | ✅ Yes | - | Repository owner username |
| `repo` | string | ✅ Yes | - | Repository name |
| `pull_number` | integer | ✅ Yes | - | Pull request number to merge |
| `commit_title` | string | ❌ No | `null` | Custom merge commit title (auto-generated if not provided) |
| `commit_message` | string | ❌ No | `null` | Additional commit message details |
| `merge_method` | string | ❌ No | `"merge"` | Merge method: "merge", "squash", or "rebase" |
| `api_token` | string | ❌ No | env:`GITHUB_API_TOKEN` | GitHub API token |

**Output Schema**:

Success response:
```json
{
  "success": true,
  "message": "Pull request merged successfully",
  "sha": "abc123def456...",
  "merged": true
}
```

Error responses:
```json
{
  "success": false,
  "message": "Pull request cannot be merged (method not allowed). Check if PR is mergeable and branch protection rules."
}
```

```json
{
  "success": false,
  "message": "Merge conflict detected. Pull request head branch must be updated."
}
```

**Examples**:

```python
# Standard merge
github_merge_pull_request("Ntrakiyski", "chrome-mcp", 1)

# Squash merge with custom message
github_merge_pull_request(
    "Ntrakiyski", 
    "chrome-mcp", 
    1, 
    commit_title="Add GitHub PR tools",
    commit_message="Implements list, get, merge, and update PR functionality",
    merge_method="squash"
)

# Rebase merge
github_merge_pull_request("Ntrakiyski", "chrome-mcp", 1, merge_method="rebase")
```

---

### 7. `github_list_pull_request_files`

**Description**: List all files changed in a pull request with addition/deletion statistics.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `owner` | string | ✅ Yes | - | Repository owner username |
| `repo` | string | ✅ Yes | - | Repository name |
| `pull_number` | integer | ✅ Yes | - | Pull request number |
| `per_page` | integer | ❌ No | `30` | Number of files per page (max: 100) |
| `page` | integer | ❌ No | `1` | Page number |
| `api_token` | string | ❌ No | env:`GITHUB_API_TOKEN` | GitHub API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Retrieved 5 files",
  "files": [
    {
      "filename": "server.py",
      "status": "modified",
      "additions": 150,
      "deletions": 20,
      "changes": 170,
      "blob_url": "https://github.com/owner/repo/blob/abc123/server.py",
      "raw_url": "https://github.com/owner/repo/raw/abc123/server.py",
      "patch": "@@ -100,7 +100,7 @@ def function():\n-    old line\n+    new line"
    }
  ],
  "count": 5
}
```

**Examples**:

```python
# List files in PR
github_list_pull_request_files("Ntrakiyski", "chrome-mcp", 1)

# Get second page of files
github_list_pull_request_files("Ntrakiyski", "chrome-mcp", 1, per_page=50, page=2)
```

---

### 8. `github_check_pull_request_merged`

**Description**: Check if a pull request has been merged (returns 204 if merged, 404 if not merged).

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `owner` | string | ✅ Yes | - | Repository owner username |
| `repo` | string | ✅ Yes | - | Repository name |
| `pull_number` | integer | ✅ Yes | - | Pull request number |
| `api_token` | string | ❌ No | env:`GITHUB_API_TOKEN` | GitHub API token |

**Output Schema**:

Merged PR:
```json
{
  "success": true,
  "message": "PR #1 has been merged",
  "merged": true
}
```

Not merged PR:
```json
{
  "success": true,
  "message": "PR #1 has NOT been merged",
  "merged": false
}
```

**Examples**:

```python
# Check merge status
result = github_check_pull_request_merged("Ntrakiyski", "chrome-mcp", 1)
if result["merged"]:
    print("PR is merged!")
else:
    print("PR is still open or closed but not merged")
```

---

### 9. `github_update_pull_request`

**Description**: Update a pull request's title, body, state, or base branch.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `owner` | string | ✅ Yes | - | Repository owner username |
| `repo` | string | ✅ Yes | - | Repository name |
| `pull_number` | integer | ✅ Yes | - | Pull request number to update |
| `title` | string | ❌ No | `null` | New PR title |
| `body` | string | ❌ No | `null` | New PR body/description |
| `state` | string | ❌ No | `null` | New PR state: "open" or "closed" |
| `base` | string | ❌ No | `null` | New base branch name |
| `api_token` | string | ❌ No | env:`GITHUB_API_TOKEN` | GitHub API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "PR #1 updated successfully",
  "pull_request": {
    "number": 1,
    "title": "Updated Title",
    "state": "open",
    "html_url": "https://github.com/owner/repo/pull/1"
  }
}
```

**Examples**:

```python
# Update PR title
github_update_pull_request("Ntrakiyski", "chrome-mcp", 1, title="New Feature: GitHub PR Tools")

# Update PR body
github_update_pull_request(
    "Ntrakiyski", 
    "chrome-mcp", 
    1, 
    body="## Changes\n- Added PR tools\n- Updated docs"
)

# Close PR
github_update_pull_request("Ntrakiyski", "chrome-mcp", 1, state="closed")

# Change base branch
github_update_pull_request("Ntrakiyski", "chrome-mcp", 1, base="develop")

# Update multiple fields
github_update_pull_request(
    "Ntrakiyski",
    "chrome-mcp",
    1,
    title="Updated Title",
    body="New description",
    state="open"
)
```

---

### 10. `github_get_repo_tree`

**Description**: Get the complete file/folder structure of a GitHub repository.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `owner` | string | ✅ Yes | - | GitHub username or organization name |
| `repo` | string | ✅ Yes | - | Repository name |
| `branch` | string | ❌ No | `"main"` | Branch name |
| `recursive` | boolean | ❌ No | `true` | Whether to get full tree recursively |
| `api_token` | string | ❌ No | env:`GITHUB_API_TOKEN` | GitHub API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Retrieved repository tree with 127 files",
  "repository": {
    "owner": "Ntrakiyski",
    "repo": "chrome-mcp",
    "branch": "main",
    "sha": "abc123def456..."
  },
  "tree": [
    {
      "path": "README.md",
      "mode": "100644",
      "type": "blob",
      "size": 4512,
      "sha": "def789..."
    }
  ],
  "file_count": 127,
  "directory_count": 15,
  "total_size_bytes": 456789,
  "truncated": false
}
```

**Examples**:

```python
# Get full repository structure
github_get_repo_tree("Ntrakiyski", "chrome-mcp")

# Get specific branch
github_get_repo_tree("Ntrakiyski", "chrome-mcp", branch="develop")
```

---

### 11. `github_get_file_content`

**Description**: Get the content of a file from a GitHub repository.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `owner` | string | ✅ Yes | - | GitHub username or organization name |
| `repo` | string | ✅ Yes | - | Repository name |
| `path` | string | ✅ Yes | - | File path within the repository |
| `branch` | string | ❌ No | `"main"` | Branch name |
| `api_token` | string | ❌ No | env:`GITHUB_API_TOKEN` | GitHub API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Successfully retrieved file src/server.py",
  "file": {
    "name": "server.py",
    "path": "src/server.py",
    "sha": "abc123def456...",
    "size": 15678,
    "encoding": "base64",
    "content": "import asyncio\nfrom mcp import Server..."
  }
}
```

**Examples**:

```python
# Get file content
result = github_get_file_content("Ntrakiyski", "chrome-mcp", "src/server.py")
content = result["file"]["content"]  # Already decoded to string
sha = result["file"]["sha"]  # Save this for updates!
```

---

### 12. `github_update_file`

**Description**: Update an existing file in a GitHub repository.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `owner` | string | ✅ Yes | - | GitHub username or organization name |
| `repo` | string | ✅ Yes | - | Repository name |
| `path` | string | ✅ Yes | - | File path within the repository |
| `content` | string | ✅ Yes | - | New file content as string |
| `message` | string | ✅ Yes | - | Commit message |
| `sha` | string | ✅ Yes | - | Current file SHA (from `github_get_file_content`) |
| `branch` | string | ❌ No | `"main"` | Branch name |
| `api_token` | string | ❌ No | env:`GITHUB_API_TOKEN` | GitHub API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "File src/server.py updated successfully",
  "commit": {
    "sha": "commit_sha...",
    "message": "Update server.py with new features"
  },
  "file": {
    "name": "server.py",
    "path": "src/server.py",
    "sha": "new_sha_xyz789...",
    "size": 6234
  }
}
```

**Examples**:

```python
# First get current file content and SHA
result = github_get_file_content("Ntrakiyski", "chrome-mcp", "src/server.py")
current_sha = result["file"]["sha"]

# Update the file
new_content = "# Updated server code\nprint('Hello World')"
github_update_file(
    "Ntrakiyski",
    "chrome-mcp",
    "src/server.py",
    new_content,
    "Add hello world message",
    current_sha
)
```

---

### 13. `github_create_file`

**Description**: Create a new file in a GitHub repository.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `owner` | string | ✅ Yes | - | GitHub username or organization name |
| `repo` | string | ✅ Yes | - | Repository name |
| `path` | string | ✅ Yes | - | File path within the repository |
| `content` | string | ✅ Yes | - | File content as string |
| `message` | string | ✅ Yes | - | Commit message |
| `branch` | string | ❌ No | `"main"` | Branch name |
| `api_token` | string | ❌ No | env:`GITHUB_API_TOKEN` | GitHub API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "File src/new_file.py created successfully",
  "commit": {
    "sha": "commit_sha...",
    "message": "Add new authentication module"
  },
  "file": {
    "name": "new_file.py",
    "path": "src/new_file.py",
    "sha": "file_sha_xyz789...",
    "size": 892
  }
}
```

**Examples**:

```python
# Create a new file
new_code = """
def authenticate(token):
    # Authentication logic
    pass
"""

github_create_file(
    "Ntrakiyski",
    "chrome-mcp",
    "src/auth.py",
    new_code,
    "Add authentication module"
)
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

### 7. `get_coolify_domain_and_envs`

**Description**: Get domain and all environment variables for a Coolify application in a single call.

This tool retrieves both the application's domain/FQDN and all environment variables, making it convenient to get complete deployment configuration information without making multiple API calls.

**Input Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `app_uuid` | string | ✅ Yes | - | Application UUID |
| `api_token` | string | ❌ No | env:`COOLIFY_API_TOKEN` | Coolify API token |

**Output Schema**:

```json
{
  "success": true,
  "message": "Successfully retrieved domain and environment variables",
  "application_uuid": "app-uuid",
  "domain": "myapp.example.com",
  "fqdn": "myapp.example.com",
  "environment_variables": [
    {
      "id": 1,
      "uuid": "env-uuid",
      "key": "DATABASE_URL",
      "value": "[REDACTED]",
      "real_value": "[REDACTED]",
      "is_literal": true,
      "is_multiline": false,
      "is_preview": false,
      "is_runtime": true,
      "is_buildtime": false,
      "is_shared": false,
      "is_shown_once": false,
      "version": "1.0",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "uuid": "env-uuid-2",
      "key": "NODE_ENV",
      "value": "production",
      "real_value": "production",
      "is_literal": true,
      "is_multiline": false,
      "is_preview": false,
      "is_runtime": true,
      "is_buildtime": true,
      "is_shared": false,
      "is_shown_once": false,
      "version": "1.0",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Environment Variable Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Database ID of the environment variable |
| `uuid` | string | Unique identifier for the environment variable |
| `key` | string | Environment variable name |
| `value` | string | Masked/displayed value (sensitive values may be masked) |
| `real_value` | string | Actual unmasked value |
| `is_literal` | boolean | Whether the value is literal or computed |
| `is_multiline` | boolean | Whether the value spans multiple lines |
| `is_preview` | boolean | Whether this is a preview environment variable |
| `is_runtime` | boolean | Whether this variable is available at runtime |
| `is_buildtime` | boolean | Whether this variable is available at build time |
| `is_shared` | boolean | Whether this variable is shared across environments |
| `is_shown_once` | boolean | Whether this variable is shown only once for security |
| `version` | string | Version of the environment variable |
| `created_at` | string | ISO 8601 timestamp of creation |
| `updated_at` | string | ISO 8601 timestamp of last update |

**Examples**:

```python
# Get domain and env vars for an application
result = get_coolify_domain_and_envs("app-uuid-here")
print(f"Domain: {result['domain']}")
print(f"Found {len(result['environment_variables'])} environment variables")

# Access specific environment variables
for env_var in result['environment_variables']:
    if env_var['key'] == 'DATABASE_URL':
        print(f"Database URL: {env_var['real_value']}")

# Use custom API token
result = get_coolify_domain_and_envs(
    app_uuid="app-uuid-here",
    api_token="custom-token"
)
```

**Use Cases**:

- **Deployment Configuration Audit**: Get all configuration in one call for documentation
- **Environment Setup**: Retrieve all environment variables to replicate configuration
- **Domain Verification**: Confirm the correct domain is assigned to an application
- **Configuration Debugging**: Check all environment variables and their values at once
- **Migration Planning**: Export complete configuration before migrating applications

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
