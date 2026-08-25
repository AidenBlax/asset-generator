import os
import io
import time
import requests
import urllib.parse
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "pixlforge_admin_secret_2026")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "pixlforge123")

# Multi-AI Pipeline: Enhances prompt via ChatGPT/Gemini style prompt engineering
def ai_enhance_prompt(description, style, main_text):
    base_prompt = f"YouTube thumbnail background for {description}. Style: {style}."
    if "gaming" in style.lower() or "fortnite" in description.lower():
        base_prompt += " Hyperrealistic 3D Unreal Engine 5 render, action-packed, high contrast, vibrant saturated colors, dramatic rim lighting, 8k resolution."
    elif "mrbeast" in style.lower() or "vlog" in style.lower():
        base_prompt += " High energy MrBeast style thumbnail background, extreme facial reaction lighting, exaggerated cinematic scene, bright sunny day, ultra detailed, 8k."
    else:
        base_prompt += " Professional Youtube thumbnail composition, eye-catching focal point, studio lighting, hyper detailed, trending on ArtStation."
    
    return base_prompt

# Multi-AI Image Fetcher with Failover
def generate_ai_background(description, style, main_text):
    enhanced_prompt = ai_enhance_prompt(description, style, main_text)
    encoded = urllib.parse.quote(enhanced_prompt)

    # 1. Primary Engine: Pollinations AI
    url_1 = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true&seed={int(time.time())}"
    try:
        res = requests.get(url_1, timeout=12)
        if res.status_code == 200 and len(res.content) > 5000:
            return Image.open(io.BytesIO(res.content)).convert("RGBA")
    except Exception:
        pass

    # 2. Secondary Engine: Lexica AI Engine
    try:
        url_2 = f"https://lexica.art/api/v1/search?q={encoded}"
        res = requests.get(url_2, timeout=8).json()
        if res.get("images"):
            img_res = requests.get(res["images"][0]["src"], timeout=8)
            return Image.open(io.BytesIO(img_res.content)).convert("RGBA")
    except Exception:
        pass

    # 3. Fallback High-Quality Engine: Unsplash Curated Gaming/Action Background
    fallback_url = "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=1280&h=720&fit=crop"
    img_res = requests.get(fallback_url)
    return Image.open(io.BytesIO(img_res.content)).convert("RGBA")

# Draw YouTube-Style Bold Text with Thick Stroke/Outline
def draw_youtube_text(img, text, position, font_size, fill_color, stroke_color):
    draw = ImageDraw.Draw(img)
    try:
        # Try loading system bold font, fallback to default if not available
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    x, y = position
    # Draw thick stroke by offsetting text
    stroke_width = max(3, font_size // 12)
    for adj_x in range(-stroke_width, stroke_width + 1):
        for adj_y in range(-stroke_width, stroke_width + 1):
            draw.text((x + adj_x, y + adj_y), text, font=font, fill=stroke_color)
            
    draw.text((x, y), text, font=font, fill=fill_color)

def process_thumbnail(img, main_text, subtitle, is_preview=True):
    img = img.resize((1280, 720), Image.Resampling.LANCZOS)
    
    # Enhance Saturation & Contrast like real YouTube thumbnails
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.3)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.15)

    # Render Main Text (Bold Yellow/White with Black Outline)
    if main_text:
        draw_youtube_text(img, main_text.upper(), (60, 80), 72, (255, 220, 0), (0, 0, 0))

    # Render Subtitle (Clean White with Black Outline)
    if subtitle:
        draw_youtube_text(img, subtitle.upper(), (65, 170), 48, (255, 255, 255), (0, 0, 0))

    # Apply PixlForge Watermark Grid on Preview
    if is_preview:
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        try:
            w_font = ImageFont.truetype("arial.ttf", 40)
        except Exception:
            w_font = ImageFont.load_default()

        for y in range(50, 720, 160):
            draw_overlay.text((150, y), "PIXLFORGE PREVIEW - UNLOCK FOR $1.99", fill=(255, 255, 255, 110), font=w_font)
            draw_overlay.line([(0, y + 40), (1280, y + 40)], fill=(255, 0, 0, 90), width=3)

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
    description = data.get("description", "Gaming").strip()
    style = data.get("style", "Fortnite / Gaming")

    bg_img = generate_ai_background(description, style, main_text)
    final_img = process_thumbnail(bg_img, main_text, subtitle, is_preview=True)

    img_io = io.BytesIO()
    final_img.convert("RGB").save(img_io, 'JPEG', quality=75)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')

@app.route("/api/hd-download", methods=["POST"])
def generate_hd():
    data = request.get_json() or {}
    main_text = data.get("main_text", "").strip()
    subtitle = data.get("subtitle", "").strip()
    description = data.get("description", "Gaming").strip()
    style = data.get("style", "Fortnite / Gaming")

    bg_img = generate_ai_background(description, style, main_text)
    final_img = process_thumbnail(bg_img, main_text, subtitle, is_preview=False)

    img_io = io.BytesIO()
    final_img.convert("RGB").save(img_io, 'JPEG', quality=98)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name="pixlforge_hd_thumbnail.jpg")

# Admin Panel Routes
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        pwd = request.form.get("password")
        if pwd == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin"))
        else:
            return render_template("admin.html", error="Invalid Password")

    if not session.get("admin"):
        return render_template("admin.html", login_required=True)

    return render_template("admin.html", login_required=False)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
