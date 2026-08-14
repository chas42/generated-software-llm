import os
import re
import tempfile
import subprocess
from typing import List, Tuple

from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25MB

TARGET_RE = re.compile(r"^(\d{1,5})x(\d{1,5})$")


def json_error(message: str, status: int):
    return jsonify({"error": message}), status


def parse_target_size(value: str) -> Tuple[int, int]:
    if not value:
        raise ValueError("targetSize is required")
    m = TARGET_RE.match(value.strip())
    if not m:
        raise ValueError("targetSize must be in the form WIDTHxHEIGHT (e.g., 500x500)")
    w = int(m.group(1))
    h = int(m.group(2))
    if w <= 0 or h <= 0:
        raise ValueError("targetSize dimensions must be positive")
    if w > 5000 or h > 5000:
        raise ValueError("targetSize too large (max 5000x5000)")
    return w, h


def parse_delay_ms(value: str) -> int:
    # OpenAPI default says 10 (ms). We'll honor that when missing.
    if value is None or value == "":
        return 10
    try:
        d = int(value)
    except ValueError as e:
        raise ValueError("delay must be an integer (milliseconds)") from e
    if d < 0:
        raise ValueError("delay must be >= 0")
    return d


def parse_bool(value: str) -> bool:
    if value is None or value == "":
        return False
    v = value.strip().lower()
    return v in ("1", "true", "t", "yes", "y", "on")


def run_convert(args: List[str]) -> None:
    # ImageMagick may be available as "convert" or "magick convert"
    candidates = ["convert", "magick"]
    last_err = None
    for bin_name in candidates:
        try:
            if bin_name == "magick":
                cmd = ["magick", "convert"] + args
            else:
                cmd = ["convert"] + args
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return
        except FileNotFoundError as e:
            last_err = e
            continue
        except subprocess.CalledProcessError as e:
            err = (e.stderr or b"").decode("utf-8", errors="replace").strip()
            raise RuntimeError(err or "Image conversion failed") from e
    raise RuntimeError("ImageMagick convert not found") from last_err


def resize_to_png(input_path: str, output_path: str, width: int, height: int) -> None:
    # Keep aspect ratio, then pad to exact WxH
    size = f"{width}x{height}"
    run_convert([
        input_path,
        "-auto-orient",
        "-resize", size,
        "-background", "none",
        "-gravity", "center",
        "-extent", size,
        output_path,
    ])


def assemble_gif(frame_paths: List[str], output_gif: str, delay_ms: int) -> None:
    # ImageMagick delay uses centiseconds (1/100s). Convert ms -> cs.
    delay_cs = max(1, int(round(delay_ms / 10.0)))
    args = ["-delay", str(delay_cs), "-loop", "0"] + frame_paths + [output_gif]
    run_convert(args)


@app.route("/create-gif", methods=["POST"])
def create_gif():
    try:
        images = request.files.getlist("images")
        if not images:
            return json_error("images is required", 400)
        if len(images) > 200:
            return json_error("too many images (max 200)", 400)

        try:
            width, height = parse_target_size(request.form.get("targetSize"))
        except ValueError as e:
            return json_error(str(e), 400)

        try:
            delay_ms = parse_delay_ms(request.form.get("delay"))
        except ValueError as e:
            return json_error(str(e), 400)

        append_reverted = parse_bool(request.form.get("appendReverted"))

        with tempfile.TemporaryDirectory(prefix="gif_creator_") as tmpdir:
            frame_paths: List[str] = []

            for idx, storage in enumerate(images):
                if not storage or storage.filename is None:
                    continue

                fname = secure_filename(storage.filename) or f"image_{idx}"
                in_path = os.path.join(tmpdir, f"in_{idx}_{fname}")
                storage.save(in_path)

                out_path = os.path.join(tmpdir, f"frame_{idx:04d}.png")
                resize_to_png(in_path, out_path, width, height)
                frame_paths.append(out_path)

            if not frame_paths:
                return json_error("no valid images were provided", 400)

            if append_reverted and len(frame_paths) > 1:
                # Forward then backward, avoid duplicating the last frame
                frame_paths = frame_paths + list(reversed(frame_paths[:-1]))

            out_gif = os.path.join(tmpdir, "output.gif")
            assemble_gif(frame_paths, out_gif, delay_ms)

            return send_file(
                out_gif,
                mimetype="image/gif",
                as_attachment=False,
                download_name="created.gif",
            )

    except RuntimeError as e:
        return json_error(str(e), 500)
    except Exception:
        return json_error("Internal Server Error", 500)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
