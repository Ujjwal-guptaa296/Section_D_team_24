"""Interactive Streamlit Web Application for Historical Document Restoration.

This application provides an interactive user interface for restoring degraded
and aged manuscripts using classical Image Processing and Computer Vision techniques.
Features include border removal, deskewing, illumination correction, noise reduction,
contrast enhancement, damage inpainting, local adaptive binarization, and quality evaluation.
"""

import io
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import cv2
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import streamlit as st

# Attempt streamlit-image-comparison import with graceful fallback
try:
    from streamlit_image_comparison import image_comparison
    HAS_IMAGE_COMPARISON = True
except ImportError:
    HAS_IMAGE_COMPARISON = False

# Import restoration pipeline modules and evaluation utilities
from src.restoration_pipeline import DocumentRestorer
from src.binarization import compare_all_methods
from src.utils import (
    compute_psnr,
    compute_ssim,
    create_comparison,
    plot_histograms,
    resize_for_display,
    ensure_grayscale,
)


# ==============================================================================
# 1. Page Configuration
# ==============================================================================
st.set_page_config(
    page_title="Document Restoration",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==============================================================================
# 2. UI-to-Internal Method Name Mappings
# ==============================================================================
DENOISE_METHOD_MAP: Dict[str, str] = {
    "Non-Local Means": "fastNlMeans",
    "Gaussian": "gaussian",
    "Median": "median",
    "Bilateral": "bilateral",
}

CONTRAST_METHOD_MAP: Dict[str, str] = {
    "CLAHE": "clahe",
    "Histogram Equalization": "histogram_eq",
    "Percentile Stretch": "percentile_stretch",
}

INPAINT_METHOD_MAP: Dict[str, str] = {
    "Telea (Fast Marching)": "telea",
    "Navier-Stokes": "ns",
}

BINARIZE_METHOD_MAP: Dict[str, str] = {
    "Sauvola": "sauvola",
    "Otsu": "otsu",
    "Adaptive Gaussian": "adaptive_gaussian",
    "Adaptive Mean": "adaptive_mean",
    "Niblack": "niblack",
}


# ==============================================================================
# 3. Helper Functions for Image Format Conversion
# ==============================================================================
def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
    """Convert PIL Image to OpenCV BGR numpy array.

    Args:
        pil_image: PIL Image object in RGB, RGBA, or L mode.

    Returns:
        np.ndarray: OpenCV image array in BGR (or 2D grayscale) format.
    """
    rgb = np.array(pil_image)
    if rgb.ndim == 2:
        return rgb
    if rgb.ndim == 3:
        if rgb.shape[2] == 4:
            return cv2.cvtColor(rgb, cv2.COLOR_RGBA2BGR)
        elif rgb.shape[2] == 3:
            return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    return rgb


def cv2_to_pil(cv2_image: np.ndarray) -> Image.Image:
    """Convert OpenCV BGR numpy array to PIL Image.

    Args:
        cv2_image: OpenCV image array in BGR or grayscale format.

    Returns:
        Image.Image: PIL Image object in RGB or L mode.
    """
    if cv2_image.ndim == 2:
        return Image.fromarray(cv2_image)
    if cv2_image.ndim == 3:
        if cv2_image.shape[2] == 3:
            return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))
        elif cv2_image.shape[2] == 4:
            return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGRA2RGBA))
    return Image.fromarray(cv2_image)


def bgr_to_rgb(img: np.ndarray) -> np.ndarray:
    """Convert OpenCV BGR image or grayscale image to RGB for Streamlit display.

    Args:
        img: OpenCV image array in BGR, BGRA, or grayscale.

    Returns:
        np.ndarray: Displayable RGB or 2D image array.
    """
    if img is None:
        return img
    if img.ndim == 2:
        return img
    if img.ndim == 3:
        if img.shape[2] == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        elif img.shape[2] == 4:
            return cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
    return img


def get_image_bytes(img: np.ndarray, file_format: str = "PNG") -> bytes:
    """Convert OpenCV BGR/grayscale image into byte buffer for download.

    Args:
        img: OpenCV image array.
        file_format: Desired target file encoding (e.g. 'PNG').

    Returns:
        bytes: Encoded byte stream.
    """
    pil_img = cv2_to_pil(img)
    buffer = io.BytesIO()
    pil_img.save(buffer, format=file_format)
    return buffer.getvalue()


