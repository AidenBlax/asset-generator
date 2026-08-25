import os
import time
import requests
import urllib.parse
from flask import Flask, render_template, request, jsonify, redirect
import stripe

app = Flask(__name__)

# Configure Stripe API Key (Set in Render Environment Variables)
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_placeholder")
DOMAIN = os.environ.get("DOMAIN", "https://pixlforge.com")


def fetch_ai_background(visual_description, main_title):
    """Multi-engine failover system to fetch a high-quality background."""
    search_query = f"{visual_description} {main_title}".strip()
    encoded_query = urllib.parse.quote(search_query)

    # Engine 1: Pollinations AI (Generative)
    try:
        url = f"https://image.pollinations.ai/prompt/{encoded_query}%20youtube%20thumbnail%20background%204k%20vibrant%20detailed?width=1280&height=720&nologo=true"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return url
    except Exception:
        pass

    # Engine 2: Lexica AI (Search-based AI renders)
    try:
        url = f"https://lexica.art/api/v1/search?q={encoded_query}%20thumbnail"
        res = requests.get(url, timeout=8)
        if res.status_code == 200:
            data = res.json()
            if data.get("images"):
                return data["images"][0]["src"]
    except Exception:
        pass

    # Engine 3: Unsplash Engine (High Quality Stock Fallback)
    try:
        clean_query = urllib.parse.quote(visual_description if visual_description else "abstract background")
        url = f"https://source.unsplash.com/1280x720/?{clean_query},wallpaper"
        res = requests.head(url, timeout=5)
        if res.status_code in [200, 302]:
            return url
    except Exception:
        pass

    # Ultimate Safety Fallback
    return "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1280&q=80"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate-preview", methods=["POST"])
def generate_preview():
    try:
        data = request.get_json() or {}
        main_text = data.get("main_text", "").strip()
        subtitle = data.get("subtitle", "").strip()
        visual_desc = data.get("visual_desc", "").strip()

        if not main_text:
            return jsonify({"success": False, "error": "Main Title Text is required."}), 400

        # Fetch background image using multi-engine system
        bg_url = fetch_ai_background(visual_desc, main_text)

        return jsonify({
            "success": True,
            "main_text": main_text,
            "subtitle": subtitle,
            "bg_url": bg_url
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    """Handles $1.99 payment via Stripe."""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "PixlForge HD Ultra Thumbnail (1080p)",
                        "description": "Full HD Unwatermarked Thumbnail Download",
                    },
                    "unit_amount": 199,  # $1.99 USD
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{DOMAIN}/?payment=success",
            cancel_url=f"{DOMAIN}/?payment=cancelled",
        )
        return jsonify({"checkout_url": session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
