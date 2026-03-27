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

# API endpoint for search WITH PAGINATION
@app.route('/search', methods=['GET'])
def search_google_maps():
    query = request.args.get('q')
    location = request.args.get('location', '')
    pages = request.args.get('pages', 3)  # Number of pages to fetch (default: 3)
    
    # Try to convert pages to int, default to 3 if invalid
    try:
        pages = int(pages)
        pages = min(pages, 5)  # Limit to 5 pages max to avoid rate limits
    except:
        pages = 3

    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    if not API_KEY:
        return jsonify({"error": "SERPAPI_KEY environment variable not set"}), 500

    search_query = f"{query} {location}".strip()
    
    all_results = []
    
    # Fetch multiple pages of results
    for page in range(pages):
        # Calculate start position (0, 20, 40, 60, ...)
        start = page * 20
        
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_maps",
            "type": "search",
            "q": search_query,
            "api_key": API_KEY,
            "hl": "en",
            "start": start  # Pagination offset
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()

            if "error" in data:
                # If error on first page, return error
                if page == 0:
                    return jsonify({"error": data["error"]}), 400
                # Otherwise, stop fetching more pages
                break

            results = data.get("local_results", [])
            
            # If no results on this page, stop
            if not results:
                break
                
            all_results.extend(results)
            
            # If less than 20 results, no more pages available
            if len(results) < 20:
                break

        except Exception as e:
            # If error on first page, return error
            if page == 0:
                return jsonify({"error": f"Server error: {str(e)}"}), 500
            # Otherwise, stop fetching more pages
            break

    return jsonify({
        "local_results": all_results,
        "total": len(all_results),
        "pages_fetched": min(page + 1, pages)
    })


# API endpoint for single page search (faster)
@app.route('/search-single', methods=['GET'])
def search_single_page():
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
    data = request.get_json()
    phones = data.get('phones', [])
    message = data.get('message', '')
    device = data.get('device', 'desktop')
    
    if not phones:
        return jsonify({"error": "No phone numbers provided"}), 400
    
    links = []
    
    for phone in phones:
        clean_phone = ''.join(filter(str.isdigit, phone))
        if len(clean_phone) == 10:
            clean_phone = f"1{clean_phone}"
        
        if device == 'desktop':
            desktop_app_link = f"ooma://sms?to=%2B{clean_phone}&body={requests.utils.quote(message)}"
            web_portal_link = f"https://office.ooma.com/app/dialer/sms?to=%2B{clean_phone}&body={requests.utils.quote(message)}"
            links.append({
                "phone": phone,
                "desktop_app": desktop_app_link,
                "web_portal": web_portal_link,
                "recommended": web_portal_link
            })
        else:
            mobile_link = f"ooma://sms?to=%2B{clean_phone}&body={requests.utils.quote(message)}"
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


# Batch SMS preparation
@app.route('/prepare-batch-sms', methods=['POST'])
def prepare_batch_sms():
    data = request.get_json()
    phones = data.get('phones', [])
    message = data.get('message', '')
    business_names = data.get('business_names', [])
    
    if not phones:
        return jsonify({"error": "No phone numbers provided"}), 400
    
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
    print("🚀 CrewFinder with Ooma Integration + Pagination!")
    print("→ Local: http://127.0.0.1:5000")
    print("→ Your Ooma Number: (330) 443-7800")
    print("→ Ooma Portal: https://office.ooma.com")
    app.run(host='0.0.0.0', port=5000, debug=True)
