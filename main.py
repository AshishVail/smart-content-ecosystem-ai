import os
import sys
import logging
import time
import threading
from flask import Flask

# Path configuration for Render
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from utils import config
    from core_logic.writer_engine import SmartWriter
    from integrations.wordpress_api import WordPressClient
except ImportError as e:
    print(f"Import Error: {e}")

# --- RENDER PORT BINDING ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Nexovent Bot is Running", 200

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')
logger = logging.getLogger("NexoventBot")

def run_bot():
    logger.info("Stabilizing server...")
    time.sleep(20) 
    try:
        writer = SmartWriter(api_key=config.AI_API_KEY)
        wp = WordPressClient(
            wp_url=config.WP_URL,
            username=config.WP_USERNAME,
            password=config.WP_APP_PASSWORD
        )
        
        topic = "Future of Artificial Intelligence 2026"
        logger.info(f"Writing article: {topic}")
        
        article = writer.generate_article(topic)
        body = article.get('body', "") if isinstance(article, dict) else article
        
        if body:
            post_id = wp.post_full_article(title=topic, content=body, status="draft")
            logger.info(f"DONE! Article ID: {post_id}")
    except Exception as e:
        logger.error(f"Bot Error: {e}")

if __name__ == "__main__":
    # 1. Start Server
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # 2. Run Automation
    run_bot()
    
    # 3. Stay Alive
    while True:
        time.sleep(3600)
