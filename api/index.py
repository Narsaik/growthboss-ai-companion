"""
Vercel Serverless Function for GrowthBoss AI Companion
Handles all routes for the web application.
"""

import os
import sys
import json
import uuid
from datetime import datetime
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import agents
from src.agents.researcher import ResearcherAgent
from src.agents.council import MarketingCouncil
from src.config import get_openai_api_key

COLLECTION_NAME = "growthboss-rag"


def get_agents():
    """Initialize and return agent instances."""
    try:
        # Note: ChromaDB won't work in serverless - each function has isolated filesystem
        # This will fail unless using ChromaDB Cloud or external vector DB
        researcher = ResearcherAgent(collection_name=COLLECTION_NAME, use_enhanced=True)
        council = MarketingCouncil(collection_name=COLLECTION_NAME)
        return researcher, council, None
    except RuntimeError as e:
        error_msg = str(e)
        if "OPENAI_API_KEY" in error_msg:
            return None, None, "OPENAI_API_KEY not set. Please configure it in Vercel environment variables."
        return None, None, error_msg
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        # Check for ChromaDB errors
        if "chroma" in error_msg.lower() or "chromadb" in error_msg.lower():
            return None, None, "ChromaDB error: Local ChromaDB doesn't work in serverless. Use ChromaDB Cloud or external vector database."
        return None, None, f"Error initializing agents ({error_type}): {error_msg}"


def serve_template():
    """Serve the main HTML page."""
    template_path = project_root / 'web' / 'templates' / 'index_chatgpt.html'
    
    if not template_path.exists():
        return '<h1>Template not found</h1>'
    
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Replace Flask url_for with static paths
    html = html.replace(
        "{{ url_for('static', filename='css/chatgpt_style.css') }}",
        "/static/css/chatgpt_style.css"
    )
    html = html.replace(
        "{{ url_for('static', filename='js/chatgpt_chat.js') }}",
        "/static/js/chatgpt_chat.js"
    )
    
    return html


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler."""
    
    def do_GET(self):
        """Handle GET requests."""
        # Get path without query string
        path = self.path.split('?')[0]
        
        # Handle static files (fallback if routing doesn't work)
        if path.startswith('/static/'):
            try:
                static_path = path.replace('/static/', '')
                file_path = project_root / 'web' / 'static' / static_path
                if file_path.exists() and file_path.is_file():
                    # Determine content type
                    if file_path.suffix == '.css':
                        content_type = 'text/css'
                    elif file_path.suffix == '.js':
                        content_type = 'application/javascript'
                    elif file_path.suffix == '.png':
                        content_type = 'image/png'
                    elif file_path.suffix == '.jpg' or file_path.suffix == '.jpeg':
                        content_type = 'image/jpeg'
                    else:
                        content_type = 'application/octet-stream'
                    
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    self.send_response(200)
                    self.send_header('Content-Type', content_type)
                    self.send_header('Cache-Control', 'public, max-age=31536000')
                    self.end_headers()
                    self.wfile.write(content)
                    return
            except Exception as e:
                pass  # Fall through to 404
        
        if path == '/' or path == '':
            # Serve main page
            try:
                html = serve_template()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Cache-Control', 'public, max-age=3600')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(f'<h1>Error loading template: {str(e)}</h1>'.encode('utf-8'))
            
        elif path == '/api/health':
            # Health check
            try:
                researcher, council, error = get_agents()
                response = {
                    'status': 'healthy' if not error else 'error',
                    'rag_initialized': researcher is not None,
                    'council_initialized': council is not None,
                    'error': error if error else None,
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as e:
                response = {
                    'status': 'error',
                    'error': str(e)
                }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        elif path == '/api/session':
            # Get or create session ID
            session_id = str(uuid.uuid4())
            response = {'session_id': session_id}
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        else:
            # Default to index for SPA routing
            try:
                html = serve_template()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(f'<h1>Error: {str(e)}</h1>'.encode('utf-8'))
    
    def do_POST(self):
        """Handle POST requests."""
        path = self.path.split('?')[0]
        
        if path == '/api/chat':
            # Handle chat API
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(body)
                
                message = data.get('message', '').strip()
                use_council = data.get('use_council', False)
                session_id = data.get('session_id') or self.headers.get('X-Session-Id')
                
                if not message:
                    response = {'error': 'Message is required'}
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                
                # Initialize agents
                researcher, council, error = get_agents()
                if error:
                    response = {
                        'error': 'Failed to initialize AI system',
                        'message': error,
                        'hint': 'Check Vercel environment variables and ChromaDB configuration'
                    }
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                
                # Use Marketing Council if requested
                if use_council:
                    response_text = council.ask(
                        question=message,
                        growthboss_context="GrowthBoss is a Toronto marketing agency offering website design, brand strategy, SEO, social/performance marketing, photography/videography, and recruitment services. We use the KLT (Know, Like, Trust) Ecosystem framework."
                    )
                    
                    response = {
                        'response': response_text,
                        'sources': [],
                        'mentors': ['Gary Vee', 'Alex Hormozi', 'Iman Gadzhi'],
                        'timestamp': datetime.now().isoformat(),
                        'session_id': session_id or str(uuid.uuid4())
                    }
                else:
                    # Use RAG system
                    if not session_id:
                        session_id = str(uuid.uuid4())
                    
                    # Create researcher with session ID
                    researcher = ResearcherAgent(
                        collection_name=COLLECTION_NAME,
                        use_enhanced=True,
                        session_id=session_id
                    )
                    
                    result = researcher.research(message, k=12, include_context=True)
                    
                    # Extract sources
                    sources = []
                    if result.get('evidence'):
                        for ctx in result.get('evidence', [])[:5]:
                            meta = ctx.get('metadata', {})
                            sources.append({
                                'title': meta.get('title') or meta.get('source', 'Unknown'),
                                'domain': meta.get('domain', 'Unknown')
                            })
                    
                    response = {
                        'response': result.get('answer', 'I apologize, but I could not generate a response.'),
                        'sources': sources,
                        'context_used': len(result.get('evidence', [])),
                        'timestamp': datetime.now().isoformat(),
                        'session_id': session_id
                    }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                response = {
                    'error': str(e),
                    'type': type(e).__name__,
                    'traceback': error_trace if os.getenv('VERCEL_ENV') == 'development' else None
                }
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            # Not found
            response = {'error': 'Not found'}
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass
