# 🚀 Deploying Chrome MCP Server to Coolify

**TL;DR:** Connect your GitHub repo to Coolify, and it will automatically detect and deploy using `docker-compose.yml`. Chrome/Chromium dependencies are handled automatically.

---

## ✅ Prerequisites

Before deploying to Coolify, ensure you have:

1. ✅ **Coolify instance running** - Either self-hosted or cloud
2. ✅ **GitHub repository** - This repository connected to Coolify
3. ✅ **Docker support** - Coolify server has Docker installed (default)

That's it! Everything else is handled automatically.

---

## 🎯 Quick Deploy (3 Steps)

### **Step 1: Connect Repository to Coolify**

1. Log into your Coolify dashboard
2. Click **"+ New Resource"**
3. Select **"Docker Compose"** as the deployment type
4. Connect your GitHub repository
5. Select the branch (e.g., `main` or `codegen-bot/screenshot-mcp-server-setup-b1046982`)

### **Step 2: Coolify Auto-Configuration**

Coolify will automatically:
- ✅ Detect the `docker-compose.yml` file
- ✅ Build the Docker image using the `Dockerfile`
- ✅ Install all Chrome/Chromium dependencies (handled by the official Playwright image)
- ✅ Configure networking and ports

**You don't need to do anything!** The configuration is already production-ready.

### **Step 3: Deploy**

Click **"Deploy"** in Coolify and wait for:
- ✅ Build to complete (~2-3 minutes first time)
- ✅ Container to start
- ✅ Health checks to pass

**That's it!** Your MCP server is live. 🎉

---

## 🏗️ What Happens Behind the Scenes

### **Docker Image Build**

Coolify will build the image using the `Dockerfile`:

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.55.0-noble
# ✅ Includes Ubuntu 24.04 LTS
# ✅ Includes all system dependencies for browsers
# ✅ Includes fonts, libraries, and graphics drivers

RUN pip install fastmcp playwright
# ✅ Installs Python packages

RUN playwright install chromium
# ✅ Downloads and installs Chromium browser
# ✅ Handled automatically in the build
```

### **Container Configuration**

The `docker-compose.yml` configures:

```yaml
ipc: host          # ✅ Prevents Chromium memory crashes
init: true         # ✅ Prevents zombie processes
shm_size: '2gb'    # ✅ Shared memory for Chromium
memory: 2048M      # ✅ Minimum 2GB RAM for Chromium
```

### **Chrome/Chromium Dependencies**

**All browser dependencies are handled automatically:**

✅ **System Libraries** - Pre-installed in the base image  
✅ **Fonts** - Pre-installed in the base image  
✅ **Graphics Drivers** - Pre-installed in the base image  
✅ **Chromium Browser** - Installed during Docker build  
✅ **Shared Memory** - Configured via `shm_size` and `ipc:host`  

**You don't need to worry about any of this!** The official Microsoft Playwright image is battle-tested for production.

---

## 🔧 Configuration Options

### **Optional: Custom Port**

By default, the MCP server runs on port `8000`.

**To change the port:**

1. In Coolify, go to your service settings
2. Update the port mapping from `8000:8000` to `YOUR_PORT:8000`
3. Redeploy

### **Optional: Custom Domain**

Coolify can automatically configure SSL/HTTPS:

1. In Coolify, go to your service settings
2. Add your custom domain (e.g., `mcp.yourdomain.com`)
3. Coolify will automatically provision SSL certificate
4. Your MCP server will be available at `https://mcp.yourdomain.com`

### **Optional: Environment Variables**

If you need to pass environment variables:

1. In Coolify, go to **Environment Variables** section
2. Add any variables you need
3. They will be automatically passed to the container

**Current environment variables:**
- `PYTHONUNBUFFERED=1` - Already configured (enables real-time logging)

---

## 📊 Resource Requirements

### **Minimum Requirements:**

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| **RAM** | 1 GB | 2 GB |
| **CPU** | 1 core | 2 cores |
| **Disk** | 2 GB | 5 GB |

### **Why These Requirements?**

- **Chromium browser** needs ~500MB-1GB RAM for rendering
- **Playwright** needs additional memory for automation
- **Docker image** is ~1.5GB (includes browser and dependencies)

The `docker-compose.yml` is already configured with:
- **2GB memory limit** - Prevents OOM kills
- **2 CPU cores** - Better performance for browser automation
- **1GB memory reservation** - Ensures minimum resources available

---

## 🔍 Verifying Deployment

### **Check Container Status**

In Coolify, you should see:
- ✅ Container status: **Running**
- ✅ Health check: **Healthy**
- ✅ Logs showing: `"FastMCP server running on port 8000"`

### **Test the MCP Server**

#### **Option 1: Using the Test Script**

If you have access to the container:

```bash
# SSH into your Coolify server
docker exec -it chrome-mcp-server python check_server.py
```

#### **Option 2: Using cURL**

```bash
# Check if the server is responding
curl http://YOUR_COOLIFY_DOMAIN:8000

# Should return MCP server information
```

#### **Option 3: Take a Screenshot**

Connect via MCP client and test:

```python
take_screenshot("https://producthunt.com")
# Should return a base64-encoded full-page screenshot
```

