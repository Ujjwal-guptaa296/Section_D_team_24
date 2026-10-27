"""Member 2: Spatial Filtering, Contrast Enhancement & Inpainting Module.

Handles:
1. Edge-preserving denoising (Fast Non-Local Means, Bilateral, Median)
2. Contrast enhancement (CLAHE in CIE L*a*b* space)
3. Defect mask detection and digital inpainting (Telea / Navier-Stokes)
"""

from typing import Tuple, Optional
import cv2
import numpy as np


def denoise_document(
    image: np.ndarray,
    method: str = "fastNlMeans",
    strength: int = 10,
    kernel_size: int = 5,
) -> np.ndarray:
    """Apply edge-preserving spatial denoising to suppress paper grain noise."""
    if image is None:
        raise ValueError("Input image is None")

    is_color = (image.ndim == 3)
    k = max(3, kernel_size if kernel_size % 2 == 1 else kernel_size + 1)
    s = max(1, strength)

    if method == "fastNlMeans":
        if is_color:
            return cv2.fastNlMeansDenoisingColored(image, None, float(s), float(s), 7, 21)
        else:
            return cv2.fastNlMeansDenoising(image, None, float(s), 7, 21)
    elif method == "bilateral":
        d = k
        sigma_color = float(s * 5)
        sigma_space = float(s * 5)
        return cv2.bilateralFilter(image, d, sigma_color, sigma_space)
    elif method == "median":
        return cv2.medianBlur(image, k)
    elif method == "gaussian":
        return cv2.GaussianBlur(image, (k, k), 0)
    else:
        return image.copy()


def enhance_contrast(
    image: np.ndarray,
    method: str = "clahe",
    clip_limit: float = 2.0,
    tile_size: int = 8,
) -> np.ndarray:
    """Enhance faded ink contrast without blowing out paper background."""
    if image is None:
        raise ValueError("Input image is None")

    is_color = (image.ndim == 3)
    t = max(2, tile_size)
    c = max(0.5, float(clip_limit))

    if method == "clahe":
        clahe = cv2.createCLAHE(clipLimit=c, tileGridSize=(t, t))
        if is_color:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab)
            l_enhanced = clahe.apply(l_channel)
            merged = cv2.merge([l_enhanced, a_channel, b_channel])
            return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
        else:
            return clahe.apply(image)

    elif method == "histogram_eq":
        if is_color:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab)
            l_eq = cv2.equalizeHist(l_channel)
            merged = cv2.merge([l_eq, a_channel, b_channel])
            return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
        else:
            return cv2.equalizeHist(image)

    return image.copy()


def detect_damage_mask(
    image: np.ndarray,
    dark_thresh: int = 30,
    light_thresh: int = 245,
    min_area: int = 100,
) -> np.ndarray:
    """Detect anomalous defect regions (ink blots, holes, tears) for inpainting."""
    if image is None:
        raise ValueError("Input image is None")

    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    dark_mask = (gray <= dark_thresh).astype(np.uint8) * 255
    light_mask = (gray >= light_thresh).astype(np.uint8) * 255
    combined = cv2.bitwise_or(dark_mask, light_mask)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    opened = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    clean_mask = np.zeros_like(gray, dtype=np.uint8)
    for c in contours:
        if cv2.contourArea(c) >= min_area:
            cv2.drawContours(clean_mask, [c], -1, 255, -1)

    return clean_mask


def inpaint_defects(
    image: np.ndarray,
    mask: Optional[np.ndarray] = None,
    method: str = "telea",
    radius: int = 5,
) -> np.ndarray:
    """Inpaint damaged regions using Fast Marching (Telea) or Navier-Stokes."""
    if image is None:
        raise ValueError("Input image is None")

    if mask is None:
        mask = detect_damage_mask(image)

    if cv2.countNonZero(mask) == 0:
        return image.copy()

    is_color = (image.ndim == 3)
    bgr_img = image if is_color else cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    inpaint_mode = cv2.INPAINT_TELEA if method.lower() == "telea" else cv2.INPAINT_NS
    inpainted = cv2.inpaint(bgr_img, mask, max(1, radius), inpaint_mode)

    if not is_color:
        return cv2.cvtColor(inpainted, cv2.COLOR_BGR2GRAY)
    return inpainted
