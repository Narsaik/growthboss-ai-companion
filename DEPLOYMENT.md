# Vercel Deployment Guide for GrowthBoss AI Companion

This guide will help you deploy the GrowthBoss AI Companion to Vercel.

## Prerequisites

1. A Vercel account (sign up at [vercel.com](https://vercel.com))
2. Vercel CLI installed: `npm i -g vercel`
3. All your API keys ready

## Step 1: Install Dependencies

Make sure you have all Python dependencies installed locally (for testing):

```bash
pip install -r requirements.txt
```

## Step 2: Prepare Environment Variables

Create a `.env` file locally (for testing) and prepare to add these to Vercel:

```env
OPENAI_API_KEY=sk-your-openai-key
FLASK_SECRET_KEY=your-secret-key-change-in-production
OPENAI_EMBED_MODEL=text-embedding-3-large
OPENAI_CHAT_MODEL=gpt-4o-mini
```

**Note:** The `OPENAI_API_KEY` is required. Get it from: https://platform.openai.com/api-keys

## Step 3: Deploy to Vercel

### Option A: Using Vercel CLI (Recommended)

```bash
# Login to Vercel
vercel login

# Deploy (follow prompts)
vercel

# For production deployment
vercel --prod
```

### Option B: Using GitHub Integration

1. Push your code to GitHub
2. Go to [vercel.com/new](https://vercel.com/new)
3. Import your GitHub repository
4. Vercel will auto-detect the Python settings

## Step 4: Configure Environment Variables in Vercel

1. Go to your project dashboard on Vercel
2. Navigate to **Settings** → **Environment Variables**
3. Add each environment variable:
   - `OPENAI_API_KEY` (required)
   - `FLASK_SECRET_KEY` (optional, for session security)
   - `OPENAI_EMBED_MODEL` (optional, defaults to text-embedding-3-large)
   - `OPENAI_CHAT_MODEL` (optional, defaults to gpt-4o-mini)
4. Make sure to add them for **Production**, **Preview**, and **Development** environments
5. Redeploy after adding environment variables

## Step 5: Verify Deployment

After deployment, Vercel will provide you with a URL like:
- `https://your-project-name.vercel.app`

Visit the URL and test:
1. Check `/api/health` endpoint - should return `{"status": "healthy"}`
2. Try asking a question through the web interface
3. Test both Knowledge Base and Marketing Council modes

## Important Notes

### ChromaDB Considerations

⚠️ **Important:** The current setup uses ChromaDB for vector storage. In serverless environments:

1. **Local ChromaDB won't work** - Each serverless function has its own isolated filesystem
2. **Options:**
   - Use ChromaDB Cloud (hosted service)
   - Use an external vector database (Pinecone, Weaviate, etc.)
   - Store vectors in a database that supports serverless (Supabase, etc.)

### Session Management

- Sessions are stateless in serverless (no persistent memory)
- Session IDs are generated per request if not provided
- Consider using Vercel Edge Config or external session storage for production

### Function Timeouts

- Hobby plan: 10 seconds max
- Pro plan: 60 seconds max (configured in `vercel.json`)
- AI responses may take longer - consider streaming responses or async processing

### Memory Limits

- Configured to 1024MB in `vercel.json`
- May need adjustment based on ChromaDB and model requirements

## Troubleshooting

### Build fails?

- Check that all dependencies are in `requirements.txt`
- Verify Python version (3.11 configured in `vercel.json`)
- Check build logs in Vercel dashboard

### Runtime errors?

- Verify environment variables are set correctly
- Check function logs in Vercel dashboard
- Ensure ChromaDB is accessible (if using hosted version)

### Static files not loading?

- Verify `vercel.json` routes are correct
- Check that files exist in `web/static/` directory
- Ensure file paths in template are correct

## Project Structure

```
.
├── api/
│   └── index.py          # Main serverless function
├── src/                   # Application source code
├── web/
│   ├── static/           # Static assets (CSS, JS)
│   └── templates/        # HTML templates
├── vercel.json           # Vercel configuration
├── requirements.txt      # Python dependencies
└── .vercelignore        # Files to exclude from deployment
```

## Next Steps

1. Set up ChromaDB Cloud or alternative vector database
2. Configure custom domain (optional)
3. Set up monitoring and analytics
4. Enable caching for better performance
5. Consider using Vercel Edge Functions for faster responses
