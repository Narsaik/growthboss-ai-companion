# GrowthBoss AI Companion

AI-powered companion application for GrowthBoss marketing agency, featuring RAG (Retrieval-Augmented Generation) and Marketing Council capabilities.

## Features

- **Knowledge Base (RAG)**: Query your business knowledge base with AI-powered search
- **Marketing Council**: Get strategic advice from AI mentors (Gary Vee, Alex Hormozi, Iman Gadzhi)
- **Web Interface**: Beautiful ChatGPT-like interface
- **Vercel Deployment**: Ready for serverless deployment

## Quick Start

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
# Create .env file
OPENAI_API_KEY=your-api-key-here
```

3. Run the web application:
```bash
python scripts/start_web_app.py
```

4. Access at: http://localhost:5000

### Deploy to Vercel

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

Quick deploy:
```bash
vercel login
vercel --prod
```

## Project Structure

```
.
├── api/              # Vercel serverless functions
├── src/              # Application source code
│   ├── agents/      # AI agents (Researcher, Council, etc.)
│   ├── rag/         # RAG system (vector store, retrieval)
│   ├── memory/      # Conversation memory
│   └── web_app.py   # Flask web application
├── web/             # Frontend (templates, static files)
├── scripts/         # Utility scripts
└── requirements.txt  # Python dependencies
```

## Environment Variables

- `OPENAI_API_KEY` (required): Your OpenAI API key
- `OPENAI_EMBED_MODEL`: Embedding model (default: text-embedding-3-large)
- `OPENAI_CHAT_MODEL`: Chat model (default: gpt-4o-mini)
- `FLASK_SECRET_KEY`: Secret key for Flask sessions

## License

Private - GrowthBoss Internal Use
