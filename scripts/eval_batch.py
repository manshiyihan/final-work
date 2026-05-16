#!/usr/bin/env python3
import argparse
import csv
import json
import mimetypes
from pathlib import Path
from urllib import error, request


def build_multipart_form_data(fields, files):
    boundary = "----CombModelEvalBoundary7MA4YWxkTrZu0gW"
    lines = []
    for name, value in fields.items():
        lines.extend(
            [
                f"--{boundary}",
                f'Content-Disposition: form-data; name="{name}"',
                "",
                str(value),
            ]
        )
    for name, file_path in files.items():
        filename = Path(file_path).name
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        file_bytes = Path(file_path).read_bytes()
        lines.extend(
            [
                f"--{boundary}",
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"',
                f"Content-Type: {content_type}",
                "",
            ]
        )
        lines.append(file_bytes)
    lines.append(f"--{boundary}--")
    lines.append("")

    body = b""
    for line in lines:
        if isinstance(line, bytes):
            body += line + b"\r\n"
        else:
            body += line.encode("utf-8") + b"\r\n"
    return body, boundary


def post_verify(api_base, audio_path):
    body, boundary = build_multipart_form_data({"input_type": "batch_eval"}, {"audio": str(audio_path)})
    req = request.Request(
        f"{api_base}/api/verify",
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_manifest(manifest_path):
    if not manifest_path:
        return {}
    label_map = {}
    with open(manifest_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            filename = (row.get("filename") or "").strip()
            label = (row.get("label") or "").strip()
            if filename:
                label_map[filename] = label
    return label_map


def main():
    parser = argparse.ArgumentParser(description="Batch evaluate audio files via /api/verify.")
    parser.add_argument("--audio_dir", type=str, required=True, help="Directory containing audio files")
    parser.add_argument("--api_base", type=str, default="http://127.0.0.1:8000", help="API base URL")
    parser.add_argument("--output_csv", type=str, default="results/eval_results.csv", help="Output CSV path")
    parser.add_argument(
        "--manifest_csv",
        type=str,
        default="",
        help="Optional manifest CSV with columns: filename,label",
    )
    args = parser.parse_args()

    audio_dir = Path(args.audio_dir)
    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    label_map = load_manifest(args.manifest_csv)

    audio_files = []
    for ext in ("*.wav", "*.mp3", "*.flac"):
        audio_files.extend(audio_dir.rglob(ext))
    audio_files = sorted(audio_files)

    rows = []
    for audio_path in audio_files:
        try:
            result = post_verify(args.api_base, audio_path)
            rows.append(
                {
                    "filename": audio_path.name,
                    "ground_truth": label_map.get(audio_path.name, ""),
                    "final_label": result.get("final_label", ""),
                    "speaker_result": result.get("speaker_result", ""),
                    "spoof_result": result.get("spoof_result", ""),
                    "risk_score": result.get("risk_score", ""),
                    "latency_ms": result.get("latency_ms", ""),
                    "ok": result.get("ok", False),
                    "error": result.get("error", ""),
                }
            )
        except error.URLError as exc:
            rows.append(
                {
                    "filename": audio_path.name,
                    "ground_truth": label_map.get(audio_path.name, ""),
                    "final_label": "",
                    "speaker_result": "",
                    "spoof_result": "",
                    "risk_score": "",
                    "latency_ms": "",
                    "ok": False,
                    "error": f"request failed: {exc}",
                }
            )

    with open(output_csv, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "filename",
                "ground_truth",
                "final_label",
                "speaker_result",
                "spoof_result",
                "risk_score",
                "latency_ms",
                "ok",
                "error",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Batch evaluation finished. files={len(rows)}, output={output_csv}")


if __name__ == "__main__":
    main()
