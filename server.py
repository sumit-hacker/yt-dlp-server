from flask import Flask, request, jsonify
import yt_dlp
from yt_dlp.utils import DownloadError, ExtractorError

app = Flask(__name__)

def fetch_video_info(url, retries=2):
    ydl_opts = {"quiet": True, "skip_download": True}
    attempt = 0
    while attempt <= retries:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        except (DownloadError, ExtractorError):
            if attempt < retries:
                attempt += 1
                continue
            raise
        except Exception:
            if attempt < retries:
                attempt += 1
                continue
            raise
    return None

def format_response(info):
    response = {
        "title": info.get("title"),
        "thumbnail": info.get("thumbnail"),
        "channel": info.get("uploader"),
        "duration": info.get("duration"),
        "like_count": info.get("like_count"),
        "comment_count": info.get("comment_count"),
        "view_count": info.get("view_count"),
        "audio_streams": [],
        "video_streams": {},
        "subtitles": {"manual": {}, "auto": {}},
        "available_languages": {"subtitles": [], "audio": []},
    }

    for f in info.get("formats", []):
        stream = {
            "ext": f.get("ext"),
            "format_id": f.get("format_id"),
            "filesize": f.get("filesize") or f.get("filesize_approx"),
            "tbr": f.get("tbr"),
            "asr": f.get("asr"),
            "height": f.get("height"),
            "url": f.get("url"),
        }
        if not stream["url"]:
            continue
        if f.get("vcodec") == "none":
            response["audio_streams"].append(stream)
        else:
            resolution = str(f.get("height") or f.get("format_note") or "unknown")
            response["video_streams"].setdefault(resolution, []).append(stream)

    subtitles = info.get("subtitles", {})
    auto_captions = info.get("automatic_captions", {})
    for lang, subs in subtitles.items():
        srt = [s["url"] for s in subs if s.get("ext") == "srt"]
        if srt:
            response["subtitles"]["manual"][lang] = srt
            response["available_languages"]["subtitles"].append(lang)
    for lang, subs in auto_captions.items():
        srt = [s["url"] for s in subs if s.get("ext") == "srt"]
        if srt:
            response["subtitles"]["auto"][lang] = srt
            if lang not in response["available_languages"]["subtitles"]:
                response["available_languages"]["subtitles"].append(lang)

    return response


@app.route("/", methods=["GET"])
def home():
    return {"message": "yt-dlp API running. Use /extract?url=<video_url> or POST /extract"}


@app.route("/extract", methods=["GET", "POST"])
def extract():
    try:
        # GET → query param
        if request.method == "GET":
            url = request.args.get("url")
        else:
            # POST → JSON body
            data = request.get_json(silent=True) or {}
            url = data.get("url")

        if not url:
            return jsonify({"error": "No URL provided"}), 400

        info = fetch_video_info(url)
        structured = format_response(info)

        return jsonify(structured)

    except DownloadError as e:
        return jsonify({"error": "DownloadError", "details": str(e)}), 500
    except ExtractorError as e:
        return jsonify({"error": "ExtractorError", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Unexpected Error", "details": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
