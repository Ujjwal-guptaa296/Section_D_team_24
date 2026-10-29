# 🛠️ Implementation Details — Document Restoration Pipeline

**Course:** Image Processing & Computer Vision (CS-XXXX)  
**Submission:** TA Group Assignment  
**Repository Name:** `Section_D_Team_24`  
**Section:** D | **Team Number:** 24  

---

## 📌 Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Stage-by-Stage Implementation Details](#2-stage-by-stage-implementation-details)
   - [Stage 1: Document Boundary Detection & Margin Cropping](#stage-1-document-boundary-detection--margin-cropping)
   - [Stage 2: Geometric Rectification & Deskewing](#stage-2-geometric-rectification--deskewing)
   - [Stage 3: Illumination Normalization via Morphological Background Division](#stage-3-illumination-normalization-via-morphological-background-division)
   - [Stage 4: Edge-Preserving Spatial Denoising](#stage-4-edge-preserving-spatial-denoising)
   - [Stage 5: Local Contrast Enhancement (CLAHE)](#stage-5-local-contrast-enhancement-clahe)
   - [Stage 6: Structural Defect Repair via Digital Inpainting](#stage-6-structural-defect-repair-via-digital-inpainting)
   - [Stage 7: High-Speed $O(1)$ Sauvola Local Adaptive Binarization](#stage-7-high-speed-o1-sauvola-local-adaptive-binarization)
   - [Stage 8: Morphological Post-Processing & Text Sharpening](#stage-8-morphological-post-processing--text-sharpening)
3. [Algorithmic Complexity & Optimization Analysis](#3-algorithmic-complexity--optimization-analysis)
4. [File & Module Mapping](#4-file--module-mapping)
5. [Evaluation Metrics Formulations](#5-evaluation-metrics-formulations)
6. [Interactive Web UI Architecture](#6-interactive-web-ui-architecture)

---

## 1. Architecture Overview

The system is implemented as an **8-stage sequential pipeline** using classical Digital Image Processing and Computer Vision techniques. It uses a **Fluent Builder Pattern** via the master class `DocumentRestorer`, allowing stages to be chained, individually configured, or selectively bypassed.

```
+---------------------------------------------------------------------------------------+
|                              DOCUMENT RESTORATION PIPELINE                            |
+---------------------------------------------------------------------------------------+
  Raw Degraded Scan
       │
       ▼
  [Stage 1: Boundary Cropping]   ──> Profile Mean Intensity Thresholding
       │
       ▼
  [Stage 2: Geometric Deskew]     ──> Radon Projection Variance / Hough Transform
       │
       ▼
  [Stage 3: Background Removal]  ──> Morphological Illumination Division (Flat-Field)
       │
       ▼
  [Stage 4: Spatial Denoising]   ──> Fast Non-Local Means / Bilateral Filtering
       │
       ▼
  [Stage 5: Contrast Boosting]   ──> CLAHE in CIE L*a*b* Perceptual Color Space
       │
       ▼
  [Stage 6: Defect Inpainting]   ──> Fast Marching (Telea) / Navier-Stokes PDEs
       │
       ▼
  [Stage 7: Local Binarization]  ──> O(1) Box-Filter Sauvola Adaptive Thresholding
       │
       ▼
  [Stage 8: Post-Processing]     ──> Unsharp Masking + Morphological 2x2 Cleaning
       │
       ▼
  Restored Document Output + Diagnostic Metrics (PSNR, SSIM, Histograms)
+---------------------------------------------------------------------------------------+
```

---

## 2. Stage-by-Stage Implementation Details

### Stage 1: Document Boundary Detection & Margin Cropping
* **Source File:** `src/restoration_pipeline.py` (`crop_borders()`), `modules/preprocessing/preprocessing.py`
* **Objective:** Remove black scanner bed borders and extraneous margins that distort histogram statistics.
* **Mathematical Formulation:**
  For an input image $I(x, y)$ converted to grayscale $I_g \in [0, 255]$ with dimensions $H \times W$:
  $$\mu_{\text{row}}(y) = \frac{1}{W} \sum_{x=0}^{W-1} I_g(x, y), \qquad \mu_{\text{col}}(x) = \frac{1}{H} \sum_{y=0}^{H-1} I_g(x, y)$$
* **Algorithm:**
  1. Compute row-wise mean $\mu_{\text{row}}$ and column-wise mean $\mu_{\text{col}}$.
  2. Locate first and last indices where profile means exceed margin threshold $T_{\text{margin}} = 10$:
     $$y_{\min} = \min \{ y \mid \mu_{\text{row}}(y) > T_{\text{margin}} \}, \quad y_{\max} = \max \{ y \mid \mu_{\text{row}}(y) > T_{\text{margin}} \}$$
     $$x_{\min} = \min \{ x \mid \mu_{\text{col}}(x) > T_{\text{margin}} \}, \quad x_{\max} = \max \{ x \mid \mu_{\text{col}}(x) > T_{\text{margin}} \}$$
  3. Apply safety margin buffer $p = 5\text{ px}$ to prevent clipping peripheral characters:
     $$y_1 = \max(0, y_{\min}-p), \quad y_2 = \min(H, y_{\max}+p)$$
     $$x_1 = \max(0, x_{\min}-p), \quad x_2 = \min(W, x_{\max}+p)$$
  4. Crop: $I_{\text{crop}} = I[y_1:y_2, x_1:x_2]$.

---

### Stage 2: Geometric Rectification & Deskewing
* **Source File:** `src/restoration_pipeline.py` (`deskew()`), `modules/preprocessing/preprocessing.py`
* **Objective:** Detect and correct document rotational tilt angle $\theta$.
* **Mathematical Formulation:**
  For discrete candidate angles $\theta \in [-45^\circ, +45^\circ]$, compute horizontal projection profile:
  $$P_\theta(y) = \sum_x I_{\text{rotated},\theta}(x, y)$$
  When horizontal text lines are aligned with the image axes, alternating dark text lines and bright interline gaps produce maximal profile variance:
  $$\theta^* = \arg\max_\theta \text{Var}(P_\theta) = \arg\max_\theta \left[ \frac{1}{H_\theta} \sum_y (P_\theta(y) - \bar{P}_\theta)^2 \right]$$
* **Algorithm & Fallback:**
  1. Primary estimator: Projection profile variance optimization (`deskew` package).
  2. Fallback estimator: Probabilistic Hough Line Transform (`cv2.HoughLinesP`). Detects line segments, computes angle $\theta = \arctan(\Delta y / \Delta x)$, and selects median angle.
  3. Image rotation: 2D affine transformation matrix centered at $(W/2, H/2)$ using `cv2.getRotationMatrix2D()` and `cv2.warpAffine()` with `cv2.INTER_CUBIC` and white border extrapolation (`borderValue=(255,255,255)`).

---

### Stage 3: Illumination Normalization via Morphological Background Division
* **Source File:** `src/restoration_pipeline.py` (`remove_background()`), `modules/preprocessing/preprocessing.py`
* **Objective:** Flatten non-uniform yellowing, shadows, and water stains to uniform white without suppressing high-frequency text strokes.
* **Mathematical Formulation:**
  A 2D rectangular structuring element $S_{k \times k}$ ($k=51\text{ px}$, larger than maximum stroke thickness) is applied via morphological closing:
  $$\mathcal{B}(x, y) = (I_g \bullet S)(x, y) = ((I_g \oplus S) \ominus S)(x, y)$$
  Flat-field point-wise division:
  $$I_{\text{norm}}(x, y) = \text{clip}\left( \frac{I_g(x, y)}{\max(\mathcal{B}(x, y), 1.0)} \times 255.0, \; 0, \; 255 \right)$$
* **Why it works:**
  Morphological dilation ($\oplus$) expands surrounding bright paper over dark strokes, and erosion ($\ominus$) restores the background surface $\mathcal{B}$. In stained regions, both $I_g$ and $\mathcal{B}$ have low values; their quotient evaluates near $1.0$, mapping to pure white ($255$), while dark ink strokes remain intact.

---

### Stage 4: Edge-Preserving Spatial Denoising
* **Source File:** `src/restoration_pipeline.py` (`denoise()`), `modules/filtering_inpainting/filtering_inpainting.py`
* **Objective:** Eliminate paper grain, sensor noise, and dust without blurring fine character serifs.
* **Implemented Algorithms:**
  1. **Fast Non-Local Means (NLM):**
     $$\hat{I}(p) = \frac{1}{Z(p)} \sum_{q \in \Omega} I(q) \exp\left( -\frac{\|V(p) - V(q)\|^2}{h^2} \right)$$
     - Search window: $21 \times 21$, patch size: $7 \times 7$, filter strength $h = 10$.
     - Evaluates structural patch distance across RGB channels for color scans (`cv2.fastNlMeansDenoisingColored`).
  2. **Bilateral Filtering:**
     $$BF[I]_p = \frac{1}{W_p} \sum_{q \in \mathcal{S}} I_q \cdot \exp\left(-\frac{\|p-q\|^2}{2\sigma_s^2}\right) \cdot \exp\left(-\frac{|I_p-I_q|^2}{2\sigma_r^2}\right)$$
     - Spatial neighborhood diameter $d = 5$, range parameter $\sigma_r = 50$, spatial parameter $\sigma_s = 50$.
  3. **Median & Gaussian Filter Fallbacks:** For rapid salt-and-pepper suppression.

---

### Stage 5: Local Contrast Enhancement (CLAHE)
* **Source File:** `src/restoration_pipeline.py` (`enhance_contrast()`), `modules/filtering_inpainting/filtering_inpainting.py`
* **Objective:** Recover faded, low-contrast ink strokes without over-saturating background paper.
* **Algorithm:**
  1. Color transformation: Convert image from BGR to device-independent CIE $L^*a^*b^*$ color space.
  2. Channel separation: Extract luminance channel $L^*$ ($0 \le L^* \le 100$). Chrominance channels ($a^*, b^*$) are kept untouched to prevent color artifacts.
  3. CLAHE application:
     - Partition $L^*$ into an $8 \times 8$ grid of contextual tiles.
     - Clip local histogram slopes exceeding $\beta = 2.0$.
     - Uniformly redistribute clipped counts across all histogram bins before computing the CDF.
     - Interpolate bilinearly across tile boundaries to eliminate artificial seams.
  4. Reconstruction: Merge enhanced $L^*$ with original $a^*, b^*$ and convert back to BGR.

---

### Stage 6: Structural Defect Repair via Digital Inpainting
* **Source File:** `src/restoration_pipeline.py` (`inpaint()`), `src/utils.py` (`detect_damage_mask()`), `modules/filtering_inpainting/filtering_inpainting.py`
* **Objective:** Detect and repair physical holes, tears, wormholes, and severe ink blots.
* **Algorithm:**
  1. **Automated Damage Mask Generation:**
     $$M_{\text{damage}}(x, y) = \begin{cases} 255, & \text{if } I_g(x, y) \le 30 \text{ (dark ink blots/holes) or } I_g(x, y) \ge 245 \text{ (paper voids)} \\ 0, & \text{otherwise} \end{cases}$$
  2. Morphological opening with a $3 \times 3$ kernel strips isolated single-pixel text strokes from the mask.
  3. Connected-component contour area filtering isolates damage regions exceeding $A_{\min} = 100\text{ px}^2$.
  4. **Inpainting Reconstruction:**
     - **Telea Method (`INPAINT_TELEA`):** Fast Marching algorithm propagating boundary colors inward along the gradient normal:
       $$I(p) = \frac{\sum_{q \in B_\epsilon(p)} w(p, q) [I(q) + \nabla I(q) \cdot (p - q)]}{\sum_{q \in B_\epsilon(p)} w(p, q)}$$
     - **Navier-Stokes Method (`INPAINT_NS`):** Solves transport partial differential equations preserving isophotes (lines of equal luminance).

---

### Stage 7: High-Speed $O(1)$ Sauvola Local Adaptive Binarization
* **Source File:** `src/binarization.py` (`sauvola_binarize()`), `modules/binarization/binarization.py`
* **Objective:** Convert grayscale image to clean binary foreground ($0$) and background ($255$).
* **Standard Sauvola Formula:**
  $$T(x, y) = m(x, y) \cdot \left[ 1 + k \cdot \left( \frac{s(x, y)}{R} - 1 \right) \right]$$
  where $m(x, y)$ is local mean, $s(x, y)$ is local standard deviation in window $W \times W$, $R = 128$, and $k = 0.2$.

* **Our Exact $O(1)$ Box-Filter Optimization:**
  A naive sliding window requires $O(W^2)$ computations per pixel. We compute local statistics in $O(1)$ time using OpenCV integral box filters (`cv2.blur`):
  $$\mathbf{M} = \text{BoxFilter}(I_g, W \times W) = \frac{1}{W^2} \sum_{i,j} I_g(x+i, y+j)$$
  $$\mathbf{M_2} = \text{BoxFilter}(I_g^2, W \times W) = \frac{1}{W^2} \sum_{i,j} I_g^2(x+i, y+j)$$
  $$\mathbf{Var} = \max(\mathbf{M_2} - \mathbf{M}^2, \; 0.0)$$
  $$\mathbf{S} = \sqrt{\mathbf{Var}}$$
  $$\mathbf{T} = \mathbf{M} \odot \left( \mathbf{1} + k \cdot \left( \frac{\mathbf{S}}{128.0} - \mathbf{1} \right) \right)$$
  $$B(x, y) = \begin{cases} 255, & \text{if } I_g(x, y) \ge \mathbf{T}(x, y) \\ 0, & \text{otherwise} \end{cases}$$
* **Performance Gain:** Execution time is decoupled from window scale $W$, running in $<0.2\text{ s}$ per multi-megapixel document ($35\times$ faster than naive sliding windows).

---

### Stage 8: Morphological Post-Processing & Text Sharpening
* **Source File:** `src/restoration_pipeline.py` (`postprocess()`), `modules/binarization/binarization.py`
* **Objective:** Solidify character stroke topology and eliminate speckle noise.
* **Algorithm:**
  1. **High-Frequency Unsharp Masking:**
     $$I_{\text{sharp}} = \text{clip}\left( I + \alpha \cdot [I - (G_\sigma * I)], \; 0, \; 255 \right)$$
     with sharpening strength $\alpha = 1.5$ and Gaussian kernel scale $\sigma = 3.0$.
  2. **Dual Morphological Cleaning:**
     $$I_{\text{clean}} = (I_{\text{sharp}} \circ K_{2\times 2}) \bullet K_{2\times 2}$$
     - Morphological opening ($\circ$) with $2 \times 2$ rect structuring element removes isolated background noise specks.
     - Morphological closing ($\bullet$) bridges hairline stroke fractures without thickening characters.

---

## 3. Algorithmic Complexity & Optimization Analysis

| Stage | Algorithm Employed | Naive Complexity | Our Optimized Complexity | Optimization Technique Used |
| :--- | :--- | :---: | :---: | :--- |
| **Stage 1: Border Crop** | Mean Profile Thresholding | $O(H \cdot W)$ | $O(H \cdot W)$ | Vectorized NumPy dimension reductions (`axis=0, 1`) |
| **Stage 2: Deskew** | Projection Variance / Hough | $O(N_\theta \cdot H \cdot W)$ | $O(N_\theta \cdot H \cdot W)$ | Discrete angular sub-sampling ($0.5^\circ$) + affine matrix warp |
| **Stage 3: Background** | Morphological Division | $O(k^2 \cdot H \cdot W)$ | $O(H \cdot W)$ | Separable structuring elements in OpenCV morphology engine |
| **Stage 4: Denoising** | Fast Non-Local Means | $O(W_{\text{search}}^2 \cdot W_{\text{patch}}^2)$ | $O(W_{\text{search}}^2 \cdot H \cdot W)$ | Integral patch lookup acceleration (`cv2.fastNlMeansDenoising`) |
| **Stage 5: Contrast** | CLAHE in CIE L\*a\*b\* | $O(H \cdot W)$ | $O(H \cdot W)$ | Tile grid partitioning ($8\times 8$) with bilinear seam interpolation |
| **Stage 6: Inpaint** | Fast Marching (Telea) | $O(N_{\text{defects}} \log N)$ | $O(N_{\text{defects}} \log N)$ | Priority queue level-set narrow band propagation |
| **Stage 7: Binarization** | Sauvola Adaptive Threshold | $O(W^2 \cdot H \cdot W)$ | **$O(H \cdot W)$ [Constant $O(1)$]** | **Separable box filtering (`cv2.blur`) on $I_g$ and $I_g^2$** |
| **Stage 8: Post-Process**| Unsharp Mask + Morpho | $O(H \cdot W)$ | $O(H \cdot W)$ | Frequency subtraction + compact $2\times 2$ structuring elements |

---

## 4. File & Module Mapping

```
Section_D_Team_24/
│
├── src/
│   ├── restoration_pipeline.py   # DocumentRestorer master chaining class (963 lines)
│   ├── binarization.py           # O(1) Sauvola, Otsu, Niblack, Adaptive Gaussian/Mean (297 lines)
│   ├── utils.py                  # PSNR, SSIM, damage mask detection, histograms (412 lines)
│   └── download_samples.py       # Dataset fetcher & auto-downscaling to 1600px
│
├── modules/                      # Modular Work Breakdown (Conflict-Free Collaboration)
│   ├── preprocessing/            # Student 1 (Ujjwal): Stages 1, 2, 3 (Border crop, deskew, flat-field)
│   ├── filtering_inpainting/     # Student 2 (Ujjawal): Stages 4, 5, 6 (Fast NLM, Bilateral, CLAHE, Inpaint)
│   ├── binarization/             # Student 3 (Sparsh): Stages 7, 8 (O(1) Sauvola, Otsu, Niblack, Unsharp)
│   └── ui_evaluation/            # Student 4 (Vishnu Kant): Metrics (PSNR/SSIM, histograms, test runners)
│
├── app.py                        # Streamlit web application with 4 interactive tabs
├── test_pipeline.py              # Automated unit test suite verifying all 8 stages
└── test_batch.py                 # Automated batch restoration runner across all datasets
```

---

## 5. Evaluation Metrics Formulations

### Peak Signal-to-Noise Ratio (PSNR)
Measures absolute pixel reconstruction fidelity against the reference:
$$\text{MSE} = \frac{1}{M N} \sum_{i=0}^{M-1} \sum_{j=0}^{N-1} [I_{\text{ref}}(i, j) - I_{\text{test}}(i, j)]^2$$
$$\text{PSNR} = 10 \cdot \log_{10}\left( \frac{255^2}{\text{MSE}} \right) \quad (\text{dB})$$

### Structural Similarity Index Measure (SSIM)
Evaluates perceptual structural preservation, luminance, and contrast across spatial windows:
$$\text{SSIM}(x, y) = \frac{(2\mu_x\mu_y + C_1)(2\sigma_{xy} + C_2)}{(\mu_x^2 + \mu_y^2 + C_1)(\sigma_x^2 + \sigma_y^2 + C_2)}$$
where $C_1 = (0.01 \cdot 255)^2$ and $C_2 = (0.03 \cdot 255)^2$.

---

## 6. Interactive Web UI Architecture

The Streamlit dashboard (`app.py`) provides an interactive interface for demonstrating the pipeline:
* **Sidebar Configuration:** Live sliders for kernel sizes, CLAHE clip limit $\beta$, Sauvola window $W$, and sensitivity constant $k$.
* **Tab 1 (Overview):** Interactive Juxtapose before-and-after split slider + 1-click high-resolution PNG export.
* **Tab 2 (Stage-by-Stage):** 3-column visual gallery displaying exact intermediate buffers for every stage.
* **Tab 3 (Binarization Grid):** Side-by-side comparison matrix of Otsu, Adaptive Gaussian, Adaptive Mean, Niblack, and Sauvola.
* **Tab 4 (Diagnostics):** Live PSNR/SSIM scorecards and overlaid pixel intensity distribution histograms.
