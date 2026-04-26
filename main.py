import os
import sys
import logging
import time
from typing import List, Optional, Dict, Any

# Import modular components
from utils import config
from core_logic.writer_engine import ContentWriter
from core_logic.seo_analyzer import SEOAnalyzer
from media_manager.image_creator import SmartMediaEngine
from integrations.wordpress_api import WordPressClient

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("SmartEcosystem.Controller")

class EcosystemController:
    def __init__(self):
        self.writer = ContentWriter(api_key=config.AI_API_KEY)
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
            article_body = self.writer.generate_article(primary_keyword)
            if not article_body: return

            logger.info("Step 2/4: SEO Audit...")
            self.seo_analyzer = SEOAnalyzer(
                content=article_body,
                primary_keyword=primary_keyword,
                secondary_keywords=secondary_keywords
            )
            seo_report = self.seo_analyzer.analyze()
            
            logger.info("Step 3/4: Creating Image...")
            image_result = self.media_engine.generate_image_sync(primary_keyword)
            image_path = image_result.get("path") if image_result.get("status") == "success" else None

            logger.info("Step 4/4: Posting to WordPress...")
            # FIXED: Changed seo_results to seo_report
            post_id = self.wp_client.post_full_article(
                title=primary_keyword.title(),
                content=article_body,
                image_path=image_path,
                status="draft",
                categories=[],
                tags=[primary_keyword] + (secondary_keywords or []),
                meta_title=primary_keyword.title(),
                meta_description=seo_report.get('meta_description', ""),
                seo_plugin=config.SEO_PLUGIN
            )

            if post_id:
                logger.info(f"SUCCESS: Article posted with ID {post_id}")
        except Exception as e:
            logger.critical(f"System Failure: {str(e)}", exc_info=True)

if __name__ == "__main__":
    controller = EcosystemController()
    main_keyword = "Future of Artificial Intelligence 2026"
    related_keywords = ["AI trends", "Automation"]
    controller.execute_workflow(main_keyword, secondary_keywords=related_keywords)