# ==============================================================================
# 4. Pipeline Execution Function
# ==============================================================================
def execute_pipeline(
    image_bgr: np.ndarray, config: Dict[str, Any]
) -> Tuple[np.ndarray, Dict[str, np.ndarray], Dict[str, float]]:
    """Run DocumentRestorer pipeline with given configuration.

    Args:
        image_bgr: Input document image in OpenCV BGR format.
        config: Configuration dictionary for all enabled/disabled stages.

    Returns:
        Tuple containing:
            - Final restored image (np.ndarray)
            - Dictionary of intermediate stage outputs (Dict[str, np.ndarray])
            - Dictionary of evaluation metrics (Dict[str, float])
    """
    restorer = DocumentRestorer()
    restorer.load_image(image_bgr)
    restorer.run_full_pipeline(config=config)
    restored = restorer.get_result()
    stage_results = restorer.get_stage_results()
    metrics = restorer.get_metrics()
    return restored, stage_results, metrics


# ==============================================================================
# 5. Session State Initialization
# ==============================================================================
if "processed" not in st.session_state:
    st.session_state["processed"] = False
if "current_image_key" not in st.session_state:
    st.session_state["current_image_key"] = None
if "original_bgr" not in st.session_state:
    st.session_state["original_bgr"] = None
if "restored_bgr" not in st.session_state:
    st.session_state["restored_bgr"] = None
if "stage_results" not in st.session_state:
    st.session_state["stage_results"] = {}
if "metrics" not in st.session_state:
    st.session_state["metrics"] = {}
if "last_error" not in st.session_state:
    st.session_state["last_error"] = None


# ==============================================================================
# 6. Sidebar Controls
# ==============================================================================
st.sidebar.header("📁 Upload Image")

uploaded_file = st.sidebar.file_uploader(
    "Choose a document image",
    type=["jpg", "jpeg", "png", "tiff", "bmp"],
    help="Upload a scanned manuscript or degraded historical document image.",
)

# Detect sample images directory if present
samples_dir = Path("samples")
sample_files = []
if samples_dir.exists() and samples_dir.is_dir():
    sample_files = sorted(
        [
            f
            for f in samples_dir.iterdir()
            if f.is_file()
            and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"]
        ]
    )

sample_choice = "None"
if len(sample_files) > 0:
    st.sidebar.markdown("**Or use a sample image:**")
    sample_options = ["None"] + [f.name for f in sample_files]
    sample_choice = st.sidebar.selectbox(
        "Select a sample document",
        options=sample_options,
        index=0,
        label_visibility="collapsed",
    )

# Determine the active image source and load input image
active_image_bgr: Optional[np.ndarray] = None
image_identifier: Optional[str] = None

if uploaded_file is not None:
    try:
        pil_img = Image.open(uploaded_file)
        active_image_bgr = pil_to_cv2(pil_img)
        image_identifier = f"upload_{uploaded_file.name}_{uploaded_file.size}"
    except Exception as e:
        st.sidebar.error(f"Error loading uploaded image: {e}")
elif sample_choice != "None":
    try:
        sample_path = samples_dir / sample_choice
        active_image_bgr = cv2.imread(str(sample_path), cv2.IMREAD_COLOR)
        if active_image_bgr is not None:
            image_identifier = f"sample_{sample_choice}"
    except Exception as e:
        st.sidebar.error(f"Error loading sample image: {e}")

# If the user changed the active image, invalidate previously processed results
if image_identifier != st.session_state["current_image_key"]:
    st.session_state["current_image_key"] = image_identifier
    st.session_state["original_bgr"] = active_image_bgr
    st.session_state["processed"] = False
    st.session_state["restored_bgr"] = None
    st.session_state["stage_results"] = {}
    st.session_state["metrics"] = {}
    st.session_state["last_error"] = None


# ------------------------------------------------------------------------------
# Sidebar: Pipeline Stage Configurations
# ------------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("⚙️ Pipeline Stages")

