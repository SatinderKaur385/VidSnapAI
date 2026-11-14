from pathlib import Path
import secrets
import uuid

from flask import Flask, abort, flash, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

from config import ELEVENLABS_API_KEY, FLASK_SECRET_KEY
from generate_process import create_reel
from text_to_audio import text_to_speech_file


PROJECT_ROOT = Path(__file__).resolve().parent
UPLOAD_FOLDER = PROJECT_ROOT / "user_uploads"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

app = Flask(__name__)
app.config["SECRET_KEY"] = FLASK_SECRET_KEY or secrets.token_hex(32)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "GET":
        return render_template("create.html")

    description = request.form.get("text", "").strip()
    uploaded_files = [
        upload for upload in request.files.values()
        if upload and upload.filename
    ]

    if not uploaded_files:
        flash("Choose at least one image to create a reel.", "danger")
        return redirect(url_for("create"))

    for upload in uploaded_files:
        extension = Path(upload.filename).suffix.lower().lstrip(".")
        if extension not in ALLOWED_EXTENSIONS:
            flash("Use JPG, JPEG, PNG, or WEBP images.", "danger")
            return redirect(url_for("create"))

    if description and not ELEVENLABS_API_KEY:
        flash(
            "To add narration, set ELEVENLABS_API_KEY in your .env file. "
            "You can also leave the text box empty to create a silent reel.",
            "danger",
        )
        return redirect(url_for("create"))

    safe_uploads = [
        (upload, secure_filename(upload.filename))
        for upload in uploaded_files
    ]
    if any(not safe_name for _, safe_name in safe_uploads):
        flash("One of the uploaded image filenames is invalid.", "danger")
        return redirect(url_for("create"))

    reel_id = uuid.uuid4().hex
    reel_folder = app.config["UPLOAD_FOLDER"] / reel_id
    reel_folder.mkdir(parents=True, exist_ok=False)

    for index, (upload, safe_name) in enumerate(safe_uploads, start=1):
        image_name = f"{index:03d}_{safe_name}"
        upload.save(reel_folder / image_name)

    (reel_folder / "desc.txt").write_text(description, encoding="utf-8")

    try:
        if description:
            text_to_speech_file(description, reel_folder)
        create_reel(reel_folder)
    except RuntimeError as error:
        flash(str(error), "danger")
        return redirect(url_for("create"))

    flash("Your reel is ready.", "success")
    return redirect(url_for("gallery"))


@app.route("/gallery")
def gallery():
    reels = []
    upload_folder = app.config["UPLOAD_FOLDER"]
    if not upload_folder.is_dir():
        return render_template("gallery.html", reels=reels)

    for folder in upload_folder.iterdir():
        reel_path = folder / "reel.mp4"
        if folder.is_dir() and reel_path.is_file():
            description_path = folder / "desc.txt"
            description = (
                description_path.read_text(encoding="utf-8").strip()
                if description_path.is_file()
                else ""
            )
            reels.append({
                "id": folder.name,
                "description": description or "Image reel",
                "created_at": reel_path.stat().st_mtime,
            })

    reels.sort(key=lambda reel: reel["created_at"], reverse=True)
    return render_template("gallery.html", reels=reels)


@app.route("/reels/<reel_id>")
def reel_file(reel_id):
    try:
        uuid.UUID(reel_id)
    except ValueError:
        abort(404)
    return send_from_directory(
        app.config["UPLOAD_FOLDER"] / reel_id,
        "reel.mp4",
        mimetype="video/mp4",
    )


if __name__ == "__main__":
    app.run(debug=True)
