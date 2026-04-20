---
name: douyin-video-to-doc
description: Use when the user provides a Douyin link or share text and wants one-document-per-video output with transcript, source metadata, and a detailed content writeup rather than a short summary
---

# Douyin Video To Doc

Turn a Douyin share link into a reusable document bundle:

- source video metadata
- local video/audio files
- local transcript files
- one Markdown document per video

Use this skill when the user wants to archive, study, summarize, or structurally organize the full content of a Douyin video.

## Output Rule

Create one Markdown file per video under the configured output directory.

Default output directory:

`%USERPROFILE%\douyin-video-docs`

Override with:

`DOUYIN_VIDEO_TO_DOC_OUTPUT_DIR`

Keep the global skill itself under:

`C:\Users\dolan\.codex\skills\douyin-video-to-doc`

On this machine, if you want outputs under your project workspace root, set:

```powershell
$env:DOUYIN_VIDEO_TO_DOC_OUTPUT_DIR = "D:\dolan_env\temp\project\personal\douyin-video-docs"
```

## Workflow

1. Run the helper script to fetch metadata, download media, extract audio, and generate transcript files.
2. Inspect the transcript and correct obvious ASR mistakes through context.
3. Write a final Markdown document with:
   - basic video info
   - processing notes
   - detailed content writeup
   - transcript raw text
4. Be explicit when transcript text came from local ASR rather than official captions.

## Script

Use:

```powershell
python C:\Users\dolan\.codex\skills\douyin-video-to-doc\scripts\douyin_video_to_doc.py --input "抖音分享文本或链接"
```

Optional flags:

```powershell
python C:\Users\dolan\.codex\skills\douyin-video-to-doc\scripts\douyin_video_to_doc.py --input "..." --model small --output-dir "D:\dolan_env\temp\project\personal\douyin-video-docs"
```

The script produces:

- `VIDEO_ID.mp4`
- `VIDEO_ID.wav`
- `VIDEO_ID.<model>.srt`
- `VIDEO_ID.<model>.txt`
- `VIDEO_ID.metadata.json`
- `YYYY-MM-DD-douyin-<slug>-<video_id>.draft.md`

Example:

```powershell
python C:\Users\dolan\.codex\skills\douyin-video-to-doc\scripts\douyin_video_to_doc.py --input "7.99 复制打开抖音，看看【每日AI评论的作品】简单讲讲最近最火的Hermes Agent https://v.douyin.com/j6ySf9z4GKg/"
```

If you want to pin output to a custom directory for the current shell:

```powershell
$env:DOUYIN_VIDEO_TO_DOC_OUTPUT_DIR = "D:\dolan_env\temp\project\personal\douyin-video-docs"
python C:\Users\dolan\.codex\skills\douyin-video-to-doc\scripts\douyin_video_to_doc.py --input "https://v.douyin.com/xxxx/"
```

## Writing Standard

The final document should not stop at a framework-level summary.

Expand the video into:

- the speaker's main claim
- argument structure
- implementation details
- examples and mechanisms
- assumptions and caveats
- inferred corrections for obvious ASR errors

If a key proper noun is uncertain, say it is inferred from context.

## Verification

Before claiming completion:

- confirm the draft and transcript files exist
- read the transcript text
- make sure the final Markdown includes both transcript and detailed writeup

## Notes

- Douyin pages often do not expose reusable official subtitles.
- In that case the transcript is local ASR output, not platform-native captions.
- Prefer the `small` model when quality matters more than speed.
