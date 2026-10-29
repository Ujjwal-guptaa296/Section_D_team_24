# 📜 Restoration and Enhancement of Degraded Historical Documents and Manuscripts

**Course:** Image Processing and Computer Vision (CS-XXXX)  
**Submission:** TA Group Assignment  
**Repository Name (as instructed):** `Section_D_Team_24`  
**Section:** D | **Team Number:** 24  

---

## 👥 Team Members

| Name | Registration Number | Primary Role / Responsibility |
| :--- | :---: | :--- |
| **Ujjwal Gupta** (Lead) | 20233296 | Preprocessing, Boundary Detection, Radon/Hough Deskewing, Morphological Flat-Field Division |
| **Ujjawal Mishra** | 20233295 | Edge-Preserving Denoising (Fast NLM/Bilateral), CLAHE in LAB Space, Digital Inpainting |
| **Sparsh Gupta** | 20233276 | High-Speed $O(1)$ Sauvola Binarization, Algorithm Benchmarking, Unsharp Mask Post-Processing |
| **Vishnu Kant Bangri** | 20233315 | Quality Evaluation (PSNR/SSIM, Histograms), Streamlit Web App (`app.py`), Integration & Testing |

---

## 📌 Submission Checklist

In accordance with the TA assignment submission instructions:
- [x] **1. Source Code:** Complete modular Python codebase in `src/` and `modules/`
- [x] **2. Dataset(s):** Multi-century authentic historical manuscripts and synthetic benchmarks in `dataset/`
- [x] **3. Implementation Details:** In-depth algorithmic formulations and derivations in `REPORT.md` and `IEEE_Report.tex`
- [x] **4. Step-by-Step Instructions:** Complete setup, dependency installation, and running instructions below
- [x] **5. PPT Presentation:** Formatted slide deck in `presentation/` (`.html` interactive viewer + `.md`)
- [x] **6. Final Project Report:** Full research paper in both Word (`.docx`) and LaTeX (`.tex` Overleaf ready)
- [x] **Repository Naming Convention:** `Section_D_Team_24`

---

## 🏗️ 8-Stage Restoration Pipeline Architecture

```
[Raw Degraded Manuscript Scan]
    │
    ├── 1. Boundary Detection & Scanner Margin Cropping (Intensity Profile Thresholding)
    ├── 2. Geometric Rectification & Deskewing (Radon Projection Variance & Hough Lines)
    ├── 3. Illumination Normalization via Morphological Background Division (Flat-Field, 51x51)
    ├── 4. Edge-Preserving Spatial Denoising (Fast Non-Local Means & Bilateral Filter)
    ├── 5. Perceptual Local Contrast Enhancement (CLAHE in CIE L*a*b* Luminance Channel)
    ├── 6. Structural Defect Repair via Inpainting (Telea Fast Marching & Navier-Stokes)
    ├── 7. High-Speed O(1) Sauvola Local Adaptive Binarization (Integral Box Filters)
    └── 8. Morphological Post-Processing & Text Sharpening (Unsharp Mask + 2x2 Opening/Closing)
    │
    ▼
[Restored High-Legibility Document & Diagnostic Metrics (PSNR / SSIM)]
```

---

## 📂 Repository Directory Structure

```
Section_D_Team_24/
│
├── dataset/                                      # [Requirement 2: Datasets]
│   ├── README.md                                 # Dataset provenance, resolutions & degradation taxonomy
│   ├── old_manuscript_01.jpg                     # Codex Gigas facsimile (13th Century, Gothic vellum)
│   ├── degraded_text_02.jpg                      # Gutenberg Bible folio (15th Century, movable type)
│   ├── old_letter_03.jpg                         # US Constitution page (18th Century, cursive bleed-through)
│   ├── faded_document_05.jpg                     # Magna Carta (13th Century, severe ink fading & stains)
│   └── synthetic_degraded.jpg                    # Calibrated synthetic test document (noise, skew, stains)
│
├── presentation/                                 # [Requirement 5: PPT Presentation]
│   ├── Presentation_Document_Restoration_Section_D_Team_24.html # Interactive full-screen slide deck
│   └── PRESENTATION_SLIDES.md                    # 12-slide markdown presentation deck
│
├── modules/                                      # [Requirement 1: Modular Source Code by Member]
│   ├── preprocessing/                            # Ujjwal Gupta (Boundary Crop, Deskew, Flat-Field Division)
│   ├── filtering_inpainting/                     # Ujjawal Mishra (Fast NLM, Bilateral, CLAHE, Inpainting)
│   ├── binarization/                             # Sparsh Gupta (O(1) Sauvola, Otsu, Niblack, Unsharp Mask)
│   └── ui_evaluation/                            # Vishnu Kant Bangri (PSNR, SSIM, Histograms, Diagnostics)
│
├── src/                                          # Unified core restoration engine
│   ├── restoration_pipeline.py                   # Master DocumentRestorer fluent builder class
│   ├── binarization.py                           # High-speed binarization methods
│   ├── utils.py                                  # Evaluation metrics, damage mask & histograms
│   └── download_samples.py                       # Automated dataset acquisition & dimension optimizer
│
├── app.py                                        # Interactive Streamlit Web Dashboard
├── Document_Restoration_IEEE_Report.docx         # [Requirement 6: Final 5-Page Word Report]
├── IEEE_Report.tex                               # [Requirement 6: Final 5-Page Overleaf LaTeX Paper]
├── REPORT.md                                     # Markdown academic research report
├── requirements.txt                              # Python environment dependencies
├── test_pipeline.py                              # Functional integration test suite
└── test_batch.py                                 # Automated batch verification runner
```

