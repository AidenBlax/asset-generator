@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        title = data.get('title', 'EPIC MOMENT')
        subtitle = data.get('subtitle', 'Gaming')

        # 1. Build prompt
        raw_prompt = (
            f"A high quality YouTube thumbnail about {subtitle}, "
            f"bold text '{title.upper()}', vibrant cinematic lighting, 8k resolution"
        )
        
        encoded_prompt = urllib.parse.quote(raw_prompt)
        ai_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1280&height=720&nologo=true"

        # 2. Add headers so the request isn't blocked
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(ai_url, headers=headers, timeout=20)

        # 3. Verify we received a valid image response
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
