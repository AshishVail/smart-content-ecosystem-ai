"""
wordpress_api.py

Professional-grade WordPress REST API integration.
Features: Secure Auth, Media Upload, SEO Meta (Yoast/RankMath), and Post Orchestration.
"""

import base64
import json
import logging
import os
import requests
from typing import List, Dict, Optional

# Markdown conversion logic (आर्टिकल को वर्डप्रेस फॉर्मेट में बदलने के लिए)
try:
    import markdown
except ImportError:
    markdown = None

# Logging setup (प्रोफेशनल एरर ट्रैकिंग)
logger = logging.getLogger("integrations.wordpress_api")
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)

class WordPressClient:
    """
    Advanced WordPress Client for automated content publishing.
    """

    def __init__(
        self,
        wp_url: str,
        username: str,
        password: Optional[str] = None,
        jwt_token: Optional[str] = None
    ):
        """
        Initialization logic for WordPress connection.
        """
        self.wp_url = wp_url.rstrip("/")
        self.username = username
        self.password = password
        self.jwt_token = jwt_token
        self.api_url = f"{self.wp_url}/wp-json/wp/v2"
        self.seo_api_url = f"{self.wp_url}/wp-json/yoast/v1" # Default to Yoast
        
        # Headers setup for authentication (सिक्योर ऑथेंटिकेशन सेटअप)
        self.headers = {}
        if jwt_token:
            self.headers['Authorization'] = f'Bearer {jwt_token}'
        elif username and password:
            auth_string = f"{username}:{password}"
            auth_b = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
            self.headers['Authorization'] = f'Basic {auth_b}'
        
        logger.info(f"WordPressClient initialized for {self.wp_url}")

    def verify_connection(self) -> bool:
        """
        Verify if the connection and credentials are valid.
        (चेक करता है कि यूजर क्रेडेंशियल्स सही हैं या नहीं)
        """
        try:
            resp = requests.get(f"{self.api_url}/users/me", headers=self.headers, timeout=15)
            resp.raise_for_status()
            user_data = resp.json()
            logger.info(f"Connected as: {user_data.get('name')}")
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def _ensure_terms(self, names: List[str], term_type: str) -> List[int]:
        """
        Check if Category/Tag exists, if not, create it.
        (कैटेगरी या टैग नहीं होने पर उन्हें अपने आप बना देता है)
        """
        ids = []
        for name in names:
            search_url = f"{self.api_url}/{term_type}?search={name}"
            try:
                resp = requests.get(search_url, headers=self.headers, timeout=10)
                items = resp.json()
                found = False
                for item in items:
                    if item['name'].lower() == name.lower():
                        ids.append(item['id'])
                        found = True
                        break
                
                if not found:
                    create_resp = requests.post(
                        f"{self.api_url}/{term_type}", 
                        headers=self.headers, 
                        json={"name": name}, 
                        timeout=15
                    )
                    ids.append(create_resp.json()['id'])
            except Exception as e:
                logger.error(f"Error ensuring term '{name}': {e}")
        return ids

    def upload_media(self, img_path: str, alt_text: Optional[str] = None) -> Optional[int]:
        """
        Upload local image to WordPress Media Library.
        (फोटो को वर्डप्रेस मीडिया लाइब्रेरी में अपलोड करता है)
        """
        if not img_path or not os.path.exists(img_path):
            logger.warning(f"Image path invalid: {img_path}")
            return None

        endpoint = f"{self.api_url}/media"
        filename = os.path.basename(img_path)
        
        # Binary upload logic for high reliability
        try:
            with open(img_path, "rb") as img_file:
                media_headers = self.headers.copy()
                media_headers['Content-Disposition'] = f'attachment; filename="{filename}"'
                # Detecting content type (Assuming WebP from our Image Engine)
                files = {'file': (filename, img_file, 'image/webp')}
                
                resp = requests.post(endpoint, files=files, headers=self.headers, timeout=45)
                resp.raise_for_status()
                media_id = resp.json().get("id")
                
                if alt_text and media_id:
                    requests.post(f"{endpoint}/{media_id}", headers=self.headers, json={"alt_text": alt_text})
                
                logger.info(f"Media uploaded. ID: {media_id}")
                return media_id
        except Exception as e:
            logger.error(f"Media upload failed: {e}")
            return None

    def update_seo_meta(self, post_id: int, title: str, description: str, plugin: str = "yoast") -> bool:
        """
        Update Yoast or RankMath Meta tags.
        (योस्ट या रैंकमैथ एसईओ टैग्स को अपडेट करने के लिए)
        """
        try:
            if plugin == "yoast":
                payload = {"yoast_wpseo_title": title, "yoast_wpseo_metadesc": description}
                resp = requests.post(f"{self.seo_api_url}/posts/{post_id}/meta", headers=self.headers, json=payload, timeout=20)
            elif plugin == "rankmath":
                payload = {"id": post_id, "title": title, "description": description}
                resp = requests.post(f"{self.wp_url}/wp-json/rankmath/v1/updateMeta", headers=self.headers, json=payload, timeout=20)
            else:
                return False
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"SEO update failed: {e}")
            return False

    def post_full_article(
        self,
        title: str,
        content: str,
        image_path: Optional[str] = None,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        status: str = 'draft',
        meta_title: Optional[str] = None,
        meta_description: Optional[str] = None,
        seo_plugin: str = "yoast"
    ) -> Optional[int]:
        """
        The main orchestrator to publish image + content + SEO.
        (यह मुख्य फंक्शन है जो फोटो, लेख और एसईओ सब कुछ एक साथ पब्लिश करता है)
        """
        # 1. Process Content (Markdown to HTML conversion)
        final_content = content
        if markdown:
            # Markdown को HTML में बदलना जरूरी है वरना WP फॉर्मेटिंग नहीं समझेगा
            final_content = markdown.markdown(content, extensions=['extra', 'tables', 'fenced_code'])

        # 2. Upload Featured Image
        featured_id = self.upload_media(image_path, alt_text=title) if image_path else None

        # 3. Ensure Categories/Tags exist
        cat_ids = self._ensure_terms(categories or [], "categories")
        tag_ids = self._ensure_terms(tags or [], "tags")

        # 4. Prepare Post Payload
        payload = {
            "title": title,
            "content": final_content,
            "status": status,
            "categories": cat_ids,
            "tags": tag_ids,
            "format": "standard"
        }
        if featured_id:
            payload["featured_media"] = featured_id

        try:
            post_url = f"{self.api_url}/posts"
            resp = requests.post(post_url, headers=self.headers, json=payload, timeout=40)
            resp.raise_for_status()
            post_id = resp.json().get("id")
            
            # 5. Update SEO Meta if provided
            if post_id and meta_title and meta_description:
                self.update_seo_meta(post_id, meta_title, meta_description, plugin=seo_plugin)
                
            logger.info(f"Article '{title}' successfully published as {status}. ID: {post_id}")
            return post_id
        except Exception as e:
            logger.error(f"Full article post failed: {e}")
            return None

# End of Module
