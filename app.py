from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import uuid

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def format_size(size):
    if not size:
        return "Unknown"
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def extract_formats(info):
    videos = []
    audios = []

    for f in info.get("formats", []):
        if f.get("vcodec") != "none" and f.get("acodec") == "none":
            videos.append({
                "format_id": f.get("format_id"),
                "resolution": f.get("height"),
                "ext": f.get("ext"),
                "size": format_size(f.get("filesize")),
                "fps": f.get("fps"),
            })

        if f.get("acodec") != "none" and f.get("vcodec") == "none":
            audios.append({
                "format_id": f.get("format_id"),
                "abr": f.get("abr"),
                "ext": f.get("ext"),
                "size": format_size(f.get("filesize")),
            })

    videos = sorted(videos, key=lambda x: x["resolution"] or 0, reverse=True)
    audios = sorted(audios, key=lambda x: x["abr"] or 0, reverse=True)

    return videos, audios


@app.route("/")
def home():
    return "API is running"


@app.route("/info", methods=["POST"])
def get_info():
    try:
        data = request.get_json()
        url = data.get("url")

        if not url:
            return jsonify({"error": "No URL"}), 400

        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)

        videos, audios = extract_formats(info)

        return jsonify({
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "videos": videos[:8],
            "audios": audios[:6],
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download", methods=["POST"])
def download():
    try:
        data = request.get_json()
        url = data["url"]
        format_id = data["format_id"]
        media_type = data["type"]

        uid = str(uuid.uuid4())
        output = os.path.join(DOWNLOAD_FOLDER, f"{uid}.%(ext)s")

        if media_type == "audio":
            ydl_opts = {
                "format": format_id,
                "outtmpl": output,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                }],
            }
        else:
            ydl_opts = {
                "format": f"{format_id}+bestaudio/best",
                "merge_output_format": "mp4",
                "outtmpl": output,
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if media_type == "audio":
            filename = os.path.splitext(filename)[0] + ".mp3"
        else:
            filename = os.path.splitext(filename)[0] + ".mp4"

        return jsonify({"file": os.path.basename(filename)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/file")
def serve_file():
    name = request.args.get("path")
    path = os.path.join(DOWNLOAD_FOLDER, os.path.basename(name))
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run()