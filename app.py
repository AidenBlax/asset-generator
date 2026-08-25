import os
import io
import time
import requests
import urllib.parse
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

# Multi-AI High Quality Engine Fetcher
def fetch_hd_background(description, style):
    prompt_query = f"YouTube thumbnail background {description}, style {style}, hyperrealistic, 8k resolution, highly detailed, vibrant lighting"
    encoded_prompt = urllib.parse.quote(prompt_query)

    # Provider 1: Pollinations AI (High Detail)
    url_1 = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&seed={int(time.time())}"
    try:
        res = requests.get(url_1, timeout=10)
        if res.status_code == 200 and len(res.content) > 5000:
            return Image.open(io.BytesIO(res.content)).convert("RGBA")
    except Exception:
        pass

    # Provider 2: Lexica Engine Fallback
    try:
        url_2 = f"https://lexica.art/api/v1/search?q={encoded_prompt}"
        res = requests.get(url_2, timeout=8).json()
        if res.get("images"):
            img_res = requests.get(res["images"][0]["src"], timeout=8)
            return Image.open(io.BytesIO(img_res.content)).convert("RGBA")
    except Exception:
        pass

    # Provider 3: Backup Solid High Quality Unsplash Abstract Background
    fallback_url = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1280&h=720&fit=crop"
    img_res = requests.get(fallback_url)
    return Image.open(io.BytesIO(img_res.content)).convert("RGBA")


def draw_text_and_watermark(img, main_text, subtitle, is_preview=True):
    img = img.resize((1280, 720))
    draw = ImageDraw.Draw(img)

    # Load default font
    font_main = ImageFont.load_default()
    font_sub = ImageFont.load_default()

    # Draw dark banner behind text for high contrast
    if main_text:
        draw.rectangle([50, 450, 1230, 650], fill=(0, 0, 0, 180))
        draw.text((70, 470), main_text.upper(), fill=(255, 215, 0), font=font_main)
    
    if subtitle:
        draw.text((70, 560), subtitle, fill=(255, 255, 255), font=font_sub)

    # If Preview mode, apply heavy diagonal watermark across the canvas
    if is_preview:
        overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Diagonal lines & watermark text
        for y in range(0, 720, 120):
            overlay_draw.text((200, y), "PIXLFORGE PREVIEW - UNLOCK FOR $1.99", fill=(255, 255, 255, 90), font=font_main)
            overlay_draw.line([(0, y), (1280, y + 100)], fill=(255, 0, 0, 80), width=4)
        
        img = Image.alpha_composite(img, overlay)

    return img


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/preview", methods=["POST"])
def generate_preview():
    data = request.get_json() or {}
    main_text = data.get("main_text", "").strip()
    subtitle = data.get("subtitle", "").strip()
    description = data.get("description", "Gaming Tech").strip()
    style = data.get("style", "Vibrant")

    bg_img = fetch_hd_background(description, style)
    final_img = draw_text_and_watermark(bg_img, main_text, subtitle, is_preview=True)

    img_io = io.BytesIO()
    final_img.convert("RGB").save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/jpeg')


@app.route("/api/hd-download", methods=["POST"])
def generate_hd():
    # Triggered after Paystack payment confirmation
    data = request.get_json() or {}
    main_text = data.get("main_text", "").strip()
    subtitle = data.get("subtitle", "").strip()
    description = data.get("description", "Gaming Tech").strip()
    style = data.get("style", "Vibrant")

    bg_img = fetch_hd_background(description, style)
    final_img = draw_text_and_watermark(bg_img, main_text, subtitle, is_preview=False)

    img_io = io.BytesIO()
    final_img.convert("RGB").save(img_io, 'JPEG', quality=95)
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name="pixlforge_hd_thumbnail.jpg")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
