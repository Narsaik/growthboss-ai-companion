"""
Vercel Serverless Function for GrowthBoss AI Companion
Simplified version that works without ChromaDB.
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


def get_openai_client():
    """Get OpenAI client if API key is available."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None, "OPENAI_API_KEY not set. Please configure it in Vercel environment variables."
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        return client, None
    except Exception as e:
        return None, f"Error initializing OpenAI: {str(e)}"


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


def chat_with_openai(client, message: str, use_council: bool = False) -> str:
    """Simple chat using OpenAI directly (no RAG)."""
    
    if use_council:
        system_prompt = """You are a Marketing Council for GrowthBoss, a Toronto marketing agency.
You channel the wisdom of marketing experts like Gary Vaynerchuk, Alex Hormozi, and Iman Gadzhi.

GrowthBoss offers:
- Website design and development
- Brand strategy and identity design
- SEO optimization
- Social media and performance marketing
- Photography and videography
- Recruitment and talent acquisition

Use the KLT (Know, Like, Trust) Ecosystem framework in your recommendations.
Provide actionable, practical advice combining insights from all three mentors."""
    else:
        system_prompt = """You are the GrowthBoss AI Companion, a helpful assistant for GrowthBoss marketing agency.

GrowthBoss is a Toronto-based marketing agency offering:
- Website design and development
- Brand strategy and identity design
- SEO optimization
- Social media and performance marketing
- Photography and videography
- Recruitment and talent acquisition

We use the KLT (Know, Like, Trust) Ecosystem framework.
Provide helpful, professional responses about marketing, business growth, and GrowthBoss services."""

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {str(e)}"


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler."""
    
    def do_GET(self):
        """Handle GET requests."""
        path = self.path.split('?')[0]
        
        # Handle static files
        if path.startswith('/static/'):
            try:
                static_path = path.replace('/static/', '')
                file_path = project_root / 'web' / 'static' / static_path
                if file_path.exists() and file_path.is_file():
                    if file_path.suffix == '.css':
                        content_type = 'text/css'
                    elif file_path.suffix == '.js':
                        content_type = 'application/javascript'
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
            except Exception:
                pass
        
        if path == '/' or path == '':
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
            
        elif path == '/api/health':
            client, error = get_openai_client()
            response = {
                'status': 'healthy' if client else 'error',
                'openai_configured': client is not None,
                'error': error,
                'timestamp': datetime.now().isoformat(),
                'note': 'RAG disabled - using direct OpenAI chat'
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        elif path == '/api/session':
            response = {'session_id': str(uuid.uuid4())}
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        else:
            try:
                html = serve_template()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
            except Exception as e:
                self.send_response(404)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<h1>Not Found</h1>')
    
    def do_POST(self):
        """Handle POST requests."""
        path = self.path.split('?')[0]
        
        if path == '/api/chat':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(body)
                
                message = data.get('message', '').strip()
                use_council = data.get('use_council', False)
                session_id = data.get('session_id') or str(uuid.uuid4())
                
                if not message:
                    response = {'error': 'Message is required'}
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                
                # Get OpenAI client
                client, error = get_openai_client()
                if error:
                    response = {
                        'error': 'Failed to initialize AI system',
                        'message': error
                    }
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                
                # Generate response
                response_text = chat_with_openai(client, message, use_council)
                
                response = {
                    'response': response_text,
                    'sources': [],
                    'timestamp': datetime.now().isoformat(),
                    'session_id': session_id
                }
                
                if use_council:
                    response['mentors'] = ['Gary Vee', 'Alex Hormozi', 'Iman Gadzhi']
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                response = {'error': str(e)}
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            response = {'error': 'Not found'}
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Session-Id')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass
