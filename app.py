"""LP用画像生成Webアプリ - Flask メインアプリケーション"""

import base64
import os
import threading
import webbrowser
from datetime import datetime
from uuid import uuid4
from flask import Flask, render_template, request, jsonify, send_from_directory

from config import (
    GOOGLE_API_KEY, UPLOAD_FOLDER, OUTPUT_FOLDER,
    ALLOWED_EXTENSIONS, ASPECT_RATIOS, MAX_PATTERNS, IS_VERCEL,
)
from generator.image_composer import generate_variations

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024 if IS_VERCEL else 32 * 1024 * 1024

# 生成進捗の管理
generation_status = {}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    session_id = request.args.get("session_id", "")
    # session_idがあれば保存済み画像のURLを渡す
    product_url = ""
    background_url = ""
    if session_id:
        session_dir = os.path.join(UPLOAD_FOLDER, session_id)
        if os.path.exists(os.path.join(session_dir, "product")):
            product_url = f"/uploads/{session_id}/product"
        if os.path.exists(os.path.join(session_dir, "background")):
            background_url = f"/uploads/{session_id}/background"
    return render_template("index.html",
                           aspect_ratios=ASPECT_RATIOS,
                           max_patterns=MAX_PATTERNS,
                           session_id=session_id,
                           product_url=product_url,
                           background_url=background_url)


@app.route("/uploads/<session_id>/<filename>")
def serve_upload(session_id, filename):
    session_dir = os.path.join(UPLOAD_FOLDER, session_id)
    return send_from_directory(session_dir, filename)


@app.route("/generate", methods=["POST"])
def generate():
    # バリデーション
    if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_api_key_here":
        return jsonify({"error": "GOOGLE_API_KEYが設定されていません。.envファイルを確認してください。"}), 400

    # session_id: 既存があれば再利用、なければ新規発行
    session_id = request.form.get("session_id", "").strip()
    if not session_id:
        session_id = str(uuid4())[:8]

    session_dir = os.path.join(UPLOAD_FOLDER, session_id)
    os.makedirs(session_dir, exist_ok=True)

    # 画像データ取得: 新しいアップロードがあればそちらを使用、なければ保存済みを使用
    product_file = request.files.get("product_image")
    background_file = request.files.get("background_image")

    product_bytes = None
    background_bytes = None

    # 商品画像
    if product_file and product_file.filename and allowed_file(product_file.filename):
        product_bytes = product_file.read()
        with open(os.path.join(session_dir, "product"), "wb") as f:
            f.write(product_bytes)
    else:
        product_path = os.path.join(session_dir, "product")
        if os.path.exists(product_path):
            with open(product_path, "rb") as f:
                product_bytes = f.read()

    # 背景画像
    if background_file and background_file.filename and allowed_file(background_file.filename):
        background_bytes = background_file.read()
        with open(os.path.join(session_dir, "background"), "wb") as f:
            f.write(background_bytes)
    else:
        background_path = os.path.join(session_dir, "background")
        if os.path.exists(background_path):
            with open(background_path, "rb") as f:
                background_bytes = f.read()

    if not product_bytes or not background_bytes:
        return jsonify({"error": "商品画像と背景画像の両方が必要です。"}), 400

    aspect_ratio = request.form.get("aspect_ratio", "1:1")
    custom_ratio = request.form.get("custom_ratio", "").strip()
    if custom_ratio:
        aspect_ratio = custom_ratio

    count = min(int(request.form.get("count", 1)), MAX_PATTERNS)
    user_instructions = request.form.get("instructions", "").strip()
    text_space = request.form.get("text_space", "none")

    if IS_VERCEL:
        # Vercel: 同期生成 → Base64で返却
        count = min(count, 1)
        try:
            results = generate_variations(
                api_key=GOOGLE_API_KEY,
                product_bytes=product_bytes,
                background_bytes=background_bytes,
                aspect_ratio=aspect_ratio,
                count=count,
                user_instructions=user_instructions,
                text_space=text_space,
            )
            images_b64 = []
            for img_data in results:
                images_b64.append("data:image/jpeg;base64," + base64.b64encode(img_data).decode())
            return jsonify({"session_id": session_id, "images": images_b64})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        # ローカル: バックグラウンドスレッドで生成
        batch_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:20]
        generation_status[batch_id] = {"completed": 0, "total": count, "done": False, "error": None}

        thread = threading.Thread(
            target=_run_generation,
            args=(batch_id, product_bytes, background_bytes, aspect_ratio, count, user_instructions, text_space),
        )
        thread.start()

        return jsonify({"batch_id": batch_id, "session_id": session_id})


def _run_generation(batch_id, product_bytes, background_bytes, aspect_ratio, count, user_instructions, text_space):
    """バックグラウンドで画像生成を実行"""
    try:
        def on_progress(completed, total):
            generation_status[batch_id]["completed"] = completed

        results = generate_variations(
            api_key=GOOGLE_API_KEY,
            product_bytes=product_bytes,
            background_bytes=background_bytes,
            aspect_ratio=aspect_ratio,
            count=count,
            user_instructions=user_instructions,
            text_space=text_space,
            progress_callback=on_progress,
        )

        # 出力フォルダに保存
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        saved_files = []
        for i, image_data in enumerate(results):
            filename = f"{batch_id}_{i + 1}.jpg"
            filepath = os.path.join(OUTPUT_FOLDER, filename)
            with open(filepath, "wb") as f:
                f.write(image_data)
            saved_files.append(filename)

        generation_status[batch_id]["done"] = True
        generation_status[batch_id]["files"] = saved_files

    except Exception as e:
        generation_status[batch_id]["done"] = True
        generation_status[batch_id]["error"] = str(e)


@app.route("/status/<batch_id>")
def status(batch_id):
    info = generation_status.get(batch_id)
    if not info:
        return jsonify({"error": "不明なバッチIDです。"}), 404
    return jsonify(info)


@app.route("/preview/<batch_id>")
def preview(batch_id):
    session_id = request.args.get("session_id", "")
    info = generation_status.get(batch_id, {})
    files = info.get("files", [])
    error = info.get("error")
    return render_template("preview.html", batch_id=batch_id, files=files, error=error,
                           output_folder=os.path.abspath(OUTPUT_FOLDER),
                           session_id=session_id)


@app.route("/output/<filename>")
def serve_output(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)


if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # ブラウザ自動起動
    threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:5000")).start()

    print("=" * 50)
    print("  LP用画像生成ツール 起動中...")
    print("  http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=False, port=5000)
