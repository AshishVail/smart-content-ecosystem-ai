import os
import sys
import logging
import time
import threading
from flask import Flask

# --- PATH FIXING (The Ultimate Solution) ---
# Ye hissa Python ko majboor karega ki wo folders ko pehchane
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'utils'))
sys.path.insert(0, os.path.join(BASE_DIR, 'core_logic'))

# Flask Server Setup
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Nexovent Bot: Active and Live", 200

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')
logger = logging.getLogger("NexoventBot")

def run_bot():
    logger.info("Bot waking up in 15 seconds...")
    time.sleep(15)
    
    try:
        # Dynamic Import: Ye imports ab fail nahi honge
        try:
            from utils import config
            from core_logic.writer_engine import SmartWriter
            from integrations.wordpress_api import WordPressClient
        except ImportError:
            import config
            from writer_engine import SmartWriter
            from wordpress_api import WordPressClient

        # Components initialization
        writer = SmartWriter(api_key=config.AI_API_KEY)
        wp = WordPressClient(
            wp_url=config.WP_URL, 
            username=config.WP_USERNAME, 
            password=config.WP_APP_PASSWORD
        )
        
        topic = "Future of Artificial Intelligence 2026"
        logger.info(f"Bot Action: Writing article on {topic}")
        
        # Generation Logic
        article = writer.generate_article(topic)
        
        # Checking content
        if isinstance(article, dict):
            body = article.get('body', "")
            title = article.get('title', topic)
        else:
            body = article
            title = topic
            
        if body:
            logger.info("Posting to WordPress...")
            post_id = wp.post_full_article(title=title, content=body, status="draft")
            logger.info(f"MISSION SUCCESS! Post ID: {post_id}")
        else:
            logger.error("AI failed to generate content.")

    except Exception as e:
        logger.error(f"Bot Logic Error: {str(e)}")

if __name__ == "__main__":
    # 1. Start Server in background
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # 2. Run Bot logic
    run_bot()
    
    # 3. Keep process alive
    while True:
        time.sleep(3600)
