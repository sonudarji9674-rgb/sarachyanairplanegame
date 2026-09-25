"""
Mini TikTok clone — Flask + SQLite.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000
"""

import os
import uuid
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXT = {"mp4", "mov", "webm"}

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-change-me"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB cap

db = SQLAlchemy(app)


# ---------- Step 2: Data model ----------
class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)
    caption = db.Column(db.String(300), default="")
    author = db.Column(db.String(80), default="anonymous")
    likes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


# ---------- Step 3: Feed (vertical scroll, newest first) ----------
@app.route("/")
def feed():
    videos = Video.query.order_by(Video.created_at.desc()).all()
    return render_template("feed.html", videos=videos)


# ---------- Step 4: Upload ----------
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files.get("video")
        caption = request.form.get("caption", "")
        author = request.form.get("author", "anonymous") or "anonymous"

        if not file or file.filename == "":
            flash("Choose a video file first.")
            return redirect(url_for("upload"))

        if not allowed_file(file.filename):
            flash("Unsupported format. Use mp4, mov, or webm.")
            return redirect(url_for("upload"))

        ext = file.filename.rsplit(".", 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        safe_name = secure_filename(unique_name)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], safe_name))

        video = Video(filename=safe_name, caption=caption, author=author)
        db.session.add(video)
        db.session.commit()
        return redirect(url_for("feed"))

    return render_template("upload.html")


# ---------- Step 5: Like button (AJAX-free, simple POST) ----------
@app.route("/like/<int:video_id>", methods=["POST"])
def like(video_id):
    video = Video.query.get_or_404(video_id)
    video.likes += 1
    db.session.commit()
    return redirect(url_for("feed"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
