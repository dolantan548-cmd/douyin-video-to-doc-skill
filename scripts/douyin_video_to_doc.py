import argparse
import json
import os
import re
import subprocess
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import requests


USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/121.0.2277.107 "
    "Version/17.0 Mobile/15E148 Safari/604.1"
)
HEADERS = {"User-Agent": USER_AGENT}
MODEL_URLS = {
    "base": "https://hf-mirror.com/ggerganov/whisper.cpp/resolve/main/ggml-base.bin",
    "small": "https://hf-mirror.com/ggerganov/whisper.cpp/resolve/main/ggml-small.bin",
}
DEFAULT_OUTPUT_DIR = Path.home() / "douyin-video-docs"


def extract_url(text: str) -> str:
    urls = re.findall(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        text,
    )
    if not urls:
        raise ValueError("No URL found in input text")
    return urls[0]


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[\\/:*?\"<>|]+", "-", text)
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff\- ]+", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text[:48] or "douyin-video"


def fetch_router_data(share_text: str) -> dict:
    share_url = extract_url(share_text)
    share_response = requests.get(share_url, headers=HEADERS, timeout=30, allow_redirects=True)
    share_response.raise_for_status()
    final_url = share_response.url
    video_id = final_url.split("?")[0].strip("/").split("/")[-1]
    page_url = f"https://www.iesdouyin.com/share/video/{video_id}"

    response = requests.get(page_url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    match = re.search(r"window\._ROUTER_DATA\s*=\s*(.*?)</script>", response.text, re.DOTALL)
    if not match:
        raise RuntimeError("Failed to find Douyin router data in page HTML")

    payload = json.loads(match.group(1).strip())
    loader = payload["loaderData"]
    if "video_(id)/page" in loader:
        item = loader["video_(id)/page"]["videoInfoRes"]["item_list"][0]
    elif "note_(id)/page" in loader:
        item = loader["note_(id)/page"]["videoInfoRes"]["item_list"][0]
    else:
        raise RuntimeError("Unsupported Douyin page structure")

    play_url = item["video"]["play_addr"]["url_list"][0].replace("playwm", "play")
    return {
        "share_url": share_url,
        "resolved_url": final_url,
        "video_id": item["aweme_id"],
        "title": item.get("desc", "").strip() or f"douyin-{item['aweme_id']}",
        "author": item.get("author", {}).get("nickname", ""),
        "duration_ms": item.get("video", {}).get("duration"),
        "play_url": play_url,
        "raw_item": item,
    }


def download_file(url: str, target: Path) -> None:
    if target.exists() and target.stat().st_size > 0:
        return
    with requests.get(url, headers=HEADERS, timeout=60, stream=True) as response:
        response.raise_for_status()
        with target.open("wb") as handle:
            for chunk in response.iter_content(8192):
                if chunk:
                    handle.write(chunk)


def run_ffmpeg(args: list[str], cwd: Path) -> None:
    subprocess.run(args, cwd=str(cwd), check=True)


def ensure_model(model_name: str, models_dir: Path) -> Path:
    models_dir.mkdir(parents=True, exist_ok=True)
    model_path = models_dir / f"ggml-{model_name}.bin"
    if model_path.exists() and model_path.stat().st_size > 0:
        return model_path
    url = MODEL_URLS[model_name]
    download_file(url, model_path)
    return model_path


def srt_to_text(srt_path: Path, txt_path: Path) -> None:
    cleaned = []
    for raw_line in srt_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.isdigit() or "-->" in line:
            continue
        cleaned.append(line)
    txt_path.write_text("\n".join(cleaned), encoding="utf-8")


def write_metadata(meta: dict, path: Path) -> None:
    export = {
        "video_id": meta["video_id"],
        "title": meta["title"],
        "author": meta["author"],
        "share_url": meta["share_url"],
        "resolved_url": meta["resolved_url"],
        "duration_ms": meta["duration_ms"],
        "play_url": meta["play_url"],
    }
    path.write_text(json.dumps(export, ensure_ascii=False, indent=2), encoding="utf-8")


def write_draft(meta: dict, transcript_txt: str, output_path: Path, model_name: str) -> None:
    slug = slugify(meta["title"])
    today = date.today().isoformat()
    doc_path = output_path / f"{today}-douyin-{slug}-{meta['video_id']}.draft.md"
    body = f"""# {meta['title']} 视频整理

## 基本信息

- 视频标题：{meta['title']}
- 作者：{meta['author'] or '未知'}
- 抖音链接：`{meta['share_url']}`
- 抖音视频 ID：`{meta['video_id']}`
- 转写模型：`{model_name}`
- 处理日期：`{today}`

## 处理说明

这条视频暂未直接拿到可复用的官方字幕，以下“字幕原文”来自本地 ASR 转写。

## 内容整理

待补充：

- 核心观点
- 完整论证链路
- 关键细节
- 作者假设与局限
- 可直接复用的结论

## 字幕原文（本地 ASR）

```text
{transcript_txt}
```
"""
    doc_path.write_text(body, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Douyin share text or URL")
    parser.add_argument("--model", choices=sorted(MODEL_URLS.keys()), default="small")
    parser.add_argument(
        "--output-dir",
        default=os.environ.get("DOUYIN_VIDEO_TO_DOC_OUTPUT_DIR", str(DEFAULT_OUTPUT_DIR)),
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    models_dir = output_dir / "models"

    meta = fetch_router_data(args.input)
    video_id = meta["video_id"]

    mp4_path = output_dir / f"{video_id}.mp4"
    wav_path = output_dir / f"{video_id}.wav"
    srt_path = output_dir / f"{video_id}.{args.model}.srt"
    txt_path = output_dir / f"{video_id}.{args.model}.txt"
    metadata_path = output_dir / f"{video_id}.metadata.json"

    download_file(meta["play_url"], mp4_path)
    if not wav_path.exists():
        run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(mp4_path),
                "-ar",
                "16000",
                "-ac",
                "1",
                str(wav_path),
            ],
            cwd=output_dir,
        )

    ensure_model(args.model, models_dir)

    if not srt_path.exists():
        run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-i",
                wav_path.name,
                "-af",
                (
                    "whisper="
                    f"model=models/ggml-{args.model}.bin:"
                    "language=zh:"
                    f"destination={srt_path.name}:"
                    "format=srt"
                ),
                "-f",
                "null",
                "-",
            ],
            cwd=output_dir,
        )

    srt_to_text(srt_path, txt_path)
    write_metadata(meta, metadata_path)
    write_draft(meta, txt_path.read_text(encoding="utf-8"), output_dir, args.model)

    print(json.dumps(
        {
            "video_id": video_id,
            "title": meta["title"],
            "author": meta["author"],
            "output_dir": str(output_dir),
            "mp4": str(mp4_path),
            "wav": str(wav_path),
            "srt": str(srt_path),
            "txt": str(txt_path),
            "metadata": str(metadata_path),
        },
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    main()
