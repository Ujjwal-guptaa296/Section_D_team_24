"""Member 4: Quality Evaluation, Diagnostics & Visualization Module.

Handles:
1. PSNR and SSIM metric computation
2. Intensity histogram analysis
3. High-resolution comparison visualizations
"""

from typing import Tuple, Optional
import cv2
import matplotlib.pyplot as plt
import numpy as np
from skimage.metrics import peak_signal_noise_ratio as _psnr
from skimage.metrics import structural_similarity as _ssim


def compute_psnr(image_true: np.ndarray, image_test: np.ndarray) -> float:
    """Compute Peak Signal-to-Noise Ratio (PSNR) between images."""
    if image_true is None or image_test is None:
        raise ValueError("Images cannot be None")

    t1, t2 = image_true, image_test
    if t1.shape[:2] != t2.shape[:2]:
        t2 = cv2.resize(t2, (t1.shape[1], t1.shape[0]))
    if t1.ndim == 3 and t2.ndim == 2:
        t2 = cv2.cvtColor(t2, cv2.COLOR_GRAY2BGR)
    elif t1.ndim == 2 and t2.ndim == 3:
        t1 = cv2.cvtColor(t1, cv2.COLOR_GRAY2BGR)

    return float(_psnr(t1, t2, data_range=255))


def compute_ssim(image_true: np.ndarray, image_test: np.ndarray) -> float:
    """Compute Structural Similarity Index Measure (SSIM)."""
    if image_true is None or image_test is None:
        raise ValueError("Images cannot be None")

    t1, t2 = image_true, image_test
    if t1.shape[:2] != t2.shape[:2]:
        t2 = cv2.resize(t2, (t1.shape[1], t1.shape[0]))

    if t1.ndim == 3:
        g1 = cv2.cvtColor(t1, cv2.COLOR_BGR2GRAY)
    else:
        g1 = t1

    if t2.ndim == 3:
        g2 = cv2.cvtColor(t2, cv2.COLOR_BGR2GRAY)
    else:
        g2 = t2

    return float(_ssim(g1, g2, data_range=255))


def generate_histogram_plot(original: np.ndarray, restored: np.ndarray) -> plt.Figure:
    """Generate comparative pixel intensity histograms."""
    g_orig = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY) if original.ndim == 3 else original
    g_rest = cv2.cvtColor(restored, cv2.COLOR_BGR2GRAY) if restored.ndim == 3 else restored

    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.hist(g_orig.ravel(), bins=64, range=(0, 256), color="#E74C3C", alpha=0.5, label="Original Scan")
    ax.hist(g_rest.ravel(), bins=64, range=(0, 256), color="#2ECC71", alpha=0.5, label="Restored Document")
    ax.set_title("Pixel Intensity Distribution Shift (Stain Removal vs. Foreground Contrast)")
    ax.set_xlabel("Pixel Luminance (0=Black, 255=White)")
    ax.set_ylabel("Pixel Frequency")
    ax.legend()
    fig.tight_layout()
    return fig
