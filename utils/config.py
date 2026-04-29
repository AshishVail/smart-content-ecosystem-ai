import os

# Fetching variables from Render Environment
# Nexovent ki nayi site ka URL yahan default mein rakhein
WP_URL = os.getenv("WP_URL", "https://dev-nexovent.pantheonsite.io")

WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

# IS LINE KO DHAYAN SE DEKHO: 
# Humne variable ka naam wahi rakha hai jo SmartWriter dhoond raha hai
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Extra Safety: Agar koi AI_API_KEY naam se bhi bulaye toh bhi mil jaye
AI_API_KEY = GROQ_API_KEY 

# Public settings
BRAND_NAME = "Nexovent"
OUTPUT_IMAGE_DIR = "generated_assets"
SEO_PLUGIN = "rank-math"
