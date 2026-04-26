import os

# Fetching variables from Render Environment
WP_URL = os.getenv("WP_URL", "https://earnguide.in")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
AI_API_KEY = os.getenv("AI_API_KEY")

# Public settings
BRAND_NAME = "Nexovent"
OUTPUT_IMAGE_DIR = "generated_assets"
SEO_PLUGIN = "rank-math"
