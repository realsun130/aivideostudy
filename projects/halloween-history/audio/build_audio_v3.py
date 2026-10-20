#!/usr/bin/env python3
"""v3 audio: original procedural score (90 BPM = 16 f/beat @24fps) + synthesized SFX + Piper VO.
All events computed from frame index (no accumulated rounding). Sound peaks land on the
picture frame or 1 frame after, never before. Output: audio/mix_v3.wav (48 kHz stereo).
Seeded: rng 1031. Deterministic."""
import json, math, os, subprocess, wave
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve, resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
SR, FPS, FPB = 48000, 24, 16
TL_NAME = os.environ.get('HH_TIMELINE', 'timeline_v3.json')        # v3.1: env-selectable
TL = json.load(open(os.path.join(HERE, TL_NAME), encoding='utf-8'))
MIX_NAME = os.environ.get('HH_MIX', 'mix_v3.wav')
VO_EQ = 'tts' in TL and 'CosyVoice3' in TL['tts'].get('model', '')     # v3.1 only; v3 unchanged
NF = TL['total_frames']; N = int(NF / FPS * SR) + SR // 2
SH = {int(k): v for k, v in TL['shots'].items()}
rng = np.random.default_rng(1031)
fs = lambda f: int(round(f / FPS * SR))            # frame -> sample
def beat_frame(b): return b * FPB                  # from index, never accumulated

def bp(x, lo, hi, order=2):
    if lo and hi: sos = butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band', output='sos')
    elif lo: sos = butter(order, lo / (SR / 2), 'high', output='sos')
    else: sos = butter(order, hi / (SR / 2), 'low', output='sos')
    return sosfilt(sos, x).astype(np.float32)

def add(buf, sig, start, pan=0.0, gain=1.0):
    if sig.ndim == 1:
        sig = np.stack([sig * math.sqrt((1 - pan) / 2) * 1.414, sig * math.sqrt((1 + pan) / 2) * 1.414], 1)
    i0 = max(0, start); i1 = min(len(buf), start + len(sig))
    if i1 > i0: buf[i0:i1] += sig[i0 - start:i1 - start] * gain

def env(n, a, r):
    e = np.ones(n, np.float32); na, nr = int(a * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e

NOTE = lambda m: 440 * 2 ** ((m - 69) / 12)

def pad(midi, dur, amp, bright=1800):
    n = int(dur * SR); t = np.arange(n) / SR; x = np.zeros(n, np.float32)
    for det in (-0.06, 0.0, 0.07):                         # 3 detuned voices, harmonics to phone band
        f = NOTE(midi + det)
        for h in range(1, 9):
            x += np.sin(2 * np.pi * f * h * t + rng.random() * 6) / h ** 1.1
    x = bp(x, None, bright) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.11 * t))
    return x * env(n, min(1.2, dur / 3), min(1.5, dur / 3)) * amp / 6

def bell(midi, amp, dur=3.0):
    n = int(dur * SR); t = np.arange(n) / SR; f = NOTE(midi); x = np.zeros(n, np.float32)
    for k, (ratio, dec) in enumerate(((1, 1.6), (2.0, 2.4), (3.01, 3.4), (4.2, 4.5), (5.4, 6.0))):
        x += np.sin(2 * np.pi * f * ratio * t) * np.exp(-t * dec) / (k + 1)
    return x * (1 - np.exp(-t * 400)) * amp

def pluck(midi, amp, dur=1.4):
    n = int(dur * SR); t = np.arange(n) / SR; f = NOTE(midi); x = np.zeros(n, np.float32)
    for k in range(1, 10):
        x += np.sin(2 * np.pi * f * k * t) * np.exp(-t * (2.5 + 0.9 * k)) / k ** 1.3
    return x * (1 - np.exp(-t * 600)) * amp

def tok(amp):           # percussive body 180–900 Hz so it survives phone speakers
    n = int(0.18 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * (230 * np.exp(-t * 18) + 120) * t) * np.exp(-t * 26)
    x += bp(rng.normal(0, 1, n), 1500, 5000) * np.exp(-t * 60) * 0.25
    return x.astype(np.float32) * amp

def boom(amp):          # cut accent: low body + 200 Hz harmonic + air
    n = int(1.6 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 55 * t) * np.exp(-t * 2.2) * 0.6 + np.sin(2 * np.pi * 196 * t) * np.exp(-t * 3.5) * 0.5
    x += bp(rng.normal(0, 1, n), 300, 3000) * np.exp(-t * 7) * 0.12
    return (x * (1 - np.exp(-t * 300))).astype(np.float32) * amp

