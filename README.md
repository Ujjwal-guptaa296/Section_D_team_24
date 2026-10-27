# 📜 Old Documents & Manuscripts Restoration

A comprehensive document restoration pipeline using classical **Image Processing & Computer Vision** techniques in Python. This project restores degraded, old, or damaged document/manuscript images through a multi-stage processing pipeline, with an interactive **Streamlit web UI** for easy demonstration.

## 🎯 Objectives

- Restore readability of old, degraded document images
- Remove noise, stains, bleed-through, and background artifacts
- Correct geometric distortions (skew, rotation)
- Enhance text contrast and sharpness
- Repair damaged/missing regions using inpainting
- Provide before/after comparison with quality metrics (PSNR, SSIM)

## 🏗️ Pipeline Architecture

The restoration pipeline consists of **8 sequential stages**, each independently toggleable:

```
Input Image
    │
    ├── 1. Border Removal & Page Crop
    ├── 2. Deskewing / Rotation Correction
    ├── 3. Background & Stain Removal (Morphological Division)
    ├── 4. Denoising (Gaussian / Median / Bilateral / Non-Local Means)
    ├── 5. Contrast Enhancement (CLAHE / Histogram EQ / Percentile Stretch)
    ├── 6. Inpainting (Telea / Navier-Stokes)
    ├── 7. Binarization (Otsu / Adaptive / Sauvola / Niblack)
    ├── 8. Post-Processing (Sharpening + Morphological Cleanup)
    │
    ▼
Output Restored Image + Quality Metrics (PSNR, SSIM)
```

## 🛠️ Technologies Used

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Core CV Library | OpenCV (cv2) |
| Image Processing | scikit-image, Pillow |
| Numerical | NumPy, SciPy |
| Deskewing | deskew library |
| Quality Metrics | PSNR, SSIM (skimage.metrics) |
| Web UI | Streamlit |
| Visualization | Matplotlib |

## 📂 Project Structure

```
ip_cv_project/
├── app.py                          # Streamlit web UI
├── requirements.txt                # Python dependencies
├── README.md                       # Project documentation
├── src/
│   ├── __init__.py
│   ├── restoration_pipeline.py     # Main pipeline class (DocumentRestorer)
│   ├── binarization.py             # Binarization methods (Otsu, Sauvola, etc.)
│   ├── utils.py                    # Helper utilities & metrics
│   └── download_samples.py         # Download sample images
└── samples/                        # Sample degraded documents
```

## 🚀 Installation & Setup

### 1. Clone / Navigate to the project directory

```bash
cd ip_cv_project
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Download sample images

```bash
python src/download_samples.py
```

### 5. Launch the web application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`.

## 💻 Usage

### Web UI (Recommended)

1. **Upload** a degraded document image (or select a sample)
2. **Configure** pipeline stages in the sidebar:
   - Toggle each stage ON/OFF
   - Adjust parameters (kernel sizes, thresholds, etc.)
3. Click **🔄 Restore Document**
4. **Explore** results across four tabs:
   - **Overview**: Before/After comparison with download
   - **Stage-by-Stage**: Intermediate results for each processing stage
   - **Binarization Comparison**: Side-by-side comparison of all methods
   - **Quality Metrics**: PSNR, SSIM scores and histogram analysis

### Programmatic Usage

```python
from src.restoration_pipeline import DocumentRestorer

# Create restorer and load image
restorer = DocumentRestorer()
restorer.load_image("samples/old_manuscript_01.jpg")

# Run full pipeline with default settings
restorer.run_full_pipeline()

# Or run individual stages with custom parameters
restorer.load_image("samples/degraded_text_02.jpg")
restorer.crop_borders(threshold=10)
restorer.deskew()
restorer.remove_background(kernel_size=51)
restorer.denoise(method='fastNlMeans', strength=10)
restorer.enhance_contrast(method='clahe', clip_limit=2.0)
restorer.binarize(method='sauvola', block_size=25, k=0.2)
restorer.postprocess(sharpen=True, morpho_clean=True)

# Get result
result = restorer.get_result()
metrics = restorer.get_metrics()
print(f"PSNR: {metrics['psnr']:.2f} dB, SSIM: {metrics['ssim']:.4f}")

# Save restored image
import cv2
cv2.imwrite("restored_output.png", result)
```

## 🔬 Key Techniques

### Binarization Methods
- **Otsu's Method**: Global threshold, maximizes inter-class variance
- **Adaptive Gaussian/Mean**: Local thresholding for uneven illumination
- **Sauvola's Method**: De-facto standard for degraded documents, O(1) implementation using box filters
- **Niblack's Method**: Local mean + standard deviation based thresholding

### Background Removal
- **Morphological Background Division**: Large closing kernel estimates background illumination; dividing by it normalizes to uniform white, cancelling yellowing and stains

### Denoising
- **Non-Local Means**: Highest quality classical filter, searches similar patches
- **Bilateral Filter**: Edge-preserving smoothing
- **Median Filter**: Effective for salt-and-pepper noise
- **Gaussian Filter**: Standard smoothing

### Inpainting
- **Telea (Fast Marching)**: Propagates colors inward from boundaries
- **Navier-Stokes**: Preserves isophotes across missing regions

## 📊 Quality Metrics

- **PSNR** (Peak Signal-to-Noise Ratio): Measures pixel-level reconstruction fidelity
- **SSIM** (Structural Similarity Index): Measures structural preservation and perceptual quality

## 👥 Team Members

- [Add your team members here]

## 📝 Subject

**Image Processing & Computer Vision** — TA Assignment (Sections C & D)

**Topic**: Old Documents and Manuscripts Restoration

## 📄 License

This project is created for academic purposes as part of the Image Processing & Computer Vision course assignment.
