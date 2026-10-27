"""Member 3: Adaptive Binarization & Post-Processing Module.

Handles:
1. High-speed O(1) Sauvola local adaptive binarization (OpenCV box filter formulation)
2. Otsu, Niblack, and Adaptive Gaussian thresholding implementations
3. Post-processing (Unsharp masking and morphological 2x2 cleanup)
"""

from typing import Dict
import cv2
import numpy as np


def sauvola_binarize(
    image: np.ndarray,
    block_size: int = 25,
    k: float = 0.2,
    r: float = 128.0,
) -> np.ndarray:
    """High-speed O(1) Sauvola adaptive thresholding using box filters."""
    if image is None:
        raise ValueError("Input image is None")

    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    w = max(3, block_size if block_size % 2 == 1 else block_size + 1)
    k_val = float(k)
    r_val = float(r) if r > 0 else 128.0

    img_f = gray.astype(np.float64)
    mean = cv2.blur(img_f, (w, w), borderType=cv2.BORDER_REFLECT)
    sq_mean = cv2.blur(img_f ** 2, (w, w), borderType=cv2.BORDER_REFLECT)
    variance = np.maximum(sq_mean - mean ** 2, 0.0)
    std = np.sqrt(variance)

    threshold = mean * (1.0 + k_val * ((std / r_val) - 1.0))
    binary = np.where(img_f >= threshold, 255, 0).astype(np.uint8)
    return binary


def otsu_binarize(image: np.ndarray) -> np.ndarray:
    """Otsu global thresholding."""
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def niblack_binarize(
    image: np.ndarray,
    block_size: int = 25,
    k: float = -0.2,
) -> np.ndarray:
    """Niblack local thresholding."""
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    w = max(3, block_size if block_size % 2 == 1 else block_size + 1)
    img_f = gray.astype(np.float64)
    mean = cv2.blur(img_f, (w, w), borderType=cv2.BORDER_REFLECT)
    sq_mean = cv2.blur(img_f ** 2, (w, w), borderType=cv2.BORDER_REFLECT)
    variance = np.maximum(sq_mean - mean ** 2, 0.0)
    std = np.sqrt(variance)

    threshold = mean + float(k) * std
    return np.where(img_f >= threshold, 255, 0).astype(np.uint8)


def adaptive_gaussian_binarize(
    image: np.ndarray,
    block_size: int = 25,
    c: int = 10,
) -> np.ndarray:
    """Adaptive Gaussian local thresholding."""
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    w = max(3, block_size if block_size % 2 == 1 else block_size + 1)
    return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, w, c)


def compare_all_binarization_methods(image: np.ndarray) -> Dict[str, np.ndarray]:
    """Run and compare all binarization algorithms."""
    return {
        "Otsu": otsu_binarize(image),
        "Adaptive Gaussian": adaptive_gaussian_binarize(image),
        "Sauvola (O(1))": sauvola_binarize(image),
        "Niblack": niblack_binarize(image),
    }


def postprocess_text(
    image: np.ndarray,
    sharpen: bool = True,
    sharpen_strength: float = 1.5,
    morpho_clean: bool = True,
) -> np.ndarray:
    """Sharpen characters with unsharp masking and eliminate speckle noise."""
    res = image.copy()
    if sharpen:
        blurred = cv2.GaussianBlur(res, (0, 0), sigmaX=3.0)
        sharpened = cv2.addWeighted(res, 1.0 + sharpen_strength, blurred, -sharpen_strength, 0.0)
        res = np.clip(sharpened, 0, 255).astype(np.uint8)

    if morpho_clean:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        opened = cv2.morphologyEx(res, cv2.MORPH_OPEN, kernel)
        res = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)

    return res
