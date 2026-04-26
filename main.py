import os
import sys
import os
import sys
import logging
import time
import threading
from flask import Flask

# Modular components
from utils import config
from core_logic.writer_engine import SmartWriter
from integrations.wordpress_api import WordPressClient

# --- RENDER PORT BINDING FIX ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is Active", 200

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    # Render ke liye debug=False aur use_reloader=False rakhen
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ------------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("NexoventBot")

def run_bot():
    time.sleep(15) # Server ko settle hone ka samay den
    logger.info("Automation process started...")
    try:
        writer = SmartWriter(api_key=config.AI_API_KEY)
        wp = WordPressClient(
            wp_url=config.WP_URL,
            username=config.WP_USERNAME,
            password=config.WP_APP_PASSWORD
        )
        
        topic = "Future of Artificial Intelligence 2026"
        article = writer.generate_article(topic)
        
        body = article.get('body', "") if isinstance(article, dict) else article
        
        if body:
            post_id = wp.post_full_article(title=topic, content=body, status="draft")
            logger.info(f"SUCCESS! Posted with ID: {post_id}")
    except Exception as e:
        logger.error(f"Bot execution error: {e}")

if __name__ == "__main__":
    # 1. Start Server in thread
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # 2. Run Bot
    run_bot()
    
    # 3. Stay alive
    while True:
        time.sleep(3600)