# a. Border Removal expander
with st.sidebar.expander("✂️ Border Removal", expanded=True):
    border_enable = st.checkbox("Enable Border Removal", value=True, key="cfg_border_en")
    border_threshold = st.slider(
        "Threshold",
        min_value=1,
        max_value=50,
        value=10,
        step=1,
        help="Mean row/col intensity threshold to isolate document content.",
        key="cfg_border_thresh",
    )

# b. Deskewing expander
with st.sidebar.expander("📐 Deskewing", expanded=True):
    deskew_enable = st.checkbox("Enable Deskewing", value=True, key="cfg_deskew_en")
    st.caption("Detects rotational document tilt using Hough lines / deskew algorithm.")

# c. Background Removal expander
with st.sidebar.expander("💡 Background Removal", expanded=True):
    bg_enable = st.checkbox("Enable Background Removal", value=True, key="cfg_bg_en")
    bg_kernel = st.slider(
        "Kernel Size",
        min_value=11,
        max_value=101,
        value=51,
        step=2,
        help="Morphological closing kernel size for background illumination estimation.",
        key="cfg_bg_kernel",
    )

# d. Denoising expander
with st.sidebar.expander("🔇 Denoising", expanded=True):
    denoise_enable = st.checkbox("Enable Denoising", value=True, key="cfg_denoise_en")
    denoise_method_ui = st.selectbox(
        "Method",
        options=["Non-Local Means", "Gaussian", "Median", "Bilateral"],
        index=0,
        key="cfg_denoise_method",
    )
    denoise_strength = st.slider(
        "Strength",
        min_value=1,
        max_value=30,
        value=10,
        step=1,
        help="Filter strength parameter (for Bilateral / Non-Local Means).",
        key="cfg_denoise_strength",
    )
    denoise_kernel = st.slider(
        "Kernel Size",
        min_value=3,
        max_value=15,
        value=5,
        step=2,
        help="Spatial kernel window size for smoothing filters.",
        key="cfg_denoise_kernel",
    )

# e. Contrast Enhancement expander
with st.sidebar.expander("📈 Contrast Enhancement", expanded=True):
    contrast_enable = st.checkbox("Enable Contrast Enhancement", value=True, key="cfg_contrast_en")
    contrast_method_ui = st.selectbox(
        "Method",
        options=["CLAHE", "Histogram Equalization", "Percentile Stretch"],
        index=0,
        key="cfg_contrast_method",
    )
    clip_limit = st.slider(
        "Clip Limit (CLAHE)",
        min_value=1.0,
        max_value=10.0,
        value=2.0,
        step=0.5,
        help="Threshold for contrast limiting in adaptive histogram equalization.",
        key="cfg_contrast_clip",
    )
    tile_size = st.slider(
        "Tile Size (CLAHE)",
        min_value=2,
        max_value=16,
        value=8,
        step=1,
        help="Grid tile dimension for local histogram equalization.",
        key="cfg_contrast_tile",
    )

# f. Inpainting expander
with st.sidebar.expander("🩹 Inpainting", expanded=False):
    inpaint_enable = st.checkbox("Enable Inpainting", value=False, key="cfg_inpaint_en")
    inpaint_method_ui = st.selectbox(
        "Method",
        options=["Telea (Fast Marching)", "Navier-Stokes"],
        index=0,
        key="cfg_inpaint_method",
    )
    inpaint_radius = st.slider(
        "Radius",
        min_value=1,
        max_value=20,
        value=5,
        step=1,
        help="Inpainting neighborhood radius surrounding damaged pixels.",
        key="cfg_inpaint_radius",
    )

# g. Binarization expander
with st.sidebar.expander("🔲 Binarization", expanded=False):
    binarize_enable = st.checkbox(
        "Enable Binarization",
        value=False,
        key="cfg_binarize_en",
        help="Disable to keep restored grayscale/color output; enable for black & white thresholding.",
    )
    binarize_method_ui = st.selectbox(
        "Method",
        options=["Sauvola", "Otsu", "Adaptive Gaussian", "Adaptive Mean", "Niblack"],
        index=0,
        key="cfg_binarize_method",
    )
    binarize_block_size = st.slider(
        "Block / Window Size",
        min_value=3,
        max_value=51,
        value=25,
        step=2,
        help="Local neighborhood window size for adaptive thresholding.",
        key="cfg_binarize_block",
    )
    binarize_k = st.slider(
        "k Parameter",
        min_value=-0.5,
        max_value=0.5,
        value=0.2,
        step=0.05,
        help="Tuning constant for Sauvola and Niblack algorithms.",
        key="cfg_binarize_k",
    )

