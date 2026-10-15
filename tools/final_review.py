#!/usr/bin/env python3
"""Post-render self check (P0-2). Own implementation; thresholds from docs/MOTION_LESSONS.md §7/§9.

usage: python3 tools/final_review.py VIDEO.mp4 [--out DIR] [--promise story_card.json | --min-motion-ratio 0.6]
       [--allow-no-audio] [--expect-width 1920 --expect-height 1080 --expect-fps 24]
Writes DIR/final_review.json and DIR/contact_sheet.png. Exit code 0 = pass, 1 = fail.
"""
import argparse, json, re, subprocess, sys, datetime, os
import numpy as np

LUFS_TARGET, LUFS_TOL = -14.0, 1.0       # §7: ~-14 LUFS
TRUE_PEAK_MAX = -1.0                     # post-encode AAC limit (DISPATCH §4: > -1 dBTP => fix); WAV master < -2
CLIP_SAMPLE_PEAK = -0.1                  # dBFS sample peak at/above this => clipping
BLACK_MIN_SEC, SILENCE_MIN_SEC, SILENCE_DB = 0.5, 1.0, -50
MOTION_DIFF_THRESH = 1.5                 # mean abs luma diff (0-255) between samples 0.5 s apart

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path])
    d = json.loads(r.stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    num, den = (v["avg_frame_rate"].split("/") + ["1"])[:2] if v else ("0", "1")
    return {
        "duration_sec": round(float(d["format"]["duration"]), 3),
        "width": v and v["width"], "height": v and v["height"],
        "fps": v and round(float(num) / float(den or 1), 3),
        "video_codec": v and v["codec_name"], "pix_fmt": v and v.get("pix_fmt"),
        "audio_codec": a and a["codec_name"], "audio_sample_rate": a and int(a["sample_rate"]),
        "has_audio": a is not None,
    }

def contact_sheet(path, dur, out_png, n=8):
    times = [dur * (i + 0.5) / n for i in range(n)]
    tmp = []
    for i, t in enumerate(times):
        f = out_png + f".{i}.png"
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1",
             "-vf", "scale=480:-2,drawtext=text='t=%.2fs':x=8:y=8:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.6" % t, f])
        if not os.path.exists(f):  # drawtext may lack font; retry plain
            run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1", "-vf", "scale=480:-2", f])
        tmp.append(f)
    from PIL import Image
    ims = [Image.open(f) for f in tmp if os.path.exists(f)]
    if not ims:
        return [], 0
    w, h = ims[0].size; cols = 4; rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (w * cols, h * rows))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    sheet.save(out_png)
    for f in tmp:
        os.remove(f)
    return [round(t, 3) for t in times], len(ims)

def blackdetect(path):
    r = run(["ffmpeg", "-v", "info", "-i", path, "-vf", f"blackdetect=d={BLACK_MIN_SEC}:pix_th=0.10", "-an", "-f", "null", "-"])
    return [{"start": float(a), "end": float(b)} for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr)]

def audio_checks(path):
    r = run(["ffmpeg", "-v", "info", "-i", path, "-vn", "-af",
             f"silencedetect=n={SILENCE_DB}dB:d={SILENCE_MIN_SEC},astats=metadata=0:measure_perchannel=none,ebur128=peak=true",
             "-f", "null", "-"])
    e = r.stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\-\d.]+)", e)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", e)]
    silences = [{"start": s, "end": (ends[i] if i < len(ends) else None)} for i, s in enumerate(starts)]
    summ = e[e.rfind("Summary:"):]
    I = re.search(r"I:\s+(-?[\d.]+|-inf) LUFS", summ)
    tp = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", summ)
    pk = re.findall(r"Peak level dB: (-?[\d.]+|-inf)", e)
    f = lambda m: None if m is None or "inf" in m else float(m)
    return {"integrated_lufs": f(I and I.group(1)), "true_peak_dbtp": f(tp and tp.group(1)),
            "sample_peak_dbfs": f(pk[-1] if pk else None), "silences": silences}

