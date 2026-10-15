import base64
import glob
import os
import re
import shutil
import sys
from flask import Flask, jsonify, request, send_from_directory

# Mock nltk.inisec just like telegram/handlers/findnews.py
sys.modules["nltk.inisec"] = type("mock", (object,), {"find_spec": lambda *args, **kwargs: None})

# Add NewsBot1 root directory to sys.path so we can import Searcher, content, and database
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from Searcher.main import run_pipeline_1
from content.main import run_pipeline_2
from database.articles_db import init_db, get_article, get_articles
from database.user_service import (
    init_database,
    user_exists,
    create_user,
    get_user_settings,
    update_settings,
    reset_settings,
)
from database.conversion import gradient_tuple_to_hex, hex_to_gradient_tuple

app = Flask(__name__, static_folder=".")
HEX_COLOR_PATTERN = re.compile(r"^#?([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")


def ensure_user(user_id: int) -> None:
    """Initialize SQLite tables and ensure the local user record exists."""
    init_db()
    init_database()
    if not user_exists(user_id):
        create_user(user_id)


@app.route("/")
def serve_ui():
    """Serve the Apple OS HTML/CSS/JS interface from /UI/index.html."""
    return send_from_directory(os.path.dirname(__file__), "index.html")


@app.route("/api/settings", methods=["GET", "POST"])
def handle_settings():
    user_id = int(request.args.get("user_id", 1) if request.method == "GET" else request.json.get("user_id", 1))
    ensure_user(user_id)

    if request.method == "GET":
        s = get_user_settings(user_id)
        grad_val = s.get("gradient_color", (0, 0, 0))
        grad_hex = gradient_tuple_to_hex(grad_val) if isinstance(grad_val, (tuple, list)) else str(grad_val)
        return jsonify({
            "text_color": s.get("text_color", "#FFFFFF"),
            "gradient_color": grad_hex,
            "platform": s.get("platform", "Instagram"),
            "tone": s.get("tone", "Professional"),
            "language": s.get("language", "English"),
            "credit": s.get("credit", 100),
        })

    data = request.json or {}
    text_color = data.get("text_color", "#FFFFFF").strip()
    gradient_color = data.get("gradient_color", "#000000").strip()

    if HEX_COLOR_PATTERN.match(text_color):
        norm_text = text_color if text_color.startswith("#") else f"#{text_color}"
        update_settings.text_color(user_id, norm_text)

    if HEX_COLOR_PATTERN.match(gradient_color):
        norm_grad = gradient_color if gradient_color.startswith("#") else f"#{gradient_color}"
        update_settings.gradient_color(user_id, hex_to_gradient_tuple(norm_grad))

    if "platform" in data:
        update_settings.platform(user_id, data["platform"])
    if "tone" in data:
        update_settings.tone(user_id, data["tone"])
    if "language" in data:
        update_settings.language(user_id, data["language"])

    return jsonify({"status": "ok"})


@app.route("/api/settings/reset", methods=["POST"])
def handle_reset_settings():
    data = request.json or {}
    user_id = int(data.get("user_id", 1))
    ensure_user(user_id)
    reset_settings(user_id)
    return jsonify({"status": "reset"})


@app.route("/api/findnews", methods=["POST"])
def api_findnews():
    """Run Searcher.run_pipeline_1 and return discovered articles for the user."""
    data = request.json or {}
    user_id = int(data.get("user_id", 1))
    category = data.get("category", "tech")
    ensure_user(user_id)

    user_cfg = get_user_settings(user_id)
    if user_cfg["credit"] < 20:
        return jsonify({"error": "Not enough credits"}), 400

    run_pipeline_1(category, user_id)
    articles = get_articles(user_id) or []

    serialized = [
        {
            "slot": slot,
            "title": getattr(art, "title", "No Title") or "No Title",
            "source": getattr(art, "source", category.capitalize()),
            "summary": getattr(art, "summary", ""),
        }
        for slot, art in enumerate(articles, start=1)
    ]
    return jsonify({"articles": serialized})


@app.route("/api/create_post", methods=["POST"])
def api_create_post():
    """Run content.run_pipeline_2 and return the generated JPG and TXT from /output."""
    data = request.json or {}
    user_id = int(data.get("user_id", 1))
    slot = int(data.get("slot", 1))
    ensure_user(user_id)

    user_credit = get_user_settings(user_id)["credit"]
    if user_credit < 20:
        return jsonify({"error": "Not enough credits"}), 400

    article = get_article(user_id, slot)
    if article is None:
        return jsonify({"error": "Article not found"}), 404

    update_settings.credit(user_id, user_credit - 20)
    run_pipeline_2(slot, user_id, article)

    base_dir = os.path.join(PROJECT_ROOT, "output")
    all_folders = [
        os.path.join(base_dir, d)
        for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d))
    ]
    if not all_folders:
        return jsonify({"error": "Output folder not found"}), 500

    latest_folder = max(all_folders, key=os.path.getmtime)
    jpg_files = glob.glob(os.path.join(latest_folder, "*.jpg"))
    txt_files = glob.glob(os.path.join(latest_folder, "*.txt"))

    if not jpg_files or not txt_files:
        shutil.rmtree(latest_folder, ignore_errors=True)
        return jsonify({"error": "Generated files missing in output directory"}), 500

    try:
        with open(txt_files[0], "r", encoding="utf-8") as f:
            caption_text = f.read()
        with open(jpg_files[0], "rb") as img_f:
            b64_img = base64.b64encode(img_f.read()).decode("utf-8")
    finally:
        shutil.rmtree(latest_folder, ignore_errors=True)

    return jsonify({
        "caption": caption_text,
        "image_data_url": f"data:image/jpeg;base64,{b64_img}",
        "credit": user_credit - 20,
    })


@app.route("/api/credits/add", methods=["POST"])
def api_add_credits():
    data = request.json or {}
    user_id = int(data.get("user_id", 1))
    amount = int(data.get("amount", 50))
    ensure_user(user_id)
    current = get_user_settings(user_id)["credit"]
    update_settings.credit(user_id, current + amount)
    return jsonify({"credit": current + amount})


if __name__ == "__main__":
    os.chdir(PROJECT_ROOT)
    print("NewsBot Local UI running at: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)