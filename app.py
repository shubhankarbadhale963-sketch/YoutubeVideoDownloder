from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)


# -------------------------------
# Helpers
# -------------------------------

def format_size(size):
    """Convert bytes to readable size"""
    if not size:
        return "Unknown"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def extract_formats(info):
    """Extract clean video/audio options"""

    videos = []
    audios = []

    for f in info["formats"]:

        # VIDEO FORMATS
        if f.get("vcodec") != "none" and f.get("acodec") == "none":
            videos.append({
                "format_id": f["format_id"],
                "resolution": f.get("height"),
                "ext": f.get("ext"),
                "size": format_size(f.get("filesize")),
                "fps": f.get("fps")
            })

        # AUDIO FORMATS
        if f.get("acodec") != "none" and f.get("vcodec") == "none":
            audios.append({
                "format_id": f["format_id"],
                "abr": f.get("abr"),
                "ext": f.get("ext"),
                "size": format_size(f.get("filesize"))
            })

    # sort qualities
    videos = sorted(videos, key=lambda x: x["resolution"] or 0, reverse=True)
    audios = sorted(audios, key=lambda x: x["abr"] or 0, reverse=True)

    return videos, audios


# -------------------------------
# Routes
# -------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# --------------------------------
# STEP 1: FETCH VIDEO INFO
# --------------------------------
@app.route("/info", methods=["POST"])
def get_info():

    url = request.json.get("url")

    ydl_opts = {
        "quiet": True,
        "skip_download": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    videos, audios = extract_formats(info)

    response = {
        "title": info["title"],
        "thumbnail": info["thumbnail"],
        "duration": info.get("duration"),
        "videos": videos[:8],   # limit for UI
        "audios": audios[:6]
    }

    return jsonify(response)


# --------------------------------
# STEP 2: DOWNLOAD SELECTED FORMAT
# --------------------------------
@app.route("/download", methods=["POST"])
def download():

    url = request.json["url"]
    format_id = request.json["format_id"]
    media_type = request.json["type"]

    unique_id = str(uuid.uuid4())

    output_template = f"{DOWNLOAD_FOLDER}/{unique_id}.%(ext)s"

    # AUDIO DOWNLOAD
    if media_type == "audio":

        ydl_opts = {
            "format": format_id,
            "outtmpl": output_template,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }]
        }

    # VIDEO DOWNLOAD
    else:

        ydl_opts = {
            "format": f"{format_id}+bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": output_template
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    # normalize final filename
    if media_type == "audio":
        filename = os.path.splitext(filename)[0] + ".mp3"
    else:
        filename = os.path.splitext(filename)[0] + ".mp4"

    return jsonify({"file": filename})


# --------------------------------
# STEP 3: SERVE FILE
# --------------------------------
@app.route("/file")
def serve_file():
    path = request.args.get("path")
    return send_file(path, as_attachment=True)


# --------------------------------
# RUN
# --------------------------------
if __name__ == "__main__":
    app.run(debug=True)