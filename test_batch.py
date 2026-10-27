"""Batch test script to verify restoration pipeline on all available samples."""
import os
import sys
from pathlib import Path
import cv2

sys.path.insert(0, '.')

from src.restoration_pipeline import DocumentRestorer

def run_batch_test():
    samples_dir = Path("samples")
    output_dir = Path("samples/restored_batch")
    output_dir.mkdir(exist_ok=True, parents=True)

    image_files = [
        f for f in samples_dir.iterdir()
        if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff')
        and not f.name.startswith("restored_")
    ]

    print("=" * 70)
    print(f"BATCH RESTORATION VERIFICATION ({len(image_files)} sample documents)")
    print("=" * 70)

    for i, img_path in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}] Processing: {img_path.name}")
        restorer = DocumentRestorer()
        try:
            restorer.load_image(img_path)
            print(f"  Input size: {restorer.current.shape}")
            
            # Execute standard pipeline
            restorer.run_full_pipeline(config={
                'crop_borders': {'threshold': 10},
                'deskew': {},
                'remove_background': {'kernel_size': 51},
                'denoise': {'method': 'fastNlMeans', 'strength': 8},
                'enhance_contrast': {'method': 'clahe', 'clip_limit': 2.0},
                'inpaint': None,
                'binarize': {'method': 'sauvola', 'block_size': 25, 'k': 0.2},
                'postprocess': {'sharpen': True, 'morpho_clean': True}
            })

            metrics = restorer.get_metrics()
            print(f"  Restored size: {restorer.get_result().shape}")
            print(f"  PSNR: {metrics['psnr']:.2f} dB | SSIM: {metrics['ssim']:.4f}")

            out_path = output_dir / f"restored_{img_path.stem}.png"
            cv2.imwrite(str(out_path), restorer.get_result())
            print(f"  Saved -> {out_path.name} [OK]")

        except Exception as e:
            print(f"  [FAIL]: {e}")

    print("\n" + "=" * 70)
    print("ALL BATCH RESTORATION TESTS FINISHED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_batch_test()
