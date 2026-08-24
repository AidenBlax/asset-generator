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

PAYMENT_LINK = "https://payhip.com/b/YOUR_LINK"

def add_watermark(image_bytes):
    """Overlays a clean, high-contrast watermark banner over the preview image."""
    img = Image.open(io.BytesIO(image_bytes)).convert('RGBA')
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Dark translucent banner top bar
    draw.rectangle([0, 0, img.width, 80], fill=(15, 23, 42, 220))

    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except IOError:
        font = ImageFont.load_default()

    draw.text((20, 20), "PREVIEW ONLY • UNLOCK FULL HD ON PAYHIP", fill=(239, 68, 68, 255), font=font)

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
        data = request.get_json() or {}
        title = data.get('title', 'EPIC CONTENT')
        subtitle = data.get('subtitle', 'Gaming')

        # Refined prompt engineered for high-converting YouTube thumbnails
        raw_prompt = (
            f"Professional YouTube thumbnail about {subtitle}, featuring bold text '{title.upper()}', "
            f"vibrant dramatic cinematic lighting, 8k resolution, trending on Artstation, clean layout"
        )
        encoded_prompt = urllib.parse.quote(raw_prompt)

        # Fallback list of models to try if one is busy
        models = ["flux", "turbo", "deliberate"]
        image_bytes = None

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

        for model in models:
            seed = uuid.uuid4().int % 100000
            ai_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1280&height=720&model={model}&seed={seed}&nologo=true"
            try:
                res = requests.get(ai_url, headers=headers, timeout=12)
                if res.status_code == 200 and 'image' in res.headers.get('Content-Type', ''):
                    image_bytes = res.content
                    break
            except requests.exceptions.RequestException:
                continue

        if image_bytes:
            watermarked_bytes = add_watermark(image_bytes)
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
            return jsonify({
                "success": False,
                "error": "Image servers busy. Please tap generate once more!"
            }), 500

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