# h. Post-Processing expander
with st.sidebar.expander("✨ Post-Processing", expanded=True):
    post_enable = st.checkbox("Enable Post-Processing", value=True, key="cfg_post_en")
    post_sharpen = st.checkbox("Apply Sharpening (Unsharp Masking)", value=True, key="cfg_post_sharp")
    post_clean = st.checkbox("Morphological Cleanup (Speckle Removal)", value=True, key="cfg_post_clean")

st.sidebar.markdown("---")

# Process Button
process_btn = st.sidebar.button("🔄 Restore Document", type="primary", use_container_width=True)

# Build pipeline configuration dictionary
pipeline_config: Dict[str, Any] = {
    "crop_borders": {"threshold": int(border_threshold)} if border_enable else False,
    "deskew": {} if deskew_enable else False,
    "remove_background": {"kernel_size": int(bg_kernel)} if bg_enable else False,
    "denoise": {
        "method": DENOISE_METHOD_MAP[denoise_method_ui],
        "strength": int(denoise_strength),
        "kernel_size": int(denoise_kernel),
    }
    if denoise_enable
    else False,
    "enhance_contrast": {
        "method": CONTRAST_METHOD_MAP[contrast_method_ui],
        "clip_limit": float(clip_limit),
        "tile_size": int(tile_size),
    }
    if contrast_enable
    else False,
    "inpaint": {
        "method": INPAINT_METHOD_MAP[inpaint_method_ui],
        "radius": int(inpaint_radius),
    }
    if inpaint_enable
    else False,
    "binarize": {
        "method": BINARIZE_METHOD_MAP[binarize_method_ui],
        "block_size": int(binarize_block_size),
        "k": float(binarize_k),
    }
    if binarize_enable
    else False,
    "postprocess": {
        "sharpen": bool(post_sharpen),
        "morpho_clean": bool(post_clean),
    }
    if post_enable
    else False,
}


# Handle process action
if process_btn:
    if active_image_bgr is None:
        st.sidebar.warning("⚠️ Please upload an image or choose a sample image first.")
    else:
        with st.spinner("Restoring document through CV pipeline..."):
            try:
                restored, stages, metrics = execute_pipeline(active_image_bgr, pipeline_config)
                st.session_state["original_bgr"] = active_image_bgr
                st.session_state["restored_bgr"] = restored
                st.session_state["stage_results"] = stages
                st.session_state["metrics"] = metrics
                st.session_state["processed"] = True
                st.session_state["last_error"] = None
                st.sidebar.success("✅ Restoration complete!")
            except Exception as e:
                st.session_state["last_error"] = str(e)
                st.sidebar.error(f"Restoration failed: {e}")


# ==============================================================================
# 7. Main Application Header
# ==============================================================================
st.title("📜 Old Documents & Manuscripts Restoration")
st.markdown(
    "##### Restore degraded historical documents using classical Image Processing & Computer Vision techniques"
)
st.markdown("---")

if st.session_state.get("last_error"):
    st.error(f"⚠️ **Pipeline Error:** {st.session_state['last_error']}")


# ==============================================================================
# 8. Main Tabs Navigation
# ==============================================================================
tab_overview, tab_stages, tab_binarize, tab_metrics = st.tabs(
    [
        "📋 Overview",
        "🔍 Stage-by-Stage Results",
        "🔲 Binarization Comparison",
        "📊 Quality Metrics",
    ]
)


