"""Document binarization module for historical and degraded document restoration.

This module provides multiple global, local adaptive, and morphological binarization
methods tailored for document images with non-uniform illumination, ink bleed-through,
fading, and degradation.
"""

import cv2
import numpy as np


def _validate_grayscale(gray_image: np.ndarray) -> np.ndarray:
    """Validate and ensure that the input image is a 2D uint8 grayscale array.

    Args:
        gray_image: Input numpy array expected to be a 2D grayscale image.

    Returns:
        np.ndarray: Validated 2D uint8 grayscale image.

    Raises:
        TypeError: If input is not an instance of numpy.ndarray.
        ValueError: If array is empty or not 2-dimensional.
    """
    if not isinstance(gray_image, np.ndarray):
        raise TypeError(
            f"Expected gray_image to be a numpy.ndarray, got {type(gray_image).__name__}"
        )
    if gray_image.size == 0:
        raise ValueError("Input image array is empty.")
    if gray_image.ndim != 2:
        raise ValueError(
            f"Input image must be a 2D grayscale array, but got shape {gray_image.shape} "
            f"with {gray_image.ndim} dimensions."
        )
    if gray_image.dtype != np.uint8:
        gray_image = np.clip(gray_image, 0, 255).astype(np.uint8)

    return gray_image


