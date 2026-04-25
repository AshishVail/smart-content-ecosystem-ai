"""
wordpress_api.py

Secure, modular WordPress REST API integration for content and media publishing.

Features:
 - Secure authentication with Application Passwords or JWT
 - Create/edit posts (title, content, markdown & HTML, categories, tags)
 - Upload images to WordPress Media Library and assign as featured
 - Support 'draft' or 'publish' status uploads
 - SEO meta integration (Yoast, RankMath)
 - Detailed error-handling and logging
 - OOP: WordPressClient class

Requires: requests, logging
"""

import base64
import json
import logging
import os
import requests
from typing import List, Dict, Optional

# =======================
# Configure Logging
# =======================
logger = logging.getLogger("integrations.wordpress_api")
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)


class WordPressClient:
    """
    Modular WordPress REST API interface for secure content and media publishing.
    """

    def __init__(
        self,
        wp_url: str,
        username: str,
        password: Optional[str] = None,
        jwt_token: Optional[str] = None
    ):
        """
        Args:
            wp_url (str): Base URL (e.g., https://example.com)
            username (str): WordPress username
            password (str): Application Password (if using basic auth)
            jwt_token (str): Optional JWT string (if using JWT auth)
        """
        self.wp_url = wp_url.rstrip("/")
        self.username = username
        self.password = password
        self.jwt_token = jwt_token
        self.session = requests.Session()

        if jwt_token:
            self.session.headers.update({'Authorization': f'Bearer {jwt_token}'})
        elif username and password:
            auth_string = f"{username}:{password}"
            auth_b = base64.b64encode(auth_string.encode("utf-8"))
            self.session.headers.update({'Authorization': f'Basic {auth_b.decode("utf-8")}'})

        self.api_url = f"{self.wp_url}/wp-json/wp/v2"
        self.seo_api_url = f"{self.wp_url}/wp-json/yoast/v1"  # or RankMath (adjust endpoint)
        logger.info("WordPressClient initialized for %s", self.wp_url)

    # -------------------------
    # Authentication Utilities
    # -------------------------
    def verify_connection(self) -> bool:
        """
        Verify credentials and connectivity.
        Returns: True if authorized and connected, else False.
        """
        try:
            resp = self.session.get(f"{self.api_url}/users/me", timeout=15)
            resp.raise_for_status()
            user = resp.json()
            logger.info(f"Authenticated as WordPress user: {user.get('name', 'Unknown')}")
            return True
        except Exception as e:
            logger.error(f"[WP] Authentication failed: {e}")
            return False

    # -------------------------
    # Post Management
    # -------------------------
    def upload_post(
        self,
        title: str,
        content: str,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        status: str = 'draft',
        format: str = 'html',
        featured_image_id: Optional[int] = None
    ) -> Optional[int]:
        """
        Create a new post in WordPress.

        Args:
            title (str): Post Title
            content (str): Content (HTML or Markdown)
            categories (List[str]): List of category names (created if not exist)
            tags (List[str]): List of tag names (created if not exist)
            status (str): 'draft' or 'publish'
            format (str): Content format, 'html' or 'markdown'
            featured_image_id (int): Media library ID for featured image

        Returns:
            int: Post ID if successful, else None
        """
        try:
            cats_ids = self._ensure_terms(categories or [], "categories")
            tags_ids = self._ensure_terms(tags or [], "tags")
            data = {
                "title": title,
                "content": content,
                "status": status,
                "categories": cats_ids,
                "tags": tags_ids,
                "format": "standard",  # or 'aside', etc.
            }
            if featured_image_id:
                data["featured_media"] = featured_image_id

            url = f"{self.api_url}/posts"
            resp = self.session.post(url, json=data, timeout=30)
            resp.raise_for_status()
            post_id = resp.json()['id']
            logger.info(f"[WP] Post created '{title}' (ID: {post_id}, Status: {status})")
            return post_id
        except Exception as e:
            logger.error(f"[WP] Failed to upload post '{title}': {e} | Response: {getattr(e, 'response', None)}")
            return None

    def _ensure_terms(self, names: List[str], term_type: str) -> List[int]:
        """
        Ensure categories/tags exist and return their IDs. Creates them if necessary.

        Args:
            names (List[str]): names
            term_type (str): 'categories' or 'tags'

        Returns:
            List[int]: IDs
        """
        ids = []
        for name in names:
            # Try get by name
            url = f"{self.api_url}/{term_type}?search={name}"
            try:
                resp = self.session.get(url, timeout=10)
                resp.raise_for_status()
                items = resp.json()
                for item in items:
                    if item['name'].lower() == name.lower():
                        ids.append(item['id'])
                        break
                else:
                    # Create term if not found
                    create_url = f"{self.api_url}/{term_type}"
                    create = self.session.post(create_url, json={"name": name}, timeout=15)
                    create.raise_for_status()
                    ids.append(create.json()['id'])
            except Exception as e:
                logger.error(f"[WP] Term fetch/create error for '{name}': {e}")
        return ids

    # -------------------------
    # Media Upload and Linking
    # -------------------------
    def upload_media(self, img_path: str, alt_text: Optional[str] = None) -> Optional[int]:
        """
        Upload an image to WordPress Media Library.

        Args:
            img_path (str): Local path to image
            alt_text (str): ALT tag

        Returns:
            int: Media ID, or None if failed
        """
        endpoint = f"{self.api_url}/media"
        filename = os.path.basename(img_path)
        headers = self.session.headers.copy()
        headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        try:
            with open(img_path, "rb") as img_file:
                files = {"file": (filename, img_file, "image/webp")}
                # WP expects POST multipart
                resp = self.session.post(endpoint, files=files, headers=headers, timeout=40)
                resp.raise_for_status()
                media_id = resp.json().get("id")
                logger.info(f"[WP] Uploaded image '{filename}', ID: {media_id}")
                # Add ALT-text if provided
                if alt_text:
                    update_url = f"{endpoint}/{media_id}"
                    self.session.post(update_url, json={"alt_text": alt_text})
                return media_id
        except Exception as e:
            logger.error(f"[WP] Image upload failed for '{img_path}': {e}")
            return None

    # -------------------------
    # SEO Meta Integration
    # -------------------------
    def update_seo_meta(
        self, post_id: int, meta_title: str, meta_description: str, plugin: str = "yoast"
    ) -> bool:
        """
        Update SEO meta using Yoast or RankMath APIs.
        Example for Yoast SEO, adjust for RankMath.

        Args:
            post_id (int): WordPress post ID
            meta_title (str): Custom title
            meta_description (str): Custom description
            plugin (str): "yoast" or "rankmath"

        Returns:
            bool: Success
        """
        try:
            if plugin == "yoast":
                seo_url = f"{self.seo_api_url}/posts/{post_id}/meta"
                payload = {"yoast_wpseo_title": meta_title, "yoast_wpseo_metadesc": meta_description}
            elif plugin == "rankmath":
                seo_url = f"{self.wp_url}/wp-json/rankmath/v1/updateMeta"
                payload = {"id": post_id, "title": meta_title, "description": meta_description}
            else:
                logger.error(f"[WP] Unknown SEO plugin: {plugin}")
                return False

            resp = self.session.post(seo_url, json=payload, timeout=20)
            resp.raise_for_status()
            logger.info(f"[WP] SEO meta updated ({plugin}) for post {post_id}")
            return True
        except Exception as e:
            logger.error(f"[WP] Failed to update SEO meta for post {post_id}: {e}")
            return False

    # -------------------------
    # High-level Orchestration
    # -------------------------
    def post_full_article(
        self,
        title: str,
        content: str,
        image_path: Optional[str] = None,
        alt_text: Optional[str] = None,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        status: str = 'draft',
        meta_title: Optional[str] = None,
        meta_description: Optional[str] = None,
        format: str = 'html',
        seo_plugin: str = "yoast"
    ) -> Optional[int]:
        """
        Complete process: Upload image, create post, link featured image, update SEO.

        Returns:
            int: Post ID or None
        """
        featured_image_id = None
        if image_path:
            featured_image_id = self.upload_media(image_path, alt_text=alt_text)
            if not featured_image_id:
                logger.error(f"[WP] Media upload failed; aborting article post for '{title}'.")
                return None

        post_id = self.upload_post(
            title=title,
            content=content,
            categories=categories,
            tags=tags,
            status=status,
            format=format,
            featured_image_id=featured_image_id
        )
        if not post_id:
            return None

        if meta_title and meta_description:
            self.update_seo_meta(post_id, meta_title, meta_description, plugin=seo_plugin)
        return post_id