# ------------------------------------------------------------------------------
# Tab 1: Overview
# ------------------------------------------------------------------------------
with tab_overview:
    # State A: No image selected or uploaded
    if st.session_state["original_bgr"] is None:
        st.info("👋 **Welcome!** Please upload a degraded document image or select a sample image from the left sidebar to begin.")

        col_feat1, col_feat2 = st.columns(2)
        with col_feat1:
            st.markdown(
                """
                ### 🛠️ Pipeline Capabilities
                - **✂️ Border Removal:** Automatically detects and crops scanning margins and dark book edges.
                - **📐 Skew Correction:** Straightens rotated scans using Hough line transform analysis.
                - **💡 Illumination Normalization:** Removes uneven yellowing, aging gradients, and foxing stains using morphological filtering.
                - **🔇 Selective Denoising:** Smooths paper grain noise using Non-Local Means, Bilateral, or Median filtering without blurring text strokes.
                """
            )
        with col_feat2:
            st.markdown(
                """
                ### 🔬 Advanced Restorations
                - **📈 Adaptive Contrast:** CLAHE local histogram equalization balances ink visibility across varying page zones.
                - **🩹 Defect Inpainting:** Fast Marching and Navier-Stokes algorithms fill tears and holes.
                - **🔲 Local Adaptive Binarization:** State-of-the-art Sauvola and Niblack thresholding isolate faded handwriting.
                - **📊 Objective Evaluation:** Real-time PSNR and SSIM visual quality metrics.
                """
            )

        st.markdown(
            """
            ---
            #### 🚀 Quick Start Guide:
            1. Use the **Upload Image** section on the left sidebar to pick your document scan.
            2. Configure pipeline parameters in the expandable sidebar sections.
            3. Click the **🔄 Restore Document** button to execute the full restoration workflow.
            4. Inspect intermediate outputs, compare binarization algorithms, and download the restored output.
            """
        )

    # State B: Image loaded but not yet processed
    elif not st.session_state["processed"]:
        orig = st.session_state["original_bgr"]
        h, w = orig.shape[:2]
        ch = orig.shape[2] if orig.ndim == 3 else 1

        st.success(f"📄 **Document Loaded:** {w} × {h} pixels ({ch} color channels).")
        st.markdown(
            "Configure your desired pipeline stages in the left sidebar and click **🔄 Restore Document** to begin restoration."
        )

        st.image(
            bgr_to_rgb(orig),
            caption=f"Original Document Scan ({w} × {h})",
            use_container_width=True,
        )

    # State C: Document restored and ready for inspection
    else:
        orig = st.session_state["original_bgr"]
        restored = st.session_state["restored_bgr"]
        metrics = st.session_state["metrics"]

        # Metric summary banner
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            psnr_text = f"{metrics.get('psnr', 0.0):.2f} dB" if metrics.get("psnr") != float("inf") else "∞ (Identical)"
            st.metric("PSNR Fidelity", psnr_text, help="Peak Signal-to-Noise Ratio (higher indicates structural fidelity)")
        with m_col2:
            st.metric("SSIM Structure", f"{metrics.get('ssim', 0.0):.4f}", help="Structural Similarity Index (-1.0 to 1.0)")
        with m_col3:
            h_r, w_r = restored.shape[:2]
            st.metric("Restored Resolution", f"{w_r} × {h_r} px")

        st.markdown("---")

        # Interactive slider or side-by-side comparison
        slider_displayed = False
        if HAS_IMAGE_COMPARISON:
            try:
                # Harmonize spatial dimensions for slider view if border cropping occurred
                h_o, w_o = orig.shape[:2]
                h_res, w_res = restored.shape[:2]

                if (h_o, w_o) != (h_res, w_res):
                    restored_slider = cv2.resize(restored, (w_o, h_o), interpolation=cv2.INTER_LINEAR)
                else:
                    restored_slider = restored

                st.subheader("↔️ Interactive Before / After Comparison")
                st.caption("Drag the central divider horizontally to inspect restoration details.")
                image_comparison(
                    img1=cv2_to_pil(orig),
                    img2=cv2_to_pil(restored_slider),
                    label1="Original",
                    label2="Restored",
                    starting_position=50,
                    show_labels=True,
                    make_responsive=True,
                    in_memory=True,
                )
                slider_displayed = True
            except Exception as e:
                slider_displayed = False

        if not slider_displayed:
            st.subheader("🖼️ Side-by-Side Comparison")
            col_left, col_right = st.columns(2)
            with col_left:
                st.markdown("**Original Document**")
                st.image(bgr_to_rgb(orig), use_container_width=True)
            with col_right:
                st.markdown("**Restored Document**")
                st.image(bgr_to_rgb(restored), use_container_width=True)

        st.markdown("---")

        # Download Restored Image
        png_bytes = get_image_bytes(restored, file_format="PNG")
        st.download_button(
            label="📥 Download Restored Document (PNG)",
            data=png_bytes,
            file_name="restored_document.png",
            mime="image/png",
            type="primary",
            use_container_width=True,
        )


