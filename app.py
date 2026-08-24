import time
import requests
import urllib.parse
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# List of free public image generation endpoints for fallback
PRIMARY_API = "https://image.pollinations.ai/prompt/"
SECONDARY_API = "https://api.v2.emojis.sh/generate/" # Example fallback API format

def generate_image_with_fallback(prompt):
    """
    Tries multiple image endpoints and retries if servers are busy.
    """
    encoded_prompt = urllib.parse.quote(prompt)
    
    # 1. Primary Attempt: Pollinations AI
    primary_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&nologo=true"
    for attempt in range(2):  # Try 2 times with a short pause
        try:
            response = requests.get(primary_url, timeout=12)
            if response.status_code == 200:
                return primary_url
        except requests.exceptions.RequestException:
            time.sleep(1)  # Wait 1 sec before retrying primary server
            
    # 2. Secondary Fallback Attempt (Lexica / Alternative Engine)
    try:
        fallback_url = f"https://lexica.art/api/v1/search?q={encoded_prompt}"
        res = requests.get(fallback_url, timeout=8)
        if res.status_code == 200:
            data = res.json()
            if data.get("images"):
                return data["images"][0]["src"]
    except Exception:
        pass

    # 3. Final Safe Fallback: High-quality placeholder image so the app never breaks
    placeholder_url = f"https://placehold.co/512x512/2b2b36/ffffff/png?text={urllib.parse.quote('Server Busy - Try Again')}"
    return placeholder_url

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json() or {}
    prompt = data.get("prompt", "").strip()
    
    if not prompt:
        return jsonify({"success": False, "error": "Please enter a prompt"}), 400
        
    image_url = generate_image_with_fallback(prompt)
    
    return jsonify({
        "success": True,
        "image_url": image_url
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
