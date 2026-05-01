import os
import sys
import logging
import time
import threading
from flask import Flask

# --- PATH FIXING ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'utils'))
sys.path.insert(0, os.path.join(BASE_DIR, 'core_logic'))

app = Flask(__name__)

@app.route('/')
def health_check():
    return "Nexovent Bot: Active and Live", 200

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')
logger = logging.getLogger("NexoventBot")

def run_bot():
    logger.info("Bot waking up in 15 seconds...")
    time.sleep(15)
    
    try:
        try:
            from utils import config
            from core_logic.writer_engine import SmartWriter
            from integrations.wordpress_api import WordPressClient
        except ImportError:
            import config
            from writer_engine import SmartWriter
            from wordpress_api import WordPressClient

        # Initialization
        writer = SmartWriter(api_key=config.GROQ_API_KEY)
        wp = WordPressClient(
            wp_url=config.WP_URL, 
            username=config.WP_USERNAME, 
            password=config.WP_APP_PASSWORD
        )
        
        # --- CHANGES HERE ---
        topic = "Future of Artificial Intelligence 2026"
        focus_keyword = "Artificial Intelligence" # Naya keyword variable
        
        logger.info(f"Bot Action: Writing article on {topic} with keyword {focus_keyword}")
        
        # Generation Logic (Ab hum dono cheezein bhej rahe hain)
        article = writer.generate_article(topic=topic, keyword=focus_keyword)
        
        if isinstance(article, dict) and article.get('status') == "success":
            body = article.get('body', "")
            title = article.get('title', topic)
            
            if body:
                logger.info("Posting to WordPress...")
                # Status ko 'publish' kar de taaki site par turant dikhe
                post_id = wp.post_full_article(title=title, content=body, status="publish")
                logger.info(f"MISSION SUCCESS! Post ID: {post_id}")
            else:
                logger.error("AI generated empty body.")
        else:
            error_msg = article.get('body') if isinstance(article, dict) else "Unknown Error"
            logger.error(f"AI failed to generate content: {error_msg}")

    except Exception as e:
        logger.error(f"Bot Logic Error: {str(e)}")

if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    run_bot()
    while True:
        time.sleep(3600)
