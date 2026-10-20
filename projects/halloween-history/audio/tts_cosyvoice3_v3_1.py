#!/usr/bin/env python3
"""v3.1 narration: Fun-CosyVoice3-0.5B-2512 zero-shot (Apache-2.0), CPU.
Reference prompt: audio/ref/ref_voxcpm2_narrator_s9.wav — a synthetic voice made with
VoxCPM2 voice design (Apache-2.0, text description only, no real person), sentence 9 text.
Weights are NOT in the repo: set COSYVOICE_REPO (git clone of FunAudioLLM/CosyVoice) and
COSYVOICE3_MODEL (snapshot of FunAudioLLM/Fun-CosyVoice3-0.5B-2512).
usage: python3 tts_cosyvoice3_v3_1.py SHOT:SEED [SHOT:SEED ...]  -> vo_v3_1/cand/sNN_seedK.wav"""
import os, sys, time, json
import torch, torchaudio
torch.set_num_threads(8)
REPO = os.environ.get('COSYVOICE_REPO', '/workspace/tts_eval/CosyVoice')
MODEL = os.environ.get('COSYVOICE3_MODEL', '/workspace/tts_eval/models/CosyVoice3')
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, 'third_party/Matcha-TTS'))
from cosyvoice.cli.cosyvoice import AutoModel
HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, 'ref', 'ref_voxcpm2_narrator_s9.wav')
REF_TEXT = '万圣夜、中元节、寒衣节。每个文化，都给想念留了一个夜晚。'
TEXT = json.load(open(os.path.join(HERE, 'vo_v3_1', 'sentences.json'), encoding='utf-8'))
m = AutoModel(model_dir=MODEL)
for job in sys.argv[1:]:
    k, seed = job.split(':'); torch.manual_seed(int(seed)); tk = k + 'tts' if k + 'tts' in TEXT else k
    t = time.time()
    g = m.inference_zero_shot(TEXT[tk], 'You are a helpful assistant.<|endofprompt|>' + REF_TEXT, REF, stream=False)
    wav = torch.cat([j['tts_speech'] for j in g], dim=1)
    out = os.path.join(HERE, 'vo_v3_1', 'cand', f's{int(k):02d}_seed{seed}.wav')
    torchaudio.save(out, wav, m.sample_rate)
    print(job, 'cpu_s', round(time.time() - t, 1), 'dur', round(wav.shape[1] / m.sample_rate, 2), flush=True)
