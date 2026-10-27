"""Quick test script for the document restoration pipeline."""
import sys
sys.path.insert(0, '.')

from src.restoration_pipeline import DocumentRestorer
from src.binarization import compare_all_methods
from src.utils import compute_psnr, compute_ssim, ensure_grayscale
import cv2

print("=" * 60)
print("Document Restoration Pipeline - Quick Test")
print("=" * 60)

# Test 1: Load image
print("\n[TEST 1] Loading synthetic sample image...")
r = DocumentRestorer()
r.load_image("samples/synthetic_degraded.jpg")
print(f"  Image loaded: {r.current.shape}")

# Test 2: Run individual stages
print("\n[TEST 2] Running pipeline stages...")

r.crop_borders()
print(f"  Border Removal: {r.current.shape}")

r.deskew()
print(f"  Deskew: {r.current.shape}")

r.remove_background()
print(f"  Background Removal: {r.current.shape}")

r.denoise(method='fastNlMeans', strength=10)
print(f"  Denoising: {r.current.shape}")

r.enhance_contrast(method='clahe', clip_limit=2.0)
print(f"  Contrast Enhancement: {r.current.shape}")

r.binarize(method='sauvola', block_size=25, k=0.2)
print(f"  Binarization: {r.current.shape}")

r.postprocess(sharpen=True, morpho_clean=True)
print(f"  Post-Processing: {r.current.shape}")

# Test 3: Get metrics
print("\n[TEST 3] Computing quality metrics...")
metrics = r.get_metrics()
print(f"  PSNR: {metrics['psnr']:.2f} dB")
print(f"  SSIM: {metrics['ssim']:.4f}")

# Test 4: Stage results
print("\n[TEST 4] Stage results collected:")
stages = r.get_stage_results()
for name, img in stages.items():
    print(f"  {name}: {img.shape}")

# Test 5: Binarization comparison
print("\n[TEST 5] Binarization method comparison...")
gray = ensure_grayscale(cv2.imread("samples/synthetic_degraded.jpg"))
results = compare_all_methods(gray)
for name, img in results.items():
    print(f"  {name}: {img.shape}, unique values: {len(set(img.flatten()))}")

# Test 6: Save result
print("\n[TEST 6] Saving restored output...")
cv2.imwrite("samples/restored_output.png", r.get_result())
print("  Saved to samples/restored_output.png")

# Test 7: Full pipeline with config
print("\n[TEST 7] Testing run_full_pipeline with config...")
r2 = DocumentRestorer()
r2.load_image("samples/synthetic_degraded.jpg")
r2.run_full_pipeline(config={
    'crop_borders': {'threshold': 10},
    'deskew': {},
    'remove_background': {'kernel_size': 51},
    'denoise': {'method': 'fastNlMeans', 'strength': 10},
    'enhance_contrast': {'method': 'clahe'},
    'inpaint': None,  # Skip
    'binarize': {'method': 'sauvola'},
    'postprocess': {'sharpen': True},
})
m2 = r2.get_metrics()
print(f"  Full pipeline PSNR: {m2['psnr']:.2f} dB")
print(f"  Full pipeline SSIM: {m2['ssim']:.4f}")

print("\n" + "=" * 60)
print("ALL TESTS PASSED!")
print("=" * 60)
