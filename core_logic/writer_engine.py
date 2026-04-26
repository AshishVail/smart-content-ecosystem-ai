import os
import sys
import logging
import time
import threading
from flask import Flask

# --- RENDER WEB SERVER (Isse Render ko signal milta rahega) ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Nexovent Bot is LIVE", 200

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')
logger = logging.getLogger("NexoventBot")

def run_bot():
    logger.info("Bot logic starting in 10 seconds...")
    time.sleep(10) 
    
    try:
        # CIRCULAR IMPORT FIX: Hum function ke andar import kar rahe hain
        from utils.config import AI_API_KEY, WP_URL, WP_USERNAME, WP_APP_PASSWORD
        from core_logic.writer_engine import SmartWriter
        from integrations.wordpress_api import WordPressClient
        
        # Initialize
        writer = SmartWriter(api_key=AI_API_KEY)
        wp = WordPressClient(wp_url=WP_URL, username=WP_USERNAME, password=WP_APP_PASSWORD)
        
        topic = "Future of Artificial Intelligence 2026"
        logger.info(f"Generating content for: {topic}")
        
        article = writer.generate_article(topic)
        
        # Content check
        body = article.get('body', "") if isinstance(article, dict) else article
        title = article.get('title', topic) if isinstance(article, dict) else topic
            
        if body:
            logger.info("Sending to earnguide.in...")
            post_id = wp.post_full_article(title=title, content=body, status="draft")
            logger.info(f"SUCCESS! Article ID: {post_id}")
        else:
            logger.error("AI returned no content.")

    except Exception as e:
        logger.error(f"Logic Error: {str(e)}")

if __name__ == "__main__":
    # 1. Start Flask Server (Render ke liye compulsory)
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # 2. Start Bot
    run_bot()
    
    # 3. Stay Alive
    while True:
        time.sleep(3600)
