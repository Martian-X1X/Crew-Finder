from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Your SerpApi Key
API_KEY = "cdd347a25101d3845335e181f736843926ded257931aad7a59af91cc38e4ee70"

@app.route('/search', methods=['GET'])
def search_google_maps():
    query = request.args.get('q')
    location = request.args.get('location', '')

    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

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


# For local development
if __name__ == '__main__':
    print("🚀 CrewFinder Backend is running!")
    print("→ Local: http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)