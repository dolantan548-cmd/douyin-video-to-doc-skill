# Douyin Video To Doc

Convert a Douyin share link into a reusable document bundle:

- downloaded video
- extracted audio
- local transcript
- metadata JSON
- one Markdown draft per video

This repository is designed as an agent skill and can also be used directly as a local workflow.

## What It Does

Input:

- a Douyin share link
- or a full share text copied from Douyin

Output:

- `VIDEO_ID.mp4`
- `VIDEO_ID.wav`
- `VIDEO_ID.<model>.srt`
- `VIDEO_ID.<model>.txt`
- `VIDEO_ID.metadata.json`
- `YYYY-MM-DD-douyin-<slug>-<video_id>.draft.md`

## Workflow

```mermaid
flowchart LR
    A[Douyin share text or link] --> B[Parse share page]
    B --> C[Download video]
    C --> D[Extract WAV audio]
    D --> E[Run local whisper.cpp ASR]
    E --> F[Generate SRT and TXT]
    B --> G[Write metadata JSON]
    F --> H[Write Markdown draft]
    G --> H
```

## Install As A Skill

If your environment supports the `skills` installer:

```bash
npx skills add <owner>/<repo> --global
```

Or install manually by placing the repository in your global skills directory.

For Codex on Windows, the global skill directory is typically:

```text
C:\Users\<you>\.codex\skills\
```

## Local Requirements

- Windows with PowerShell
- Python 3.10+
- `ffmpeg` available on `PATH`
- internet access for downloading Douyin pages and whisper.cpp model files

The script uses `ffmpeg`'s built-in `whisper` filter with local `ggml` models downloaded from `hf-mirror.com`.

## Configuration

Default output directory:

```text
%USERPROFILE%\douyin-video-docs
```

Override with environment variable:

```powershell
$env:DOUYIN_VIDEO_TO_DOC_OUTPUT_DIR = "D:\dolan_env\temp\project\personal\douyin-video-docs"
```

You can also override per run:

```powershell
python .\scripts\douyin_video_to_doc.py --input "https://v.douyin.com/xxxx/" --output-dir "D:\custom\path"
```

## Usage

From the repository root:

```powershell
python .\scripts\douyin_video_to_doc.py --input "https://v.douyin.com/j6ySf9z4GKg/"
```

Using full copied share text:

```powershell
python .\scripts\douyin_video_to_doc.py --input "7.99 复制打开抖音，看看【每日AI评论的作品】简单讲讲最近最火的Hermes Agent #ai #技术分享 #Agent https://v.douyin.com/j6ySf9z4GKg/"
```

Choosing a model explicitly:

```powershell
python .\scripts\douyin_video_to_doc.py --input "https://v.douyin.com/j6ySf9z4GKg/" --model small
```

Current model choices:

- `base`
- `small`

Use `small` when quality matters more than speed.

## How To Turn Drafts Into Final Docs

The script generates a draft Markdown file with:

- basic video info
- processing note
- transcript raw text
- placeholders for detailed writeup

Recommended next step:

1. Read the transcript text.
2. Correct obvious ASR mistakes from context.
3. Expand the draft into:
   - core argument
   - detailed mechanism
   - examples
   - caveats
   - reusable conclusions

## Notes And Limits

- Douyin pages often do not expose reusable official subtitles.
- In those cases the transcript is local ASR output, not official captions.
- Proper nouns may require manual correction from context.
- Some Douyin links may expire or redirect differently depending on region and platform behavior.
