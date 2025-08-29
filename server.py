from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return {
        "message": "yt-dlp server running",
        "usage": {
            "POST": "/extract  with JSON { 'url': '<video_url>' }",
            "GET": "/extract?url=<video_url>"
        }
    }

@app.route("/extract", methods=["GET", "POST"])
def extract():
    # Handle POST (JSON body)
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        url = data.get("url")
    else:
        # Handle GET (?url=...)
        url = request.args.get("url")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    ydl_opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            for f in info.get("formats", []):
                formats.append({
                    "format_id": f.get("format_id"),
                    "ext": f.get("ext"),
                    "resolution": f.get("resolution") or f"{f.get('width')}x{f.get('height')}",
                    "fps": f.get("fps"),
                    "filesize": f.get("filesize"),
                    "url": f.get("url"),
                })

            return jsonify({
                "title": info.get("title"),
                "uploader": info.get("uploader"),
                "thumbnail": info.get("thumbnail"),
                "formats": formats
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
