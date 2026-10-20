#!/usr/bin/env python3
"""v3.1: picked CosyVoice3 takes -> trimmed/stretched vo_v3_1/shotNN.wav + timeline_v3_1.json.
Shot length = ceil((4 lead + VO + 8 handoff) / 16) x 16 (cuts stay on the 90 BPM beat grid);
shot 01 >= 128 f (globe move), shot 09 keeps a 68 f tail for the lamp blow-outs + fade.
Pitch-preserving stretch (ffmpeg atempo, WSOLA) only if the film would exceed MAX_FRAMES; factor <= 1.15.
Internal pauses longer than PAUSE_CAP are shortened to PAUSE_CAP (natural pauses otherwise kept)."""
import json, math, os, subprocess, sys
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, 'vo_v3_1')
NOCAP = {6, 7}   # pause cap + stretch together blurred 芜菁 / 就捣蛋 in ASR -> keep their pauses intact
PICK = {1: 7, 2: 7, 3: 8, 4: 7, 5: 7, 6: 12, 7: 7, 8: 7, 9: 8}
FPS, FPB, LEAD, OUTH, TAIL9 = 24, 16, 4, 8, 68
PAUSE_CAP = float(os.environ.get('PAUSE_CAP', 0.45)); MAX_FRAMES = int(os.environ.get('MAX_FRAMES', 2080))  # 86.7 s (user: target <= ~85 s; chosen to keep stretch <= 1.11)
S = json.load(open(os.path.join(D, 'sentences.json'), encoding='utf-8'))

def load(k):
    x, sr = sf.read(os.path.join(D, 'cand', f's{k:02d}_seed{PICK[k]}.wav'), dtype='float32')
    return (x if x.ndim == 1 else x.mean(1)), sr

def tidy(x, sr, k=0):
    hop = int(0.01 * sr); fr = len(x) // hop
    e = np.sqrt(np.convolve(x ** 2, np.ones(hop * 3) / (hop * 3), 'same')[::hop][:fr] + 1e-12)
    on = 20 * np.log10(e) > (20 * np.log10(e.max()) - 40)
    idx = np.where(on)[0]; a, b = max(0, idx[0] - 6), min(fr, idx[-1] + 12)   # 60 ms pre-roll, 120 ms tail
    x = x[a * hop:b * hop]; on = on[a:b]
    keep = np.ones(len(x), bool); i = 0; cap = int((99 if k in NOCAP else PAUSE_CAP) / 0.01); trimmed = []
    while i < len(on):
        if not on[i]:
            j = i
            while j < len(on) and not on[j]: j += 1
            if j - i > cap and i > 0 and j < len(on):
                c0 = i + cap // 2; c1 = j - cap // 2
                keep[c0 * hop:c1 * hop] = False; trimmed.append(round((j - i) * 0.01, 2))
            i = j
        else: i += 1
    y = x[keep]
    # 10 ms crossfades are implicit: cuts land in near-silence (< -40 dB)
    return y, trimmed

def plan(stretch):
    t, f0, out = {}, 0, []
    for k in range(1, 10):
        x, sr = load(k); y, tr = tidy(x, sr, k); dur = len(y) / sr / stretch
        vo_f = int(math.ceil(dur * FPS))
        n = int(math.ceil((LEAD + vo_f + (TAIL9 if k == 9 else OUTH)) / FPB)) * FPB
        if k == 1: n = max(n, 128)
        out.append((k, f0, n, vo_f, dur, tr)); f0 += n
    return out, f0

st = float(os.environ.get('STRETCH', 1.11))   # fixed: 1.11 keeps ASR clean on all 9 (1.15 blurred 就捣蛋)
while 'STRETCH_SEARCH' in os.environ:
    rows, total = plan(st)
    if total <= MAX_FRAMES or st >= 1.15: break
    st = round(st + 0.01, 2)
rows, total = plan(st)
print('stretch', st, 'total', total, round(total / FPS, 2), 's')
for r in rows: print(r[:5], 'pauses capped', r[5])
if '--write' in sys.argv:
    shots = {}
    for k, f0, n, vo_f, dur, tr in rows:
        x, sr = load(k); y, _ = tidy(x, sr, k)
        tmp = os.path.join(D, f'_t{k}.wav'); outp = os.path.join(D, f'shot{k:02d}.wav')
        sf.write(tmp, y, sr, subtype='PCM_16')
        af = f'atempo={st},' if st > 1.0 else ''   # WSOLA, pitch-preserving; rubberband smeared consonants (ASR: 就->球)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', tmp, '-af', f'{af}aresample=48000', '-ac', '1',
                        '-c:a', 'pcm_s16le', outp], check=True); os.remove(tmp)
        real = sf.info(outp).duration
        shots[str(k)] = dict(start=f0, end=f0 + n - 1, frames=n, vo_start_frame=f0 + LEAD,
                             vo_frames=int(math.ceil(real * FPS)), text=S[str(k)], tts_text=S[str(k)],
                             file=f'vo_v3_1/shot{k:02d}.wav', vo_dur=round(real, 3), seed=PICK[k], stretch=st)
    n9 = shots['9']['frames']; v9 = shots['9']['vo_frames']
    # shot 09 v2 knots: hold names until sentence 2 ("每个文化…") ~ 30% into VO, main line done at VO end
    y9, sr9 = sf.read(os.path.join(D, 'shot09.wav')); hop = sr9 // 100
    e = np.sqrt(np.convolve(y9 ** 2, np.ones(hop * 3) / (hop * 3), 'same')[::hop] + 1e-12)
    on = 20 * np.log10(e / e.max()) > -40
    st2 = next(i for i in range(250, len(on)) if on[i] and not on[i - 15:i].any())   # first onset after >=150 ms gap past 2.5 s
    s2 = LEAD + int(round(st2 / 100 * FPS))
    remap9 = [[0, 0], [s2, 54], [s2 + 8, 150], [n9 - 46, 264], [n9 - 1, 286]]
    tl = dict(fps=FPS, bpm=90, frames_per_beat=FPB, total_frames=total, total_seconds=total / FPS,
              tts=dict(model='Fun-CosyVoice3-0.5B-2512 (FunAudioLLM)', mode='zero-shot',
                       reference='audio/ref/ref_voxcpm2_narrator_s9.wav (synthetic VoxCPM2 voice-design clip, Apache-2.0, no real person)',
                       license='Apache-2.0', stretch=st, pause_cap_s=PAUSE_CAP),
              shots=shots, remap9=remap9)
    json.dump(tl, open(os.path.join(HERE, 'timeline_v3_1.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('wrote timeline_v3_1.json')
