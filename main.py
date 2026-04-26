import os
import sys
import logging
import time
import threading
from flask import Flask

# Path fix: Python ko batao ki saari files isi folder mein hain
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Direct Imports (No try-except, taaki error saaf dikhe)
from utils import config
from core_logic.writer_engine import SmartWriter
from integrations.wordpress_api import WordPressClient

# --- RENDER SERVER ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Nexovent Bot: Online", 200

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')
logger = logging.getLogger("NexoventBot")

def run_bot():
    logger.info("Bot starting in 15 seconds...")
    time.sleep(15) 
    try:
        # Initialize components
        writer = SmartWriter(api_key=config.AI_API_KEY)
        wp = WordPressClient(
            wp_url=config.WP_URL,
            username=config.WP_USERNAME,
            password=config.WP_APP_PASSWORD
        )
        
        topic = "Future of Artificial Intelligence 2026"
        logger.info(f"Task: Writing about {topic}")
        
        # Action
        article = writer.generate_article(topic)
        
        # Body extraction logic
        if isinstance(article, dict):
            body = article.get('body', "")
            title = article.get('title', topic)
        else:
            body = article
            title = topic
            
        if body:
            post_id = wp.post_full_article(title=title, content=body, status="draft")
            logger.info(f"MISSION SUCCESS! Post ID: {post_id}")
        else:
            logger.error("AI returned empty content.")

    except Exception as e:
        logger.error(f"Bot Error: {str(e)}")

if __name__ == "__main__":
    # 1. Start Flask Server
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # 2. Run Bot
    run_bot()
    
    # 3. Keep process alive
    while True:
        time.sleep(3600)
