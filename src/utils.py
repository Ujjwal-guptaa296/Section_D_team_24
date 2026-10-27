"""Helper utilities for document restoration pipeline.

This module provides metrics (PSNR, SSIM), image format normalization, side-by-side
comparisons, damage mask detection, histogram visualization, and display resizing.
"""

import cv2
import matplotlib.pyplot as plt
import numpy as np
from skimage.metrics import peak_signal_noise_ratio, structural_similarity


def ensure_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert an image to 2D uint8 grayscale if color, returning as-is if already grayscale.

    Args:
        image: Input image as numpy array.

    Returns:
        np.ndarray: 2D uint8 grayscale image.

    Raises:
        TypeError: If image is not an instance of numpy.ndarray.
        ValueError: If image is empty or has unsupported dimensions.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Expected numpy.ndarray, got {type(image).__name__}")
    if image.size == 0:
        raise ValueError("Input image is empty.")

    if image.ndim == 2:
        gray = image.copy()
    elif image.ndim == 3:
        channels = image.shape[2]
        if channels == 1:
            gray = image[:, :, 0].copy()
        elif channels == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif channels == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        else:
            raise ValueError(f"Unsupported number of channels: {channels}")
    else:
        raise ValueError(f"Unsupported image dimensions: {image.ndim}")

    if gray.dtype != np.uint8:
        gray = np.clip(gray, 0, 255).astype(np.uint8)

    return gray


