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
# Flask server ko sabse pehle start karenge taaki Render ko signal mil jaye
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Ecosystem Controller is Active", 200

def run_health_server():
    try:
        port = int(os.environ.get("PORT", 10000))
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Server Error: {e}")
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
            
            # Smart parsing to handle dict or string response
            if isinstance(article_data, dict):
                article_body = article_data.get('body', "")
                article_title = article_data.get('title', primary_keyword.title())
            else:
                article_body = article_data
                article_title = primary_keyword.title()

            if not article_body: 
                logger.error("Content generation failed. Body is empty.")
                return

            logger.info("Step 2/4: SEO Audit...")
            seo_report = {}
            try:
                self.seo_analyzer = SEOAnalyzer(
                    content=article_body,
                    primary_keyword=primary_keyword,
                    secondary_keywords=secondary_keywords
                )
                seo_report = self.seo_analyzer.analyze()
                # Ensure seo_report is a dictionary to prevent 'NoneType' errors
                if seo_report is None:
                    seo_report = {}
            except Exception as e:
                logger.warning(f"SEO Audit failed, using defaults: {e}")
                seo_report = {}
            
            logger.info("Step 3/4: Creating Image...")
            image_path = None
            try:
                image_result = self.media_engine.generate_image_sync(primary_keyword)
                if image_result and image_result.get("status") == "success":
                    image_path = image_result.get("path")
            except Exception as e:
                logger.warning(f"Image creation failed: {e}")

            logger.info("Step 4/4: Posting to WordPress...")
            
            # FIXED: Added safety check to prevent Attribute Error for meta_description
            meta_desc = "Professional article about " + primary_keyword
            if isinstance(seo_report, dict):
                meta_desc = seo_report.get('meta_description', meta_desc)
            
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
            
            logger.info(f"Workflow completed in {time.time() - start_time:.2f} seconds.")

        except Exception as e:
            logger.critical(f"System Failure: {str(e)}", exc_info=True)

if __name__ == "__main__":
    # 1. Start Flask server in background FIRST for Render health check
    t = threading.Thread(target=run_health_server)
    t.daemon = True
    t.start()
    
    # 2. Wait for server to bind
    time.sleep(3)
    
    # 3. Run Automation Logic
    controller = EcosystemController()
    main_keyword = "Future of Artificial Intelligence 2026"
    related_keywords = ["AI trends", "Automation"]
    
    controller.execute_workflow(main_keyword, secondary_keywords=related_keywords)
    
    # 4. Keep alive forever so Render doesn't stop the service
    while True:
        time.sleep(3600)