# ------------------------------------------------------------------------------
# Tab 2: Stage-by-Stage Results
# ------------------------------------------------------------------------------
with tab_stages:
    if not st.session_state["processed"]:
        st.info("ℹ️ Please run the restoration pipeline on a document to visualize intermediate stage results.")
    else:
        stage_dict = st.session_state["stage_results"]
        st.markdown("### 🔬 Intermediate Pipeline Outputs")
        st.markdown("Review the transformed document state at every active restoration step:")

        stage_keys = list(stage_dict.keys())
        # Display stages in a responsive 3-column layout
        num_cols = 3
        for row_start in range(0, len(stage_keys), num_cols):
            cols = st.columns(num_cols)
            for offset in range(num_cols):
                idx = row_start + offset
                with cols[offset]:
                    if idx < len(stage_keys):
                        stage_name = stage_keys[idx]
                        stage_img = stage_dict[stage_name]
                        h_s, w_s = stage_img.shape[:2]
                        channels_desc = "Grayscale" if stage_img.ndim == 2 else f"Color ({stage_img.shape[2]} ch)"

                        st.markdown(f"**Step {idx + 1}: {stage_name}**")
                        st.image(
                            bgr_to_rgb(stage_img),
                            caption=f"{stage_name} ({w_s} × {h_s}, {channels_desc})",
                            use_container_width=True,
                        )

        # Technical descriptions of each stage
        with st.expander("📖 Algorithmic Stage Details & Explanations"):
            st.markdown(
                """
                - **Border Removal:** Uses intensity thresholding along image margins to eliminate black scanner borders and non-document edges.
                - **Deskewing:** Detects dominant text line orientations via Hough transform and applies affine rotation with cubic interpolation.
                - **Background Removal:** Morphological closing with a large structuring element models uneven illumination and page stains, dividing the raw image by this background estimate to produce uniform brightness.
                - **Denoising:** Employs spatial filtering (Non-Local Means, Bilateral, Gaussian, or Median) to suppress paper grain noise while preserving sharp character contours.
                - **Contrast Enhancement:** Contrast Limited Adaptive Histogram Equalization (CLAHE) amplifies local stroke contrast without blowing out paper highlights.
                - **Inpainting:** Auto-detects holes or ink stains and reconstructs missing regions using Fast Marching (Telea) or Navier-Stokes PDE inpainting.
                - **Binarization:** Converts grayscale intensities to crisp binary text using local thresholding.
                - **Post-Processing:** Applies unsharp masking for stroke crispness followed by morphological opening/closing to eliminate stray salt-and-pepper artifacts.
                """
            )


# ------------------------------------------------------------------------------
# Tab 3: Binarization Comparison
# ------------------------------------------------------------------------------
with tab_binarize:
    if st.session_state["original_bgr"] is None:
        st.info("ℹ️ Please upload or select a document image to compare binarization algorithms.")
    else:
        st.markdown("### 🔲 Document Binarization Benchmark")
        st.markdown(
            "Compare classical global and local adaptive binarization algorithms side-by-side to determine the optimal thresholding method for OCR and readability."
        )

        # Allow user to select whether to test binarization on original or pre-processed image
        options = ["Original Document Image"]
        if st.session_state["processed"]:
            options.insert(0, "Current Restored / Pre-processed Image")

        chosen_input = st.radio(
            "Select input image for binarization evaluation:",
            options=options,
            horizontal=True,
            key="binarize_source_choice",
        )

        target_source = (
            st.session_state["restored_bgr"]
            if (st.session_state["processed"] and chosen_input == options[0])
            else st.session_state["original_bgr"]
        )

        with st.spinner("Executing binarization algorithms..."):
            gray_input = ensure_grayscale(target_source)
            bin_results = compare_all_methods(gray_input)

        # Method descriptions for user guidance
        method_descriptions: Dict[str, str] = {
            "Otsu": "Global thresholding maximizing inter-class variance. Optimal for documents with uniform lighting.",
            "Adaptive Gaussian": "Local thresholding weighted by a Gaussian window. Effective for continuous gradient shading.",
            "Adaptive Mean": "Local thresholding using arithmetic neighborhood mean. Fast, sensitive local baseline.",
            "Sauvola": "Local variance thresholding: T = m * (1 + k * (s/R - 1)). Standard benchmark for degraded historical manuscripts.",
            "Niblack": "Local thresholding: T = m + k * s. High stroke sensitivity; may introduce background noise in uniform zones.",
        }

        # Render in a clean multi-column grid
        bin_keys = list(bin_results.keys())
        col_grid = st.columns(3)

        for i, method_name in enumerate(bin_keys):
            target_col = col_grid[i % 3]
            with target_col:
                st.markdown(f"#### {method_name}")
                st.image(
                    bin_results[method_name],
                    caption=f"{method_name} Binary Output",
                    use_container_width=True,
                )
                st.caption(method_descriptions.get(method_name, ""))


