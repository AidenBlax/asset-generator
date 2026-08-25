import os
import io
import time
import requests
import urllib.parse
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

app = Flask(__name__)

# Multi-AI Engine Image Retrieval (Ensures servers are NEVER busy)
def fetch_high_quality_bg(description, style):
    # Construct professional YouTube thumbnail prompts based on user reference styles
    style_prompts = {
        "Gaming / Fortnite": "gaming thumbnail background, vibrant neon lighting, high action, cinematic, Unreal Engine 5 render, 8k",
        "MrBeast Action": "high energy action scene, dramatic lighting, vivid colors, hyper-detailed, extreme depth of field, 8k photo",
        "High-Contrast Viral": "vibrant colorful youtube thumbnail background, bright lighting, dramatic perspective, hyperrealistic, 8k",
        "Dark & Cinematic": "dark atmospheric cinematic lighting, intense mood, high contrast, ray tracing, 8k render"
    }
    
    base_style = style_prompts.get(style, style_prompts["Gaming / Fortnite"])
    full_prompt = f"{description}, {base_style}, no text, masterpiece"
    encoded_prompt = urllib.parse.quote(full_prompt)

    # AI Provider 1: Pollinations AI (Primary HD)
    try:
        url_1 = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&seed={int(time.time())}"
        res = requests.get(url_1, timeout=12)
        if res.status_code == 200 and len(res.content) > 10000:
            return Image.open(io.BytesIO(res.content)).convert("RGBA")
    except Exception:
        pass

    # AI Provider 2: Lexica Engine (Secondary Fallback)
    try:
        url_2 = f"https://lexica.art/api/v1/search?q={encoded_prompt}"
        res = requests.get(url_2, timeout=8).json()
        if res.get("images"):
            img_res = requests.get(res["images"][0]["src"], timeout=8)
            return Image.open(io.BytesIO(img_res.content)).convert("RGBA")
    except Exception:
        pass

    # Backup High Quality Unsplash Gaming/Action Canvas
    fallback_url = "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=1280&h=720&fit=crop"
    img_res = requests.get(fallback_url)
    return Image.open(io.BytesIO(img_res.content)).convert("RGBA")


def apply_pro_thumbnail_design(base_img, main_text, subtitle, style, is_preview=True):
    # 1. Resize to YouTube standard (1280x720) & enhance contrast/saturation like MrBeast/Fortnite thumbnails
    img = base_img.resize((1280, 720))
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.3) # 30% saturation boost
    
    # 2. Add dramatic top & bottom dark vignette gradient for text readability
    overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    # Bottom text gradient shield
    for i in range(250):
        alpha = int((i / 250) * 180)
        draw_overlay.line([(0, 720 - i), (1280, 720 - i)], fill=(0, 0, 0, alpha))
        
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # 3. Text Rendering with Thick Outlines & Dropshadows
    try:
        # Standard system fonts
        font_main = ImageFont.truetype("arialbd.ttf", 85)
        font_sub = ImageFont.truetype("arialbd.ttf", 55)
    except Exception:
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # Draw Main Text (Yellow/Gold with thick Black Border - Fortnite/Viral Style)
    if main_text:
        x, y = 60, 480
        text_upper = main_text.upper()
        
        # Thick stroke/outline effect
        outline_range = 6
        for ox in range(-outline_range, outline_range + 1):
            for oy in range(-outline_range, outline_range + 1):
                draw.text((x + ox, y + oy), text_upper, font=font_main, fill=(0, 0, 0, 255))
                
        # Main Text Fill (Vibrant Yellow #FFD700)
        draw.text((x, y), text_upper, font=font_main, fill=(255, 215, 0, 255))

    # Draw Subtitle (White with Black Border)
    if subtitle:
        sx, sy = 65, 590
        sub_upper = subtitle.upper()
        
        for ox in range(-4, 5):
            for oy in range(-4, 5):
                draw.text((sx + ox, sy + oy), sub_upper, font=font_sub, fill=(0, 0, 0, 255))
                
        draw.text((sx, sy), sub_upper, font=font_sub, fill=(255, 255, 255, 255))

    # 4. Watermark for Free Peak Preview
    if is_preview:
        wm_layer = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        wm_draw = ImageDraw.Draw(wm_layer)
        
        # Diagonal lines and lock text across the preview
        for pos in range(0, 1280, 300):
            wm_draw.text((pos, 200), "PIXLFORGE PREVIEW - UNLOCK FOR $1.99", fill=(255, 255, 255, 90), font=font_main)
            wm_draw.text((pos - 100, 400), "PIXLFORGE.COM - WATERMARK", fill=(255, 215, 0, 90), font=font_main)
            wm_draw.line([(0, pos/2), (1280, pos/2 + 200)], fill=(255, 0, 0, 100), width=6)
            
        img = Image.alpha_composite(img, wm_layer)

    return img


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/preview", methods=["POST"])
def generate_preview():
    data = request.get_json() or {}
    main_text = data.get("main_text", "").strip()
    subtitle = data.get("subtitle", "").strip()
    description = data.get("description", "Gaming computer setup").strip()
    style = data.get("style", "Gaming / Fortnite")

    bg_img = fetch_high_quality_bg(description, style)
    final_img = apply_pro_thumbnail_design(bg_img, main_text, subtitle, style, is_preview=True)

    img_io = io.BytesIO()
    final_img.convert("RGB").save(img_io, 'JPEG', quality=75)
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/jpeg')


@app.route("/api/hd-download", methods=["POST"])
def generate_hd():
    data = request.get_json() or {}
    main_text = data.get("main_text", "").strip()
    subtitle = data.get("subtitle", "").strip()
    description = data.get("description", "Gaming computer setup").strip()
    style = data.get("style", "Gaming / Fortnite")

    bg_img = fetch_high_quality_bg(description, style)
    final_img = apply_pro_thumbnail_design(bg_img, main_text, subtitle, style, is_preview=False)

    img_io = io.BytesIO()
    final_img.convert("RGB").save(img_io, 'JPEG', quality=95)
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name="pixlforge_hd_thumbnail.jpg")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
