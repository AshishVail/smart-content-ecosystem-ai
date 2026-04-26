import os
import sys
import logging
import time
import threading
from flask import Flask

# --- PATH FIX ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# --- IMPORTS (Sahi tareeke se) ---
try:
    from utils import config
    from core_logic.writer_engine import SmartWriter
    from integrations.wordpress_api import WordPressClient
except ImportError as e:
    print(f"Crucial Import Error: {e}")

# --- RENDER SERVER ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Nexovent Bot is Active", 200

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')
logger = logging.getLogger("NexoventBot")

def run_bot():
    logger.info("Bot logic starting in 20 seconds...")
    time.sleep(20) 
    try:
        # Check if config is loaded
        if 'config' not in globals() and 'config' not in locals():
            from utils import config

        # Initialize
        writer = SmartWriter(api_key=config.AI_API_KEY)
        wp = WordPressClient(
            wp_url=config.WP_URL,
            username=config.WP_USERNAME,
            password=config.WP_APP_PASSWORD
        )
        
        topic = "Future of Artificial Intelligence 2026"
        logger.info(f"Working on topic: {topic}")
        
        article = writer.generate_article(topic)
        
        if isinstance(article, dict):
            body = article.get('body', "")
            title = article.get('title', topic)
        else:
            body = article
            title = topic
            
        if body:
            logger.info("Posting to WordPress...")
            post_id = wp.post_full_article(title=title, content=body, status="draft")
            if post_id:
                logger.info(f"SUCCESS! Article ID: {post_id}")
        else:
            logger.error("AI returned empty content.")

    except Exception as e:
        logger.error(f"Bot Internal Error: {str(e)}")

if __name__ == "__main__":
    # 1. Start Server
    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()
    
    # 2. Run Bot
    run_bot()
    
    # 3. Stay Alive
    while True:
        time.sleep(3600)