def ensure_color(image: np.ndarray) -> np.ndarray:
    """Convert an image to 3-channel uint8 BGR if grayscale, returning as-is if already color.

    Args:
        image: Input image as numpy array.

    Returns:
        np.ndarray: 3-channel (BGR) uint8 image.

    Raises:
        TypeError: If image is not an instance of numpy.ndarray.
        ValueError: If image is empty or has unsupported dimensions.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Expected numpy.ndarray, got {type(image).__name__}")
    if image.size == 0:
        raise ValueError("Input image is empty.")

    if image.ndim == 2:
        color = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    elif image.ndim == 3:
        channels = image.shape[2]
        if channels == 1:
            color = cv2.cvtColor(image[:, :, 0], cv2.COLOR_GRAY2BGR)
        elif channels == 3:
            color = image.copy()
        elif channels == 4:
            color = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        else:
            raise ValueError(f"Unsupported number of channels: {channels}")
    else:
        raise ValueError(f"Unsupported image dimensions: {image.ndim}")

    if color.dtype != np.uint8:
        color = np.clip(color, 0, 255).astype(np.uint8)

    return color


def compute_psnr(original: np.ndarray, restored: np.ndarray) -> float:
    """Compute Peak Signal-to-Noise Ratio (PSNR) between original and restored images.

    Handles same-image case by returning float('inf'), converts color images to
    grayscale if needed, and aligns spatial dimensions before computing PSNR.

    Args:
        original: Original or ground-truth document image.
        restored: Restored document image.

    Returns:
        float: PSNR value in decibels (dB), or float('inf') if images are identical.
    """
    orig_gray = ensure_grayscale(original)
    rest_gray = ensure_grayscale(restored)

    # Harmonize spatial dimensions if needed
    if orig_gray.shape != rest_gray.shape:
        rest_gray = cv2.resize(
            rest_gray,
            (orig_gray.shape[1], orig_gray.shape[0]),
            interpolation=cv2.INTER_AREA
            if (rest_gray.shape[0] > orig_gray.shape[0])
            else cv2.INTER_LINEAR,
        )

    # Handle identical images case (MSE = 0 -> PSNR = inf)
    if np.array_equal(orig_gray, rest_gray):
        return float("inf")

    psnr_val = peak_signal_noise_ratio(orig_gray, rest_gray, data_range=255)
    return float(psnr_val)


def compute_ssim(original: np.ndarray, restored: np.ndarray) -> float:
    """Compute Structural Similarity Index (SSIM) between original and restored images.

    Handles multichannel color images automatically, falls back to grayscale
    conversion if channel counts differ, and adjusts window size for small images.

    Args:
        original: Original document image.
        restored: Restored document image.

    Returns:
        float: SSIM value in [-1.0, 1.0], where 1.0 indicates perfect structural match.
    """
    # Fast path for identical images
    if original.shape == restored.shape and np.array_equal(original, restored):
        return 1.0

    # Determine whether multichannel calculation applies
    if (
        original.ndim == 3
        and restored.ndim == 3
        and original.shape[2] == restored.shape[2]
        and original.shape[2] in (3, 4)
    ):
        orig = original.copy()
        rest = restored.copy()
        channel_axis = -1
    else:
        # Convert to grayscale if dimensionality or channel counts differ
        orig = ensure_grayscale(original)
        rest = ensure_grayscale(restored)
        channel_axis = None

    # Harmonize spatial dimensions if needed
    if orig.shape[:2] != rest.shape[:2]:
        rest = cv2.resize(
            rest,
            (orig.shape[1], orig.shape[0]),
            interpolation=cv2.INTER_AREA
            if (rest.shape[0] > orig.shape[0])
            else cv2.INTER_LINEAR,
        )

    if np.array_equal(orig, rest):
        return 1.0

    # Adaptive window size for small image dimensions (skimage default is 7)
    min_dim = min(orig.shape[0], orig.shape[1])
    win_size = min(7, min_dim)
    if win_size % 2 == 0:
        win_size -= 1

    if win_size < 3:
        return 1.0 if np.array_equal(orig, rest) else 0.0

    kwargs = {"win_size": win_size, "data_range": 255}
    if channel_axis is not None:
        kwargs["channel_axis"] = channel_axis

    ssim_val = structural_similarity(orig, rest, **kwargs)
    return float(ssim_val)


def _draw_banner_label(image: np.ndarray, label_text: str) -> np.ndarray:
    """Draw a high-contrast label badge on the top-left of an image.

    Args:
        image: 3-channel BGR uint8 image.
        label_text: Text string to display (e.g. 'Before', 'After').

    Returns:
        np.ndarray: Image copy with rendered label badge.
    """
    annotated = image.copy()
    h, w = annotated.shape[:2]

    # Dynamically scale font parameters based on image size
    scale = max(0.5, min(h, w) / 600.0)
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = max(1, int(round(scale * 2.0)))

    (tw, th), baseline = cv2.getTextSize(label_text, font, scale, thickness)
    pad = max(6, int(8 * scale))
    x1, y1 = pad, pad
    x2 = x1 + tw + 2 * pad
    y2 = y1 + th + baseline + 2 * pad

    # Draw dark background badge with subtle light border for readability on any background
    cv2.rectangle(annotated, (x1, y1), (x2, y2), (20, 20, 20), cv2.FILLED)
    cv2.rectangle(annotated, (x1, y1), (x2, y2), (220, 220, 220), max(1, int(scale)))

    text_x = x1 + pad
    text_y = y1 + pad + th
    cv2.putText(
        annotated,
        label_text,
        (text_x, text_y),
        font,
        scale,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA,
    )
    return annotated


def create_comparison(before: np.ndarray, after: np.ndarray) -> np.ndarray:
    """Create a side-by-side comparison image labeled with 'Before' and 'After'.

    Handles color vs. grayscale differences by standardizing to 3-channel BGR,
    resizes images to match vertical dimensions if needed, and draws high-contrast
    labels on each panel.

    Args:
        before: Original or input document image.
        after: Processed or restored document image.

    Returns:
        np.ndarray: Combined side-by-side image in BGR format.
    """
    # Normalize color format to 3-channel BGR
    b_color = ensure_color(before)
    a_color = ensure_color(after)

    h_before, w_before = b_color.shape[:2]
    h_after, w_after = a_color.shape[:2]

    # Align height of 'after' to match 'before'
    if h_before != h_after:
        scale = float(h_before) / float(h_after)
        target_w = max(1, int(round(w_after * scale)))
        interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
        a_color = cv2.resize(a_color, (target_w, h_before), interpolation=interp)

    # Render 'Before' and 'After' badges
    b_labeled = _draw_banner_label(b_color, "Before")
    a_labeled = _draw_banner_label(a_color, "After")

    # Concatenate horizontally
    comparison = np.hstack([b_labeled, a_labeled])
    return comparison


def detect_damage_mask(
    gray_image: np.ndarray,
    dark_threshold: int = 30,
    light_threshold: int = 245,
    min_area: int = 100,
) -> np.ndarray:
    """Detect damaged areas in document images (holes, tears, ink stains, missing regions).

    Identifies extreme dark spots (holes/burns/ink smudges) and extreme light spots
    (torn-away regions/paper voids), applies morphological noise filtering, and
    keeps only connected components with area >= min_area.

    Args:
        gray_image: Document image as numpy array (grayscale or color).
        dark_threshold: Intensity cutoff for dark damage spots (0-255).
        light_threshold: Intensity cutoff for light missing regions (0-255).
        min_area: Minimum contour area in pixels to be retained as damage.

    Returns:
        np.ndarray: Binary mask (uint8) where damaged pixels are 255 and clean are 0.

    Raises:
        ValueError: If thresholds are invalid or min_area is negative.
    """
    if not (0 <= dark_threshold <= 255 and 0 <= light_threshold <= 255):
        raise ValueError("Thresholds must be within [0, 255].")
    if dark_threshold > light_threshold:
        raise ValueError("dark_threshold cannot exceed light_threshold.")
    if min_area < 0:
        raise ValueError("min_area must be non-negative.")

    gray = ensure_grayscale(gray_image)

    # Detect extreme dark defects (holes, tears, ink stains)
    dark_mask = (gray <= dark_threshold).astype(np.uint8) * 255

    # Detect extreme bright defects (missing paper fragments, severe bleaching)
    light_mask = (gray >= light_threshold).astype(np.uint8) * 255

    # Combine both defect types
    raw_mask = cv2.bitwise_or(dark_mask, light_mask)

    # Morphological cleaning to eliminate isolated scanning artifacts and fill pinholes
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    cleaned_mask = cv2.morphologyEx(raw_mask, cv2.MORPH_OPEN, kernel)
    cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel)

    # Area filtering using contour analysis
    damage_mask = np.zeros_like(gray, dtype=np.uint8)
    contours, _ = cv2.findContours(
        cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    for cnt in contours:
        if cv2.contourArea(cnt) >= min_area:
            cv2.drawContours(damage_mask, [cnt], -1, 255, thickness=cv2.FILLED)

    return damage_mask


def plot_histograms(before: np.ndarray, after: np.ndarray) -> plt.Figure:
    """Create a matplotlib figure displaying overlaid intensity histograms for before and after images.

    Plots the 'Before' histogram in semi-transparent blue and the 'After' histogram
    in semi-transparent red for direct visual assessment of contrast and tone adjustments.

    Args:
        before: Document image prior to restoration.
        after: Document image after restoration.

    Returns:
        plt.Figure: The created matplotlib figure object.
    """
    b_gray = ensure_grayscale(before)
    a_gray = ensure_grayscale(after)

    fig, ax = plt.subplots(figsize=(8, 5), dpi=100)

    # Overlaid normalized histograms
    ax.hist(
        b_gray.ravel(),
        bins=256,
        range=(0, 256),
        color="blue",
        alpha=0.5,
        label="Before",
        density=True,
    )
    ax.hist(
        a_gray.ravel(),
        bins=256,
        range=(0, 256),
        color="red",
        alpha=0.5,
        label="After",
        density=True,
    )

    ax.set_title("Pixel Intensity Distribution (Before vs. After)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Pixel Intensity (0 - 255)", fontsize=11)
    ax.set_ylabel("Normalized Frequency (Density)", fontsize=11)
    ax.set_xlim([0, 255])
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, linestyle="--", alpha=0.5)

    fig.tight_layout()
    return fig


def resize_for_display(image: np.ndarray, max_dim: int = 800) -> np.ndarray:
    """Resize an image so its largest dimension is at most max_dim, preserving aspect ratio.

    Uses cv2.INTER_AREA for clean downsampling. If the image is already smaller
    than or equal to max_dim along its largest axis, a copy of the original is returned.

    Args:
        image: Image array to resize.
        max_dim: Maximum allowable length of the longest edge in pixels.

    Returns:
        np.ndarray: Resized image or original copy.

    Raises:
        TypeError: If image is not a numpy.ndarray.
        ValueError: If max_dim is non-positive or image is empty.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Expected image to be a numpy.ndarray, got {type(image).__name__}")
    if image.size == 0:
        raise ValueError("Input image is empty.")
    if max_dim <= 0:
        raise ValueError(f"max_dim must be positive, got {max_dim}")

    h, w = image.shape[:2]
    max_side = max(h, w)

    if max_side <= max_dim:
        return image.copy()

    scale = float(max_dim) / float(max_side)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))

    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
