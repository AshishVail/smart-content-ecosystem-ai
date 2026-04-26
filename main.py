import os
import sys
import logging
from flask import Flask, request, jsonify, render_template_string

# Ensure the core_logic directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from core_logic.writer_engine import SmartWriter
except ImportError:
    sys.path.append(os.getcwd())
    from core_logic.writer_engine import SmartWriter

# Setup professional logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API_Gateway")

app = Flask(__name__)
writer_engine = SmartWriter()

# HTML Dashboard Template with Markdown Preview Support
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Content Engine | Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .prose h1 { font-size: 2rem; font-weight: 800; margin-bottom: 1rem; color: #111827; }
        .prose h2 { font-size: 1.5rem; font-weight: 700; margin-top: 1.5rem; margin-bottom: 0.75rem; color: #1f2937; }
        .prose h3 { font-size: 1.25rem; font-weight: 600; margin-top: 1.25rem; margin-bottom: 0.5rem; color: #374151; }
        .prose p { margin-bottom: 1rem; line-height: 1.6; color: #4b5563; }
        .prose ul { list-style-type: disc; padding-left: 1.5rem; margin-bottom: 1rem; }
        .prose table { width: 100%; border-collapse: collapse; margin: 1rem 0; border: 1px solid #e5e7eb; }
        .prose th, .prose td { border: 1px solid #e5e7eb; padding: 0.5rem; text-align: left; }
        .prose th { background-color: #f9fafb; }
    </style>
</head>
<body class="bg-slate-50">
    <nav class="bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center shadow-sm">
        <div class="flex items-center gap-2">
            <div class="w-8 h-8 bg-blue-600 rounded flex items-center justify-center text-white font-bold">A</div>
            <span class="text-xl font-bold">AI Content Console <span class="text-blue-600">v2.1</span></span>
        </div>
        <div class="text-emerald-600 text-sm font-medium flex items-center gap-2">
            <span class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span> Online
        </div>
    </nav>

    <main class="max-w-7xl mx-auto px-6 py-10">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            
            <!-- Controls (4 cols) -->
            <div class="lg:col-span-4 space-y-6">
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
                    <h3 class="font-bold text-slate-800 mb-4">Content Generator</h3>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-xs font-bold uppercase text-slate-500 mb-1">Target Keyword</label>
                            <input type="text" id="testKeyword" placeholder="e.g. Best AI Tools" class="w-full border p-3 rounded-lg outline-none focus:ring-2 focus:ring-blue-500">
                        </div>
                        <div>
                            <label class="block text-xs font-bold uppercase text-slate-500 mb-1">Article Tone</label>
                            <select id="testTone" class="w-full border p-3 rounded-lg outline-none">
                                <option value="professional">Professional</option>
                                <option value="informative">Informative</option>
                                <option value="creative">Creative</option>
                            </select>
                        </div>
                        <button onclick="runTest()" id="testBtn" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg transition-all">
                            Generate Article
                        </button>
                    </div>
                </div>

                <div class="bg-slate-800 text-slate-300 p-6 rounded-2xl shadow-inner">
                    <h4 class="text-xs font-bold uppercase text-slate-500 mb-3">API Endpoint</h4>
                    <code class="text-emerald-400 text-xs break-all block">POST /generate</code>
                </div>
            </div>

            <!-- Results (8 cols) -->
            <div class="lg:col-span-8">
                <div id="loading" class="hidden bg-white p-12 rounded-2xl border border-slate-200 text-center shadow-sm">
                    <div class="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p class="text-slate-600 font-medium">Engine is writing your SEO article... please wait 30-60 seconds.</p>
                </div>

                <div id="resultArea" class="hidden space-y-4">
                    <div class="flex gap-2">
                        <button onclick="showTab('preview')" id="tab-preview" class="px-4 py-2 bg-blue-600 text-white rounded-t-lg font-bold">Article Preview</button>
                        <button onclick="showTab('json')" id="tab-json" class="px-4 py-2 bg-slate-200 text-slate-700 rounded-t-lg font-bold">Raw JSON</button>
                    </div>

                    <div id="preview-box" class="bg-white p-8 md:p-12 rounded-b-2xl rounded-tr-2xl border border-slate-200 shadow-sm prose max-w-none min-h-[500px]">
                        <!-- Rendered Article -->
                    </div>

                    <div id="json-box" class="hidden bg-slate-900 p-6 rounded-b-2xl rounded-tr-2xl border border-slate-200 shadow-sm overflow-x-auto">
                        <pre id="jsonResult" class="text-emerald-400 text-xs"></pre>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        let currentResult = null;

        function showTab(type) {
            const preview = document.getElementById('preview-box');
            const json = document.getElementById('json-box');
            const tPrev = document.getElementById('tab-preview');
            const tJson = document.getElementById('tab-json');

            if(type === 'preview') {
                preview.classList.remove('hidden');
                json.classList.add('hidden');
                tPrev.className = 'px-4 py-2 bg-blue-600 text-white rounded-t-lg font-bold';
                tJson.className = 'px-4 py-2 bg-slate-200 text-slate-700 rounded-t-lg font-bold';
            } else {
                json.classList.remove('hidden');
                preview.classList.add('hidden');
                tJson.className = 'px-4 py-2 bg-blue-600 text-white rounded-t-lg font-bold';
                tPrev.className = 'px-4 py-2 bg-slate-200 text-slate-700 rounded-t-lg font-bold';
            }
        }

        async function runTest() {
            const keyword = document.getElementById('testKeyword').value;
            const tone = document.getElementById('testTone').value;
            const btn = document.getElementById('testBtn');
            const loading = document.getElementById('loading');
            const resultArea = document.getElementById('resultArea');

            if(!keyword) return alert('Please enter a keyword');

            btn.disabled = true;
            loading.classList.remove('hidden');
            resultArea.classList.add('hidden');

            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ keyword, tone })
                });
                const data = await response.json();
                
                currentResult = data;
                
                // Set JSON view
                document.getElementById('jsonResult').textContent = JSON.stringify(data, null, 2);
                
                // Set Preview view
                const bodyContent = data.body || "No content generated";
                document.getElementById('preview-box').innerHTML = marked.parse(bodyContent);
                
                loading.classList.add('hidden');
                resultArea.classList.remove('hidden');
                showTab('preview');

            } catch (err) {
                alert('Connection Error with AI Engine');
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
    return render_template_string(DASHBOARD_HTML)

@app.route('/generate', methods=['POST'])
def generate_content():
    data = request.get_json()
    if not data or 'keyword' not in data:
        return jsonify({"status": "error", "message": "Keyword is required"}), 400
    
    keyword = data.get('keyword')
    tone = data.get('tone', 'professional')
    
    try:
        # Calls the updated SmartWriter with better cleaning
        result = writer_engine.generate_article(keyword=keyword, tone=tone)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
