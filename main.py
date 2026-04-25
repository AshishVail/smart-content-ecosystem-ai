"""
main.py - Smart Content Ecosystem Orchestrator
------------------------------------------------
This master control script integrates all core packages for content, SEO,
media, distribution, and configuration. It provides a CLI-driven workflow,
robust error handling, and dynamic progress tracking.

Author: Your Name
Date: 2026-04-25
"""

import sys
import os
import time
from typing import Dict, Any, List, Optional

# Import tqdm for progress bar
try:
    from tqdm import tqdm
except ImportError:
    tqdm = None  # fallback if unavailable

import argparse

# ----- Core Imports (according to your package structure) -----
from core_logic.writer_engine import SmartWriter, ToneStyle, WriterConfig
from core_logic.seo_analyzer import SEOAnalyzer
from media_manager.image_creator import SmartMedia
from media_manager.meta_tagger import MetaManager
from integrations.wordpress_api import WordPressClient
from integrations.social_share import SocialDistributor
from utils import Config, logger

# ---- Constants ----
PROGRESS_STEPS = [
    ("Configuration & Logger", 10),
    ("Content Generation", 20),
    ("SEO Analysis", 30),
    ("Image Creation", 50),
    ("WordPress Publishing", 70),
    ("Social Sharing", 100),
]

SOCIAL_PLATFORMS = ["instagram", "threads", "x"]  # Supported social integrations

# ---- Utility Functions ----

def progress_bar(stage: str, percent: int):
    """
    Print or show progress bar depending on tqdm availability.
    """
    bar_len = 40
    done = int(bar_len * percent / 100)
    sys.stdout.write(f"\r[{stage}] [{'=' * done}{' ' * (bar_len-done)}] {percent}%")
    sys.stdout.flush()
    if percent == 100:
        print()

def confirm_retry_skip(error_msg: str) -> str:
    """
    Prompt user to Retry/Skip/Abort on error.
    Returns: "retry", "skip", or "abort"
    """
    print(f"\n[ERROR]: {error_msg}")
    while True:
        resp = input("Type 'retry' to try again, 'skip' to continue to next step, or 'abort' to exit: ").strip().lower()
        if resp in ('retry', 'skip', 'abort'):
            return resp
        print("Invalid input. Please type 'retry', 'skip', or 'abort'.")

def show_stage(stage_idx):
    stage, percent = PROGRESS_STEPS[stage_idx]
    progress_bar(stage, percent)

def show_final_summary(report: dict):
    print("\n" + "="*65)
    print("SMART CONTENT ECOSYSTEM - EXECUTION SUMMARY")
    print("="*65)
    print(f"WordPress Post URL: {report.get('wp_url', '')}")
    print("Social Media Post IDs:")
    for plat, pid in report.get('social_posts', {}).items():
        print(f"  - {plat.capitalize()}: {pid}")
    print("\nProcess complete. Review logs for details.\n" + "="*65)

# ---- Main Workflow ----

