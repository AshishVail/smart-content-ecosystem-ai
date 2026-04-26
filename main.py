import os
import sys
import logging
import time
from multiprocessing import Process # Threading ki jagah Process use karenge
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
    return "Bot is Active", 200

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    # use_reloader=False aur debug=False hona bahut zaruri hai
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ------------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("SmartEcosystem.Controller")

def start_bot_logic():
    """Bot ka asli kaam yahan hoga"""
    time.sleep(5) # Server ko set hone ka time do
    controller = EcosystemController()
    main_keyword = "Future of Artificial Intelligence 2026"
    related_keywords = ["AI trends", "Automation"]
    controller.execute_workflow(main_keyword, secondary_keywords=related_keywords)
    
    # Kaam khatam hone ke baad bhi script ko zinda rakho taaki Render kill na kare
    while True:
        time.sleep(3600)

class EcosystemController:
    def __init__(self):
        self.writer = SmartWriter(api_key=config.AI_API_KEY)
        self.wp_client = WordPressClient(
            wp_url=config.WP_URL,
            username=config.WP_USERNAME,
            password=config.WP_APP_PASSWORD
        )
        self.media_engine = SmartMediaEngine({
            "brand_name": config.BRAND_NAME,
            "output_path": config.OUTPUT_IMAGE_DIR
        })

    def execute_workflow(self, primary_keyword: str, secondary_keywords: Optional[List[str]] = None):
        logger.info(f"Starting workflow for: '{primary_keyword}'")
        try:
            if not self.wp_client.verify_connection():
                logger.error("WordPress authentication failed.")
                return

            logger.info("Step 1/4: Generating Content...")
            article_data = self.writer.generate_article(primary_keyword)
            
            article_body = article_data.get('body', "") if isinstance(article_data, dict) else article_data
            article_title = article_data.get('title', primary_keyword.title()) if isinstance(article_data, dict) else primary_keyword.title()

            if not article_body: return

            logger.info("Step 2/4: SEO Audit...")
            seo_report = {}
            try:
                self.seo_analyzer = SEOAnalyzer(content=article_body, primary_keyword=primary_keyword)
                seo_report = self.seo_analyzer.analyze() or {}
            except: seo_report = {}
            
            logger.info("Step 3/4: Creating Image...")
            image_path = None
            try:
                res = self.media_engine.generate_image_sync(primary_keyword)
                if res and res.get("status") == "success": image_path = res.get("path")
            except: pass

            logger.info("Step 4/4: Posting to WordPress...")
            meta_desc = seo_report.get('meta_description', f"About {primary_keyword}") if isinstance(seo_report, dict) else f"About {primary_keyword}"
            
            post_id = self.wp_client.post_full_article(
                title=article_title,
                content=article_body,
                image_path=image_path,
                status="draft",
                tags=[primary_keyword],
                meta_description=meta_desc,
                seo_plugin=config.SEO_PLUGIN
            )

            if post_id:
                logger.info(f"SUCCESS: Article posted with ID {post_id}")
            
        except Exception as e:
            logger.critical(f"System Failure: {str(e)}", exc_info=True)

if __name__ == "__main__":
    # 1. Server ko alag process mein chalao
    server_process = Process(target=run_health_server)
    server_process.start()
    
    # 2. Bot ko main process mein chalao
    start_bot_logic()
