import os
import sys
import logging
import time
import threading
from flask import Flask

# --- PATH FIX (Isse 'utils' mil jayega) ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Ab imports try karo
try:
    from utils import config
    from core_logic.writer_engine import SmartWriter
    from integrations.wordpress_api import WordPressClient
except Exception as e:
    print(f"Import error fix attempt: {e}")

# --- RENDER SERVER ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Nexovent Bot is LIVE", 200

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')
logger = logging.getLogger("NexoventBot")

def run_bot():
    logger.info("Bot starting in 10s...")
    time.sleep(10)
    try:
        # Direct use from config
        writer = SmartWriter(api_key=config.AI_API_KEY)
        wp = WordPressClient(
            wp_url=config.WP_URL, 
            username=config.WP_USERNAME, 
            password=config.WP_APP_PASSWORD
        )
        
        topic = "Future of Artificial Intelligence 2026"
        logger.info(f"Working on: {topic}")
        
        article = writer.generate_article(topic)
        body = article.get('body', "") if isinstance(article, dict) else article
        
        if body:
            post_id = wp.post_full_article(title=topic, content=body, status="draft")
            logger.info(f"DONE! Article ID: {post_id}")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    run_bot()
    while True:
        time.sleep(3600)