def otsu_binarize(gray_image: np.ndarray) -> np.ndarray:
    """Binarize a grayscale document image using Otsu's global thresholding.

    Otsu's thresholding automatically computes an optimal global threshold
    by maximizing inter-class variance between foreground text and background.

    Args:
        gray_image: 2D grayscale image as uint8 numpy array.

    Returns:
        np.ndarray: Binary image (uint8) with values 0 (text/ink) and 255 (background).
    """
    validated = _validate_grayscale(gray_image)
    _, binary = cv2.threshold(
        validated, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return binary


def adaptive_gaussian_binarize(
    gray_image: np.ndarray, block_size: int = 11, C: int = 2
) -> np.ndarray:
    """Binarize a grayscale document image using adaptive Gaussian thresholding.

    The threshold value is a weighted sum (Gaussian window) of the neighborhood
    values minus the constant C, adapting to local illumination gradients.

    Args:
        gray_image: 2D grayscale image as uint8 numpy array.
        block_size: Size of the neighborhood window. Must be an odd integer >= 3.
        C: Constant subtracted from the calculated weighted mean.

    Returns:
        np.ndarray: Binary image (uint8) with values 0 (text/ink) and 255 (background).

    Raises:
        ValueError: If block_size is not an odd integer >= 3.
    """
    if block_size < 3 or block_size % 2 == 0:
        raise ValueError(
            f"block_size must be an odd integer >= 3, got {block_size}"
        )

    validated = _validate_grayscale(gray_image)
    return cv2.adaptiveThreshold(
        validated,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        block_size,
        C,
    )


def adaptive_mean_binarize(
    gray_image: np.ndarray, block_size: int = 11, C: int = 2
) -> np.ndarray:
    """Binarize a grayscale document image using adaptive mean thresholding.

    The threshold value is the arithmetic mean of the local neighborhood
    minus the constant C.

    Args:
        gray_image: 2D grayscale image as uint8 numpy array.
        block_size: Size of the neighborhood window. Must be an odd integer >= 3.
        C: Constant subtracted from the calculated mean.

    Returns:
        np.ndarray: Binary image (uint8) with values 0 (text/ink) and 255 (background).

    Raises:
        ValueError: If block_size is not an odd integer >= 3.
    """
    if block_size < 3 or block_size % 2 == 0:
        raise ValueError(
            f"block_size must be an odd integer >= 3, got {block_size}"
        )

    validated = _validate_grayscale(gray_image)
    return cv2.adaptiveThreshold(
        validated,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        block_size,
        C,
    )


def sauvola_binarize(
    gray_image: np.ndarray,
    window_size: int = 25,
    k: float = 0.2,
    R: float = 128.0,
) -> np.ndarray:
    """Binarize a grayscale document image using Sauvola's local adaptive thresholding.

    Implements the fast O(1) algorithm using OpenCV box filters (cv2.blur).
    Sauvola's method improves over Niblack when background contrast varies,
    computing the local threshold as:
        threshold = mean * (1 + k * (std / R - 1))
    Pixels with intensity >= threshold are set to 255 (background), else 0 (text).

    Args:
        gray_image: 2D grayscale image as uint8 numpy array.
        window_size: Local neighborhood window size. Must be an odd integer >= 3.
        k: User-defined tuning factor (typically between 0.2 and 0.5).
        R: Dynamic range of standard deviation (default 128.0 for 8-bit images).

    Returns:
        np.ndarray: Binary image (uint8) with values 0 (text/ink) and 255 (background).

    Raises:
        ValueError: If window_size is not an odd integer >= 3 or R <= 0.
    """
    if window_size < 3 or window_size % 2 == 0:
        raise ValueError(
            f"window_size must be an odd integer >= 3, got {window_size}"
        )
    if R <= 0:
        raise ValueError(f"Dynamic range parameter R must be positive, got {R}")

    validated = _validate_grayscale(gray_image)
    img_float = validated.astype(np.float64)
    ksize = (window_size, window_size)

    # Fast O(1) computation of local mean via box filter
    mean = cv2.blur(img_float, ksize, borderType=cv2.BORDER_REFLECT)

    # Fast O(1) computation of local mean of squares
    mean_sq = cv2.blur(img_float**2, ksize, borderType=cv2.BORDER_REFLECT)

    # Local variance: Var(X) = E[X^2] - (E[X])^2 (clip to 0 for numerical stability)
    variance = np.maximum(mean_sq - (mean**2), 0.0)
    std = np.sqrt(variance)

    # Sauvola threshold calculation
    threshold = mean * (1.0 + k * ((std / R) - 1.0))

    # Binary classification: pixel >= threshold -> 255, else 0
    binary = np.where(img_float >= threshold, np.uint8(255), np.uint8(0))
    return binary


def niblack_binarize(
    gray_image: np.ndarray, window_size: int = 25, k: float = -0.2
) -> np.ndarray:
    """Binarize a grayscale document image using Niblack's local adaptive thresholding.

    Implements the fast O(1) algorithm using OpenCV box filters (cv2.blur).
    The local threshold is computed as:
        threshold = mean + k * std
    Pixels with intensity >= threshold are set to 255 (background), else 0 (text).

    Args:
        gray_image: 2D grayscale image as uint8 numpy array.
        window_size: Local neighborhood window size. Must be an odd integer >= 3.
        k: User-defined tuning factor (typically -0.1 to -0.2 for dark text).

    Returns:
        np.ndarray: Binary image (uint8) with values 0 (text/ink) and 255 (background).

    Raises:
        ValueError: If window_size is not an odd integer >= 3.
    """
    if window_size < 3 or window_size % 2 == 0:
        raise ValueError(
            f"window_size must be an odd integer >= 3, got {window_size}"
        )

    validated = _validate_grayscale(gray_image)
    img_float = validated.astype(np.float64)
    ksize = (window_size, window_size)

    # Fast O(1) computation of local mean via box filter
    mean = cv2.blur(img_float, ksize, borderType=cv2.BORDER_REFLECT)

    # Fast O(1) computation of local mean of squares
    mean_sq = cv2.blur(img_float**2, ksize, borderType=cv2.BORDER_REFLECT)

    # Local variance: Var(X) = E[X^2] - (E[X])^2 (clip to 0 for numerical stability)
    variance = np.maximum(mean_sq - (mean**2), 0.0)
    std = np.sqrt(variance)

    # Niblack threshold calculation
    threshold = mean + k * std

    # Binary classification: pixel >= threshold -> 255, else 0
    binary = np.where(img_float >= threshold, np.uint8(255), np.uint8(0))
    return binary


def black_hat_text(gray_image: np.ndarray, kernel_size: int = 15) -> np.ndarray:
    """Enhance dark text in a document using the morphological Black-Hat transform.

    The Black-Hat transform computes the difference between the morphological
    closing of an image and the input image (close(img) - img). For light
    background documents, this isolates dark text strokes. The result is then
    inverted and normalized to yield enhanced dark text on a bright background.

    Args:
        gray_image: 2D grayscale image as uint8 numpy array.
        kernel_size: Size of rectangular structuring element (width and height).

    Returns:
        np.ndarray: Enhanced grayscale image (uint8, NOT binary) with normalized text contrast.

    Raises:
        ValueError: If kernel_size is less than 1.
    """
    if kernel_size < 1:
        raise ValueError(f"kernel_size must be >= 1, got {kernel_size}")

    validated = _validate_grayscale(gray_image)

    # Rectangular structuring element suitable for text strokes
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))

    # Black-hat isolates dark elements smaller than kernel on bright background
    blackhat = cv2.morphologyEx(validated, cv2.MORPH_BLACKHAT, kernel)

    # Invert so text remains dark and background bright
    inverted = cv2.bitwise_not(blackhat)

    # Check for uniform response edge case
    min_val, max_val = int(np.min(inverted)), int(np.max(inverted))
    if min_val == max_val:
        return validated.copy()

    # Normalize to full [0, 255] dynamic range
    enhanced = cv2.normalize(
        inverted, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U
    )
    return enhanced


def compare_all_methods(gray_image: np.ndarray) -> dict:
    """Apply all document binarization methods using default parameters.

    Args:
        gray_image: 2D grayscale image as uint8 numpy array.

    Returns:
        dict: Mapping of method names to binary images (uint8, 0 or 255).
              Keys: 'Otsu', 'Adaptive Gaussian', 'Adaptive Mean', 'Sauvola', 'Niblack'.
    """
    validated = _validate_grayscale(gray_image)

    return {
        "Otsu": otsu_binarize(validated),
        "Adaptive Gaussian": adaptive_gaussian_binarize(validated),
        "Adaptive Mean": adaptive_mean_binarize(validated),
        "Sauvola": sauvola_binarize(validated),
        "Niblack": niblack_binarize(validated),
    }
