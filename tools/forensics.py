#!/usr/bin/env python3
"""Frame forensics for a rendered film (成片逐帧查错).

Ported from Leonxlnx/shanshui tools/forensics.mjs (MIT License,
Copyright (c) Leonxlnx, https://github.com/Leonxlnx/shanshui). Python port and
extensions (skip windows from a shot list, cut padding, timecodes, ghost check)
for realsun130/aivideostudy.

Decodes the video with ffmpeg into small grey frames and reports:
  pops   单帧跳变: one frame differs from both neighbours much more than they differ from each other
  jumps  动作突跳: a frame step far above the local median step (motion lurch)
  holds  画面冻住: stretches longer than --hold-sec where nothing changes
  dips   亮度骤降: luminance below (1 - --dip) x the max within +-1 s (fade-through-dark)
  ghosts 叠影/溶解: a stretch where every frame is ~a mix of the frames before and after
         (two images half-visible at once, e.g. a crossfade double exposure). Heuristic.
Events inside declared transition windows are flagged inTransition (pops) or skipped.

usage:
  python3 tools/forensics.py out/film.mp4 [--shots shots.json] [--skip 1176-1248 --skip 30.5s-32s]
        [--cuts 144,408 --cut-pad 12] [--from 0] [--json out/qa/forensics.json]

--shots JSON accepts any of:
  {"fps":24, "transitions":[[a,b],...], "cuts":[f,...], "ranges":{"1":[0,143],...}}   (frames)
  [{"start": 5.1, "in": {"dur": 1.8}}, ...]                                           (shanshui style, seconds)
  "ranges" makes every shot boundary a cut (padded by --cut-pad).
Exit code: 0 always (it is a report); use --fail to exit 1 when anything is found outside transitions.
"""
import argparse, json, os, subprocess, sys
import numpy as np


def probe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                          'stream=r_frame_rate,width,height', '-of', 'json', path],
                         capture_output=True, text=True, check=True).stdout
    s = json.loads(out)['streams'][0]
    n, d = s['r_frame_rate'].split('/')
    return float(n) / float(d or 1), int(s['width']), int(s['height'])


def decode(path, w, h):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vf', f'scale={w}:{h}:flags=area,format=gray',
                        '-f', 'rawvideo', '-'], capture_output=True, check=True)
    buf = np.frombuffer(p.stdout, np.uint8)
    n = len(buf) // (w * h)
    return buf[:n * w * h].reshape(n, h, w).astype(np.float32)


def tc(frame, fps):
    s = frame / fps
    return f'{int(s // 60):02d}:{s % 60:06.3f}'


def parse_range(txt, fps):
    a, b = txt.split('-', 1)
    conv = lambda v: int(round(float(v[:-1]) * fps)) if v.endswith('s') else int(v)
    return conv(a.strip()), conv(b.strip())


