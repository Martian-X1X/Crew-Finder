from flask import Flask, request, jsonify, send_from_directory
import requests
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Read API Key from environment variable
API_KEY = os.environ.get("SERPAPI_KEY")

# Serve the frontend
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# API endpoint for search
@app.route('/search', methods=['GET'])
def search_google_maps():
    query = request.args.get('q')
    location = request.args.get('location', '')

    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    if not API_KEY:
        return jsonify({"error": "SERPAPI_KEY environment variable not set"}), 500

    search_query = f"{query} {location}".strip()

    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_maps",
        "type": "search",
        "q": search_query,
        "api_key": API_KEY,
        "hl": "en"
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        data = response.json()

        if "error" in data:
            return jsonify({"error": data["error"]}), 400

        results = data.get("local_results", [])
        return jsonify({"local_results": results})

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


if __name__ == '__main__':
    print("🚀 CrewFinder is running!")
    app.run(host='0.0.0.0', port=5000, debug=True)