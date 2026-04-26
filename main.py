import os
import sys
import logging
import time
import threading
from flask import Flask

# --- PATH FIX (Sabse Zaruri) ---
# Ye line Python ko batati hai ki utils aur core_logic isi folder mein hain
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Ab direct import karo, bina try-except ke
from utils import config
from core_logic.writer_engine import SmartWriter
from integrations.wordpress_api import WordPressClient

# --- RENDER SERVER ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is Active and Running", 200

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')
logger = logging.getLogger("NexoventBot")

def run_bot():
    logger.info("Stabilizing server for 15 seconds...")
    time.sleep(15) 
    try:
        # Initialize components using imported classes
        writer = SmartWriter(api_key=config.AI_API_KEY)
        wp = WordPressClient(
            wp_url=config.WP_URL,
            username=config.WP_USERNAME,
            password=config.WP_APP_PASSWORD
        )
        
        topic = "Future of Artificial Intelligence 2026"
        logger.info(f"Generating content for: {topic}")
        
        # Article generation
        article = writer.generate_article(topic)
        
        # Handling different response types
        if isinstance(article, dict):
            body = article.get('body', "")
            title = article.get('title', topic)
        else:
            body = article
            title = topic
            
        if body:
            post_id = wp.post_full_article(title=title, content=body, status="draft")
            logger.info(f"SUCCESS! Article posted with ID: {post_id}")
        else:
            logger.error("AI returned empty body.")

    except Exception as e:
        logger.error(f"Bot Internal Error: {str(e)}")

if __name__ == "__main__":
    # 1. Server ko background mein chalao
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # 2. Main Bot logic chalao
    run_bot()
    
    # 3. Process ko zinda rakho
    while True:
        time.sleep(3600)
