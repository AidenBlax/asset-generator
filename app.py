import os
import uuid
import urllib.parse
import requests
from flask import Flask, render_template, request, jsonify
from PIL import Image, ImageDraw, ImageFont
import io

# THIS LINE DEFINES 'app' SO RENDER/GUNICORN CAN FIND IT
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

        # Build prompt for Pollinations AI
        raw_prompt = (
            f"A high quality YouTube thumbnail about {subtitle}, "
            f"bold text '{title.upper()}', vibrant cinematic lighting, 8k resolution"
        )
        
        encoded_prompt = urllib.parse.quote(raw_prompt)
        ai_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1280&height=720&nologo=true"

        # Headers to prevent request blocking
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(ai_url, headers=headers, timeout=20)

        # Verify image format before processing
        if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
            watermarked_bytes = add_watermark(response.content)

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
                "error": "The AI image generator is busy right now. Please click generate again!"
            }), 500

    except Exception as e:
        return jsonify({"success": False, "error": "Server timeout. Try again in a few seconds."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