def motion_ratio(path, dur):
    # 2 samples/s, 64x36 grayscale; ratio of 0.5 s windows whose mean abs diff exceeds threshold
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", "fps=2,scale=64:36,format=gray",
                        "-f", "rawvideo", "-"], capture_output=True)
    a = np.frombuffer(r.stdout, np.uint8)
    n = a.size // (64 * 36)
    if n < 2:
        return None, []
    a = a[: n * 64 * 36].reshape(n, 36, 64).astype(np.float32)
    d = np.abs(np.diff(a, axis=0)).mean(axis=(1, 2))
    return round(float((d > MOTION_DIFF_THRESH).mean()), 3), [round(float(x), 2) for x in d]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--out")
    ap.add_argument("--promise", help="JSON with delivery_promise {mode, min_motion_shot_ratio}")
    ap.add_argument("--min-motion-ratio", type=float)
    ap.add_argument("--allow-no-audio", action="store_true")
    ap.add_argument("--expect-width", type=int); ap.add_argument("--expect-height", type=int)
    ap.add_argument("--expect-fps", type=float)
    a = ap.parse_args()
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.video)), "final_review")
    os.makedirs(out, exist_ok=True)
    reasons, warnings = [], []

    p = probe(a.video)
    if a.expect_width and p["width"] != a.expect_width: reasons.append(f"width {p['width']} != {a.expect_width}")
    if a.expect_height and p["height"] != a.expect_height: reasons.append(f"height {p['height']} != {a.expect_height}")
    if a.expect_fps and abs((p["fps"] or 0) - a.expect_fps) > 0.01: reasons.append(f"fps {p['fps']} != {a.expect_fps}")
    if p["pix_fmt"] not in ("yuv420p", None): warnings.append(f"pix_fmt {p['pix_fmt']} (yuv420p safest for players)")

    sheet = os.path.join(out, "contact_sheet.png")
    times, nframes = contact_sheet(a.video, p["duration_sec"], sheet)
    if nframes < 4: reasons.append(f"contact sheet has only {nframes} frames (<4)")

    blacks = blackdetect(a.video)
    if blacks: reasons.append(f"{len(blacks)} black segment(s) >= {BLACK_MIN_SEC}s: " + ", ".join(f"{b['start']:.2f}-{b['end']:.2f}s" for b in blacks))

    audio = None
    if p["has_audio"]:
        audio = audio_checks(a.video)
        L, tp, sp = audio["integrated_lufs"], audio["true_peak_dbtp"], audio["sample_peak_dbfs"]
        if L is None: reasons.append("integrated loudness unmeasurable (silent track?)")
        elif abs(L - LUFS_TARGET) > LUFS_TOL: reasons.append(f"integrated {L} LUFS outside {LUFS_TARGET}±{LUFS_TOL}")
        if tp is not None and tp > TRUE_PEAK_MAX: reasons.append(f"post-encode true peak {tp} dBTP > {TRUE_PEAK_MAX}")
        if sp is not None and sp >= CLIP_SAMPLE_PEAK: reasons.append(f"clipping: sample peak {sp} dBFS")
        if audio["silences"]: warnings.append(f"{len(audio['silences'])} silence(s) >= {SILENCE_MIN_SEC}s at {SILENCE_DB} dB — confirm intentional")
    elif not a.allow_no_audio:
        reasons.append("no audio stream (pass --allow-no-audio for silent deliverables)")
    else:
        warnings.append("no audio stream (allowed)")

    ratio, diffs = motion_ratio(a.video, p["duration_sec"])
    promise = None
    if a.promise:
        promise = json.load(open(a.promise)).get("delivery_promise")
    elif a.min_motion_ratio is not None:
        promise = {"mode": "motion_led", "min_motion_shot_ratio": a.min_motion_ratio}
    if promise and promise.get("min_motion_shot_ratio") is not None and ratio is not None:
        if ratio < promise["min_motion_shot_ratio"]:
            reasons.append(f"delivery promise broken: motion ratio {ratio} < {promise['min_motion_shot_ratio']} ({promise.get('mode')})")

    res = {
        "schema": "final_review/1", "video": os.path.abspath(a.video),
        "reviewed_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "fail" if reasons else "pass", "reasons": reasons, "warnings": warnings,
        "probe": p, "contact_sheet": {"path": sheet, "frame_times_sec": times, "frames": nframes},
        "black_segments": blacks, "audio": audio,
        "motion": {"ratio_moving_windows": ratio, "threshold": MOTION_DIFF_THRESH, "diff_series": diffs},
        "delivery_promise": promise,
        "thresholds": {"lufs_target": LUFS_TARGET, "lufs_tolerance": LUFS_TOL, "true_peak_max_dbtp": TRUE_PEAK_MAX,
                        "clip_sample_peak_dbfs": CLIP_SAMPLE_PEAK, "black_min_sec": BLACK_MIN_SEC,
                        "silence_min_sec": SILENCE_MIN_SEC, "silence_db": SILENCE_DB},
    }
    with open(os.path.join(out, "final_review.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: res[k] for k in ("status", "reasons", "warnings")}, ensure_ascii=False, indent=2))
    sys.exit(0 if not reasons else 1)

if __name__ == "__main__":
    main()