---

## 🐛 Troubleshooting

### **Issue: Container Fails to Start**

**Check the logs in Coolify:**

```bash
# Common issues and solutions:
```

| Error | Cause | Solution |
|-------|-------|----------|
| `ENOSPC: no space left` | Disk full | Increase disk space or clean up old images |
| `OOMKilled` | Out of memory | Increase memory limit to 2GB+ |
| `chromium: error while loading shared libraries` | Missing dependencies | Rebuild image (dependencies should auto-install) |

### **Issue: Screenshots Fail**

**Check if Chromium is installed:**

```bash
docker exec -it chrome-mcp-server playwright --version
# Should show: Version 1.55.0
```

**Check if Chromium can launch:**

```bash
docker exec -it chrome-mcp-server python -c "
import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        print('✅ Chromium launched successfully!')
        await browser.close()

asyncio.run(test())
"
```

### **Issue: "Shared Memory" Errors**

**Error message:** `Failed to create shared memory segment`

**Solution:** Already handled! The `docker-compose.yml` includes:
- `ipc: host` - Shares host's IPC namespace
- `shm_size: '2gb'` - Allocates 2GB shared memory

If you still see this error, verify Coolify allows these Docker flags.

### **Issue: Zombie Processes**

**Error message:** Too many processes, container slow

**Solution:** Already handled! The `docker-compose.yml` includes:
- `init: true` - Enables proper PID 1 process management

This prevents zombie processes from accumulating.

---

## 🔒 Security Considerations

### **Browser Sandbox**

The MCP server runs Chromium with:
- ✅ Headless mode (no GUI)
- ✅ `--no-sandbox` flag (required for Docker)
- ✅ `--disable-dev-shm-usage` (uses disk instead of shared memory)

**This is safe for trusted websites** like ProductHunt, GitHub, etc.

**For untrusted websites**, consider:
- Running as non-root user
- Using seccomp security profiles
- Limiting network access

### **Resource Limits**

The `docker-compose.yml` includes resource limits:
- **Memory limit:** 2GB (prevents runaway memory usage)
- **CPU limit:** 2 cores (prevents CPU hogging)

These protect your server from resource exhaustion.

---

## 📈 Performance Optimization

### **For High-Volume Usage**

If taking many screenshots:

1. **Increase memory limit:**
   ```yaml
   memory: 4096M  # 4GB for heavy usage
   ```

2. **Add more CPU cores:**
   ```yaml
   cpus: '4.0'  # 4 cores for parallel processing
   ```

3. **Consider browser pooling:**
   - The current implementation reuses a single browser instance
   - This is optimal for most use cases
   - For extremely high volume, consider a browser pool

### **For Cost Optimization**

If on a tight budget:

1. **Reduce memory (not recommended below 2GB):**
   ```yaml
   memory: 1536M  # 1.5GB minimum
   ```

2. **Use 1 CPU core:**
   ```yaml
   cpus: '1.0'
   ```

**Warning:** Going below recommended resources may cause:
- ❌ Chromium crashes
- ❌ Slow screenshot generation
- ❌ Out-of-memory (OOM) kills

---

## 🎉 Success Checklist

After deployment, verify:

- ✅ Container is running in Coolify
- ✅ Logs show "FastMCP server running on port 8000"
- ✅ No error messages in logs
- ✅ Can connect to the MCP server
- ✅ Screenshots work correctly
- ✅ Full-page screenshots capture entire page
- ✅ Parameters (delay, viewport) work as expected

---

## 📚 Next Steps

After successful deployment:

1. **Connect MCP Client** - Use your preferred MCP client to connect
2. **Test All Features** - Try different parameters (delay, viewport, full_page)
3. **Monitor Resources** - Check memory/CPU usage in Coolify
4. **Set Up Alerts** - Configure Coolify alerts for container crashes
5. **Backup Configuration** - Save your Coolify configuration

---

## 🆘 Need Help?

If you encounter issues:

1. **Check Coolify Logs** - Most issues are visible in logs
2. **Verify Docker Build** - Ensure image builds successfully
3. **Test Locally First** - Run `docker-compose up` locally to debug
4. **Check Resource Limits** - Ensure server has enough RAM/CPU
5. **Review Browser Errors** - Look for Chromium-specific errors

---

## 📖 Summary

**Deploying to Coolify is simple:**

1. ✅ Connect GitHub repo to Coolify
2. ✅ Coolify detects `docker-compose.yml`
3. ✅ Click Deploy
4. ✅ Done!

**Chrome/Chromium is handled automatically:**
- ✅ Official Microsoft Playwright image includes all dependencies
- ✅ Browser is installed during Docker build
- ✅ Memory and IPC settings prevent crashes
- ✅ Production-tested and battle-hardened

**No manual intervention needed!** Just connect and deploy. 🚀

---

## 🔗 Related Documentation

- [PARAMETERS.md](PARAMETERS.md) - Complete parameter reference
- [README.md](README.md) - Project overview
- [Playwright Docker Guide](https://playwright.dev/python/docs/docker) - Official docs
- [Coolify Documentation](https://coolify.io/docs) - Coolify setup

---

**Happy deploying! 🎉**

