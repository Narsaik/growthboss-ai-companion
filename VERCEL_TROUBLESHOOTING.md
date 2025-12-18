# Vercel Deployment Troubleshooting Guide

## Common Issues and Solutions

### 1. ChromaDB Not Working in Serverless

**Problem:** ChromaDB uses local file storage which doesn't persist in serverless functions.

**Error Messages:**
- "ChromaDB error: Local ChromaDB doesn't work in serverless"
- "No such file or directory" errors related to ChromaDB

**Solutions:**

#### Option A: Use ChromaDB Cloud (Recommended)
1. Sign up at https://www.trychroma.com/
2. Get your API key and host
3. Update `src/rag/vectorstore.py` to use ChromaDB Cloud:
```python
import chromadb
from chromadb.config import Settings

client = chromadb.HttpClient(
    host="your-host.chroma.cloud",
    port=443,
    headers={"X-Chroma-Token": "your-api-key"}
)
```

#### Option B: Use Alternative Vector Database
- **Pinecone**: https://www.pinecone.io/
- **Weaviate**: https://weaviate.io/
- **Qdrant**: https://qdrant.tech/

#### Option C: Disable RAG (Use Council Only)
Temporarily disable RAG features and use only the Marketing Council mode.

### 2. Environment Variables Not Set

**Problem:** `OPENAI_API_KEY` is missing or incorrect.

**Error Messages:**
- "OPENAI_API_KEY is not set"
- "Failed to initialize AI system"

**Solution:**
1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Add `OPENAI_API_KEY` with your OpenAI API key
3. Make sure it's added for **Production**, **Preview**, and **Development**
4. Redeploy the project

### 3. Static Files Not Loading

**Problem:** CSS/JS files return 404.

**Solution:**
- The `vercel.json` has been updated to handle static files
- If still not working, check that files exist in `web/static/` directory
- Verify file paths in the HTML template are correct

### 4. Function Timeout

**Problem:** Requests timeout after 10 seconds (Hobby plan) or 60 seconds (Pro plan).

**Error Messages:**
- "Function execution exceeded timeout"

**Solutions:**
- Upgrade to Vercel Pro plan (60s timeout)
- Optimize agent initialization (cache agents if possible)
- Use streaming responses for long operations
- Consider async processing for heavy operations

### 5. Import Errors

**Problem:** Module not found errors.

**Error Messages:**
- "ModuleNotFoundError: No module named 'X'"

**Solution:**
- Ensure all dependencies are in `requirements.txt`
- Check that package names are correct
- Some packages may not be compatible with Vercel's Python runtime

### 6. Build Failures

**Problem:** Deployment fails during build.

**Solutions:**
1. Check build logs in Vercel Dashboard
2. Verify `requirements.txt` syntax is correct
3. Ensure Python version is compatible (3.11 or 3.12)
4. Some packages may need to be pinned to specific versions

### 7. CORS Errors

**Problem:** Browser shows CORS errors when making API requests.

**Solution:**
- CORS headers have been added to all API responses
- If still having issues, check browser console for specific errors

## Debugging Steps

1. **Check Vercel Function Logs:**
   - Go to Vercel Dashboard → Your Project → Functions
   - Click on a function → View logs
   - Look for error messages and stack traces

2. **Test Health Endpoint:**
   ```
   https://your-project.vercel.app/api/health
   ```
   This should return status information.

3. **Check Environment Variables:**
   - Verify all required variables are set
   - Check variable names are correct (case-sensitive)
   - Ensure they're set for the correct environment

4. **Local Testing:**
   ```bash
   # Install Vercel CLI
   npm i -g vercel
   
   # Test locally
   vercel dev
   ```

## Quick Fixes

### Disable RAG Temporarily
If ChromaDB is causing issues, you can modify `api/index.py` to skip RAG initialization:

```python
def get_agents():
    try:
        # Skip RAG for now
        researcher = None
        council = MarketingCouncil(collection_name=COLLECTION_NAME)
        return researcher, council, None
    except Exception as e:
        return None, None, str(e)
```

### Add Better Error Messages
All error responses now include helpful messages. Check the response body in browser DevTools Network tab.

## Getting Help

1. Check Vercel Function Logs (most important!)
2. Review error messages in browser console
3. Test endpoints individually:
   - `/api/health` - Should work even without ChromaDB
   - `/api/session` - Should always work
   - `/api/chat` - May fail if ChromaDB not configured

## Next Steps

1. **Set up ChromaDB Cloud** (recommended for production)
2. **Configure all environment variables** in Vercel
3. **Test each endpoint** individually
4. **Monitor function logs** for any errors
