"""
main.py

Smart Content Ecosystem - Web Service Entry Point for Render.com

This script integrates a Flask web server to run in a PaaS environment
such as Render.com. It provides home and health endpoints, ensures Render's
dynamic port assignment, and is structured for future automation expansion.

Author: Ashish (Nexovent), 2026

"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, request
from threading import Thread
import traceback
import time

# --- Core Imports ---
try:
    # Direct relative or full path for core logic import
    from core_logic.writer_engine import SmartWriter, ToneStyle, WriterConfig
    # If your package layout changes, update the import path accordingly.
except ImportError as e:
    # Log import errors and fail fast for deployment
    logging.critical(f"ImportError: Cannot import SmartWriter from core_logic.writer_engine: {e}")
    sys.exit(1)

# --- App Setup ---
app = Flask(__name__)

# --- Logging Setup (File and Console) ---
LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "web_service.log")

file_handler = RotatingFileHandler(LOG_FILE, maxBytes=2*1024*1024, backupCount=2, encoding="utf-8")
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s",
    "%Y-%m-%d %H:%M:%S"
)

file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)
app.logger.addHandler(console_handler)

app.logger.propagate = False

# --- Global variable to track health ---
HEALTH_STATUS = {
    "ready": True,
    "last_error": None,
    "uptime": time.time()
}

# --- Home Route ---
@app.route("/", methods=["GET"])
def home():
    """
    Home endpoint for service status.
    Used by Render.com to check if service is running.
    """
    app.logger.info("Home (/) endpoint called. Reporting status: online.")
    return jsonify({
        "status": "online",
        "service": "Smart Content Ecosystem Web API",
        "uptime_seconds": int(time.time() - HEALTH_STATUS["uptime"]),
        "health": HEALTH_STATUS["ready"]
    }), 200

# --- Health Route ---
@app.route("/health", methods=["GET"])
def health():
    """
    Quick Render health check endpoint.
    Returns 200 if service is up and healthy.
    """
    health_report = {
        "health": HEALTH_STATUS["ready"],
        "uptime_seconds": int(time.time() - HEALTH_STATUS["uptime"]),
        "last_error": HEALTH_STATUS["last_error"]
    }
    status_code = 200 if HEALTH_STATUS["ready"] else 500
    app.logger.info("Health (/health) endpoint called. Status: %s", HEALTH_STATUS["ready"])
    return jsonify(health_report), status_code

# --- Automation Placeholder ---
def start_automation():
    """
    Placeholder for continuous or scheduled automation tasks.
    Insert your article generation jobs or routines here.
    This function will be started in a daemon thread on service launch.

    Example:
    while True:
        # generate articles, share to services
        time.sleep(repeat_interval)
    """
    app.logger.info("start_automation() invoked (placeholder), ready for future expansion.")
    while True:
        # Sleep to simulate a background service. Replace with your automation tasks.
        time.sleep(60)
        # You may add logging/heartbeat here as required.

# --- Robust Error Handler for All Uncaught Flask Exceptions ---
@app.errorhandler(Exception)
def handle_exception(e):
    """
    Catch-all Flask error handler.
    Logs exception stacktrace for production debugging, and returns a clear error message.
    """
    tb = traceback.format_exc()
    HEALTH_STATUS["ready"] = False
    HEALTH_STATUS["last_error"] = str(e)
    app.logger.error(f"Exception occurred: {e}\nTraceback:\n{tb}")
    resp = {
        "error": "Internal Server Error",
        "detail": str(e),
        "traceback": tb if app.debug else "Contact administrator.",
    }
    return jsonify(resp), 500

# --- Sample Writer Endpoint (Optional for demonstration) ---
@app.route("/generate", methods=["POST"])
def generate_article():
    """
    Generates an article using SmartWriter.
    Expects JSON: { "keyword": "AI", "tone": "professional" }
    """
    data = request.get_json(force=True)
    keyword = data.get("keyword", "").strip()
    tone = data.get("tone", "professional").strip().lower()
    app.logger.info(f"Received article generation request: keyword='{keyword}', tone='{tone}'")
    if not keyword:
        return jsonify({"error": "Missing keyword parameter."}), 400
    try:
        writer_cfg = WriterConfig(
            tone=ToneStyle[tone.upper()] if tone in ToneStyle.__members__ else ToneStyle.PROFESSIONAL,
            min_word_count=2000
        )
        writer = SmartWriter(config=writer_cfg)
        result = writer.generate_article(keyword, tone)
        article = {
            "title": result.get("title", ""),
            "body": result.get("body", result.get("raw"))
        }
        app.logger.info(f"Article generated successfully for keyword: {keyword}")
        return jsonify({"result": article}), 200
    except Exception as e:
        app.logger.error(f"Error in /generate: {e}\n{traceback.format_exc()}")
        HEALTH_STATUS["ready"] = False
        HEALTH_STATUS["last_error"] = str(e)
        return jsonify({"error": "Failed to generate article.", "detail": str(e)}), 500

# --- Main Entrypoint ---
def main():
    """
    Main entry point to start Flask server and automation thread.
    Ensures the app works both locally and on Render.com, using the environment PORT.
    """
    port = int(os.environ.get("PORT", 5000))
    app.logger.info(f"Starting Flask Smart Content Ecosystem API on port {port}.")

    # Start automation in background thread (daemon)
    automation_thread = Thread(target=start_automation, daemon=True)
    automation_thread.start()
    app.logger.info("Automation thread started in the background.")

    try:
        # Flask 'debug' is False by default for production; Render manages reloaders.
        app.run(host="0.0.0.0", port=port, debug=False)
    except Exception as e:
        app.logger.critical(f"Flask failed to start: {e}")
        sys.exit(1)


# --- Run if main ---
if __name__ == "__main__":
    """
    This is the production entry point for Render.com.
    It launches the Flask app and the placeholder automation loop.
    """
    main()

# ----
# End of main.py
# ----
