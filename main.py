import os
import sys
import logging
import time
import threading
from flask import Flask

# Modular components
try:
    from utils import config
    from core_logic.writer_engine import SmartWriter
    from integrations.wordpress_api import WordPressClient
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from utils import config
    from core_logic.writer_engine import SmartWriter
    from integrations.wordpress_api import WordPressClient

# --- RENDER PORT BINDING FIX ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Nexovent Bot is Active", 200

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("NexoventBot")

def run_bot():
    logger.info("Waiting for server to stabilize...")
    time.sleep(15) 
    
    logger.info("Automation workflow initiated...")
    try:
        writer = SmartWriter(api_key=config.AI_API_KEY)
        wp = WordPressClient(
            wp_url=config.WP_URL,
            username=config.WP_USERNAME,
            password=config.WP_APP_PASSWORD
        )
        
        topic = "Future of Artificial Intelligence 2026"
        logger.info(f"Generating article for: {topic}")
        
        article = writer.generate_article(topic)
        
        if isinstance(article, dict):
            body = article.get('body', "")
            title = article.get('title', topic)
        else:
            body = article
            title = topic
        
        if body:
            post_id = wp.post_full_article(title=title, content=body, status="draft")
            if post_id:
                logger.info(f"SUCCESS! Article posted with ID: {post_id}")
    except Exception as e:
        logger.error(f"Bot execution error: {str(e)}")

if __name__ == "__main__":
    # 1. Start Flask Server
    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()
    
    # 2. Run Bot
    run_bot()
    
    # 3. Stay Alive
    while True:
        time.sleep(3600)
