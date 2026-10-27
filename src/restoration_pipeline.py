"""Document Restoration Pipeline.

This module provides the main orchestration class `DocumentRestorer` for
restoring degraded and aged document images through a chained/fluent pipeline.
Stages include border cropping, deskewing, background removal, denoising,
contrast enhancement, inpainting, binarization, and morphological post-processing.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union
import cv2
import numpy as np

# Attempt deskew library import with fallback
try:
    from deskew import determine_skew
    HAS_DESKEW = True
except ImportError:
    HAS_DESKEW = False

# Import binarization and utility functions, providing fallback implementations
# if the sibling modules are not yet installed or executed in different contexts.
try:
    from src.binarization import (
        otsu_binarize,
        adaptive_gaussian_binarize,
        adaptive_mean_binarize,
        sauvola_binarize,
        niblack_binarize,
        black_hat_text,
    )
    from src.utils import ensure_grayscale, ensure_color, compute_psnr, compute_ssim
except ImportError:
    try:
        from binarization import (
            otsu_binarize,
            adaptive_gaussian_binarize,
            adaptive_mean_binarize,
            sauvola_binarize,
            niblack_binarize,
            black_hat_text,
        )
        from utils import ensure_grayscale, ensure_color, compute_psnr, compute_ssim
    except ImportError:
        # Fallback implementations to guarantee standalone module operability
        def ensure_grayscale(image: np.ndarray) -> np.ndarray:
            """Ensure image is single-channel grayscale uint8."""
            if not isinstance(image, np.ndarray):
                raise TypeError(f"Expected numpy.ndarray, got {type(image)}")
            if image.ndim == 2:
                return image.astype(np.uint8)
            if image.ndim == 3:
                channels = image.shape[2]
                if channels == 1:
                    return image[:, :, 0].astype(np.uint8)
                if channels == 3:
                    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                if channels == 4:
                    return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            raise ValueError(f"Unsupported image shape for grayscale conversion: {image.shape}")

        def ensure_color(image: np.ndarray) -> np.ndarray:
            """Ensure image is 3-channel BGR color uint8."""
            if not isinstance(image, np.ndarray):
                raise TypeError(f"Expected numpy.ndarray, got {type(image)}")
            if image.ndim == 2:
                return cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_GRAY2BGR)
            if image.ndim == 3:
                channels = image.shape[2]
                if channels == 1:
                    return cv2.cvtColor(image[:, :, 0].astype(np.uint8), cv2.COLOR_GRAY2BGR)
                if channels == 3:
                    return image.astype(np.uint8)
                if channels == 4:
                    return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            raise ValueError(f"Unsupported image shape for color conversion: {image.shape}")

        def compute_psnr(image_true: np.ndarray, image_test: np.ndarray) -> float:
            """Compute Peak Signal-to-Noise Ratio between two images."""
            img1 = image_true.astype(np.float64)
            img2 = image_test.astype(np.float64)
            if img1.shape != img2.shape:
                img2 = cv2.resize(
                    img2,
                    (image_true.shape[1], image_true.shape[0]),
                    interpolation=cv2.INTER_LINEAR,
                )
                if img1.ndim == 3 and img2.ndim == 2:
                    img2 = cv2.cvtColor(img2.astype(np.uint8), cv2.COLOR_GRAY2BGR).astype(np.float64)
                elif img1.ndim == 2 and img2.ndim == 3:
                    img2 = cv2.cvtColor(img2.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float64)
            mse = float(np.mean((img1 - img2) ** 2))
            if mse == 0.0:
                return float("inf")
            max_val = 255.0
            return float(10.0 * np.log10((max_val ** 2) / mse))

        def compute_ssim(image_true: np.ndarray, image_test: np.ndarray) -> float:
            """Compute Structural Similarity Index (SSIM) between two images."""
            try:
                from skimage.metrics import structural_similarity as ssim_metric
                gray1 = ensure_grayscale(image_true)
                gray2 = ensure_grayscale(image_test)
                if gray1.shape != gray2.shape:
                    gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))
                return float(ssim_metric(gray1, gray2, data_range=255))
            except Exception:
                # Direct OpenCV fallback computation
                gray1 = ensure_grayscale(image_true).astype(np.float64)
                gray2 = ensure_grayscale(image_test).astype(np.float64)
                if gray1.shape != gray2.shape:
                    gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))
                c1 = (0.01 * 255) ** 2
                c2 = (0.03 * 255) ** 2
                kernel = cv2.getGaussianKernel(11, 1.5)
                window = np.outer(kernel, kernel.transpose())
                mu1 = cv2.filter2D(gray1, -1, window)[5:-5, 5:-5]
                mu2 = cv2.filter2D(gray2, -1, window)[5:-5, 5:-5]
                mu1_sq = mu1 ** 2
                mu2_sq = mu2 ** 2
                mu1_mu2 = mu1 * mu2
                sigma1_sq = cv2.filter2D(gray1 ** 2, -1, window)[5:-5, 5:-5] - mu1_sq
                sigma2_sq = cv2.filter2D(gray2 ** 2, -1, window)[5:-5, 5:-5] - mu2_sq
                sigma12 = cv2.filter2D(gray1 * gray2, -1, window)[5:-5, 5:-5] - mu1_mu2
                ssim_map = ((2 * mu1_mu2 + c1) * (2 * sigma12 + c2)) / (
                    (mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2)
                )
                return float(np.clip(np.mean(ssim_map), -1.0, 1.0))

        def otsu_binarize(image: np.ndarray) -> np.ndarray:
            """Perform Otsu thresholding."""
            gray = ensure_grayscale(image)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return thresh

        def adaptive_gaussian_binarize(
            image: np.ndarray, block_size: int = 25, c_val: int = 10
        ) -> np.ndarray:
            """Perform adaptive Gaussian thresholding."""
            gray = ensure_grayscale(image)
            b_size = block_size if block_size % 2 == 1 else block_size + 1
            b_size = max(3, b_size)
            return cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, b_size, c_val
            )

        def adaptive_mean_binarize(
            image: np.ndarray, block_size: int = 25, c_val: int = 10
        ) -> np.ndarray:
            """Perform adaptive mean thresholding."""
            gray = ensure_grayscale(image)
            b_size = block_size if block_size % 2 == 1 else block_size + 1
            b_size = max(3, b_size)
            return cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, b_size, c_val
            )

        def sauvola_binarize(
            image: np.ndarray,
            window_size: int = 25,
            k: float = 0.2,
            r: float = 128.0,
        ) -> np.ndarray:
            """Perform Sauvola local thresholding."""
            gray = ensure_grayscale(image).astype(np.float32)
            w = window_size if window_size % 2 == 1 else window_size + 1
            w = max(3, w)
            mean = cv2.blur(gray, (w, w))
            mean_sq = cv2.blur(gray * gray, (w, w))
            variance = np.maximum(mean_sq - (mean * mean), 0.0)
            std = np.sqrt(variance)
            threshold = mean * (1.0 + k * (std / r - 1.0))
            return (gray > threshold).astype(np.uint8) * 255

        def niblack_binarize(
            image: np.ndarray, window_size: int = 25, k: float = 0.2
        ) -> np.ndarray:
            """Perform Niblack local thresholding."""
            gray = ensure_grayscale(image).astype(np.float32)
            w = window_size if window_size % 2 == 1 else window_size + 1
            w = max(3, w)
            mean = cv2.blur(gray, (w, w))
            mean_sq = cv2.blur(gray * gray, (w, w))
            variance = np.maximum(mean_sq - (mean * mean), 0.0)
            std = np.sqrt(variance)
            threshold = mean + (k * std)
            return (gray > threshold).astype(np.uint8) * 255

        def black_hat_text(image: np.ndarray, kernel_size: int = 15) -> np.ndarray:
            """Extract dark text features using Black Hat morphological transform."""
            gray = ensure_grayscale(image)
            k = kernel_size if kernel_size % 2 == 1 else kernel_size + 1
            k = max(3, k)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
            return cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)


class DocumentRestorer:
    """Core pipeline class orchestrating end-to-end historical document restoration.

    Uses a builder/fluent design pattern where each transformation method
    modifies internal state and returns `self` for seamless method chaining.
    Maintains intermediate stage results for debugging, visualization, and inspection.

    Attributes:
        original (Optional[np.ndarray]): Original loaded document image in BGR format.
        current (Optional[np.ndarray]): Current working image buffer across pipeline stages.
        stage_results (Dict[str, np.ndarray]): Dictionary mapping stage names to output images.
        is_loaded (bool): Indicator whether an image has been successfully loaded.
    """

    def __init__(self) -> None:
        """Initialize empty document restoration state."""
        self.original: Optional[np.ndarray] = None
        self.current: Optional[np.ndarray] = None
        self.stage_results: Dict[str, np.ndarray] = {}
        self.is_loaded: bool = False

    def _check_loaded(self) -> None:
        """Validate that an image is currently loaded in the pipeline.

        Raises:
            ValueError: If no image has been loaded via `load_image()`.
        """
        if not self.is_loaded or self.current is None or self.original is None:
            raise ValueError(
                "No image is currently loaded. Please call load_image() before performing pipeline operations."
            )

    def load_image(self, source: Union[str, Path, np.ndarray]) -> "DocumentRestorer":
        """Load an image from a filesystem path or a numpy array.

        Args:
            source (Union[str, Path, np.ndarray]): File path or numpy image array.

        Returns:
            DocumentRestorer: self for chaining.

        Raises:
            FileNotFoundError: If the specified file path does not exist.
            ValueError: If the source cannot be loaded or is invalid/empty.
            TypeError: If the source is neither path-like nor a numpy array.
        """
        img: Optional[np.ndarray] = None

        if isinstance(source, (str, Path)):
            path_obj = Path(source).resolve()
            if not path_obj.exists():
                raise FileNotFoundError(f"Image file does not exist: {path_obj}")
            if not path_obj.is_file():
                raise ValueError(f"Path is not a regular file: {path_obj}")

            # Standard OpenCV read
            img = cv2.imread(str(path_obj), cv2.IMREAD_COLOR)

            # Fallback for Windows Unicode file paths using np.fromfile
            if img is None:
                try:
                    file_bytes = np.fromfile(str(path_obj), dtype=np.uint8)
                    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                except Exception:
                    img = None

            if img is None or img.size == 0:
                raise ValueError(f"Failed to decode image from path: {path_obj}")

        elif isinstance(source, np.ndarray):
            if source.size == 0:
                raise ValueError("Provided image numpy array is empty.")
            img = source.copy()

            # Normalize floating point data to uint8 if necessary
            if np.issubdtype(img.dtype, np.floating):
                max_val = float(img.max()) if img.max() > 0 else 1.0
                scale = 255.0 if max_val <= 1.0 else 1.0
                img = np.clip(img * scale, 0, 255).astype(np.uint8)
            elif img.dtype != np.uint8:
                img = np.clip(img, 0, 255).astype(np.uint8)

            # Ensure self.original is in BGR format
            if img.ndim == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            elif img.ndim == 3:
                channels = img.shape[2]
                if channels == 1:
                    img = cv2.cvtColor(img[:, :, 0], cv2.COLOR_GRAY2BGR)
                elif channels == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                elif channels != 3:
                    raise ValueError(f"Unsupported number of image channels: {channels}")
            else:
                raise ValueError(f"Unsupported image dimensions: {img.ndim}D")
        else:
            raise TypeError(
                f"Unsupported source type: {type(source)}. Must be str, Path, or np.ndarray."
            )

        # Store baseline image states
        self.original = img.copy()
        self.current = img.copy()
        self.stage_results = {"Original": self.current.copy()}
        self.is_loaded = True

        return self

    def crop_borders(self, threshold: int = 10, padding: int = 5) -> "DocumentRestorer":
        """Crop dark scanner border margins and isolate document page content.

        Converts the image temporarily to grayscale, computes row and column
        mean intensities, and finds content boundaries where the mean intensity
        exceeds the dark margin threshold.

        Args:
            threshold (int): Minimum mean intensity for row/column content (default: 10).
            padding (int): Pixel margin added around the detected content box (default: 5).

        Returns:
            DocumentRestorer: self for chaining.

        Raises:
            ValueError: If no image is currently loaded.
        """
        self._check_loaded()
        assert self.current is not None

        gray = ensure_grayscale(self.current)
        h, w = gray.shape[:2]

        # Compute average intensity across rows and columns
        row_means = np.mean(gray, axis=1)
        col_means = np.mean(gray, axis=0)

        valid_rows = np.where(row_means > threshold)[0]
        valid_cols = np.where(col_means > threshold)[0]

        # Handle edge cases: completely dark image or no valid content found
        if valid_rows.size == 0 or valid_cols.size == 0:
            # Retain image unchanged if no region crosses the content threshold
            self.stage_results["Border Removal"] = self.current.copy()
            return self

        ymin, ymax = int(valid_rows[0]), int(valid_rows[-1])
        xmin, xmax = int(valid_cols[0]), int(valid_cols[-1])

        # Apply padding and clamp to image dimensions
        ymin = max(0, ymin - padding)
        ymax = min(h, ymax + padding + 1)
        xmin = max(0, xmin - padding)
        xmax = min(w, xmax + padding + 1)

        # Crop content bounding box if valid dimensions exist
        if ymax > ymin and xmax > xmin:
            self.current = self.current[ymin:ymax, xmin:xmax].copy()

        self.stage_results["Border Removal"] = self.current.copy()
        return self

    def deskew(self) -> "DocumentRestorer":
        """Correct rotational skew of the document.

        Attempts to detect skew angle using the `deskew` library. If unavailable
        or if detection fails, falls back to Hough line transform detection on Canny
        edges. Rotates the image with cubic interpolation and white border fill,
        skipping rotation if the detected angle is negligible (< 0.1 degrees).

        Returns:
            DocumentRestorer: self for chaining.

        Raises:
            ValueError: If no image is currently loaded.
        """
        self._check_loaded()
        assert self.current is not None

        detected_angle: Optional[float] = None

        # 1. Primary method: deskew library
        if HAS_DESKEW:
            try:
                gray = ensure_grayscale(self.current)
                angle_val = determine_skew(gray)
                if angle_val is not None and not np.isnan(angle_val):
                    detected_angle = float(angle_val)
            except Exception:
                detected_angle = None

        # 2. Fallback method: Canny edges + HoughLinesP
        if detected_angle is None:
            gray = ensure_grayscale(self.current)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150, apertureSize=3)

            min_line_len = max(30, gray.shape[1] // 5)
            lines = cv2.HoughLinesP(
                edges,
                rho=1,
                theta=np.pi / 180.0,
                threshold=100,
                minLineLength=min_line_len,
                maxLineGap=20,
            )

            # Relax criteria if strict Hough found no lines
            if lines is None or len(lines) == 0:
                lines = cv2.HoughLinesP(
                    edges,
                    rho=1,
                    theta=np.pi / 180.0,
                    threshold=50,
                    minLineLength=30,
                    maxLineGap=10,
                )

            if lines is not None and len(lines) > 0:
                angles = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    dx = float(x2 - x1)
                    dy = float(y2 - y1)
                    if dx == 0.0:
                        continue
                    theta = float(np.degrees(np.arctan2(dy, dx)))
                    # Constrain to near-horizontal text angle range [-45, 45]
                    if theta < -45.0:
                        theta += 90.0
                    elif theta > 45.0:
                        theta -= 90.0
                    if abs(theta) <= 45.0:
                        angles.append(theta)

                if len(angles) > 0:
                    detected_angle = float(np.median(angles))
                else:
                    detected_angle = 0.0
            else:
                detected_angle = 0.0

        angle = detected_angle if detected_angle is not None else 0.0

        # Rotate if skew angle is significant (>= 0.1 degrees)
        if abs(angle) >= 0.1:
            h, w = self.current.shape[:2]
            center = (w / 2.0, h / 2.0)
            rot_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            border_fill = (255, 255, 255) if self.current.ndim == 3 else 255

            self.current = cv2.warpAffine(
                self.current,
                rot_matrix,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=border_fill,
            )

        self.stage_results["Deskew"] = self.current.copy()
        return self

    def remove_background(self, kernel_size: int = 51) -> "DocumentRestorer":
        """Remove uneven illumination, yellowing, and document background stains.

        Operates on grayscale image representation. Employs a large rectangular
        morphological closing kernel to estimate background illumination, then
        divides the original image by the estimated background and normalizes to [0, 255].

        Args:
            kernel_size (int): Size of rectangular structuring element (default: 51).

        Returns:
            DocumentRestorer: self for chaining.

        Raises:
            ValueError: If no image is currently loaded.
        """
        self._check_loaded()
        assert self.current is not None

        gray = ensure_grayscale(self.current)

        # Ensure kernel dimensions are positive and odd
        k = kernel_size if kernel_size % 2 == 1 else kernel_size + 1
        k = max(3, k)

        # Estimate background illumination using morphological closing
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
        background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

        # Avoid zero division and normalize
        bg_safe = np.maximum(background.astype(np.float32), 1.0)
        normalized = (gray.astype(np.float32) / bg_safe) * 255.0
        self.current = np.clip(normalized, 0, 255).astype(np.uint8)

        self.stage_results["Background Removal"] = self.current.copy()
        return self

    def denoise(
        self,
        method: str = "fastNlMeans",
        strength: int = 10,
        kernel_size: int = 5,
    ) -> "DocumentRestorer":
        """Apply noise reduction filtering to the document image.

        Supported methods:
            - 'gaussian': Standard Gaussian blur filtering.
            - 'median': Median blur filter (preserves sharp edges).
            - 'bilateral': Edge-preserving bilateral filter.
            - 'fastNlMeans': Non-local means denoising (colored or grayscale).

        Args:
            method (str): Filtering algorithm name (default: 'fastNlMeans').
            strength (int): Denoising intensity parameter for bilateral/fastNlMeans (default: 10).
            kernel_size (int): Spatial kernel filter size (default: 5).

        Returns:
            DocumentRestorer: self for chaining.

        Raises:
            ValueError: If no image is loaded or if an unsupported method is requested.
        """
        self._check_loaded()
        assert self.current is not None

        k = kernel_size if kernel_size % 2 == 1 else kernel_size + 1
        k = max(1, k)
        method_key = method.strip().lower()

        if method_key == "gaussian":
            self.current = cv2.GaussianBlur(self.current, (k, k), 0)

        elif method_key == "median":
            # Median blur requires odd kernel size >= 3
            k_median = max(3, k)
            self.current = cv2.medianBlur(self.current, k_median)

        elif method_key == "bilateral":
            sigma_val = float(strength) * 7.5
            self.current = cv2.bilateralFilter(
                self.current,
                d=9,
                sigmaColor=sigma_val,
                sigmaSpace=sigma_val,
            )

        elif method_key == "fastnlmeans":
            h_val = float(strength)
            if self.current.ndim == 2 or (
                self.current.ndim == 3 and self.current.shape[2] == 1
            ):
                gray_in = ensure_grayscale(self.current)
                self.current = cv2.fastNlMeansDenoising(gray_in, h=h_val)
            else:
                self.current = cv2.fastNlMeansDenoisingColored(
                    self.current,
                    h=h_val,
                    hColor=h_val,
                )

        else:
            raise ValueError(
                f"Unsupported denoising method: '{method}'. "
                "Supported methods are: 'gaussian', 'median', 'bilateral', 'fastNlMeans'."
            )

        self.stage_results["Denoising"] = self.current.copy()
        return self

    def enhance_contrast(
        self,
        method: str = "clahe",
        clip_limit: float = 2.0,
        tile_size: int = 8,
    ) -> "DocumentRestorer":
        """Enhance contrast of text and document structure.

        Supported methods:
            - 'clahe': Contrast Limited Adaptive Histogram Equalization.
            - 'histogram_eq': Standard global histogram equalization.
            - 'percentile_stretch': Linear stretch between 1st and 99th intensity percentiles.

        For color images, enhancement is applied in the LAB color space L-channel
        to avoid color distortions.

        Args:
            method (str): Contrast enhancement method (default: 'clahe').
            clip_limit (float): Threshold for contrast limiting in CLAHE (default: 2.0).
            tile_size (int): Grid tile dimensions for CLAHE (default: 8).

        Returns:
            DocumentRestorer: self for chaining.

        Raises:
            ValueError: If no image is loaded or if an unsupported method is specified.
        """
        self._check_loaded()
        assert self.current is not None

        method_key = method.strip().lower()

        if method_key == "clahe":
            t_size = max(1, tile_size)
            clahe = cv2.createCLAHE(
                clipLimit=float(clip_limit),
                tileGridSize=(t_size, t_size),
            )
            if self.current.ndim == 3 and self.current.shape[2] == 3:
                lab = cv2.cvtColor(self.current, cv2.COLOR_BGR2LAB)
                l_channel, a_channel, b_channel = cv2.split(lab)
                l_channel = clahe.apply(l_channel)
                merged = cv2.merge((l_channel, a_channel, b_channel))
                self.current = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
            else:
                gray = ensure_grayscale(self.current)
                self.current = clahe.apply(gray)

        elif method_key == "histogram_eq":
            if self.current.ndim == 3 and self.current.shape[2] == 3:
                lab = cv2.cvtColor(self.current, cv2.COLOR_BGR2LAB)
                l_channel, a_channel, b_channel = cv2.split(lab)
                l_channel = cv2.equalizeHist(l_channel)
                merged = cv2.merge((l_channel, a_channel, b_channel))
                self.current = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
            else:
                gray = ensure_grayscale(self.current)
                self.current = cv2.equalizeHist(gray)

        elif method_key == "percentile_stretch":
            if self.current.ndim == 3 and self.current.shape[2] == 3:
                lab = cv2.cvtColor(self.current, cv2.COLOR_BGR2LAB)
                l_channel, a_channel, b_channel = cv2.split(lab)
                p_low, p_high = np.percentile(l_channel, (1.0, 99.0))
                if p_high > p_low:
                    stretched = (l_channel.astype(np.float32) - p_low) / (p_high - p_low) * 255.0
                    l_channel = np.clip(stretched, 0, 255).astype(np.uint8)
                merged = cv2.merge((l_channel, a_channel, b_channel))
                self.current = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
            else:
                gray = ensure_grayscale(self.current)
                p_low, p_high = np.percentile(gray, (1.0, 99.0))
                if p_high > p_low:
                    stretched = (gray.astype(np.float32) - p_low) / (p_high - p_low) * 255.0
                    self.current = np.clip(stretched, 0, 255).astype(np.uint8)
                else:
                    self.current = gray

        else:
            raise ValueError(
                f"Unsupported contrast enhancement method: '{method}'. "
                "Supported methods are: 'clahe', 'histogram_eq', 'percentile_stretch'."
            )

        self.stage_results["Contrast Enhancement"] = self.current.copy()
        return self

    def inpaint(
        self,
        mask: Optional[np.ndarray] = None,
        radius: int = 5,
        method: str = "telea",
    ) -> "DocumentRestorer":
        """Inpaint damaged regions, stains, holes, or specks in the document.

        Ensures the working image is in color format for inpainting. If no mask is
        provided, auto-detects anomalous regions based on extreme dark (< 30) or
        extreme light (> 245) spot intensities.

        Supported methods:
            - 'telea': Fast Marching Method based inpainting (cv2.INPAINT_TELEA).
            - 'ns': Navier-Stokes fluid dynamics based inpainting (cv2.INPAINT_NS).

        Args:
            mask (Optional[np.ndarray]): Binary damage mask (255 for damaged pixels).
            radius (int): Inpainting neighborhood radius around pixels (default: 5).
            method (str): Inpainting algorithm, 'telea' or 'ns' (default: 'telea').

        Returns:
            DocumentRestorer: self for chaining.

        Raises:
            ValueError: If no image is loaded or if an unsupported method is specified.
        """
        self._check_loaded()
        assert self.current is not None

        # Inpainting requires color image
        color_img = ensure_color(self.current)
        h, w = color_img.shape[:2]

        # Auto-detect mask if not supplied
        if mask is None:
            gray = ensure_grayscale(color_img)
            damage_mask = np.zeros(gray.shape, dtype=np.uint8)
            damage_mask[(gray < 30) | (gray > 245)] = 255
        else:
            damage_mask = ensure_grayscale(mask)
            if damage_mask.shape[:2] != (h, w):
                damage_mask = cv2.resize(
                    damage_mask,
                    (w, h),
                    interpolation=cv2.INTER_NEAREST,
                )
            damage_mask = (damage_mask > 0).astype(np.uint8) * 255

        # Select OpenCV inpaint algorithm flag
        method_key = method.strip().lower()
        if method_key == "telea":
            inpaint_flag = cv2.INPAINT_TELEA
        elif method_key == "ns":
            inpaint_flag = cv2.INPAINT_NS
        else:
            raise ValueError(
                f"Unsupported inpainting method: '{method}'. "
                "Supported methods are: 'telea', 'ns'."
            )

        # Execute inpaint if damaged pixels exist
        if np.any(damage_mask > 0):
            self.current = cv2.inpaint(
                color_img,
                damage_mask,
                inpaintRadius=max(1, radius),
                flags=inpaint_flag,
            )
        else:
            self.current = color_img.copy()

        self.stage_results["Inpainting"] = self.current.copy()
        return self

    def binarize(
        self,
        method: str = "sauvola",
        block_size: int = 25,
        k: float = 0.2,
    ) -> "DocumentRestorer":
        """Convert grayscale document image into high-contrast binary (black & white).

        Converts the image to grayscale first, then dispatches to the specified
        binarization algorithm.

        Supported methods:
            - 'otsu': Global Otsu thresholding.
            - 'adaptive_gaussian': Local adaptive Gaussian weighted thresholding.
            - 'adaptive_mean': Local adaptive arithmetic mean thresholding.
            - 'sauvola': Sauvola local thresholding (optimal for degraded documents).
            - 'niblack': Niblack local thresholding.

        Args:
            method (str): Binarization algorithm name (default: 'sauvola').
            block_size (int): Neighborhood window size (maps to window_size for Sauvola/Niblack) (default: 25).
            k (float): Threshold adjustment factor for Sauvola/Niblack (default: 0.2).

        Returns:
            DocumentRestorer: self for chaining.

        Raises:
            ValueError: If no image is loaded or if an unsupported method is specified.
        """
        self._check_loaded()
        assert self.current is not None

        gray = ensure_grayscale(self.current)
        b_size = block_size if block_size % 2 == 1 else block_size + 1
        b_size = max(3, b_size)
        method_key = method.strip().lower()

        if method_key == "otsu":
            binary_img = otsu_binarize(gray)
        elif method_key == "adaptive_gaussian":
            binary_img = adaptive_gaussian_binarize(gray, block_size=b_size)
        elif method_key == "adaptive_mean":
            binary_img = adaptive_mean_binarize(gray, block_size=b_size)
        elif method_key == "sauvola":
            binary_img = sauvola_binarize(gray, window_size=b_size, k=float(k))
        elif method_key == "niblack":
            binary_img = niblack_binarize(gray, window_size=b_size, k=float(k))
        else:
            raise ValueError(
                f"Unsupported binarization method: '{method}'. "
                "Supported methods are: 'otsu', 'adaptive_gaussian', 'adaptive_mean', 'sauvola', 'niblack'."
            )

        self.current = binary_img
        self.stage_results["Binarization"] = self.current.copy()
        return self

    def postprocess(
        self,
        sharpen: bool = True,
        morpho_clean: bool = True,
        sharpen_strength: float = 1.5,
    ) -> "DocumentRestorer":
        """Apply final post-processing, sharpening, and speckle cleaning.

        Args:
            sharpen (bool): Whether to apply unsharp masking (default: True).
            morpho_clean (bool): Whether to perform opening/closing cleaning (default: True).
            sharpen_strength (float): Strength multiplier for unsharp masking (default: 1.5).

        Returns:
            DocumentRestorer: self for chaining.

        Raises:
            ValueError: If no image is currently loaded.
        """
        self._check_loaded()
        assert self.current is not None

        # 1. Unsharp masking
        if sharpen:
            blurred = cv2.GaussianBlur(self.current, (0, 0), sigmaX=3.0)
            sharpened = cv2.addWeighted(
                self.current,
                1.0 + float(sharpen_strength),
                blurred,
                -float(sharpen_strength),
                0.0,
            )
            self.current = np.clip(sharpened, 0, 255).astype(np.uint8)

        # 2. Morphological speckle cleaning
        if morpho_clean:
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            opened = cv2.morphologyEx(self.current, cv2.MORPH_OPEN, kernel)
            closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
            self.current = closed

        self.stage_results["Post-Processing"] = self.current.copy()
        return self

    def run_full_pipeline(
        self, config: Optional[Dict[str, Any]] = None
    ) -> "DocumentRestorer":
        """Execute the full restoration pipeline in standard sequential order.

        Standard stage order:
            1. crop_borders
            2. deskew
            3. remove_background
            4. denoise
            5. enhance_contrast
            6. inpaint
            7. binarize
            8. postprocess

        Config is a dictionary where keys are stage names and values are either:
            - A dict of keyword parameters for the stage method.
            - None or False to disable/skip the stage.
            - True or {} to run the stage with its default parameters.

        If config is None, all stages are executed with their default settings.

        Args:
            config (Optional[Dict[str, Any]]): Stage configuration dictionary.

        Returns:
            DocumentRestorer: self for chaining.

        Raises:
            ValueError: If no image is currently loaded.
        """
        self._check_loaded()

        stage_order = [
            "crop_borders",
            "deskew",
            "remove_background",
            "denoise",
            "enhance_contrast",
            "inpaint",
            "binarize",
            "postprocess",
        ]

        for stage_name in stage_order:
            stage_fn = getattr(self, stage_name)

            if config is None:
                # Default configuration: run all stages with defaults
                stage_fn()
            else:
                if stage_name in config:
                    stage_cfg = config[stage_name]
                    # Disabled stage when set to None or False
                    if stage_cfg is None or stage_cfg is False:
                        continue
                    if isinstance(stage_cfg, dict):
                        stage_fn(**stage_cfg)
                    elif stage_cfg is True:
                        stage_fn()
                    else:
                        raise ValueError(
                            f"Invalid configuration value for stage '{stage_name}': {stage_cfg}"
                        )
                else:
                    # Unspecified stages default to running
                    stage_fn()

        return self

    def get_result(self) -> np.ndarray:
        """Return a copy of the current processed document image.

        Returns:
            np.ndarray: Processed image buffer.

        Raises:
            ValueError: If no image is currently loaded.
        """
        self._check_loaded()
        assert self.current is not None
        return self.current.copy()

    def get_stage_results(self) -> Dict[str, np.ndarray]:
        """Return a copy of all intermediate and final stage results.

        Returns:
            Dict[str, np.ndarray]: Mapping of stage names to result images.

        Raises:
            ValueError: If no image is currently loaded.
        """
        self._check_loaded()
        return {k: v.copy() for k, v in self.stage_results.items()}

    def get_metrics(self) -> Dict[str, float]:
        """Compute visual quality metrics (PSNR and SSIM) between original and current image.

        Handles dimension and channel discrepancies (e.g. Due to border cropping
        or binarization) by aligning geometries before evaluation.

        Returns:
            Dict[str, float]: Dictionary with keys 'psnr' and 'ssim'.

        Raises:
            ValueError: If no image is currently loaded.
        """
        self._check_loaded()
        assert self.original is not None
        assert self.current is not None

        ref_img = self.original.copy()
        test_img = self.current.copy()

        # Align dimensions if border cropping or transformations modified spatial size
        if test_img.shape[:2] != ref_img.shape[:2]:
            test_img = cv2.resize(
                test_img,
                (ref_img.shape[1], ref_img.shape[0]),
                interpolation=cv2.INTER_LINEAR,
            )

        # Align channel counts to enable accurate metric comparison
        if ref_img.ndim == 3 and test_img.ndim == 2:
            test_img = cv2.cvtColor(test_img, cv2.COLOR_GRAY2BGR)
        elif ref_img.ndim == 2 and test_img.ndim == 3:
            ref_img = cv2.cvtColor(ref_img, cv2.COLOR_GRAY2BGR)

        psnr_score = float(compute_psnr(ref_img, test_img))
        ssim_score = float(compute_ssim(ref_img, test_img))

        return {"psnr": psnr_score, "ssim": ssim_score}
