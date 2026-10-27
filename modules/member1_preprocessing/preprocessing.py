"""Member 1: Geometric Rectification & Preprocessing Module.

Handles:
1. Border detection and cropping (intensity thresholding)
2. Deskewing (Radon projection profile / Hough transform)
3. Background removal & stain correction (Morphological flat-field division)
"""

from typing import Tuple, Optional
import cv2
import numpy as np

try:
    from deskew import determine_skew
    HAS_DESKEW = True
except ImportError:
    HAS_DESKEW = False


def crop_document_borders(image: np.ndarray, threshold: int = 10, padding: int = 5) -> np.ndarray:
    """Crop dark scanner border margins from the document image."""
    if image is None:
        raise ValueError("Input image is None")

    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    h, w = gray.shape
    row_means = np.mean(gray, axis=1)
    col_means = np.mean(gray, axis=0)

    row_indices = np.where(row_means > threshold)[0]
    col_indices = np.where(col_means > threshold)[0]

    if len(row_indices) == 0 or len(col_indices) == 0:
        return image.copy()

    y_min = max(0, int(row_indices[0]) - padding)
    y_max = min(h, int(row_indices[-1]) + padding + 1)
    x_min = max(0, int(col_indices[0]) - padding)
    x_max = min(w, int(col_indices[-1]) + padding + 1)

    if (y_max - y_min) < 10 or (x_max - x_min) < 10:
        return image.copy()

    return image[y_min:y_max, x_min:x_max].copy()


def deskew_document(image: np.ndarray, max_angle: float = 45.0) -> Tuple[np.ndarray, float]:
    """Detect and correct document skew rotation."""
    if image is None:
        raise ValueError("Input image is None")

    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    angle = 0.0
    if HAS_DESKEW:
        try:
            detected_angle = determine_skew(gray)
            if detected_angle is not None and abs(detected_angle) <= max_angle:
                angle = float(detected_angle)
        except Exception:
            angle = 0.0

    if angle == 0.0:
        # Fallback using Hough Lines
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10)
        if lines is not None and len(lines) > 0:
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if x2 - x1 != 0:
                    deg = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                    if abs(deg) <= max_angle:
                        angles.append(deg)
            if angles:
                angle = float(np.median(angles))

    if abs(angle) < 0.1:
        return image.copy(), 0.0

    h, w = image.shape[:2]
    center = (w / 2.0, h / 2.0)
    rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image,
        rot_mat,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255) if image.ndim == 3 else 255,
    )
    return rotated, angle


def remove_background_illumination(image: np.ndarray, kernel_size: int = 51) -> np.ndarray:
    """Normalize non-uniform yellowing and lighting using morphological flat-field division."""
    if image is None:
        raise ValueError("Input image is None")

    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    k = max(3, kernel_size if kernel_size % 2 == 1 else kernel_size + 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
    background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

    bg_float = np.maximum(background.astype(np.float32), 1.0)
    norm = (gray.astype(np.float32) / bg_float) * 255.0
    return np.clip(norm, 0, 255).astype(np.uint8)
