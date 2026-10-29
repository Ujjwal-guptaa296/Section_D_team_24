# 📁 Member 1: Geometric Rectification & Preprocessing

**Assigned Member:** Student 1 (Lead)

### 📌 Responsibilities:
1. **Document Border Detection:** Eliminates dark scanner margins using intensity profile thresholding.
2. **Deskewing:** Detects document rotation angle via Radon projection profiles and Hough Line transforms and rectifies skew.
3. **Morphological Background Division:** Flat-field correction using morphological closing with large kernels ($51\times 51$) to eliminate uneven lighting, shadows, and yellowing.
4. **Dataset Acquisition:** Sourcing and optimizing the authentic historical document scans.

### 🚀 Standalone Test:
```bash
python -c "import cv2; from modules.preprocessing import crop_document_borders; print('Preprocessing module functional')"
```
