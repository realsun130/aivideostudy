"""Structure tensor → stroke orientation field (numpy only)."""
from __future__ import annotations

import numpy as np


def _gaussian_kernel1d(sigma: float) -> np.ndarray:
    radius = max(1, int(3 * sigma))
    x = np.arange(-radius, radius + 1, dtype=np.float64)
    k = np.exp(-(x * x) / (2 * sigma * sigma))
    k /= k.sum()
    return k


def _separable_convolve(img: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Convolve HxW (or HxWxC) with 1D kernel, separable, reflect pad."""
    r = len(kernel) // 2

    def conv1d_rows(a: np.ndarray) -> np.ndarray:
        pad = np.pad(a, ((0, 0), (r, r)), mode="reflect")
        out = np.zeros_like(a, dtype=np.float64)
        for i, w in enumerate(kernel):
            out += w * pad[:, i : i + a.shape[1]]
        return out

    def conv1d_cols(a: np.ndarray) -> np.ndarray:
        pad = np.pad(a, ((r, r), (0, 0)), mode="reflect")
        out = np.zeros_like(a, dtype=np.float64)
        for i, w in enumerate(kernel):
            out += w * pad[i : i + a.shape[0], :]
        return out

    if img.ndim == 2:
        return conv1d_cols(conv1d_rows(img.astype(np.float64)))
    # per-channel
    chans = [conv1d_cols(conv1d_rows(img[..., c].astype(np.float64))) for c in range(img.shape[2])]
    return np.stack(chans, axis=-1)


def sobel_gradients(gray: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return Ix, Iy for HxW float image."""
    kx = np.array([-1.0, 0.0, 1.0])
    # separable sobel-ish: smooth then diff
    smooth = _gaussian_kernel1d(0.8)
    g = _separable_convolve(gray, smooth)
    # central differences
    Ix = np.zeros_like(g)
    Iy = np.zeros_like(g)
    Ix[:, 1:-1] = (g[:, 2:] - g[:, :-2]) * 0.5
    Iy[1:-1, :] = (g[2:, :] - g[:-2, :]) * 0.5
    Ix[:, 0] = g[:, 1] - g[:, 0]
    Ix[:, -1] = g[:, -1] - g[:, -2]
    Iy[0, :] = g[1, :] - g[0, :]
    Iy[-1, :] = g[-1, :] - g[-2, :]
    return Ix, Iy


def structure_tensor_field(
    gray: np.ndarray,
    sigma: float = 2.5,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute stroke direction (radians, along isophote), coherence [0,1],
    and gradient magnitude.

    Stroke angle is perpendicular to the dominant gradient (tangent to edges /
    along fur flow), matching classic painterly / ETF practice.
    """
    g = gray.astype(np.float64)
    if g.max() > 1.5:
        g = g / 255.0
    Ix, Iy = sobel_gradients(g)
    jxx = Ix * Ix
    jyy = Iy * Iy
    jxy = Ix * Iy
    k = _gaussian_kernel1d(sigma)
    jxx = _separable_convolve(jxx, k)
    jyy = _separable_convolve(jyy, k)
    jxy = _separable_convolve(jxy, k)

    # orientation of minor eigenvector (edge tangent / isophote)
    # θ = 0.5 * atan2(2 Jxy, Jxx - Jyy) is major axis of tensor (gradient dir)
    # stroke along θ + π/2
    grad_angle = 0.5 * np.atan2(2.0 * jxy, jxx - jyy)
    stroke_angle = grad_angle + (np.pi * 0.5)

    # coherence from eigenvalue gap
    tmp = np.sqrt(((jxx - jyy) * 0.5) ** 2 + jxy * jxy)
    l1 = (jxx + jyy) * 0.5 + tmp
    l2 = (jxx + jyy) * 0.5 - tmp
    coherence = np.zeros_like(l1)
    denom = l1 + l2 + 1e-8
    coherence = (l1 - l2) / denom
    coherence = np.clip(coherence, 0.0, 1.0)

    mag = np.sqrt(Ix * Ix + Iy * Iy)
    return stroke_angle.astype(np.float32), coherence.astype(np.float32), mag.astype(np.float32)