def main():
    """
    Main CLI workflow for the Smart Content Ecosystem.
    """
    # Step 0: CLI Arguments
    parser = argparse.ArgumentParser(description="Smart Content Ecosystem Orchestrator")
    parser.add_argument("--keyword", "-k", required=True, help="Main keyword or topic for content generation.")
    parser.add_argument("--tone", "-t", choices=["professional", "casual", "informative", "creative"], default="professional", help="Tone/style for the content.")
    parser.add_argument("--lang", "-l", default="en", help="Content language (default: en)")
    parser.add_argument("--wordcount", "-w", type=int, default=2000, help="Minimum word count (default: 2000)")
    parser.add_argument("--retry-on-fail", action="store_true", help="Automatically retry a failed step once before asking.")
    args = parser.parse_args()

    # Progress tracking data
    report = {
        "wp_url": "",
        "social_posts": {},
        "stages": {},
    }
    current_stage = 0

    # -------- Step 1: Load Configuration and Logger --------
    show_stage(current_stage)
    try:
        config = Config()
        logger.info("Configuration loaded successfully.")
    except Exception as e:
        logger.log_traceback("Configuration loading failed.")
        print("Critical configuration error. Aborting.")
        sys.exit(1)
    current_stage += 1

    # -------- Step 2: Content Generation with SmartWriter --------
    writer = None
    while True:
        show_stage(current_stage)
        try:
            writer_cfg = WriterConfig(
                tone=ToneStyle[args.tone.upper()],
                min_word_count=args.wordcount,
            )
            writer = SmartWriter(config=writer_cfg)
            content_result = writer.generate(target_keyword=args.keyword)
            markdown_content = content_result['markdown']
            html_content = content_result['html']
            outline = content_result['outline']
            logger.info("High-quality content generated for keyword '%s'.", args.keyword)
            break
        except Exception as e:
            logger.log_traceback("SmartWriter: Content generation error.")
            action = confirm_retry_skip("Content generation failed.")
            if action == 'abort':
                return
            elif action == 'skip':
                break
    current_stage += 1

    # -------- Step 3: SEO Analysis --------
    seo_data = {}
    while True:
        show_stage(current_stage)
        try:
            analyzer = SEOAnalyzer(
                content=markdown_content,
                primary_keyword=args.keyword,
                # Optionally fetch related keywords here
            )
            seo_report = analyzer.seo_score_and_improvements()
            seo_data = seo_report
            logger.info("SEO analysis complete. Score: %s", seo_report['score'])
            break
        except Exception as e:
            logger.log_traceback("SEOAnalyzer: SEO analysis error.")
            action = confirm_retry_skip("SEO analysis failed.")
            if action == 'abort':
                return
            elif action == 'skip':
                break
    current_stage += 1

    # -------- Step 4: Image Generation and Optimization --------
    heading_list = []
    # Use outline or parse headings
    for line in outline.splitlines():
        line = line.strip()
        if line.startswith('- '):
            continue
        if line.startswith('#'):
            heading_core = line.lstrip('#').strip()
            if heading_core and not heading_core.lower().startswith('article outline'):
                heading_list.append(heading_core)
    # Fallback single image if there are no headings
    if not heading_list:
        heading_list.append(args.keyword.title())
    media_paths, image_meta, featured_image_path = [], [], None
    while True:
        show_stage(current_stage)
        try:
            # Generate, watermark, and save all images
            smedia = SmartMedia(brand="Nexovent")
            results = smedia.process_article_headings(heading_list, model="dall-e-3")
            featured = results[0] if results else None
            if not featured or 'banner' not in featured:
                raise Exception("No featured image generated.")
            featured_image_path = featured['banner']
            media_paths = [img['banner'] for img in results if 'banner' in img]
            logger.info("Generated and watermarked images for headings: %r", [r['heading'] for r in results])

            # Batch meta-tagging
            mmgr = MetaManager(os.path.dirname(featured_image_path))
            mmgr.batch_process(context=args.keyword)
            image_meta = mmgr.metadata_records
            logger.info("Batch meta tagging and alt text complete for generated images.")
            break
        except Exception as e:
            logger.log_traceback("Image creation and optimization failed.")
            action = confirm_retry_skip("Image generation or optimization failed.")
            if action == 'abort':
                return
            elif action == 'skip':
                break
    current_stage += 1

    # -------- Step 5: Upload to WordPress --------
    wp_post_id = None
    wp_url = ""
    while True:
        show_stage(current_stage)
        try:
            wp = WordPressClient(
                wp_url=config.WORDPRESS_URL,
                username=config.WORDPRESS_USER,
                password=config.WORDPRESS_PASSWORD
            )
            # Verify connection
            if not wp.verify_connection():
                raise Exception("WordPress authentication failed.")
            alt_text = image_meta[0]['alt'] if image_meta else args.keyword
            featured_image_id = None
            if featured_image_path:
                featured_image_id = wp.upload_media(featured_image_path, alt_text)
            # Generate meta
            meta_title = seo_data.get('meta_description', args.keyword)
            meta_description = seo_data.get('meta_description', args.keyword)
            # Final status (ask user, else draft)
            pub_status = "publish" if input("Publish immediately? (y/N): ").strip().lower() == "y" else "draft"
            post_id = wp.upload_post(
                title=args.keyword.title(),
                content=html_content,
                categories=[],
                tags=[],
                status=pub_status,
                format='html',
                featured_image_id=featured_image_id
            )
            if not post_id:
                raise Exception("Post upload failed.")
            # Write SEO meta info (Yoast or RankMath)
            _ = wp.update_seo_meta(
                post_id,
                meta_title=meta_title,
                meta_description=meta_description,
                plugin="yoast"
            )
            # Get post URL
            wp_url = f"{config.WORDPRESS_URL.rstrip('/')}/?p={post_id}"
            report['wp_url'] = wp_url
            logger.info("WordPress post successful: %s", wp_url)
            break
        except Exception as e:
            logger.log_traceback("WordPress Publishing failed")
            action = confirm_retry_skip("WordPress publishing failed.")
            if action == 'abort':
                return
            elif action == 'skip':
                break
    current_stage += 1

    # -------- Step 6: Share to Social Media --------
    social_ids = {}
    while True:
        show_stage(current_stage)
        try:
            if not wp_url:
                raise Exception("WordPress URL unavailable for sharing.")
            distributor = SocialDistributor()
            post_summary = seo_data.get('meta_description', args.keyword)
            main_keywords = [args.keyword]
            hashtags = [args.keyword.replace(" ", "")]
            for plat in SOCIAL_PLATFORMS:
                print(f"Queuing post for {plat}...")
                distributor.schedule_post(
                    platform=plat,
                    summary=post_summary,
                    main_keywords=main_keywords,
                    hashtags=hashtags,
                    image_path=featured_image_path,
                    article_url=wp_url,
                    delay_range_sec=(2, 6)
                )
                # Log latest social post ID if available
                if distributor.log:
                    for entry in reversed(distributor.log):
                        if entry['platform'] == plat:
                            social_ids[plat] = entry['post_id']
                            break
            report['social_posts'] = social_ids
            logger.info("Social media sharing complete: %s", social_ids)
            break
        except Exception as e:
            logger.log_traceback("Social Share failed.")
            action = confirm_retry_skip("Social sharing failed.")
            if action == 'abort':
                return
            elif action == 'skip':
                break
    current_stage += 1

    # -------- Final Summary --------
    show_stage(current_stage)
    show_final_summary(report)
    logger.info("Master execution finished successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.log_traceback("Application crashed at the outermost level.")
        print("Fatal error encountered. Please check your logs for details.")
