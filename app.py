import os
import uuid
import urllib.parse
import requests
from flask import Flask, render_template, request, jsonify
from PIL import Image, ImageDraw, ImageFont
import io

app = Flask(__name__)

OUTPUT_DIR = os.path.join('static', 'outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Replace with your actual Payhip product link
PAYMENT_LINK = "https://payhip.com/b/YOUR_LINK"

def add_watermark(image_bytes):
    """Adds a watermarked banner over the AI image."""
    img = Image.open(io.BytesIO(image_bytes)).convert('RGBA')
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Dark banner at the top
    draw.rectangle([0, 0, img.width, 90], fill=(15, 23, 42, 220))

    try:
        font = ImageFont.truetype("arial.ttf", 42)
    except IOError:
        font = ImageFont.load_default()

    draw.text((30, 25), "PREVIEW ONLY • PAY TO UNLOCK CLEAN HD", fill=(239, 68, 68, 255), font=font)

    watermarked_img = Image.alpha_composite(img, overlay).convert('RGB')
    
    img_io = io.BytesIO()
    watermarked_img.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io.getvalue()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        title = data.get('title', 'EPIC MOMENT')
        subtitle = data.get('subtitle', 'Gaming')

        # 1. Build a detailed AI prompt
        raw_prompt = (
            f"A high quality cinematic YouTube thumbnail about {subtitle}, "
            f"featuring prominent text that says '{title.upper()}', "
            f"vibrant glowing colors, 8k resolution, trending on ArtStation, gaming aesthetic"
        )
        
        # 2. URL-encode the prompt for Pollinations API
        encoded_prompt = urllib.parse.quote(raw_prompt)
        ai_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1280&height=720&seed={uuid.uuid4().int % 10000}&nologo=true"

        # 3. Fetch the AI-generated image from Pollinations (Free)
        response = requests.get(ai_url, timeout=25)

        if response.status_code == 200:
            # 4. Apply watermark
            watermarked_bytes = add_watermark(response.content)

            # 5. Save locally for preview
            filename = f"preview_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            with open(filepath, "wb") as f:
                f.write(watermarked_bytes)

            return jsonify({
                "success": True,
                "preview_url": f"/static/outputs/{filename}",
                "payment_url": PAYMENT_LINK
            })
        else:
            return jsonify({"success": False, "error": "AI image server busy. Try again."}), 500

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
