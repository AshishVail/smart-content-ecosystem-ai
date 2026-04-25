import os
import sys
import logging
from flask import Flask, request, jsonify, render_template_string

# Adding current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from core_logic.writer_engine import SmartWriter
    import core_logic.writer_engine as we
except ImportError:
    sys.path.append(os.getcwd())
    from core_logic.writer_engine import SmartWriter

# Setup professional logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API_Gateway")

app = Flask(__name__)
writer_engine = SmartWriter()

# HTML Dashboard Template (Professional UI)
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Console | Content Ecosystem</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Fira+Code&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; }
        pre { font-family: 'Fira Code', monospace; }
        .endpoint-badge { background: #10b981; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }
    </style>
</head>
<body class="bg-slate-50 text-slate-900">
    <nav class="bg-white border-b border-slate-200 px-8 py-4 flex justify-between items-center">
        <div class="flex items-center gap-2">
            <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">A</div>
            <span class="text-xl font-bold tracking-tight">AI Content Engine <span class="text-blue-600">v2.0</span></span>
        </div>
        <div class="flex items-center gap-4">
            <span class="flex items-center gap-1.5 text-sm font-medium text-emerald-600">
                <span class="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse"></span> Server Online
            </span>
        </div>
    </nav>

    <main class="max-w-6xl mx-auto px-8 py-12">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-12">
            <!-- Documentation Section -->
            <div>
                <h2 class="text-3xl font-bold mb-4 text-slate-800">API Documentation</h2>
                <p class="text-slate-600 mb-8 text-lg">Use this endpoint to automate high-quality SEO article generation.</p>
                
                <div class="space-y-6">
                    <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                        <div class="flex items-center gap-3 mb-4">
                            <span class="endpoint-badge">POST</span>
                            <code class="text-blue-600 font-bold">/generate</code>
                        </div>
                        <p class="text-sm text-slate-500 mb-4">Generates a full-length Markdown article based on a keyword.</p>
                        
                        <h4 class="text-xs font-bold uppercase text-slate-400 mb-2">Request Body (JSON)</h4>
                        <pre class="bg-slate-900 text-blue-300 p-4 rounded-lg text-sm">
{
  "keyword": "string",
  "tone": "professional | informative | creative"
}</pre>
                    </div>

                    <div class="bg-slate-800 p-6 rounded-xl shadow-lg">
                        <h4 class="text-xs font-bold uppercase text-slate-400 mb-4">Direct cURL Example</h4>
                        <pre class="text-emerald-400 text-xs overflow-x-auto">
curl -X POST {{ url_for('generate_content', _external=True) }} \\
     -H "Content-Type: application/json" \\
     -d '{"keyword": "AI Trends", "tone": "professional"}'</pre>
                    </div>
                </div>
            </div>

            <!-- Live Test Console -->
            <div class="bg-white rounded-2xl border border-slate-200 shadow-xl overflow-hidden">
                <div class="bg-slate-50 px-6 py-4 border-b border-slate-200">
                    <h3 class="font-bold text-slate-700">Live API Explorer</h3>
                </div>
                <div class="p-6">
                    <div class="mb-4">
                        <label class="block text-sm font-semibold mb-2">Keyword</label>
                        <input type="text" id="testKeyword" placeholder="e.g. Future of Finance" class="w-full border border-slate-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 outline-none">
                    </div>
                    <div class="mb-6">
                        <label class="block text-sm font-semibold mb-2">Tone</label>
                        <select id="testTone" class="w-full border border-slate-300 rounded-lg p-3">
                            <option value="professional">Professional</option>
                            <option value="informative">Informative</option>
                            <option value="creative">Creative</option>
                        </select>
                    </div>
                    <button onclick="runTest()" id="testBtn" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg transition-all flex items-center justify-center gap-2">
                        Execute Request
                    </button>

                    <div id="loading" class="hidden mt-4 text-center text-blue-600 text-sm font-medium">
                        Processing AI Generation...
                    </div>

                    <div id="responseBox" class="hidden mt-6">
                        <h4 class="text-xs font-bold uppercase text-slate-400 mb-2">Response JSON</h4>
                        <div class="bg-slate-900 rounded-lg p-4 max-h-[300px] overflow-y-auto">
                            <pre id="jsonResult" class="text-emerald-400 text-xs"></pre>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        async function runTest() {
            const keyword = document.getElementById('testKeyword').value;
            const tone = document.getElementById('testTone').value;
            const btn = document.getElementById('testBtn');
            const loading = document.getElementById('loading');
            const responseBox = document.getElementById('responseBox');
            const jsonResult = document.getElementById('jsonResult');

            if(!keyword) return alert('Enter a keyword');

            btn.disabled = true;
            loading.classList.remove('hidden');
            responseBox.classList.add('hidden');

            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ keyword, tone })
                });
                const data = await response.json();
                jsonResult.textContent = JSON.stringify(data, null, 2);
                responseBox.classList.remove('hidden');
            } catch (err) {
                alert('API Error');
            } finally {
                btn.disabled = false;
                loading.classList.add('hidden');
            }
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    """Returns a professional API Dashboard."""
    return render_template_string(DASHBOARD_HTML)

@app.route('/generate', methods=['POST'])
def generate_content():
    """Main API endpoint for article generation."""
    data = request.get_json()
    if not data or 'keyword' not in data:
        return jsonify({"status": "error", "message": "Keyword is required"}), 400
    
    keyword = data.get('keyword')
    tone = data.get('tone', 'professional')
    
    logger.info(f"API Request: Keyword={keyword}, Tone={tone}")
    
    try:
        result = writer_engine.generate_article(keyword=keyword, tone=tone)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Execution Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
