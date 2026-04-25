import os
import sys
import logging
from flask import Flask, request, jsonify

# Setup professional logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MainApp")

# Adding current directory to path to ensure core_logic is found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Correct import based on your folder structure (No 'src' prefix)
try:
    from core_logic.writer_engine import SmartWriter
    logger.info("SmartWriter imported successfully from core_logic.")
except ImportError as e:
    logger.error(f"Import Error: {str(e)}")
    # Fallback to absolute path if needed
    sys.path.append(os.getcwd())
    from core_logic.writer_engine import SmartWriter

app = Flask(__name__)

# Initialize the engine
try:
    writer_engine = SmartWriter()
except Exception as e:
    logger.error(f"Failed to initialize SmartWriter engine: {e}")
    writer_engine = None

@app.route('/', methods=['GET'])
def health_check():
    """Endpoint to check if the server is running."""
    return jsonify({
        "status": "active",
        "message": "AI Content System is Live and Ready",
        "engine_loaded": writer_engine is not None
    }), 200

@app.route('/generate', methods=['POST'])
def generate_content():
    """Endpoint to trigger article generation."""
    if not writer_engine:
        return jsonify({"error": "Writer engine is not initialized. Check logs."}), 500

    data = request.get_json()
    if not data or 'keyword' not in data:
        return jsonify({"error": "Missing 'keyword' in request body"}), 400
    
    keyword = data.get('keyword')
    tone = data.get('tone', 'professional')
    
    logger.info(f"Generating content for keyword: {keyword}")
    
    try:
        result = writer_engine.generate_article(keyword=keyword, tone=tone)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Generation process failed: {str(e)}")
        return jsonify({"error": "Internal processing error occurred"}), 500

if __name__ == "__main__":
    # Binding to 0.0.0.0 and dynamic port is mandatory for Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
