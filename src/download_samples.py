"""
Download sample degraded document images from public domain sources.

This script downloads historical document images that can be used to test
and demonstrate the document restoration pipeline. All images are from
public domain sources (Wikimedia Commons, Internet Archive).
"""

import os
import urllib.request
import ssl
from pathlib import Path


# Sample degraded document images from public domain sources
SAMPLE_IMAGES = {
    "old_manuscript_01.jpg": {
        "url": "https://en.wikipedia.org/wiki/Special:FilePath/Codex_Gigas_facsimile.jpg",
        "description": "Codex Gigas facsimile - Medieval manuscript page"
    },
    "degraded_text_02.jpg": {
        "url": "https://en.wikipedia.org/wiki/Special:FilePath/Gutenberg_Bible,_Lenox_Copy,_New_York_Public_Library,_2009._Pic_01.jpg",
        "description": "Gutenberg Bible - Historical printed text"
    },
    "old_letter_03.jpg": {
        "url": "https://en.wikipedia.org/wiki/Special:FilePath/Constitution_of_the_United_States,_page_1.jpg",
        "description": "US Constitution page 1 - Historical handwritten document"
    },
    "ancient_scroll_04.jpg": {
        "url": "https://en.wikipedia.org/wiki/Special:FilePath/Dead_Sea_Scroll_-_part_of_Isaiah_Scroll_(Isa_57.17_-_59.9).jpg",
        "description": "Dead Sea Scroll - Ancient degraded manuscript"
    },
    "faded_document_05.jpg": {
        "url": "https://en.wikipedia.org/wiki/Special:FilePath/Magna_Carta_(British_Library_Cotton_MS_Augustus_II.106).jpg",
        "description": "Magna Carta - Faded historical document"
    },
}


def download_samples(output_dir: str = "samples") -> list:
    """
    Download sample degraded document images to the specified directory.

    Args:
        output_dir: Directory to save downloaded images.

    Returns:
        List of paths to successfully downloaded images.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    downloaded = []
    
    # Create an SSL context that doesn't verify certificates
    # (some institutional networks block certificate verification)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    for filename, info in SAMPLE_IMAGES.items():
        filepath = output_path / filename
        
        if filepath.exists():
            print(f"  [SKIP] {filename} already exists")
            downloaded.append(str(filepath))
            continue
        
        print(f"  [DOWNLOADING] {filename}")
        print(f"    Source: {info['description']}")
        
        try:
            req = urllib.request.Request(
                info["url"],
                headers={"User-Agent": "Mozilla/5.0 (DocumentRestorationProject/1.0)"}
            )
            with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
                data = response.read()
            
            with open(filepath, "wb") as f:
                f.write(data)
            
            # Verify the downloaded file is a valid image
            file_size = os.path.getsize(filepath)
            if file_size < 1000:  # Less than 1KB is suspicious
                print(f"    [WARNING] File seems too small ({file_size} bytes), might be invalid")
                os.remove(filepath)
                continue
            
            print(f"    [OK] Saved ({file_size / 1024:.1f} KB)")

            # Auto-resize huge scans to max dimension 1600px for responsive UI performance
            try:
                import cv2
                img = cv2.imread(str(filepath))
                if img is not None:
                    h, w = img.shape[:2]
                    if max(h, w) > 1600:
                        scale = 1600.0 / max(h, w)
                        new_w, new_h = int(w * scale), int(h * scale)
                        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
                        cv2.imwrite(str(filepath), resized, [cv2.IMWRITE_JPEG_QUALITY, 92])
                        print(f"    [OPTIMIZED] Resized to {new_w}x{new_h} for responsive performance")
            except Exception:
                pass

            downloaded.append(str(filepath))
            
        except Exception as e:
            print(f"    [ERROR] Failed to download: {e}")
            # Clean up partial download
            if filepath.exists():
                os.remove(filepath)
    
    print(f"\nDownloaded {len(downloaded)}/{len(SAMPLE_IMAGES)} sample images to '{output_dir}/'")
    return downloaded


def create_synthetic_sample(output_dir: str = "samples") -> str:
    """
    Create a synthetic degraded document image for testing if downloads fail.
    Uses OpenCV to generate a text image with artificial degradation.
    
    Args:
        output_dir: Directory to save the synthetic image.
    
    Returns:
        Path to the created image.
    """
    try:
        import cv2
        import numpy as np
    except ImportError:
        print("OpenCV not installed. Cannot create synthetic sample.")
        return ""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    filepath = output_path / "synthetic_degraded.jpg"

    if filepath.exists():
        print(f"  [SKIP] synthetic_degraded.jpg already exists")
        return str(filepath)

    # Create a white page
    height, width = 800, 600
    img = np.ones((height, width), dtype=np.uint8) * 240

    # Add text lines
    font = cv2.FONT_HERSHEY_SIMPLEX
    lines = [
        "The Quick Brown Fox",
        "Jumps Over The Lazy Dog",
        "",
        "Lorem ipsum dolor sit amet,",
        "consectetur adipiscing elit.",
        "Sed do eiusmod tempor",
        "incididunt ut labore et",
        "dolore magna aliqua.",
        "",
        "Document Restoration Test",
        "Sample Page - Year 1823",
    ]

    y = 80
    for line in lines:
        if line:
            cv2.putText(img, line, (40, y), font, 0.6, (20, 20, 20), 1, cv2.LINE_AA)
        y += 40

    # Add artificial degradation

    # 1. Add random noise (paper grain)
    noise = np.random.normal(0, 15, img.shape).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # 2. Add stains (dark blobs)
    for _ in range(5):
        cx = np.random.randint(50, width - 50)
        cy = np.random.randint(50, height - 50)
        radius = np.random.randint(20, 60)
        intensity = np.random.randint(150, 200)
        cv2.circle(img, (cx, cy), radius, (intensity,), -1)

    # 3. Add yellowing effect (uneven background)
    gradient = np.linspace(0, 40, width).astype(np.uint8)
    gradient = np.tile(gradient, (height, 1))
    img = np.clip(img.astype(np.int16) - gradient.astype(np.int16), 0, 255).astype(np.uint8)

    # 4. Add slight blur (simulating aging)
    img = cv2.GaussianBlur(img, (3, 3), 0.8)

    # 5. Add border artifacts
    img[:10, :] = np.random.randint(0, 50, (10, width), dtype=np.uint8)
    img[-10:, :] = np.random.randint(0, 50, (10, width), dtype=np.uint8)
    img[:, :8] = np.random.randint(0, 50, (height, 8), dtype=np.uint8)
    img[:, -8:] = np.random.randint(0, 50, (height, 8), dtype=np.uint8)

    # 6. Slight rotation (skew)
    center = (width // 2, height // 2)
    M = cv2.getRotationMatrix2D(center, 2.5, 1.0)
    img = cv2.warpAffine(img, M, (width, height), borderValue=200)

    cv2.imwrite(str(filepath), img)
    print(f"  [OK] Created synthetic_degraded.jpg")
    return str(filepath)


if __name__ == "__main__":
    print("=" * 60)
    print("Document Restoration - Sample Image Downloader")
    print("=" * 60)
    print()

    print("Downloading sample images from public domain sources...")
    print("-" * 60)
    downloaded = download_samples()

    if len(downloaded) < 2:
        print("\nFew images downloaded. Creating synthetic sample...")
        print("-" * 60)
        create_synthetic_sample()

    print()
    print("=" * 60)
    print("Done! You can now run the restoration pipeline.")
    print("  streamlit run app.py")
    print("=" * 60)
