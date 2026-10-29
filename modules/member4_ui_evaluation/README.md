# 📁 Member 4: Quality Evaluation, Web UI & System Integration

**Assigned Member:** Student 4

### 📌 Responsibilities:
1. **Interactive Streamlit Web Dashboard (`app.py`):** Real-time sidebar controls, interactive Juxtapose before/after slider, and stage-by-stage visualizer tabs.
2. **Quantitative Benchmarking:** Computing PSNR and SSIM scores across all manuscripts, handling spatial dimensions and channel alignment.
3. **Diagnostic Visualizations:** Histogram distribution plotting (before vs. after) and high-res export functionality.
4. **System Integration & Testing:** Automated test suites (`test_pipeline.py`, `test_batch.py`) and batch processing verification.

### 🚀 Standalone Test:
```bash
python -c "import numpy as np; from modules.ui_evaluation import compute_psnr; print('UI & evaluation module functional')"
```
