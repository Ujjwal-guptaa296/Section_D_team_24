# 📜 Dataset Description & Provenance

**Subject:** Image Processing and Computer Vision (Section D, Team 24)  
**Topic:** Restoration and Enhancement of Degraded Historical Documents and Manuscripts  

---

## 1. Overview of Historical Document Datasets

This repository includes a multi-century corpus of authentic historical manuscripts, incunabula prints, and calibrated synthetic benchmarks. The documents span the 13th to 18th centuries and represent diverse physical degradation phenomena:

| File Name | Historical Origin & Epoch | Resolution | Modality | Primary Degradation Features |
| :--- | :--- | :---: | :--- | :--- |
| **`old_manuscript_01.jpg`** | *Codex Gigas* Facsimile (13th Century) | $1200 \times 1600$ | Vellum / Latin Gothic Script | Severe parchment darkening, illumination falloff, Gothic strokes, scanning glare |
| **`degraded_text_02.jpg`** | *Gutenberg Bible* Folio (15th Century) | $1000 \times 1600$ | Rag Paper / Movable Type | Ink fading, paper yellowing, asymmetric lighting gradients |
| **`old_letter_03.jpg`** | *US Constitution* (18th Century) | $1600 \times 1321$ | Parchment / Cursive Calligraphy | Heavy reverse-side ink bleed-through, faded iron gall strokes |
| **`faded_document_05.jpg`** | *Magna Carta* (13th Century) | $1066 \times 1600$ | Vellum / Latin Script | Severe ink fading, moisture stains, low contrast |
| **`synthetic_degraded.jpg`** | Calibrated Synthetic Benchmark | $800 \times 600$ | Digital Synthetic Text | Rotational skew ($+2.5^\circ$), Gaussian noise ($\sigma=20$), radial stain gradients |

---

## 2. Dataset Provenance and Public Domain Sources

All authentic historical manuscripts are derived from open-access, public domain digital archives:
1. **Codex Gigas (Devil's Bible):** National Library of Sweden (Kungliga biblioteket), Facsimile reproduction.
2. **Gutenberg Bible:** New York Public Library (Lenox Copy), Rare Book Division.
3. **Constitution of the United States:** National Archives and Records Administration (NARA), Washington, D.C.
4. **Magna Carta:** British Library (Cotton MS Augustus II.106).

---

## 3. Dataset Preprocessing & Optimization

Historical scans often exceed $60\text{ MP}$ ($8000 \times 7000\text{ pixels}$), requiring tens of gigabytes of RAM during convolution and spatial filtering. For this repository:
- All images have been downscaled using area-relation interpolation (`cv2.INTER_AREA`) to a standardized maximum dimension of $1600\text{ pixels}$.
- High-fidelity visual quality and fine stroke typography are strictly preserved.
- Real-time restoration, interactive slider manipulation, and batch benchmarks execute in under $1\text{ second}$ per document on standard consumer hardware.

---

## 4. Download and Reproduction Script

You can re-download and automatically optimize the complete raw public domain dataset at any time by executing:
```bash
python src/download_samples.py
```
This script downloads the archival scans directly and applies automated dimension optimization.