---

## 🚀 Step-by-Step Instructions on How to Run the Code

### 1. Prerequisites
- **Python 3.10+** installed on your system.
- Git installed (for cloning).

### 2. Clone the Repository
```bash
git clone https://github.com/<your-username>/Section_D_Team_24.git
cd Section_D_Team_24
```


- **Choose a sample:** Select from built-in manuscripts (Codex Gigas, Gutenberg Bible, US Constitution, Magna Carta) or upload your own scan.
- **Adjust parameters:** Toggle any stage and tweak sliders in real time in the sidebar.
- **Click:** Click **`🔄 Restore Document`** to execute the pipeline.
- **Explore tabs:** Inspect the Juxtapose before/after comparison slider, intermediate stages, binarization grid, and PSNR/SSIM histogram cards.

### 6. Verify Modular Components (Optional CLI Check)
* **Verify Preprocessing & Deskewing:**
  ```bash
  python -c "import cv2; from modules.preprocessing import crop_document_borders; print('Preprocessing OK')"
  ```
* **Verify Sauvola Binarization:**
  ```bash
  python -c "import cv2; from modules.binarization import sauvola_binarize; print('Binarization OK')"
  ```
* **Verify Quality Evaluation:**
  ```bash
  python -c "import numpy as np; from modules.ui_evaluation import compute_psnr; print('Evaluation OK')"
  ```

---

## 📊 Experimental Results Summary

### Table 1: Quantitative Performance Across Historical Datasets
| Document Sample | Resolution | Degradation Modalities | Restored PSNR | Restored SSIM | Runtime |
| :--- | :---: | :--- | :---: | :---: | :---: |
| **Synthetic Benchmark** | $800 \times 600$ | Stains, Skew ($2.5^\circ$), Noise, Margins | **11.43 dB** | **0.6416** | 0.18 s |
| **US Constitution** | $1600 \times 1321$ | Heavy Cursive Bleed-Through, Fading | **9.33 dB** | **0.3569** | 0.62 s |
| **Magna Carta** | $1066 \times 1600$ | Severe Fading, Dark Stains, Low Contrast | **7.62 dB** | **0.1706** | 0.48 s |
| **Codex Gigas** | $1200 \times 1600$ | Parchment Yellowing, Glare, Gothic Script | **6.60 dB** | **0.3399** | 0.54 s |
| **Gutenberg Bible** | $1000 \times 1600$ | Illumination Falloff, Faded Moveable Type | **4.54 dB** | **0.2978** | 0.44 s |

> **Note on PSNR:** Lower numerical PSNR is desirable because dark brown/yellow stains ($I \approx 120$) are mapped to pure white ($255$), producing large MSE while dramatically boosting visual legibility.

### Table 2: Binarization Paradigm Comparison
| Algorithm | Threshold Scope | Non-Uniform Illumination | Bleed-Through Handling | Background Noise Level |
| :--- | :---: | :---: | :---: | :---: |
| **Otsu's Method** | Global | Fails (stains turn solid black) | Very Poor | Low |
| **Adaptive Mean** | Local | Moderate | Poor (erases faint text) | Moderate |
| **Adaptive Gaussian** | Local | Good | Fair | Moderate |
| **Niblack's Method** | Local | Good | Moderate | Severe (heavy grain noise) |
| **Sauvola (Ours)** | **Local $O(1)$** | **Superior** | **Excellent (isolated strokes)** | **Minimal (clean white page)** |

---

## 🖥️ PPT Presentation Deck

The project presentation deck is located in [`presentation/`](presentation/):
1. **PowerPoint Presentation (`.pptx`):** **[`presentation/Presentation_Document_Restoration_Section_D_Team_24.pptx`](presentation/Presentation_Document_Restoration_Section_D_Team_24.pptx)** — 12-slide modern 16:9 widescreen presentation deck ready to present directly in Microsoft PowerPoint.
2. **Interactive Presentation (`.html`):** [`presentation/Presentation_Document_Restoration_Section_D_Team_24.html`](presentation/Presentation_Document_Restoration_Section_D_Team_24.html) — In-browser slide viewer with print-to-PDF support.
3. **Markdown Notes:** [`presentation/PRESENTATION_SLIDES.md`](presentation/PRESENTATION_SLIDES.md) — Slide-by-slide speaker notes.

---

## 📑 Final Project Report

The final project report is provided in two standard formats:
1. **Overleaf / LaTeX Paper (4–5 Pages):** [`IEEE_Report.tex`](IEEE_Report.tex)
2. **Microsoft Word Report (4–5 Pages):** [`Document_Restoration_IEEE_Report.docx`](Document_Restoration_IEEE_Report.docx)

Both follow the required academic sections: **Abstract**, **Introduction**, **Methodology**, **Results and Discussion**, and **Conclusion**.
