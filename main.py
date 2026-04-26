import os
import sys
import logging
import time
import threading
from flask import Flask
from typing import List, Optional, Dict, Any

# Modular components
from utils import config
from core_logic.writer_engine import SmartWriter
from core_logic.seo_analyzer import SEOAnalyzer
from media_manager.image_creator import SmartMediaEngine
from integrations.wordpress_api import WordPressClient

# --- RENDER PORT BINDING FIX ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Ecosystem Controller is Active", 200

def run_health_server():
    # Force Render to see the port immediately
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
# ------------------------------

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("SmartEcosystem.Controller")

class EcosystemController:
    def __init__(self):
        self.writer = SmartWriter(api_key=config.AI_API_KEY)
        self.seo_analyzer = None
        self.media_engine = SmartMediaEngine({
            "brand_name": config.BRAND_NAME,
            "output_path": config.OUTPUT_IMAGE_DIR
        })
        self.wp_client = WordPressClient(
            wp_url=config.WP_URL,
            username=config.WP_USERNAME,
            password=config.WP_APP_PASSWORD
        )

    def execute_workflow(self, primary_keyword: str, secondary_keywords: Optional[List[str]] = None):
        start_time = time.time()
        logger.info(f"Starting workflow for: '{primary_keyword}'")

        try:
            if not self.wp_client.verify_connection():
                logger.error("WordPress authentication failed.")
                return

            logger.info("Step 1/4: Generating Content...")
            article_data = self.writer.generate_article(primary_keyword)
            
            if isinstance(article_data, dict):
                article_body = article_data.get('body', "")
                article_title = article_data.get('title', primary_keyword.title())
            else:
                article_body = article_data
                article_title = primary_keyword.title()

            if not article_body: 
                logger.error("Content generation failed.")
                return

            logger.info("Step 2/4: SEO Audit...")
            seo_report = {}
            try:
                self.seo_analyzer = SEOAnalyzer(
                    content=article_body,
                    primary_keyword=primary_keyword,
                    secondary_keywords=secondary_keywords
                )
                seo_report = self.seo_analyzer.analyze() or {}
            except Exception as e:
                logger.warning(f"SEO Audit failed: {e}")
            
            logger.info("Step 3/4: Creating Image...")
            image_path = None
            try:
                image_result = self.media_engine.generate_image_sync(primary_keyword)
                if image_result and image_result.get("status") == "success":
                    image_path = image_result.get("path")
            except Exception as e:
                logger.warning(f"Image creation failed: {e}")

            logger.info("Step 4/4: Posting to WordPress...")
            meta_desc = seo_report.get('meta_description', f"New update on {primary_keyword}")
            
            post_id = self.wp_client.post_full_article(
                title=article_title,
                content=article_body,
                image_path=image_path,
                status="draft",
                categories=[],
                tags=[primary_keyword] + (secondary_keywords or []),
                meta_title=article_title,
                meta_description=meta_desc,
                seo_plugin=config.SEO_PLUGIN
            )

            if post_id:
                logger.info(f"SUCCESS: Article posted with ID {post_id}")
            
        except Exception as e:
            logger.critical(f"System Failure: {str(e)}", exc_info=True)

if __name__ == "__main__":
    # 1. Start Flask server FIRST in a thread
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # 2. Give the server a moment to bind to the port
    time.sleep(5)
    
    # 3. Now run your bot logic
    controller = EcosystemController()
    main_keyword = "Future of Artificial Intelligence 2026"
    related_keywords = ["AI trends", "Automation"]
    
    controller.execute_workflow(main_keyword, secondary_keywords=related_keywords)
    
    # Keep the process alive for Render
    while True:
        time.sleep(3600)
