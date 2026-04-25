"""
image_creator.py

AI-powered image creation, processing, and management module for Smart Content Ecosystems.

Features:
- AI Image Generation Integration (DALL-E 3, Midjourney, Stable Diffusion APIs)
- Automatic image compression (WebP, Pillow)
- Dynamic watermarking (custom logo or 'Nexovent' text)
- SEO-friendly file names & alt-text generator
- Multi-size image support (thumbnail, social, banner)
- Robust error handling
- OOP structure: SmartMedia class
"""

import os
import io
import logging
from typing import List, Optional, Dict
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
import requests
import hashlib

# ====== (Optional) Configurations for API endpoints/tokens =======
DALL_E_API_URL = "https://api.openai.com/v1/images/generations"
DALL_E_API_KEY = os.getenv("DALL_E_API_KEY")  # Place your key here or in env
# Same structure for other APIs...

# ====== Logging Setup =======
logger = logging.getLogger("media_manager.image_creator")
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)

# ====== Main Class =========

class SmartMedia:
    """
    SmartMedia: Handles AI image generation, processing, and SEO meta for articles.
    """

    def __init__(self, brand: str = "Nexovent", output_dir: str = "./ai_images", logo_path: Optional[str] = None):
        """
        Args:
            brand (str): Brand name/text for watermarking
            output_dir (str): Directory to store processed images
            logo_path (Optional[str]): Path to watermark logo (PNG). If None, watermark text is used.
        """
        self.brand = brand
        self.output_dir = output_dir
        self.logo_path = logo_path
        os.makedirs(self.output_dir, exist_ok=True)

    # --------- AI Image Generation ---------

    def generate_ai_image(self, prompt: str, model: str = "dall-e-3") -> Optional[Image.Image]:
        """
        Generate image using DALL-E 3, Midjourney, or Stable Diffusion.
        (Here: DALL-E 3. Extend as needed.)

        Args:
            prompt (str): Image generation prompt
            model (str): AI model name ("dall-e-3", "midjourney", etc.)

        Returns:
            PIL.Image.Image or None if failed
        """
        logger.info(f"Attempting to generate image: '{prompt}' with {model}")
        try:
            if model == "dall-e-3":
                return self._generate_dalle_image(prompt)
            else:
                logger.warning(f"Model '{model}' not implemented. (Try 'dall-e-3')")
                return None
        except Exception as e:
            logger.error(f"AI image generation failed: {e}")
            return None

    def _generate_dalle_image(self, prompt: str) -> Optional[Image.Image]:
        """
        Call OpenAI DALL-E 3 API.
        Returns PIL Image or None.
        """
        headers = {
            "Authorization": f"Bearer {DALL_E_API_KEY}"
        }
        data = {
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "response_format": "url"
        }
        try:
            response = requests.post(DALL_E_API_URL, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            image_url = result['data'][0]['url']
            img_bytes = requests.get(image_url).content
            img = Image.open(io.BytesIO(img_bytes))
            return img.convert("RGBA")
        except Exception as e:
            logger.error(f"DALL-E API error: {e}")
            return None

    # --------- Image Compression & Format ---------

    def compress_and_save_webp(self, img: Image.Image, out_path: str, quality: int = 80) -> Optional[str]:
        """
        Compress image as WebP.
        Args:
            img (Image.Image): PIL image
            out_path (str): Output file path
            quality (int): Compression quality (0-100)
        Returns:
            str: Output filename if successful, else None
        """
        try:
            img = img.convert("RGB")
            img.save(out_path, "webp", quality=quality, method=6)
            logger.info(f"Saved compressed WebP: {out_path}")
            return out_path
        except (OSError, UnidentifiedImageError) as e:
            logger.error(f"Compression failed: {e}")
            return None

    # --------- Dynamic Watermarking ---------

    def apply_watermark(self, img: Image.Image, opacity: float = 0.25) -> Image.Image:
        """
        Apply a logo or text watermark.
        Args:
            img (PIL.Image.Image): Image to watermark
            opacity (float): Watermark alpha (0-1)
        Returns:
            PIL.Image.Image: Watermarked image
        """
        img = img.convert("RGBA")
        watermark_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        w, h = img.size

        if self.logo_path and os.path.exists(self.logo_path):
            try:
                logo = Image.open(self.logo_path).convert("RGBA")
                # Resize logo for overlay (10% size)
                logo_w, logo_h = int(w * 0.2), int(h * 0.2)
                logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
                pos = (w - logo_w - 20, h - logo_h - 20)  # Bottom right
                # Set opacity
                alpha = logo.split()[3].point(lambda p: int(p * opacity))
                logo.putalpha(alpha)
                watermark_layer.paste(logo, pos, logo)
            except Exception as e:
                logger.error(f"Logo watermark error: {e}")
        else:
            # Draw text watermark
            draw = ImageDraw.Draw(watermark_layer)
            try:
                font_size = int(min(w, h) * 0.05)
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()
            text = self.brand
            text_w, text_h = draw.textsize(text, font=font)
            text_x, text_y = w - text_w - 20, h - text_h - 20
            draw.text((text_x, text_y), text, font=font, fill=(255,255,255,int(255*opacity)))

        # Composite watermark onto image
        watermarked = Image.alpha_composite(img, watermark_layer)
        return watermarked.convert("RGB")

    # --------- Image Resizing ---------

    def generate_resized_images(self, img: Image.Image, base_name: str) -> Dict[str, str]:
        """
        Create multiple sizes: thumbnail, social, banner.
        Args:
            img (PIL.Image.Image)
            base_name (str): For filenames
        Returns:
            Dict: size name → saved file path
        """
        sizes = {
            "thumbnail": (256, 256),
            "social": (800, 418),
            "banner": (1200, 628),
        }
        paths = {}
        for size_name, (w, h) in sizes.items():
            resized = img.copy()
            resized.thumbnail((w,h), Image.LANCZOS)
            fname = f"{base_name}_{size_name}.webp"
            outpath = os.path.join(self.output_dir, fname)
            if self.compress_and_save_webp(resized, outpath):
                paths[size_name] = outpath
        return paths

    # --------- META: Filename & Alt Text ---------

    def make_image_slug(self, heading: str) -> str:
        """Generate SEO-friendly and unique file name slug from heading."""
        # Shorten, slugify, and add a hash for uniqueness:
        slug = "-".join(re.findall(r'\w+', heading.lower()))[:50]
        unique = hashlib.md5(heading.encode()).hexdigest()[:6]
        return f"{slug}-{unique}"

    def generate_alt_text(self, heading: str, purpose: str = "illustration") -> str:
        """Auto generate SEO-friendly ALT text for image."""
        # ALT text is important for accessibility/SEO.
        return f"{purpose.capitalize()} of {heading.strip()} by Nexovent AI"

    # --------- Main Orchestration ---------

    def process_article_headings(
        self,
        headings: List[str],
        model: str = "dall-e-3"
    ) -> List[Dict[str, str]]:
        """
        For each heading, generate, compress, watermark, and export images in all sizes.

        Args:
            headings (List[str]): List of article headings
            model (str): Image generator model

        Returns:
            List[Dict]: Info about each processed image
        """
        results = []
        for heading in headings:
            slug = self.make_image_slug(heading)
            alt_text = self.generate_alt_text(heading)
            prompt = f"{heading} professional illustration, detailed, high-res, no text, digital art"
            try:
                img = self.generate_ai_image(prompt, model=model)
                if img is None:
                    logger.warning(f"Skipping: image not generated for '{heading}'")
                    continue

                img = self.apply_watermark(img)
                sizes = self.generate_resized_images(img, slug)
                result = {
                    "heading": heading,
                    "file_slug": slug,
                    "alt": alt_text,
                    "prompt": prompt,
                }
                for size, path in sizes.items():
                    result[size] = path
                results.append(result)
            except Exception as e:
                logger.error(f"Failed processing heading '{heading}': {e}")
        return results

# --------- Optional CLI Demo ---------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate branded images for article headings.")
    parser.add_argument("--headings", nargs="+", help="Headings to create images for.", required=True)
    parser.add_argument("--brand", type=str, default="Nexovent", help="Brand name for watermark text.")
    parser.add_argument("--dir", type=str, default="./ai_images")
    parser.add_argument("--logo", type=str, default=None)
    parser.add_argument("--model", type=str, default="dall-e-3")
    args = parser.parse_args()

    sm = SmartMedia(brand=args.brand, output_dir=args.dir, logo_path=args.logo)
    results = sm.process_article_headings(args.headings, model=args.model)

    print(f"Processed {len(results)} images:")
    for r in results:
        print(r)
