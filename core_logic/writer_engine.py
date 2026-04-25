writer_engine.py

LLM-powered SmartWriter using Groq Platform (Llama-3 via groq SDK).
Automated, SEO-optimized, human-like multi-section content generation.

Features:
- Groq integration, singleton client with robust error handling
- Structured SmartWriter class with generate_article(keyword, tone)
- High-quality prompt engineering for SEO/Markdown/Headers format
- Optional JSON-mode for output parsing (title/sections/body separation)
- Streaming support (prints response as model streams for great UX)
- PEP 8 compliance, type hints, and professional docstrings

Author: Ashish (Nexovent)
"""

import os
import sys
import time
import logging
import json
from typing import Dict, Any, Optional

try:
    from groq import Groq, RateLimitError
except ImportError:
    raise ImportError("groq-sdk is required. Install via: pip install groq")

# --- Logging ---
logger = logging.getLogger("core_logic.writer_engine")
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)

# --- Supported Models (newest Llama-3 variant preferred) ---
DEFAULT_MODEL = "llama-3-70b-8192"  # fallback if 'llama-3.3-70b-versatile' not present
MODEL_CANDIDATES = [
    "llama-3.3-70b-versatile",
    "llama-3-70b-8192",
]

# --- API Key Setup ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    raise EnvironmentError("Set the GROQ_API_KEY environment variable for Groq access.")

# --- Groq Client (Singleton) ---
class GroqClientSingleton:
    """
    Singleton for Groq client.
    """
    _instance: Optional[Groq] = None

    @classmethod
    def get_client(cls) -> Groq:
        if cls._instance is None:
            cls._instance = Groq(api_key=GROQ_API_KEY)
            logger.info("Groq client initialized.")
        return cls._instance

def get_model_name() -> str:
    """
    Return best-available Llama-3 model.
    """
    # Optionally implement logic to fetch available models from API
    # and pick the best match. For now, static fallback.
    for m in MODEL_CANDIDATES:
        return m
    return DEFAULT_MODEL

# -------- Prompt Templates & Tone Map ------

TONE_STYLES = {
    "professional": "Write with expert authority, keeping language clear and formal.",
    "casual": "Write in a friendly, relaxed conversational style.",
    "informative": "Emphasize clarity and facts, optimize for reader understanding.",
    "creative": "Write imaginatively with figurative language and engaging analogies.",
}

SYSTEM_PROMPT = """You are SmartWriter: an advanced AI content writer focused on SEO,
human readability, and professional formatting.

Follow ALL these rules for EVERY response:
- Write in a natural, engaging, human-like tone ({tone}).
- Structure output with Markdown and HTML dual compatibility.
- Use exactly one H1 heading as article title.
- Use H2 and H3 headings for structure.
- Include bullet points and numbered lists where relevant.
- Bold all main keywords and important terms (Markdown: **like this**).
- Start with a compelling introduction.
- End with a strong, memorable conclusion.
- If possible, return a JSON object with "title" and "body" fields
  (body should include all markdown for outline, sections, intro, conclusion).
- The response must be at least 2000 words (unless otherwise specified).

If unsure, write extra detail rather than less.
"""

USER_PROMPT_TEMPLATE =
Write an SEO-optimized, in-depth article about "{keyword}".
Adjust your language style for this tone: "{tone}".
"""

# ------------- SmartWriter Class --------------