# ------------------------------------------------------------------------------
# Tab 4: Quality Metrics
# ------------------------------------------------------------------------------
with tab_metrics:
    if not st.session_state["processed"]:
        st.info("ℹ️ Please run the restoration pipeline on a document to compute quantitative quality metrics.")
    else:
        orig = st.session_state["original_bgr"]
        restored = st.session_state["restored_bgr"]
        metrics = st.session_state["metrics"]

        st.markdown("### 📊 Objective Quality Evaluation")

        # Metric KPI cards
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            psnr_val = metrics.get("psnr", 0.0)
            psnr_str = f"{psnr_val:.2f} dB" if psnr_val != float("inf") else "∞ (Identical)"
            st.metric(
                label="Peak Signal-to-Noise Ratio (PSNR)",
                value=psnr_str,
                help="Logarithmic ratio between peak signal energy and mean-squared reconstruction error.",
            )
        with col_m2:
            ssim_val = metrics.get("ssim", 0.0)
            st.metric(
                label="Structural Similarity Index (SSIM)",
                value=f"{ssim_val:.4f}",
                help="Perceptual similarity index assessing luminance, contrast, and structural consistency (-1.0 to 1.0).",
            )
        with col_m3:
            quality_grade = (
                "High Fidelity"
                if ssim_val >= 0.80
                else ("Moderate Similarity" if ssim_val >= 0.60 else "Heavy Modification")
            )
            st.metric(label="Structural Match Grade", value=quality_grade)

        st.markdown("---")

        # Pixel Intensity Distribution (Histogram Comparison)
        st.markdown("#### 📈 Pixel Intensity Distribution (Before vs. After)")
        st.caption(
            "Overlaid intensity histograms reveal how background normalization and contrast enhancement separate ink from paper."
        )

        fig = plot_histograms(orig, restored)
        st.pyplot(fig)
        plt.close(fig)

        st.markdown("---")

        # Metric interpretation guide
        with st.expander("📚 Understanding Document Restoration Metrics", expanded=True):
            st.markdown(
                """
                - **Why can PSNR decrease after cleaning?**
                  In standard image compression, higher PSNR is strictly better. In **document restoration**, however, the original image contains heavy defects (yellowing, ink bleed-through, stains, paper shadows). Normalizing the background and removing dark stains intentionally alters pixel values across wide areas, which increases Mean Squared Error (MSE) and lowers raw PSNR while dramatically improving human readability and OCR accuracy.

                - **How to evaluate SSIM:**
                  SSIM measures structural preservation. An SSIM score between **0.65 and 0.95** typically reflects an ideal balance: text glyphs and letter contours are preserved, while noise artifacts, blur, and uneven lighting are removed.

                - **Interpreting the Histogram:**
                  - **Original (Blue):** Degraded documents typically present a broad, muddy distribution centered between intensities 80–180 due to aged yellow paper and faded ink.
                  - **Restored (Red):** A well-restored document exhibits a distinct bimodal distribution: a sharp high-intensity peak near **240–255** (clean white paper) and a well-defined low-intensity peak near **0–50** (crisp dark text).
                """
            )