def windows_from_shots(path, fps, cut_pad):
    data = json.load(open(path, encoding='utf-8'))
    wins = []
    if isinstance(data, list):  # shanshui SHOTS
        for s in data:
            if s.get('in') and 'start' in s:
                a = s['start'] - 0.05; b = s['start'] + s['in']['dur'] + 0.05
                wins.append((int(np.floor(a * fps)), int(np.ceil(b * fps))))
        return wins
    f = data.get('fps', fps)
    k = fps / f
    for a, b in data.get('transitions', []):
        wins.append((int(a * k), int(b * k)))
    cuts = list(data.get('cuts', []))
    rng = data.get('ranges')
    if rng:
        bounds = sorted(v[0] for v in rng.values())[1:]
        cuts += bounds
    for c in cuts:
        wins.append((int(c * k) - cut_pad, int(c * k) + cut_pad))
    return wins


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('video')
    ap.add_argument('--shots', help='JSON shot list / transition windows')
    ap.add_argument('--skip', action='append', default=[], help='transition window a-b in frames, or 1.5s-3s')
    ap.add_argument('--cuts', default='', help='comma list of cut frames (each padded by --cut-pad)')
    ap.add_argument('--cut-pad', type=int, default=12, help='frames ignored either side of a cut (default 12)')
    ap.add_argument('--from', dest='t0', type=float, default=0.0, help='film time of the clip first frame (s)')
    ap.add_argument('--size', type=int, default=160, help='long side of the analysis frame (default 160)')
    ap.add_argument('--pop-min', type=float, default=1.2)
    ap.add_argument('--pop-ratio', type=float, default=3.0)
    ap.add_argument('--jump-min', type=float, default=1.5, help='min step (0-255 grey MAD); shanshui used 1.0 on 160x90')
    ap.add_argument('--jump-ratio', type=float, default=4.0)
    ap.add_argument('--hold-sec', type=float, default=0.8)
    ap.add_argument('--hold-eps', type=float, default=0.02)
    ap.add_argument('--dip', type=float, default=0.25)
    ap.add_argument('--ghost-min-frames', type=int, default=0, help='min run length for a ghost stretch (default fps/3)')
    ap.add_argument('--no-ghost', action='store_true')
    ap.add_argument('--json', help='write the report here')
    ap.add_argument('--fail', action='store_true', help='exit 1 if anything outside transitions')
    a = ap.parse_args()

    fps, vw, vh = probe(a.video)
    if vw >= vh:
        W, H = a.size, max(2, int(round(a.size * vh / vw / 2)) * 2)
    else:
        H, W = a.size, max(2, int(round(a.size * vw / vh / 2)) * 2)
    fr = decode(a.video, W, H)
    n = len(fr)
    off = int(round(a.t0 * fps))

    wins = []
    if a.shots:
        wins += windows_from_shots(a.shots, fps, a.cut_pad)
    for s in a.skip:
        wins.append(parse_range(s, fps))
    for c in filter(None, a.cuts.split(',')):
        c = int(c); wins.append((c - a.cut_pad, c + a.cut_pad))
    in_tr = np.zeros(n, bool)
    for x, y in wins:
        lo, hi = max(0, x - off), min(n - 1, y - off)
        if hi >= lo:
            in_tr[lo:hi + 1] = True

    mad = lambda x, y: float(np.mean(np.abs(x - y)))
    diffs = np.zeros(n, np.float32)
    diffs[1:] = np.mean(np.abs(fr[1:] - fr[:-1]), axis=(1, 2))
    lum = fr.mean(axis=(1, 2))
    F = lambda i: i + off
    ev = lambda i, **kw: dict(frame=F(i), tc=tc(F(i), fps), **kw)
    rep = dict(file=os.path.basename(a.video), fps=fps, frames=n, analysis_size=[W, H],
               median_step=round(float(np.median(diffs[1:])), 3) if n > 1 else 0,
               skip_windows=[list(w) for w in wins], pops=[], jumps=[], holds=[], dips=[], ghosts=[])

    # pops
    for i in range(1, n - 1):
        around = mad(fr[i - 1], fr[i + 1])
        spike = float(min(diffs[i], diffs[i + 1]))
        if spike > a.pop_min and spike > a.pop_ratio * around + 0.5:
            rep['pops'].append(ev(i, spike=round(spike, 2), neighbours=round(around, 2), inTransition=bool(in_tr[i])))
    # jumps (frames i / i+1 of a pop are reported as the pop, not again as jumps)
    pop_frames = {p['frame'] - off for p in rep['pops']}
    for i in range(3, n - 3):
        if in_tr[i] or i in pop_frames or (i - 1) in pop_frames:
            continue
        local = float(np.median(diffs[max(1, i - 15):i + 15]))
        if diffs[i] > max(a.jump_min, local * a.jump_ratio):
            rep['jumps'].append(ev(i, step=round(float(diffs[i]), 2), local=round(local, 2)))
    # holds
    run = 0
    for i in range(1, n + 1):
        if i < n and diffs[i] < a.hold_eps:
            run += 1
        else:
            if run > fps * a.hold_sec:
                s0, s1 = F(i - run), F(i)
                rep['holds'].append(dict(from_frame=s0, to_frame=s1, from_tc=tc(s0, fps), to_tc=tc(s1, fps),
                                         seconds=round(run / fps, 2)))
            run = 0
    # dips (sampled ~6x per second, merged into stretches)
    step = max(1, int(round(fps / 6))); r = int(round(fps))
    cur = None
    for i in list(range(0, n, step)) + [None]:
        hit = False
        if i is not None and not in_tr[i]:
            mx = float(lum[max(0, i - r):min(n, i + r)].max())
            hit = lum[i] < mx * (1 - a.dip)
        if hit:
            if cur is None:
                cur = dict(from_frame=F(i), to_frame=F(i), lum=float(lum[i]), localMax=mx)
            else:
                cur['to_frame'] = F(i); cur['lum'] = min(cur['lum'], float(lum[i])); cur['localMax'] = max(cur['localMax'], mx)
        elif cur is not None:
            cur.update(from_tc=tc(cur['from_frame'], fps), to_tc=tc(cur['to_frame'], fps),
                       lum=round(cur['lum'], 1), localMax=round(cur['localMax'], 1))
            rep['dips'].append(cur); cur = None
    # ghosts: frame i is well explained as a mix of frames i-k and i+k (dissolve / double exposure)
    if not a.no_ghost and n > 10:
        k = max(2, int(round(fps / 6)))
        score = np.zeros(n, np.float32)
        for i in range(k, n - k):
            A, B, X = fr[i - k].ravel(), fr[i + k].ravel(), fr[i].ravel()
            d = A - B
            dd = float(d @ d)
            spread = float(np.mean(np.abs(d)))
            if spread < 1.5 or dd == 0:  # nothing changes much: not a dissolve
                continue
            u = float(np.clip(((A - X) @ d) / dd, 0, 1))
            if u < 0.2 or u > 0.8:      # mostly one image: not a double exposure
                continue
            res_mix = float(np.mean(np.abs(X - (A - u * d))))
            res_near = min(float(np.mean(np.abs(X - A))), float(np.mean(np.abs(X - B))))
            # a mix explains the frame much better than either neighbour alone
            if res_mix < 0.45 * res_near and res_near > 1.0:
                score[i] = 1 - res_mix / res_near
        run_s = None
        for i in range(n + 1):
            on = i < n and score[i] > 0 and not in_tr[i]
            if on and run_s is None:
                run_s = i
            elif not on and run_s is not None:
                if i - run_s >= (a.ghost_min_frames or max(6, int(round(fps / 3)))):
                    s0, s1 = F(run_s), F(i - 1)
                    rep['ghosts'].append(dict(from_frame=s0, to_frame=s1, from_tc=tc(s0, fps), to_tc=tc(s1, fps),
                                              frames=i - run_s, peak=round(float(score[run_s:i].max()), 2)))
                run_s = None

    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump(rep, open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    pops_out = [p for p in rep['pops'] if not p['inTransition']]
    print(f"{rep['file']}: {n} frames @ {fps:g} fps, analysis {W}x{H}, median step {rep['median_step']}, "
          f"{len(wins)} skip windows")
    print(f"pops: {len(rep['pops'])} ({len(pops_out)} outside transitions)")
    for p in pops_out[:20]:
        print('  pop  ', json.dumps(p, ensure_ascii=False))
    print(f"motion jumps outside transitions: {len(rep['jumps'])}")
    for j in rep['jumps'][:20]:
        print('  jump ', json.dumps(j, ensure_ascii=False))
    print(f"holds > {a.hold_sec} s: {len(rep['holds'])}")
    for h in rep['holds'][:10]:
        print(f"  hold  f{h['from_frame']}-f{h['to_frame']} ({h['from_tc']}-{h['to_tc']}, {h['seconds']} s)")
    print(f"luminance dips > {int(a.dip * 100)}%: {len(rep['dips'])}")
    for d in rep['dips'][:10]:
        print(f"  dip   f{d['from_frame']}-f{d['to_frame']} ({d['from_tc']}-{d['to_tc']}), min lum {d['lum']} vs local max {d['localMax']}")
    if not a.no_ghost:
        print(f"ghost / dissolve stretches outside transitions: {len(rep['ghosts'])}")
        for g in rep['ghosts'][:10]:
            print(f"  ghost f{g['from_frame']}-f{g['to_frame']} ({g['from_tc']}-{g['to_tc']}, {g['frames']} f, peak {g['peak']})")
    found = pops_out or rep['jumps'] or rep['holds'] or rep['dips'] or rep['ghosts']
    sys.exit(1 if (a.fail and found) else 0)


if __name__ == '__main__':
    main()