class SmartWriter:
    """
    SmartWriter generates long-form, SEO-optimized articles with professional formatting using Groq's Llama-3 model.
    """

    def __init__(self, model: Optional[str] = None):
        """
        Initializes the SmartWriter.
        :param model: Optional Llama-3 variant (defaults to latest available)
        """
        self.client = GroqClientSingleton.get_client()
        self.model = model or get_model_name()

    def generate_article(self, keyword: str, tone: str = "professional", json_mode: bool = True, stream: bool = False) -> Dict[str, Any]:
        """
        Generate an SEO article using Llama-3 with Groq.

        :param keyword: Target keyword/topic
        :param tone: Writing style, one of 'professional', 'casual', 'informative', 'creative'
        :param json_mode: Request output in JSON (title, body)
        :param stream: Use streaming output for UX
        :return: Dict with 'title', 'body', and 'raw' (raw string output)
        """
        sys_prompt = SYSTEM_PROMPT.format(tone=TONE_STYLES.get(tone.lower(), TONE_STYLES['professional']))
        user_prompt = USER_PROMPT_TEMPLATE.format(keyword=keyword, tone=tone)
        if json_mode:
            user_prompt += "\nReturn the article as a JSON object with 'title' and 'body'."

        logger.info("Starting LLM completion for SmartWriter...")
        completion = ""
        try:
            if stream:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    stream=True,
                    temperature=0.8,
                    max_tokens=4096
                )
                # Handle the stream event loop (prints in real time)
                print("\n[Streaming article from Llama-3...]\n")
                for chunk in response:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        sys.stdout.write(delta)
                        sys.stdout.flush()
                        completion += delta
                print("\n")
            else:
                rsp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.8,
                    max_tokens=4096
                )
                completion = rsp.choices[0].message.content
        except RateLimitError as e:
            logger.error("Groq API rate limit exceeded: %s", e)
            raise
        except Exception as e:
            logger.error(f"Groq API error: {repr(e)}")
            raise

        # --- Parse LLM output (JSON mode preferred) ---
        output = {"title": "", "body": "", "raw": completion}
        if json_mode:
            try:
                # Often returns as "```json ... ```"
                raw_txt = completion.strip()
                if raw_txt.startswith("```json"):
                    raw_txt = raw_txt.strip('` \n')[6:]  # Remove ```json
                # Fix for trailing fences and whitespace
                raw_txt = raw_txt.split("```")[0].strip()

                data = json.loads(raw_txt)
                output["title"] = data.get("title", "")
                output["body"] = data.get("body", "")
            except Exception:
                logger.warning("Failed to parse as JSON, falling back to text parsing.")
                # Try to extract title and rest
                lines = completion.splitlines()
                found_title = False
                for line in lines:
                    if line.startswith("# "):  # H1 as title
                        output["title"] = line.strip('# ').strip()
                        found_title = True
                        continue
                    if found_title:
                        output["body"] += line + "\n"
                if not output["title"]:
                    output["title"] = f"Article on {keyword}"
                if not output["body"]:
                    output["body"] = completion

        else:
            # No parsing, just return the text
            output["body"] = completion

        return output


# --------------- CLI DEMO ---------------

def print_divider():
    print("\n" + "="*60 + "\n")

def interactive_demo():
    """
    Run SmartWriter in the console with CLI input.
    """
    print("SMART CONTENT ECOSYSTEM: Article Generator (Groq Llama-3)")
    keyword = input("Enter the article keyword/topic: ").strip()
    tone = input("Select the tone (professional/casual/informative/creative): ").strip().lower()
    json_mode_str = input("Use JSON output mode? (Y/n): ").strip().lower()
    json_mode = (json_mode_str != 'n')
    stream_str = input("Stream the model output as it arrives? (y/N): ").strip().lower()
    stream = (stream_str == 'y')
    writer = SmartWriter()
    try:
        result = writer.generate_article(keyword=keyword, tone=tone, json_mode=json_mode, stream=stream)
        print_divider()
        print(f"TITLE: {result['title']}")
        print_divider()
        print(result['body'] if result['body'] else result['raw'])
        print_divider()
    except RateLimitError:
        print("Rate limit exceeded. Please wait and try again (or contact administrator).")
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    interactive_demo()

---

**Key Features & Professional Practices:**

- **Groq LLM Integration**: Uses `groq` SDK with Llama-3, API Key from the environment.
- **SmartWriter Class**: Clean API, `generate_article(keyword, tone)`, optional JSON output, PEP8, and docstrings.
- **Prompt Engineering**: Ensures SEO best practices: H1, H2, H3, bold keywords, lists, intro/conclusion.
- **JSON Mode**: Default output has `"title"` and `"body"` fields for direct post-processing.
- **Robust Error Handling**: Handles RateLimitError and client exceptions, with high-visibility logging.
- **Streaming**: Watch the model's text as it arrives for an enhanced interactive UX.
- **CLI Demo**: Run as a standalone article generator; extend or import as you wish.

---

This script is designed for direct integration in your ecosystem
and supports future growth (prompt tuning, advanced model routing, streaming applications, etc).
```
