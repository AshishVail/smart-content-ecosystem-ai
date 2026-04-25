import os
import logging
from flask import Flask, request, jsonify
from src.core_logic.writer_engine import SmartWriter

# Setup professional logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MainApp")

app = Flask(__name__)

# Initialize the engine
# Note: Ensure GROQ_API_KEY is set in Render Environment Variables
writer_engine = SmartWriter()

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "active", "message": "Smart Content Ecosystem is Live"}), 200

@app.route('/generate', methods=['POST'])
def generate_content():
    data = request.get_json()
    
    if not data or 'keyword' not in data:
        return jsonify({"error": "Missing 'keyword' in request body"}), 400
    
    keyword = data.get('keyword')
    tone = data.get('tone', 'professional')
    
    logger.info(f"Received request to generate article for: {keyword}")
    
    try:
        # Calling the clean generate_article method from our new engine
        result = writer_engine.generate_article(keyword=keyword, tone=tone)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        return jsonify({"error": "An internal error occurred during generation"}), 500

if __name__ == "__main__":
    # Render requires binding to 0.0.0.0 and using the PORT environment variable
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
