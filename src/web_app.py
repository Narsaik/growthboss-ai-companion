"""
GrowthBoss Web Application - AI Companion Interface
Multi-user web interface for accessing the RAG system and Marketing Council.
"""

import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.researcher import ResearcherAgent
from src.agents.council import MarketingCouncil
from src.config import get_openai_api_key

# Get absolute paths for templates and static folders
template_dir = project_root / 'web' / 'templates'
static_dir = project_root / 'web' / 'static'

app = Flask(__name__, template_folder=str(template_dir), static_folder=str(static_dir))
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'growthboss-ai-companion-secret-key-change-in-production')
CORS(app)

# Initialize RAG system
COLLECTION_NAME = "growthboss-rag"
researcher = None
council = None

def init_agents():
    """Initialize RAG and Marketing Council agents."""
    global researcher, council
    try:
        researcher = ResearcherAgent(collection_name=COLLECTION_NAME, use_enhanced=True)
        council = MarketingCouncil(collection_name=COLLECTION_NAME)
        return True
    except RuntimeError as e:
        # RuntimeError typically means missing API key
        error_msg = str(e)
        print(f"❌ Configuration Error: {error_msg}")
        print("💡 Tip: Create a .env file in the project root with your API keys.")
        return False
    except Exception as e:
        error_type = type(e).__name__
        print(f"❌ Error initializing agents ({error_type}): {e}")
        print("💡 Check that:")
        print("   - OpenAI API key is set correctly")
        print("   - ChromaDB is accessible")
        print("   - Vector store collection exists")
        return False

# Don't initialize on import - will initialize on first request
# This prevents errors if RAG system isn't ready yet

@app.route('/')
def index():
    """Main chat interface - ChatGPT-like purple interface."""
    # Generate session ID if not exists
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    # Use the new ChatGPT-like interface with purple GrowthBoss branding
    return render_template('index_chatgpt.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages."""
    global researcher, council
    
    try:
        data = request.json
        message = data.get('message', '').strip()
        use_council = data.get('use_council', False)
        session_id = session.get('session_id', str(uuid.uuid4()))
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Initialize agents if not already done
        if researcher is None:
            if not init_agents():
                return jsonify({
                    'error': 'Failed to initialize AI system',
                    'message': 'Please check that OPENAI_API_KEY is set in your .env file or environment variables.'
                }), 500
        
        # Use Marketing Council if requested
        if use_council:
            if council is None:
                council = MarketingCouncil(collection_name=COLLECTION_NAME)
            
            response_text = council.ask(
                question=message,
                growthboss_context="GrowthBoss is a Toronto marketing agency offering website design, brand strategy, SEO, social/performance marketing, photography/videography, and recruitment services. We use the KLT (Know, Like, Trust) Ecosystem framework."
            )
            
            return jsonify({
                'response': response_text,
                'sources': [],
                'mentors': ['Gary Vee', 'Alex Hormozi', 'Iman Gadzhi'],
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id
            })
        
        # Use RAG system with session ID
        # Initialize researcher if needed
        if researcher is None:
            if not init_agents():
                return jsonify({
                    'error': 'Failed to initialize RAG system',
                    'message': 'Please check that OPENAI_API_KEY is set in your .env file or environment variables.'
                }), 500
        
        # Create new researcher instance with session ID if session changed or memory doesn't exist
        if researcher is not None:
            needs_new_instance = False
            if not hasattr(researcher, 'memory'):
                needs_new_instance = True
            elif hasattr(researcher.memory, 'session_id') and researcher.memory.session_id != session_id:
                needs_new_instance = True
            
            if needs_new_instance:
                researcher = ResearcherAgent(collection_name=COLLECTION_NAME, use_enhanced=True, session_id=session_id)
        
        result = researcher.research(message, k=12, include_context=True)
        
        # Extract sources from evidence
        sources = []
        if result.get('evidence'):
            for ctx in result.get('evidence', [])[:5]:  # Top 5 sources
                meta = ctx.get('metadata', {})
                sources.append({
                    'title': meta.get('title') or meta.get('source', 'Unknown'),
                    'domain': meta.get('domain', 'Unknown')
                })
        
        return jsonify({
            'response': result.get('answer', 'I apologize, but I could not generate a response.'),
            'sources': sources,
            'context_used': len(result.get('evidence', [])),
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id
        })
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    try:
        # Check if agents are initialized
        if researcher is None:
            init_agents()
        
        return jsonify({
            'status': 'healthy',
            'rag_initialized': researcher is not None,
            'council_initialized': council is not None,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/session', methods=['GET'])
def get_session():
    """Get current session ID."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return jsonify({'session_id': session.get('session_id')})

if __name__ == '__main__':
    print("=" * 70)
    print("GrowthBoss AI Companion - Starting Web Server")
    print("=" * 70)
    
    # Initialize agents
    if init_agents():
        print("✅ RAG system initialized")
        print("✅ Marketing Council initialized")
    else:
        print("⚠️  Warning: Some systems may not be initialized")
    
    print("\n🌐 Starting web server...")
    
    # Production settings
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('PORT', os.getenv('FLASK_PORT', '5000')))
    
    print(f"📍 Debug mode: {debug_mode}")
    print(f"📍 Host: {host}")
    print(f"📍 Port: {port}")
    print(f"📍 Access at: http://localhost:{port}")
    print(f"💡 Production URL: https://narsaik.com")
    print("\n" + "=" * 70)
    
    app.run(debug=debug_mode, host=host, port=port)
