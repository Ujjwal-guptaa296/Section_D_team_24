"""Member 2 module init."""
from .filtering_inpainting import (
    denoise_document,
    enhance_contrast,
    detect_damage_mask,
    inpaint_defects,
)

__all__ = [
    "denoise_document",
    "enhance_contrast",
    "detect_damage_mask",
    "inpaint_defects",
]
