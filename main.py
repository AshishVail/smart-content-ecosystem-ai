"""
main.py

The Central Orchestrator for the Smart Content Ecosystem.
This script integrates the Writer, SEO Analyzer, Image Engine, and WordPress API
to automate the full lifecycle of a professional blog post.

Workflow:
1. Keyword Input & Initialization
2. Content Generation (AI Writer)
3. SEO Audit & Optimization (SEO Analyzer)
4. Visual Asset Creation (Pollinations Image Engine)
5. Automated Publishing (WordPress REST API)
"""

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

# Configure Professional Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("ecosystem_execution.log")
    ]
)
logger = logging.getLogger("SmartEcosystem.Controller")

class EcosystemController:
    """
    Controller class to manage the integration of all content modules.
    """

    def __init__(self):
        # Initialize sub-modules using configuration settings
        self.writer = ContentWriter(api_key=config.AI_API_KEY)
        self.seo_analyzer = None # Dynamic initialization per keyword
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
        """
        Executes the end-to-end automated publishing workflow.
        """
        start_time = time.time()
        logger.info(f"Starting automation workflow for keyword: '{primary_keyword}'")

        try:
            # Step 1: Verification
            if not self.wp_client.verify_connection():
                logger.error("Abort: WordPress authentication failed. Check credentials in config.py")
                return

            # Step 2: Content Generation
            logger.info("Step 1/4: Generating AI Content...")
            article_body = self.writer.generate_article(primary_keyword)
            if not article_body:
                logger.error("Content generation failed. Check AI API status.")
                return
            logger.info("Content successfully generated.")

            # Step 3: SEO Analysis & Meta Generation
            logger.info("Step 2/4: Performing SEO Audit...")
            self.seo_analyzer = SEOAnalyzer(
                content=article_body,
                primary_keyword=primary_keyword,
                secondary_keywords=secondary_keywords
            )
            seo_report = self.seo_analyzer.analyze()
            logger.info(f"SEO Audit Complete. Score: {seo_report['seo_score']}/100")
            
            if seo_report['improvements']:
                logger.warning(f"SEO Improvements Suggested: {seo_report['improvements']}")

            # Step 4: AI Image Generation
            logger.info("Step 3/4: Creating Visual Assets (Pollinations AI)...")
            image_result = self.media_engine.generate_image_sync(primary_keyword)
            
            image_path = None
            if image_result.get("status") == "success":
                image_path = image_result.get("path")
                logger.info(f"Image localized at: {image_path}")
            else:
                logger.warning("Image generation failed. Proceeding without featured image.")

            # Step 5: WordPress Publishing
            logger.info("Step 4/4: Synchronizing with WordPress REST API...")
            post_id = self.wp_client.post_full_article(
                title=primary_keyword.title(),
                content=article_body,
                image_path=image_path,
                status="draft", # Set to 'publish' for immediate live posting
                categories=[],   # Add category names here
                tags=[primary_keyword] + (secondary_keywords or []),
                meta_title=primary_keyword.title(),
                meta_description=seo_results.get('meta_description', ""),
                seo_plugin=config.SEO_PLUGIN
            )

            if post_id:
                elapsed_time = round(time.time() - start_time, 2)
                logger.info(f"SUCCESS: Article posted with ID {post_id} in {elapsed_time}s.")
                print(f"\n--- Workflow Complete ---\nPost ID: {post_id}\nKeyword: {primary_keyword}\nStatus: Drafted\n-------------------------")
            else:
                logger.error("Post creation failed at the API level.")

        except Exception as e:
            logger.critical(f"Critical System Failure: {str(e)}", exc_info=True)

if __name__ == "__main__":
    # Example Execution
    controller = EcosystemController()
    
    # Define your target keyword and variations
    main_keyword = "Future of Artificial Intelligence 2026"
    related_keywords = ["AI trends", "Machine Learning", "Automation"]
    
    controller.execute_workflow(main_keyword, secondary_keywords=related_keywords)
