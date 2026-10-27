# 📁 Member 3: Adaptive Binarization & Post-Processing

**Assigned Member:** Student 3

### 📌 Responsibilities:
1. **$O(1)$ Sauvola Binarization:** Deriving and implementing the fast integral box-filter formulation of Sauvola thresholding ($T = m \cdot [1 + k(s/R - 1)]$) using `cv2.blur`.
2. **Multi-Method Thresholding Suite:** Implementation and benchmarking of Otsu's global method, Niblack's local variance method, and Adaptive Gaussian thresholding.
3. **Text Refinement & Sharpening:** Unsharp masking and $2\times 2$ morphological opening/closing for character continuity and speckle cleanup.

### 🚀 Standalone Test:
```bash
python -c "import cv2; from modules.member3_binarization import sauvola_binarize; print('Member 3 module functional')"
```