# -------------------------
# CLI Demo (Optional)
# -------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="WordPress API Integration Demo")
    parser.add_argument("--site", required=True, help="WordPress Site URL (https://example.com)")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=False)
    parser.add_argument("--jwt", required=False)
    parser.add_argument("--title", required=True)
    parser.add_argument("--content", required=True)
    parser.add_argument("--image", required=False)
    parser.add_argument("--status", default="draft", choices=["publish", "draft"])
    parser.add_argument("--meta_title", required=False)
    parser.add_argument("--meta_desc", required=False)
    parser.add_argument("--category", nargs="*", default=[])
    parser.add_argument("--tag", nargs="*", default=[])
    args = parser.parse_args()

    client = WordPressClient(
        wp_url=args.site,
        username=args.username,
        password=args.password,
        jwt_token=args.jwt
    )
    if not client.verify_connection():
        print("Failed to authenticate to WordPress API.")
        exit(1)

    post_id = client.post_full_article(
        title=args.title,
        content=args.content,
        image_path=args.image,
        alt_text=args.meta_title,
        categories=args.category,
        tags=args.tag,
        status=args.status,
        meta_title=args.meta_title,
        meta_description=args.meta_desc
    )
    if post_id:
        print(f"Article posted with ID: {post_id}")
    else:
        print("Failed to post article.")
