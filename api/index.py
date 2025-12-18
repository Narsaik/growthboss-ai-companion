from flask import Flask, request, jsonify, Response
import os
import json
import uuid
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

# Project root
project_root = Path(__file__).parent.parent


def get_openai_client():
    """Get OpenAI client if API key is available."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None, "OPENAI_API_KEY not set. Configure in Vercel Dashboard > Settings > Environment Variables"
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        return client, None
    except Exception as e:
        return None, f"OpenAI init error: {str(e)}"


def chat_with_openai(client, message: str, use_council: bool = False) -> str:
    """Chat using OpenAI directly."""
    
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
        return f"Error: {str(e)}"


@app.route("/")
def index():
    """Serve the main page."""
    template_path = project_root / "web" / "templates" / "index_chatgpt.html"
    
    if not template_path.exists():
        return "<h1>GrowthBoss AI - Template not found</h1>", 404
    
    with open(template_path, "r", encoding="utf-8") as f:
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
    
    return Response(html, mimetype="text/html")


@app.route("/static/<path:filename>")
def static_files(filename):
    """Serve static files."""
    file_path = project_root / "web" / "static" / filename
    
    if not file_path.exists():
        return "Not found", 404
    
    # Determine content type
    suffix = file_path.suffix.lower()
    content_types = {
        ".css": "text/css",
        ".js": "application/javascript",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml",
    }
    content_type = content_types.get(suffix, "application/octet-stream")
    
    with open(file_path, "rb") as f:
        content = f.read()
    
    return Response(content, mimetype=content_type)


@app.route("/api/health")
def health():
    """Health check endpoint."""
    client, error = get_openai_client()
    return jsonify({
        "status": "healthy" if client else "error",
        "openai_configured": client is not None,
        "error": error,
        "timestamp": datetime.now().isoformat()
    })


@app.route("/api/session")
def session():
    """Get session ID."""
    return jsonify({"session_id": str(uuid.uuid4())})


@app.route("/api/chat", methods=["POST"])
def chat():
    """Chat endpoint."""
    try:
        data = request.get_json() or {}
        message = data.get("message", "").strip()
        use_council = data.get("use_council", False)
        session_id = data.get("session_id") or str(uuid.uuid4())
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        client, error = get_openai_client()
        if error:
            return jsonify({
                "error": "AI system not configured",
                "message": error
            }), 500
        
        response_text = chat_with_openai(client, message, use_council)
        
        result = {
            "response": response_text,
            "sources": [],
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        }
        
        if use_council:
            result["mentors"] = ["Gary Vee", "Alex Hormozi", "Iman Gadzhi"]
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# This is required for Vercel
if __name__ == "__main__":
    app.run()
