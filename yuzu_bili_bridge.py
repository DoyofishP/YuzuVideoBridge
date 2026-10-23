#!/usr/bin/env python3
# YuzuBiliBridge v0.1 - turn a Bilibili video into timestamped visual sheets and text.
# Personal local processing; never uploads login cookies or raw videos.
import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

def run(cmd, *, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, text=True, encoding="utf-8", errors="replace",
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode:
        raise RuntimeError(f"Command failed: {' '.join(str(x) for x in cmd)}\n{r.stderr[-2500:]}")
    return r.stdout

def clock(seconds):
    seconds = max(0, float(seconds))
    h = int(seconds // 3600)
    m = int(seconds // 60) % 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:06.3f}" if h else f"{m:02}:{s:06.3f}"

def safe_id(value):
    return re.sub(r"[^0-9A-Za-z_-]+", "_", str(value)).strip("_")[:80] or "video"

def download_video(url, tempdir, browser):
    from yt_dlp import YoutubeDL
    opts = dict(
        format="bv*+ba/b",
        merge_output_format="mp4",
        outtmpl=str(tempdir / "source.%(ext)s"),
        noplaylist=True, quiet=False, no_warnings=False,
        writesubtitles=True, writeautomaticsub=True,
        subtitleslangs=["zh-Hans", "zh-CN", "zh", "en"],
        subtitlesformat="srt/vtt/best",
        restrictfilenames=True,
    )
    if browser:
        opts["cookiesfrombrowser"] = (browser,)
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    matches = [f for f in tempdir.glob("source.*")
               if f.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov", ".flv"}]
    if not matches:
        raise RuntimeError("No playable video was downloaded; check yt-dlp output.")
    return info, max(matches, key=lambda x: x.stat().st_size)

def get_duration(video):
    obj=json.loads(run(["ffprobe","-v","quiet","-show_format","-of","json",str(video)]))
    return float(obj["format"]["duration"])

def make_sheets(video, dst, duration, fps):
    from PIL import Image, ImageDraw, ImageFont
    frame_dir=dst.parent / "_frame_cache"
    frame_dir.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(video),
         "-vf",f"fps={fps},scale=480:-2","-q:v","4",str(frame_dir/"frame_%05d.jpg")])
    frames=sorted(frame_dir.glob("frame_*.jpg"))
    if not frames:
        raise RuntimeError("ffmpeg produced no frames.")
    dst.mkdir(parents=True, exist_ok=True)
    cols, rows=3, 4
    cellw, cellh=480, 300
    per_sheet=cols*rows
    names=[]
    for group_index in range(math.ceil(len(frames)/per_sheet)):
        subset=frames[group_index*per_sheet:(group_index+1)*per_sheet]
        sheet=Image.new("RGB",(cols*cellw,rows*cellh),(24,24,30))
        dr=ImageDraw.Draw(sheet)
        for j, f in enumerate(subset):
            absolute=group_index*per_sheet+j
            x=(j%cols)*cellw
            y=(j//cols)*cellh
            with Image.open(f) as src:
                src.thumbnail((cellw, cellh-24))
                sheet.paste(src,(x+(cellw-src.width)//2,y+24+(cellh-24-src.height)//2))
            dr.rectangle((x,y,x+cellw-1,y+23),fill=(20,20,27))
            dr.text((x+8,y+4),f"{clock(absolute/fps)}   #{absolute+1}",fill=(255,255,255))
        filename=f"sheet_{group_index+1:03d}.jpg"
        sheet.save(dst/filename,quality=85,optimize=True)
        names.append(f"images/{filename}")
    shutil.rmtree(frame_dir,ignore_errors=True)
    return names, len(frames)

def subtitles_from_download(tempdir, packet):
    candidates = [x for x in tempdir.glob("source.*") if x.suffix.lower() in {".srt",".vtt"}]
    if not candidates:
        return None
    chosen = next((x for x in candidates if "zh" in x.name.lower()), candidates[0])
    target=packet/("subtitles"+chosen.suffix.lower())
    shutil.copy2(chosen,target)
    return target.name

def offline_asr(video, packet, model):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None, "faster-whisper not installed; run pip install faster-whisper"
    wav=packet.parent/"_audio16k.wav"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(video),
         "-vn","-ac","1","-ar","16000",str(wav)])
    try:
        model_instance=WhisperModel(model,device="cpu",compute_type="int8")
        segments, meta=model_instance.transcribe(str(wav),beam_size=3,vad_filter=True)
        lines=[]
        for s in segments:
            lines.append(f"[{clock(s.start)} → {clock(s.end)}] {s.text.strip()}")
        dest=packet/"transcript.txt"
        dest.write_text("\n".join(lines)+"\n",encoding="utf-8")
        return dest.name, f"Whisper {model}; detected={meta.language}"
    finally:
        wav.unlink(missing_ok=True)

def main():
    ap=argparse.ArgumentParser(description="Prepare Bilibili frames + dialogue for Yuzu via GitHub.")
    ap.add_argument("url",help="https://b23.tv/... or https://www.bilibili.com/video/BV...")
    ap.add_argument("--repo",type=Path,help="Path to an existing local clone of a PRIVATE GitHub repo")
    ap.add_argument("--push",action="store_true",help="Commit and push the prepared packet (requires --repo)")
    ap.add_argument("--browser",choices=["chrome","edge","firefox"],help="Optional: use local Bilibili browser login session")
    ap.add_argument("--fps",type=float,default=1.0,help="Visual samples per second; default 1")
    ap.add_argument("--asr",action="store_true",help="Offline speech recognition using faster-whisper")
    ap.add_argument("--asr-model",default="base",help="Whisper model size: tiny/base/small/medium")
    ap.add_argument("--max-minutes",type=float,default=20,help="Safety ceiling; default 20 minutes")
    args=ap.parse_args()
    if not (args.url.startswith("https://b23.tv/") or
            args.url.startswith("https://www.bilibili.com/") or
            args.url.startswith("https://m.bilibili.com/")):
        ap.error("Only HTTPS b23.tv/bilibili.com video links are accepted.")
    if args.fps<=0 or args.fps>3:
        ap.error("--fps must be >0 and <=3")
    if args.push and args.repo is None:
        ap.error("--push requires --repo")
    for cmd in ("ffmpeg","ffprobe"):
        if not shutil.which(cmd):
            raise RuntimeError(f"{cmd} not found in PATH; install FFmpeg first.")
    repo = args.repo.resolve() if args.repo else None
    base = (repo/"packets") if repo else Path.home()/"YuzuVideoBridge"/"packets"
    if repo and not (repo/".git").exists():
        raise RuntimeError(f"{repo} is not a Git clone. Clone your PRIVATE repo first.")
    with tempfile.TemporaryDirectory(prefix="yuzu-bili-") as td:
        temp=Path(td)
        info, video=download_video(args.url,temp,args.browser)
        duration=get_duration(video)
        if duration>args.max_minutes*60:
            raise RuntimeError(f"Video duration {duration/60:.1f}m exceeds max {args.max_minutes}m")
        video_id=safe_id(info.get("id") or info.get("display_id") or "clip")
        packet=base/video_id
        packet.mkdir(parents=True, exist_ok=True)
        sheets,nframes=make_sheets(video,packet/"images",duration,args.fps)
        subtitle=subtitles_from_download(temp,packet)
        transcript=None
        asr_note=None
        if args.asr:
            try:
                transcript,asr_note=offline_asr(video,packet,args.asr_model)
            except Exception as e:
                asr_note=f"ASR failed: {e}"
                print(asr_note,file=sys.stderr)
        if not transcript and not subtitle:
            (packet/"TRANSCRIPT_MISSING.txt").write_text(
                "No available subtitles. For spoken dialogue install faster-whisper "
                "and rerun with --asr.\n",encoding="utf-8")
        manifest={
            "title":info.get("title"),"video_id":info.get("id"),
            "url":info.get("webpage_url") or args.url,
            "duration_seconds":round(duration,3),
            "frame_sampling_fps":args.fps,"sampled_frames":nframes,
            "image_sheets":sheets,"subtitle_file":subtitle,
            "transcript_file":transcript,"asr_note":asr_note,
            "generated_utc":datetime.now(timezone.utc).isoformat(),
            "privacy":"Screenshots/transcript only. No original video or browser cookies uploaded."
        }
        (packet/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
        (packet/"README.txt").write_text(
            f"Title: {manifest['title']}\nOriginal: {manifest['url']}\n"
            f"Duration: {clock(duration)}\n"
            f"Read manifest.json, then sheets in order. Sampled at {args.fps}fps.\n"
            "For detailed examination, request targeted frames or denser sampling.\n",
            encoding="utf-8")
        print(f"\nDONE: {packet}")
        print(f"Image sheets: {len(sheets)}, frames: {nframes}; transcript={transcript or subtitle or 'NONE'}")
        if args.push:
            rel=packet.relative_to(repo)
            run(["git","add","--",str(rel)],cwd=repo)
            staged=subprocess.run(["git","diff","--cached","--quiet"],cwd=repo)
            if staged.returncode:
                run(["git","commit","-m",f"Add Bilibili visual packet {video_id}"],cwd=repo)
                run(["git","push"],cwd=repo)
            print(f"PUSHED: {rel.as_posix()}")
            print(f"Ask Yuzu to open: packets/{video_id}/manifest.json in your private repo.")

if __name__=="__main__":
    try: main()
    except Exception as exc:
        print(f"\nERROR: {exc}",file=sys.stderr)
        sys.exit(1)
