import os
import json
import logging
import re
from groq import Groq, RateLimitError

# Configure professional logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WriterEngine")

class SmartWriter:
    """
    Advanced Content Generation Engine using Groq's Large Language Models.
    Designed for high-performance SEO article generation with robust parsing.
    """

    def __init__(self, model="llama-3-70b-8192"):
        """
        Initializes the Groq client using environment variables.
        Ensures the system is secure and production-ready.
        """
        self.api_key = os.getenv("GROQ_API_KEY", "")
        if not self.api_key:
            logger.error("System Failure: GROQ_API_KEY is not defined.")
            raise EnvironmentError("Critical Configuration Missing: GROQ_API_KEY.")
        
        self.client = Groq(api_key=self.api_key)
        self.model = model

    def _generate_system_instructions(self):
        """
        Defines the structural and stylistic guidelines for the AI agent.
        Ensures output strictly follows Markdown and JSON standards.
        """
        return (
            "You are a professional SEO Content Architect. Your objective is to craft "
            "high-quality, long-form, and authoritative articles that rank on search engines. "
            "Technical Requirements:\n"
            "1. Generate a compelling H1 title.\n"
            "2. Utilize H2 and H3 subheadings for hierarchical structure.\n"
            "3. Include a hook-driven introduction and a conclusive summary.\n"
            "4. Use semantic formatting including bullet points and bold text for key concepts.\n"
            "5. Ensure the word count targets 1500+ words for depth.\n"
            "STRICT OUTPUT PROTOCOL: Return the response ONLY as a valid JSON object. "
            "Structure: {\"title\": \"string\", \"body\": \"markdown_content\"}"
        )

    def generate_article(self, keyword, tone="professional"):
        """
        Executes the content generation workflow.
        Handles API communication and processes the raw response.
        """
        logger.info(f"Initiating generation sequence for keyword: {keyword}")
        
        system_prompt = self._generate_system_instructions()
        user_prompt = (
            f"Compose an exhaustive, SEO-optimized article regarding: '{keyword}'. "
            f"Required Tone: {tone}. Content must be ready for professional publishing."
        )

        try:
            # API Request Orchestration
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4096,
                top_p=1,
                stream=False
            )

            response_payload = completion.choices[0].message.content.strip()
            
            # Extracting and validating the JSON payload
            return self._process_and_validate_payload(response_payload)

        except RateLimitError:
            logger.error("API Gateway: Rate limit threshold exceeded.")
            return {
                "title": "Service Temporarily Unavailable",
                "body": "The system has reached its maximum capacity. Please wait before retrying."
            }
        except Exception as e:
            logger.error(f"Core Engine Exception: {str(e)}")
            return {
                "title": "System Error",
                "body": f"The generation process encountered an error: {str(e)}"
            }

    def _process_and_validate_payload(self, raw_content):
        """
        Sanitizes the raw AI output and converts it into a structured dictionary.
        Implements fallback mechanisms for non-standard JSON responses.
        """
        try:
            # Attempt to extract JSON if encapsulated in Markdown blocks
            if "```json" in raw_content:
                match = re.search(r'```json\s*(.*?)\s*```', raw_content, re.DOTALL)
                if match:
                    return json.loads(match.group(1))
            
            # Direct JSON deserialization
            return json.loads(raw_content)
        
        except (json.JSONDecodeError, Exception):
            logger.warning("Standard parsing failed. Implementing structural recovery.")
            
            # Heuristic recovery: split title and content manually
            content_lines = raw_content.split('\n')
            title = content_lines[0].replace("#", "").strip()
            body = "\n".join(content_lines[1:])
            
            return {
                "title": title if title else "Generated Article",
                "body": body if body else raw_content
            }

# End of Logic. No test scripts included to prevent deployment conflicts on Render.
