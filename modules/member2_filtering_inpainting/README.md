# 📁 Member 2: Spatial Filtering, Contrast Enhancement & Inpainting

**Assigned Member:** Student 2

### 📌 Responsibilities:
1. **Edge-Preserving Denoising:** Fast Non-Local Means (NLM) & Bilateral Filtering to suppress paper texture and grain without blurring fine pen strokes.
2. **Local Contrast Enhancement:** Contrast Limited Adaptive Histogram Equalization (CLAHE) applied specifically to the luminance ($L^*$) channel in CIE $L^*a^*b^*$ color space.
3. **Defect Repair via Inpainting:** Automated damage mask generation and reconstruction using Telea's Fast Marching Method and Navier-Stokes PDEs.

### 🚀 Standalone Test:
```bash
python -c "import cv2; from modules.filtering_inpainting import denoise_document; print('Filtering & inpainting module functional')"
```
