import os
import uuid
from flask import Flask, render_template, request, jsonify
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

# Ensure output directory exists
OUTPUT_DIR = os.path.join('static', 'outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Replace this link later with your real Payhip checkout link!
PAYMENT_LINK = "https://payhip.com"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        title = data.get('title', 'MY ASSET TITLE')
        subtitle = data.get('subtitle', 'SUBTITLE HERE')
        bg_color = data.get('color', '#1e293b')

        # 1. Create Base Canvas (1280x720 HD)
        img = Image.new('RGB', (1280, 720), color=bg_color)
        draw = ImageDraw.Draw(img)

        # 2. Add Graphic Accent Banner
        draw.rectangle([0, 600, 1280, 720], fill="#0f172a")

        # Load standard fonts
        try:
            font_large = ImageFont.truetype("arial.ttf", 64)
            font_small = ImageFont.truetype("arial.ttf", 36)
            font_watermark = ImageFont.truetype("arial.ttf", 48)
        except IOError:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_watermark = ImageFont.load_default()

        # 3. Draw User Text
        draw.text((100, 250), title.upper(), fill="#ffffff", font=font_large)
        draw.text((100, 350), subtitle, fill="#38bdf8", font=font_small)

        # 4. Apply Watermark Overlay
        for y in range(100, 720, 200):
            for x in range(100, 1280, 350):
                draw.text((x, y), "PREVIEW ONLY - PAY TO UNLOCK", fill="#ef4444", font=font_watermark)

        # 5. Save Watermarked Image
        filename = f"preview_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        img.save(filepath)

        return jsonify({
            "success": True,
            "preview_url": f"/static/outputs/{filename}",
            "payment_url": PAYMENT_LINK
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    # Dynamic port configuration for Render hosting
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)