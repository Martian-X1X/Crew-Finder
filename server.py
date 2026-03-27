from flask import Flask, request, jsonify, send_from_directory
import requests
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# SerpApi Configuration
API_KEY = os.environ.get("SERPAPI_KEY")

# Ooma Configuration - Your number
OOMA_PHONE_NUMBER = "3304437800"
OOMA_WEB_PORTAL = "https://office.ooma.com"

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


# Generate Ooma-specific links
@app.route('/ooma-links', methods=['POST'])
def generate_ooma_links():
    """
    Generate links that open Ooma specifically
    - Desktop: Opens Ooma web portal or desktop app
    - Mobile: Opens Ooma mobile app
    """
    data = request.get_json()
    
    phones = data.get('phones', [])
    message = data.get('message', '')
    device = data.get('device', 'desktop')  # 'desktop' or 'mobile'
    
    if not phones:
        return jsonify({"error": "No phone numbers provided"}), 400
    
    links = []
    
    for phone in phones:
        # Clean phone number
        clean_phone = ''.join(filter(str.isdigit, phone))
        if len(clean_phone) == 10:
            clean_phone = f"1{clean_phone}"
        
        if device == 'desktop':
            # Desktop options:
            # Option 1: Ooma desktop app custom URL scheme (try this first)
            desktop_app_link = f"ooma://sms?to=%2B{clean_phone}&body={requests.utils.quote(message)}"
            
            # Option 2: Ooma web portal (direct SMS compose page)
            # Note: You may need to be logged into Ooma portal
            web_portal_link = f"https://office.ooma.com/app/dialer/sms?to=%2B{clean_phone}&body={requests.utils.quote(message)}"
            
            links.append({
                "phone": phone,
                "desktop_app": desktop_app_link,
                "web_portal": web_portal_link,
                "recommended": web_portal_link  # More reliable
            })
        else:
            # Mobile: Standard SMS link (opens Ooma if it's your SMS app)
            # Or use Ooma's custom URL scheme for mobile
            mobile_link = f"ooma://sms?to=%2B{clean_phone}&body={requests.utils.quote(message)}"
            # Fallback to standard SMS
            standard_sms = f"sms:%2B{clean_phone}?body={requests.utils.quote(message)}"
            
            links.append({
                "phone": phone,
                "ooma_app": mobile_link,
                "standard_sms": standard_sms
            })
    
    return jsonify({
        "device": device,
        "links": links,
        "count": len(links),
        "ooma_portal": OOMA_WEB_PORTAL
    })


# Batch SMS preparation - returns all data for sending
@app.route('/prepare-batch-sms', methods=['POST'])
def prepare_batch_sms():
    """
    Prepare batch SMS data
    Returns formatted data for copy-paste or API use
    """
    data = request.get_json()
    
    phones = data.get('phones', [])
    message = data.get('message', '')
    business_names = data.get('business_names', [])
    
    if not phones:
        return jsonify({"error": "No phone numbers provided"}), 400
    
    # Format phone numbers
    formatted = []
    for i, phone in enumerate(phones):
        clean_phone = ''.join(filter(str.isdigit, phone))
        if len(clean_phone) == 10:
            clean_phone = f"1{clean_phone}"
        
        formatted.append({
            "original": phone,
            "formatted": f"+{clean_phone}",
            "business": business_names[i] if i < len(business_names) else "Unknown"
        })
    
    # Generate copy-paste formats
    comma_separated = ", ".join([f['formatted'] for f in formatted])
    newline_separated = "\n".join([f['formatted'] for f in formatted])
    
    return jsonify({
        "phones": formatted,
        "message": message,
        "copy_formats": {
            "comma_separated": comma_separated,
            "newline_separated": newline_separated,
            "count": len(formatted)
        },
        "ooma_portal": "https://office.ooma.com/app/dialer"
    })


if __name__ == '__main__':
    print("🚀 CrewFinder with Ooma Integration!")
    print("→ Local: http://127.0.0.1:5000")
    print("→ Your Ooma Number: (330) 443-7800")
    print("→ Ooma Portal: https://office.ooma.com")
    app.run(host='0.0.0.0', port=5000, debug=True)