def reverb(x, sec=2.2, mix=0.28):
    n = int(sec * SR); t = np.arange(n) / SR
    ir = rng.normal(0, 1, (n, 2)).astype(np.float32) * np.exp(-t * 3.2)[:, None]
    ir[:, 0] = bp(ir[:, 0], 200, 7000); ir[:, 1] = bp(ir[:, 1], 200, 7000)
    ir /= np.sqrt((ir ** 2).sum(0))
    wet = np.stack([fftconvolve(x[:, c], ir[:, c])[:len(x)] for c in range(2)], 1)
    return x * (1 - mix) + wet * mix

# ---------------------------------------------------------------- score
mus = np.zeros((N, 2), np.float32)
S = lambda k: SH[k]['start']; E = lambda k: SH[k]['end'] + 1
def sec(a, b): return (b - a) / FPS
# mysterious 01–03 : D minor drone + bells on bar downbeats (64 f)
add(mus, pad(38, sec(0, E(3)) + 1.0, 0.55), 0, -0.2); add(mus, pad(45, sec(0, E(3)) + 1.0, 0.35), 0, 0.25)
for b in range(0, E(3) // 64):
    add(mus, bell([62, 65, 69, 64][b % 4], 0.10), fs(beat_frame(b * 4)), pan=0.3 * math.sin(b))
# 04 solemn church: open fifths, bells every 2 beats
add(mus, pad(50, sec(S(4), E(4)) + 1.0, 0.45, 1400), fs(S(4)), -0.1); add(mus, pad(57, sec(S(4), E(4)) + 1.0, 0.30, 1400), fs(S(4)), 0.2)
for b in range(S(4) // FPB, E(4) // FPB, 2):
    add(mus, bell(74 if (b // 2) % 2 else 69, 0.06), fs(beat_frame(b)), pan=0.2)
# 05 famine: low D + Bb, slow descending line one note per bar
add(mus, pad(38, sec(S(5), E(5)) + 1.2, 0.60, 1200), fs(S(5)), -0.15); add(mus, pad(46, sec(S(5), E(5)) + 1.2, 0.35, 1200), fs(S(5)), 0.2)
for i, m in enumerate([62, 60, 58, 57]):
    f = S(5) + i * 64
    if f < E(5): add(mus, pad(m, 2.6, 0.30, 2200), fs(f), 0.0)
# 06 warm: F major plucks on every beat
add(mus, pad(53, sec(S(6), E(6)) + 1.0, 0.40), fs(S(6)), -0.2)
for i, b in enumerate(range(S(6) // FPB, E(6) // FPB)):
    add(mus, pluck([65, 69, 72, 69][i % 4], 0.11), fs(beat_frame(b)), pan=[-0.3, 0.1, 0.3, -0.1][i % 4])
# 07–08 lively: D major eighth-note arpeggio (8 f) + tok on beats
add(mus, pad(50, sec(S(7), E(8)) + 1.0, 0.35), fs(S(7)), 0.0)
for e8 in range(S(7) // 8, E(8) // 8):
    add(mus, pluck([74, 78, 81, 78][e8 % 4], 0.06 + (0.03 if e8 % 2 == 0 else 0)), fs(e8 * 8), pan=0.35 * math.sin(e8))
    if e8 % 2 == 0: add(mus, tok(0.16), fs(e8 * 8), 0.0)
# 09 quiet resonant: D major pad, bells every 2 bars, final chord
add(mus, pad(50, sec(S(9), NF) + 1.0, 0.42), fs(S(9)), -0.15); add(mus, pad(57, sec(S(9), NF) + 1.0, 0.25), fs(S(9)), 0.2)
for b in range(S(9) // 64, NF // 64, 2):
    add(mus, bell(74, 0.07, 4.0), fs(beat_frame(b * 4)), 0.1)
# cut accents on every shot start (cuts are on beats)
for k in range(2, 10):
    add(mus, boom(0.32), fs(S(k) + 1))       # 1 frame after the cut
mus = reverb(mus)
if VO_EQ:   # v3.1: low shelf on the bed (-6 dB under ~120 Hz) so the phone band carries the mix
    mus = np.stack([mus[:, c] - 0.5 * bp(mus[:, c], None, 120, 2) for c in range(2)], 1).astype(np.float32)
# end: musical fade to silence over last 1.5 s
mus[fs(NF - 36):fs(NF)] *= np.linspace(1, 0, fs(NF) - fs(NF - 36))[:, None]
mus[fs(NF):] = 0

# ---------------------------------------------------------------- SFX
sfx = np.zeros((N, 2), np.float32)
def crackle(dur, density=60):
    n = int(dur * SR); x = bp(rng.normal(0, 1, n), 300, 3000) * 0.18
    for _ in range(int(density * dur)):
        p = rng.integers(0, n - 300); L = rng.integers(60, 300)
        x[p:p + L] += bp(rng.normal(0, 1, L), 1200, 6000) * np.linspace(1, 0, L) * rng.uniform(0.2, 0.9)
    return x
# bonfires ignite 02 (v2 lf2 18 + 3i, linear remap) -> crackle bed through 03
r2 = (SH[2]['frames'] - 1) / (407 - 144)
ign0 = S(2) + int(round(18 * r2))
c = crackle(sec(ign0, E(3)) + 0.5); c *= env(len(c), 0.6, 0.6)
add(sfx, c, fs(ign0 + 1), 0.0, 0.55)
for i in range(8):                      # small ignition puffs on each fire's frame (+1)
    f = S(2) + int(round((18 + 3 * i) * r2)) + 1
    add(sfx, bp(rng.normal(0, 1, int(0.25 * SR)), 200, 2500) * np.exp(-np.arange(int(0.25 * SR)) / SR * 14), fs(f), 0.4 * math.sin(i), 0.35)
# candle 04 (quiet, close)
c = crackle(sec(S(4), E(4)), 18); c *= env(len(c), 0.4, 0.5); add(sfx, c, fs(S(4) + 1), 0.4, 0.22)
# ocean 05
n = fs(E(5)) - fs(S(5)); t = np.arange(n) / SR
oc = bp(rng.normal(0, 1, n), 150, 1800) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.14 * t - 1.2)) ** 1.6
add(sfx, oc * env(n, 0.8, 0.8), fs(S(5) + 1), 0.0, 0.42)
# 08 window clicks (seeded order, approx v2 turn-on times) + card ticks
r8 = (SH[8]['frames'] - 1) / (1775 - 1584)
for i, lf2 in enumerate([12, 16, 22, 27, 33, 40, 47, 55]):
    add(sfx, tok(0.10) * 0.6, fs(S(8) + int(round(lf2 * r8)) + 1), pan=0.5 * math.sin(i * 2.1))
for ci in range(3):
    add(sfx, bell(86, 0.05, 0.8), fs(S(8) + int(round((40 + ci * 14) * r8)) + 1), pan=[0.5, -0.5, 0.5][ci])
# 09 lamp blow-outs on extinguish frames (lf3 210/226/242) + 1
def lf9(lf3):    # v3 local frame (old 256-f shot) -> this timeline's local frame via v2 knots
    if 'remap9' not in TL: return lf3
    old = [(0, 0), (54, 54), (62, 150), (210, 264), (255, 286)]
    v2f = float(np.interp(lf3, *zip(*old))); xs, ys = zip(*TL['remap9'])
    return int(round(np.interp(v2f, ys, xs)))
for i, lf3 in enumerate(lf9(x) for x in (210, 226, 242)):
    n = int(0.9 * SR); t = np.arange(n) / SR
    b = bp(rng.normal(0, 1, n), 250, 3500) * np.exp(-t * 4) * (1 - np.exp(-t * 40))
    add(sfx, b, fs(S(9) + lf3 + 1), pan=0.0, gain=0.45)
# 01: Ireland ring chime (lf 78 + 1); fly-through whoosh peaking on the cut
N1 = SH[1]['frames']; CH = 78 if N1 <= 128 else 78 + (N1 - 128)   # ring lights at anim lf 78
add(sfx, bell(81, 0.10, 2.5), fs(CH + 1), 0.2)
def whoosh(dur, peak_at):
    n = int(dur * SR); t = np.arange(n) / SR
    e = np.where(t < peak_at, (t / peak_at) ** 2.2, np.exp(-(t - peak_at) * 7))
    lo = bp(rng.normal(0, 1, n), 300, 1500); hi = bp(rng.normal(0, 1, n), 1500, 6000)
    mixw = np.clip(t / peak_at, 0, 1)
    return ((lo * (1 - mixw) + hi * mixw) * e).astype(np.float32)
w = whoosh(1.9, 1.5); add(sfx, w, fs(S(2) + 1) - int(1.5 * SR), 0.0, 0.32)
for k in range(3, 10):   # whip-through-light: 8 f in + 8 f out; peak 1 frame after cut
    w = whoosh(0.75, 8 / FPS); add(sfx, w, fs(S(k) + 1) - int(8 / FPS * SR), pan=0.2 * (-1) ** k, gain=0.30)

# ---------------------------------------------------------------- VO (per shot, voice-driven)
def read_wav(p):
    with wave.open(p) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        return x, w.getframerate()
vo = np.zeros(N, np.float32)
for k, sh in SH.items():
    x, sr = read_wav(os.path.join(HERE, sh['file']))
    x = resample_poly(x, 2, 1).astype(np.float32) if sr == 24000 else (resample_poly(x, 320, 147).astype(np.float32) if sr == 22050 else x)
    x = bp(x, 80, None)                                  # rumble cut
    if VO_EQ:                                            # v3.1 deep CosyVoice3 voice: tame chest below ~160 Hz for phones
        x = bp(x, 100, None, 2); x = (x - 0.55 * bp(x, None, 170, 2)).astype(np.float32)   # HPF 100 + ~-7 dB low shelf
    i0 = fs(sh['vo_start_frame']); vo[i0:i0 + len(x)] += x[:N - i0]

def write(p, x):
    x = np.asarray(x, np.float32)
    if x.ndim == 1: x = np.stack([x, x], 1)
    with wave.open(p, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())

def lufs(p):
    out = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', p, '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    blk = out[out.rfind('Summary:'):]
    I = float(blk.split('I:')[1].split('LUFS')[0]); tp = float(blk.split('Peak:')[1].split('dBFS')[0])
    return I, tp

def gain_to(x, path, target):
    write(path, x); I, _ = lufs(path); g = 10 ** ((target - I) / 20); return x * g, I

tmp = os.path.join(HERE, 'score')
vo, I0 = gain_to(vo, f'{tmp}/_vo.wav', -16.0)
mus, _ = gain_to(mus, f'{tmp}/_mus.wav', -19.5)
sfx_s, _ = gain_to(sfx, f'{tmp}/_sfx.wav', -27.0)
# ducking: music -9 dB while voice is present (attack 40 ms, release 350 ms)
e = np.abs(vo); win = int(0.03 * SR)
e = np.convolve(e, np.ones(win) / win, 'same')
on = (e > 10 ** (-42 / 20)).astype(np.float32)
g = np.empty_like(on); cur = 0.0; a = 1 - math.exp(-1 / (0.04 * SR)); r = 1 - math.exp(-1 / (0.35 * SR))
for i in range(len(on)):
    cur += (on[i] - cur) * (a if on[i] > cur else r); g[i] = cur
duck = 10 ** (-9 * g / 20)
mix = mus * duck[:, None] + sfx_s + np.stack([vo, vo], 1)
mix = mix[:fs(NF)]
write(f'{tmp}/_mix_pre.wav', mix)
write(f'{tmp}/vo_only.wav', np.stack([vo, vo], 1)[:fs(NF)])
write(f'{tmp}/bed_only.wav', (mus * duck[:, None] + sfx_s)[:fs(NF)])
# final: linear loudness to -14 LUFS, true peak ≤ -1.5 dBTP via gentle limiter (≤3 dB GR)
I, tp = lufs(f'{tmp}/_mix_pre.wav')
out = os.path.join(HERE, MIX_NAME)
print('pre-mix I/TP', I, tp)
# iterate: linear gain + 4x-oversampled limiter (true-peak safe) until I = -14 ± 0.15 and TP <= -1.3
gain = -14 - I
for it in range(6):
    subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', f'{tmp}/_mix_pre.wav', '-af',
                    f'highpass=f=35,volume={gain:.2f}dB,aresample=192000,alimiter=limit=0.79:attack=3:release=120:level=false,aresample=48000',
                    '-ar', '48000', '-c:a', 'pcm_s16le', out], check=True)
    fI, fTP = lufs(out); print('pass', it, round(gain, 2), fI, fTP)
    if abs(fI + 14) <= 0.15 and fTP <= -1.3: break
    gain += -14 - fI
print('final', (fI, fTP))
print('vo-only', lufs(f'{tmp}/vo_only.wav'), 'bed-only', lufs(f'{tmp}/bed_only.wav'))
# phone-band check is done in QA with soundfile (mix 150 Hz-6 kHz = 0.80 of energy)
