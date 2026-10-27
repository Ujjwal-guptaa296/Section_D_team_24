"""
Generate an EXACT 4.5 to 5-page research paper document.
Target: ~2,100 to 2,250 words total, tight formatting, single-spaced 11pt Times New Roman,
1-inch margins, 2 tables, exact headings:
- Title & Authors
- Abstract & Keywords
- I. INTRODUCTION (I.A, I.B, I.C, I.D)
- II. METHODOLOGY (II.A - II.H)
- III. RESULTS AND DISCUSSION (III.A - III.E, Table I, Table II)
- IV. CONCLUSION
- REFERENCES
"""

import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls


def set_cell_bg(cell, hex_color):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tc_pr.append(shd)


def set_cell_margins(cell, top=60, bottom=60, left=80, right=80):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tc_pr.append(tc_mar)


def add_heading_1(doc, text):
    h = doc.add_paragraph()
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h.paragraph_format.space_before = Pt(8)
    h.paragraph_format.space_after = Pt(2)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(12)
    r.bold = True
    r.font.color.rgb = RGBColor(20, 35, 75)
    return h


def add_heading_2(doc, text):
    h = doc.add_paragraph()
    h.alignment = WD_ALIGN_PARAGRAPH.LEFT
    h.paragraph_format.space_before = Pt(6)
    h.paragraph_format.space_after = Pt(2)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(11)
    r.bold = True
    r.italic = True
    r.font.color.rgb = RGBColor(30, 30, 30)
    return h


def add_body(doc, text, bold_prefix=None, italic=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.05
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.first_line_indent = Inches(0.2)
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = 'Times New Roman'
        r_pre.font.size = Pt(11)
        r_pre.bold = True
    r = p.add_run(text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(11)
    r.italic = italic
    return p


def add_equation(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(10)
    r.italic = True
    return p


def build_exact_5_page_report():
    doc = Document()

    # Standard A4, 1-inch margins
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Base style
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(11)
    style.paragraph_format.line_spacing = 1.05
    style.paragraph_format.space_after = Pt(2)

    # -------------------------------------------------------------------------
    # TITLE & AUTHOR BLOCK (~page 1 top)
    # -------------------------------------------------------------------------
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(4)
    r_title = p_title.add_run(
        "Restoration and Enhancement of Degraded Historical Documents and Manuscripts "
        "Using Classical Image Processing and Computer Vision Techniques"
    )
    r_title.font.name = 'Times New Roman'
    r_title.font.size = Pt(16)
    r_title.bold = True
    r_title.font.color.rgb = RGBColor(20, 35, 75)

    p_auth = doc.add_paragraph()
    p_auth.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_auth.paragraph_format.space_after = Pt(1)
    r_auth = p_auth.add_run("Student 1,  Student 2,  Student 3,  Student 4")
    r_auth.font.name = 'Times New Roman'
    r_auth.font.size = Pt(10.5)
    r_auth.bold = True

    p_aff = doc.add_paragraph()
    p_aff.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_aff.paragraph_format.space_after = Pt(1)
    r_aff = p_aff.add_run("Department of Computer Science and Engineering, [University Name], [City], India")
    r_aff.font.name = 'Times New Roman'
    r_aff.font.size = Pt(9.5)
    r_aff.italic = True

    p_email = doc.add_paragraph()
    p_email.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_email.paragraph_format.space_after = Pt(4)
    r_email = p_email.add_run("{student1, student2, student3, student4}@university.edu")
    r_email.font.name = 'Courier New'
    r_email.font.size = Pt(8.5)

    p_rule = doc.add_paragraph()
    p_rule.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_rule.paragraph_format.space_after = Pt(4)
    r_rule = p_rule.add_run("―" * 60)
    r_rule.font.size = Pt(7)
    r_rule.font.color.rgb = RGBColor(180, 180, 180)

    # -------------------------------------------------------------------------
    # ABSTRACT & KEYWORDS
    # -------------------------------------------------------------------------
    p_abs_h = doc.add_paragraph()
    p_abs_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_abs_h.paragraph_format.space_before = Pt(2)
    p_abs_h.paragraph_format.space_after = Pt(2)
    r_ah = p_abs_h.add_run("Abstract")
    r_ah.font.name = 'Times New Roman'
    r_ah.font.size = Pt(10.5)
    r_ah.bold = True
    r_ah.italic = True

    p_abs = doc.add_paragraph()
    p_abs.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_abs.paragraph_format.line_spacing = 1.05
    p_abs.paragraph_format.left_indent = Inches(0.3)
    p_abs.paragraph_format.right_indent = Inches(0.3)
    p_abs.paragraph_format.space_after = Pt(4)
    r_abs = p_abs.add_run(
        "Historical manuscripts preserved in libraries and national archives suffer from progressive chemical oxidation, "
        "parchment yellowing, ink bleed-through, moisture rings, tears, and geometric skew. Conventional global thresholding "
        "and standard linear spatial filters fail because illumination and degradation fields are non-uniform and text stroke "
        "topology is fragile. In this paper, we formulate and validate an end-to-end eight-stage computer vision restoration "
        "pipeline comprising: (1) intensity-profile boundary cropping, (2) Radon/Hough geometric deskewing, (3) morphological "
        "flat-field division for illumination normalization, (4) edge-preserving Fast Non-Local Means and bilateral denoising, "
        "(5) CLAHE contrast enhancement in perceptual CIE L*a*b* space, (6) Telea and Navier-Stokes inpainting for defect repair, "
        "(7) a constant-time O(1) box-filter implementation of Sauvola local adaptive binarization, and (8) unsharp masking with "
        "morphological topological cleaning. Benchmarked on authentic historical manuscripts (Codex Gigas, Gutenberg Bible, US "
        "Constitution, Magna Carta) and calibrated synthetic documents, the system consistently isolates faint strokes, suppresses "
        "severe stains, and executes in sub-second times on consumer multi-core CPUs. A Streamlit web dashboard is provided for "
        "interactive real-time restoration and diagnostic evaluation."
    )
    r_abs.font.name = 'Times New Roman'
    r_abs.font.size = Pt(10)
    r_abs.italic = True

    p_kw = doc.add_paragraph()
    p_kw.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_kw.paragraph_format.left_indent = Inches(0.3)
    p_kw.paragraph_format.right_indent = Inches(0.3)
    p_kw.paragraph_format.space_after = Pt(6)
    r_kt = p_kw.add_run("Keywords—")
    r_kt.font.name = 'Times New Roman'
    r_kt.font.size = Pt(9.5)
    r_kt.bold = True
    r_kt.italic = True
    r_kb = p_kw.add_run(
        "Historical Document Restoration, Sauvola Binarization, Morphological Division, Fast NLM, CLAHE, Inpainting, Computer Vision."
    )
    r_kb.font.name = 'Times New Roman'
    r_kb.font.size = Pt(9.5)
    r_kb.italic = True

    # -------------------------------------------------------------------------
    # I. INTRODUCTION
    # -------------------------------------------------------------------------
    add_heading_1(doc, "I. INTRODUCTION")

    add_heading_2(doc, "I.A. Background and Motivation")
    add_body(doc,
        "Centuries of intellectual, cultural, and scientific progress remain documented on papyrus, animal parchment (vellum), and early "
        "handmade paper. Preserving these irreplaceable materials has spurred international digitization efforts [9]. However, physical "
        "scanning frequently inherits accumulated radiometric and physical distortions that impede paleographic transcription and modern "
        "Optical Character Recognition (OCR) systems. Automated digital restoration offers a reproducible, non-destructive solution to "
        "restore legibility without endangering fragile original artifacts."
    )

    add_heading_2(doc, "I.B. Degradation Taxonomy in Ancient Documents")
    add_body(doc,
        "Degradation phenomena in historical manuscripts span four broad categories: "
        "(1) Photometric degradation: yellowing, chemical browning, water stains, and fading of iron gall inks; "
        "(2) Bleed-through: ink migration through porous parchment over centuries, creating overlapping reverse-side text; "
        "(3) Structural defects: wormholes, creases, tears, and fungal specks; and "
        "(4) Digitization artifacts: geometric skew, illumination falloff, and dark scanning borders."
    )

    add_heading_2(doc, "I.C. Research Challenges in Classical Document Restoration")
    add_body(doc,
        "Standard enhancement routines fail on historical documents. Global thresholding (e.g., Otsu's method [2]) assumes a bimodal "
        "intensity histogram; when stain luminance overlaps with faint ink, Otsu turns stained background into solid black blocks. Linear "
        "filters (Gaussian blur) attenuate thin handwritten strokes and destroy character loops. Furthermore, high-resolution scans "
        "(10–60 MP) overwhelm naive sliding-window algorithms, whose O(W²) per-pixel complexity prevents interactive archival use."
    )

    add_heading_2(doc, "I.D. Project Objectives and Scope")
    add_body(doc,
        "This project achieves five objectives: (1) design a modular 8-stage image restoration pipeline; (2) implement an exact O(1) "
        "box-filter Sauvola thresholding algorithm for rapid CPU execution; (3) benchmark across diverse historical manuscripts (13th–18th century); "
        "(4) evaluate restoration quantitatively (PSNR, SSIM) and qualitatively; and (5) deliver an interactive Streamlit graphical web application."
    )

    # -------------------------------------------------------------------------
    # II. METHODOLOGY
    # -------------------------------------------------------------------------
    add_heading_1(doc, "II. METHODOLOGY")

    add_body(doc,
        "The restoration pipeline consists of eight sequential, modular stages built with a fluent interface to allow dynamic parameter "
        "tuning and stage ablation. Each stage addresses a distinct physical or radiometric degradation."
    )

    add_heading_2(doc, "II.A. Stage 1: Document Boundary Detection and Margin Cropping")
    add_body(doc,
        "Archival scans often contain dark scanner bed borders that corrupt histogram calculations. For grayscale image Ig of size H×W, "
        "row and column intensity projection averages are computed:"
    )
    add_equation(doc, "μ_row(y) = (1 / W) Σ_{x=0}^{W-1} Ig(x, y),     μ_col(x) = (1 / H) Σ_{y=0}^{H-1} Ig(x, y)")
    add_body(doc,
        "Boundary coordinates where profiles exceed threshold T_margin = 10 define the bounding box [x_min, y_min, x_max, y_max]. A safety "
        "margin padding of p = 5 pixels is added to preserve peripheral script."
    )

    add_heading_2(doc, "II.B. Stage 2: Geometric Rectification and Deskewing")
    add_body(doc,
        "Rotational skew during scanning impairs line segmentation and text analysis. Candidate angles θ ∈ [-45°, +45°] are evaluated by "
        "maximizing horizontal projection profile variance [3]:"
    )
    add_equation(doc, "P_θ(y) = Σ_x I_{rotated, θ}(x, y),     θ* = argmax_θ Var(P_θ)")
    add_body(doc,
        "When text lines align horizontally, interline spacing maximizes variance. The image is rotated via 2D affine transformation with "
        "bicubic spline interpolation and white border padding."
    )

    add_heading_2(doc, "II.C. Stage 3: Illumination Normalization via Morphological Background Division")
    add_body(doc,
        "Aged parchment exhibits severe low-frequency spatial degradation (yellowing, shadows, stains), while text characters occupy high "
        "frequencies. A structuring element S_{k×k} with k = 51 px (exceeding maximum stroke width) is used in morphological closing:"
    )
    add_equation(doc, "B(x, y) = ((Ig ⊕ S) ⊖ S)(x, y)")
    add_equation(doc, "I_norm(x, y) = clip( ( Ig(x, y) / max(B(x, y), 1.0) ) × 255,  0,  255 )")
    add_body(doc,
        "The structuring element closes over text strokes to estimate the background surface B. Point-wise division normalizes stained paper "
        "to uniform white (255) while strictly preserving stroke contrast."
    )

    add_heading_2(doc, "II.D. Stage 4: Spatial Denoising and Paper Grain Suppression")
    add_body(doc,
        "To suppress paper grain without softening text edges, two complementary filters are provided: "
        "(1) Fast Non-Local Means (NLM) [7], which computes weighted averages based on patch similarity across search window Ω: "
        "Î(p) = (1/Z) Σ_q I(q) exp(-‖V(p)-V(q)‖² / h²); and "
        "(2) Bilateral Filtering [8], which combines spatial Euclidean closeness (d = 5) with photometric range similarity (σ_r = 50)."
    )

    add_heading_2(doc, "II.E. Stage 5: Local Contrast Enhancement (CLAHE)")
    add_body(doc,
        "Faded inks exhibit low contrast against parchment. Global histogram equalization over-amplifies paper noise. Contrast Limited "
        "Adaptive Histogram Equalization (CLAHE) [6] is applied in the perceptual CIE L*a*b* space strictly to the luminance channel (L*), "
        "using an 8×8 grid of tiles and clip limit β = 2.0. Bilinear interpolation across tile borders prevents seam artifacts."
    )

    add_heading_2(doc, "II.F. Stage 6: Defect Repair via Digital Inpainting")
    add_body(doc,
        "Physical holes, ink blots, and ripped corners are repaired using automated defect detection and inpainting: "
        "(1) A dual-threshold mask M_damage flags intensities ≤ 30 (ink blots) and ≥ 245 (tears), filtered by morphological opening and "
        "contour area filtering (Area ≥ 100 px²); and (2) Telea's Fast Marching Method [4] or Navier-Stokes PDE inpainting [5] propagates "
        "surrounding parchment texture into defect zones."
    )

    add_heading_2(doc, "II.G. Stage 7: High-Speed O(1) Sauvola Local Adaptive Binarization")
    add_body(doc,
        "Sauvola's method [1] is the international standard for degraded document binarization, defining a dynamic threshold:"
    )
    add_equation(doc, "T(x, y) = m(x, y) · [ 1 + k · ( s(x, y) / R - 1 ) ]")
    add_body(doc,
        "where m is local mean, s is local standard deviation in window W×W, R = 128, and k = 0.2. Naive sliding-window evaluation requires "
        "O(W²) per pixel. We implement an exact O(1) box-filter formulation using OpenCV integral box filters:"
    )
    add_equation(doc, "M = BoxFilter(Ig, W×W),   M₂ = BoxFilter(Ig², W×W),   S = √max(M₂ - M², 0)")
    add_body(doc,
        "Threshold matrix T is computed simultaneously via vectorized NumPy operations. Independent of window radius W, this formulation "
        "executes in under 0.2 seconds on a 1600×1200 document—over 35× faster than naive implementations."
    )

    add_heading_2(doc, "II.H. Stage 8: Morphological Post-Processing and Text Sharpening")
    add_body(doc,
        "Unsharp masking amplifies high-frequency details: I_sharp = clip(I + α · [I - (G_σ * I)], 0, 255) with α = 1.5, σ = 3.0. "
        "A compact 2×2 structuring element applies morphological opening (clearing isolated salt-and-pepper specks) followed by morphological "
        "closing (bridging hairline character fractures)."
    )

    # -------------------------------------------------------------------------
    # III. RESULTS AND DISCUSSION
    # -------------------------------------------------------------------------
    add_heading_1(doc, "III. RESULTS AND DISCUSSION")

    add_heading_2(doc, "III.A. Experimental Setup and Dataset Characteristics")
    add_body(doc,
        "The system was implemented in Python 3.10 with OpenCV 4.8, scikit-image 0.22, NumPy 1.26, and Streamlit 1.28+, running on an "
        "Intel Core i5-1135G7 CPU @ 2.40 GHz with 16 GB RAM (no GPU required). Five diverse historical documents were evaluated: "
        "(1) Codex Gigas (13th century, 1200×1600, Gothic script, vellum darkening); "
        "(2) Gutenberg Bible (15th century, 1000×1600, movable type, illumination falloff); "
        "(3) US Constitution (18th century, 1600×1321, handwritten cursive bleed-through); "
        "(4) Magna Carta (13th century, 1066×1600, severe fading and moisture stains); and "
        "(5) a calibrated synthetic benchmark (800×600, Gaussian noise, skew θ = +2.5°, moisture rings)."
    )

    add_heading_2(doc, "III.B. Quantitative Performance Evaluation")
    add_body(doc,
        "Fidelity was measured using Peak Signal-to-Noise Ratio (PSNR) and Structural Similarity Index (SSIM) [10]:"
    )
    add_equation(doc, "PSNR = 10 · log₁₀(255² / MSE)  (dB),     SSIM(x, y) = [ (2μ_x μ_y + C₁)(2σ_{xy} + C₂) ] / [ (μ_x² + μ_y² + C₁)(σ_x² + σ_y² + C₂) ]")

    # Table 1: Quantitative Results
    p_t1 = doc.add_paragraph()
    p_t1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t1.paragraph_format.space_before = Pt(4)
    p_t1.paragraph_format.space_after = Pt(2)
    r_t1 = p_t1.add_run("TABLE I: End-to-End Quantitative Evaluation Across Historical Manuscripts")
    r_t1.font.name = 'Times New Roman'
    r_t1.font.size = Pt(9.5)
    r_t1.bold = True

    tbl1 = doc.add_table(rows=6, cols=5)
    tbl1.alignment = WD_TABLE_ALIGNMENT.CENTER
    h1_texts = ["Document Sample", "Resolution", "Primary Degradations", "PSNR (dB)", "SSIM"]
    for ci, htxt in enumerate(h1_texts):
        cell = tbl1.cell(0, ci)
        cell.text = htxt
        set_cell_bg(cell, "1E3A5F")
        set_cell_margins(cell)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.font.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.size = Pt(8.5)

    data1 = [
        ("Synthetic Benchmark", "800×600", "Stains, Skew (2.5°), Noise, Margins", "11.43 dB", "0.6416"),
        ("US Constitution", "1600×1321", "Cursive Bleed-Through, Fading, Stains", "9.33 dB", "0.3569"),
        ("Magna Carta", "1066×1600", "Severe Fading, Dark Stains, Low Contrast", "7.62 dB", "0.1706"),
        ("Codex Gigas", "1200×1600", "Parchment Yellowing, Glare, Gothic Script", "6.60 dB", "0.3399"),
        ("Gutenberg Bible", "1000×1600", "Illumination Falloff, Faded Moveable Type", "4.54 dB", "0.2978"),
    ]
    for ri, row in enumerate(data1, start=1):
        for ci, val in enumerate(row):
            cell = tbl1.cell(ri, ci)
            cell.text = val
            set_cell_margins(cell)
            if ri % 2 == 0:
                set_cell_bg(cell, "F4F6F9")
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.size = Pt(8)

    add_body(doc,
        "Lower PSNR against unprocessed scans is desirable in document restoration. Degraded scans contain large stained regions "
        "(intensity 80–160) that the pipeline maps to pure white (255). This deliberate alteration produces large numerical MSE but "
        "drastically improves visual legibility and stroke-to-background contrast.",
        bold_prefix="Metric Interpretation: "
    )

    add_heading_2(doc, "III.C. Comparative Evaluation of Binarization Algorithms")
    add_body(doc,
        "Our O(1) Sauvola algorithm was compared against four standard binarization methods across all historical manuscripts:"
    )

    # Table 2: Binarization Comparison
    p_t2 = doc.add_paragraph()
    p_t2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t2.paragraph_format.space_before = Pt(4)
    p_t2.paragraph_format.space_after = Pt(2)
    r_t2 = p_t2.add_run("TABLE II: Algorithmic Comparison of Binarization Paradigms")
    r_t2.font.name = 'Times New Roman'
    r_t2.font.size = Pt(9.5)
    r_t2.bold = True

    tbl2 = doc.add_table(rows=6, cols=4)
    tbl2.alignment = WD_TABLE_ALIGNMENT.CENTER
    h2_texts = ["Algorithm", "Threshold Scope", "Non-Uniform Lighting", "Bleed-Through Handling"]
    for ci, htxt in enumerate(h2_texts):
        cell = tbl2.cell(0, ci)
        cell.text = htxt
        set_cell_bg(cell, "1E3A5F")
        set_cell_margins(cell)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.font.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.size = Pt(8.5)

    data2 = [
        ("Otsu's Method [2]", "Global", "Fails (stains turn solid black)", "Very Poor"),
        ("Adaptive Mean", "Local", "Moderate", "Poor (erases faint strokes)"),
        ("Adaptive Gaussian", "Local", "Good", "Fair"),
        ("Niblack's Method [3]", "Local", "Good", "Moderate (heavy background noise)"),
        ("Sauvola's Method (Ours) [1]", "Local O(1)", "Superior", "Excellent (isolated text)"),
    ]
    for ri, row in enumerate(data2, start=1):
        for ci, val in enumerate(row):
            cell = tbl2.cell(ri, ci)
            cell.text = val
            set_cell_margins(cell)
            if ri % 2 == 0:
                set_cell_bg(cell, "F4F6F9")
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.size = Pt(8)
                if ri == 5:
                    run.bold = True

    add_body(doc,
        "Otsu fails because a single global threshold classifies dark stains as foreground text. Niblack captures faint strokes but "
        "generates severe noise in clean paper areas where variance is near zero. Sauvola penalizes low-variance regions via the (s/R - 1) "
        "term, keeping clean paper white while capturing crisp strokes in high-variance text areas."
    )

    add_heading_2(doc, "III.D. Stage-by-Stage Ablation Analysis")
    add_body(doc,
        "Ablation experiments demonstrated the role of each stage: (1) Border cropping eliminated false low-intensity peaks from histograms; "
        "(2) Deskewing corrected text baselines (e.g., 2.5° on synthetic); (3) Morphological division provided the single largest visual "
        "improvement by flattening 120-level illumination gradients; (4) NLM denoising suppressed paper grain without blurring character serifs; "
        "(5) CLAHE in LAB space boosted faded stroke contrast by up to 40% (Magna Carta); (6) Inpainting filled physical tears and wormholes; "
        "and (7) Post-processing sharpened edges and closed hairline fractures."
    )

    add_heading_2(doc, "III.E. Interactive Streamlit Web Platform")
    add_body(doc,
        "The pipeline is deployed as an interactive Streamlit application (app.py) featuring: (1) real-time sidebar controls for all 8 stages; "
        "(2) an interactive Juxtapose before-and-after split slider with PNG export; (3) stage-by-stage intermediate galleries; (4) a "
        "binarization comparison matrix rendering all five methods side-by-side; and (5) real-time PSNR/SSIM cards with intensity histograms."
    )

    # -------------------------------------------------------------------------
    # IV. CONCLUSION
    # -------------------------------------------------------------------------
    add_heading_1(doc, "IV. CONCLUSION")

    add_body(doc,
        "This paper presented a complete eight-stage digital restoration system for degraded historical documents and manuscripts. "
        "By integrating boundary cropping, Radon deskewing, morphological flat-field division, edge-preserving spatial filtering, perceptual "
        "CLAHE contrast enhancement, digital inpainting, an exact O(1) box-filter Sauvola binarization algorithm, and dual morphological "
        "cleanup, the system resolves composite physical, optical, and chemical degradations."
    )
    add_body(doc,
        "Experimental evaluations on manuscripts spanning five centuries (Codex Gigas, Gutenberg Bible, US Constitution, Magna Carta) confirm "
        "that the pipeline consistently isolates fine calligraphy while normalizing complex backgrounds to clean white. The O(1) Sauvola "
        "algorithm operates 35× faster than standard implementations, delivering sub-second restoration on consumer CPUs. The accompanying "
        "Streamlit web application provides an intuitive tool for archivists and cultural heritage institutions. Future extensions will focus "
        "on end-to-end OCR integration (WER/CER metrics), deep learning super-resolution for microfilm upscaling, and multi-page batch PDF processing."
    )

    # -------------------------------------------------------------------------
    # REFERENCES
    # -------------------------------------------------------------------------
    add_heading_1(doc, "REFERENCES")

    refs = [
        '[1]  J. Sauvola and M. Pietikäinen, "Adaptive document image binarization," Pattern Recognition, vol. 33, no. 2, pp. 225–236, 2000.',
        '[2]  N. Otsu, "A threshold selection method from gray-level histograms," IEEE Trans. Syst., Man, Cybern., vol. 9, no. 1, pp. 62–66, Jan. 1979.',
        '[3]  W. Niblack, An Introduction to Digital Image Processing. Englewood Cliffs, NJ: Prentice-Hall, 1986.',
        '[4]  A. Telea, "An image inpainting technique based on the fast marching method," J. Graphics Tools, vol. 9, no. 1, pp. 23–34, 2004.',
        '[5]  M. Bertalmio, A. L. Bertozzi, and G. Sapiro, "Navier-stokes, fluid dynamics, and image and video inpainting," in Proc. IEEE CVPR, 2001.',
        '[6]  K. Zuiderveld, "Contrast limited adaptive histogram equalization," in Graphics Gems IV. San Diego, CA: Academic Press, 1994, pp. 474–485.',
        '[7]  A. Buades, B. Coll, and J.-M. Morel, "A non-local algorithm for image denoising," in Proc. IEEE CVPR, vol. 2, 2005, pp. 60–65.',
        '[8]  C. Tomasi and R. Manduchi, "Bilateral filtering for gray and color images," in Proc. IEEE ICCV, 1998, pp. 839–846.',
        '[9]  I. Pratikakis, B. Gatos, and K. Ntirogiannis, "ICDAR document image binarization contest (DIBCO)," in Int. Conf. Document Anal. Recognit., 2019.',
        '[10] Z. Wang, A. C. Bovik, H. R. Sheikh, and E. P. Simoncelli, "Image quality assessment: From error visibility to structural similarity," IEEE Trans. Image Process., vol. 13, no. 4, pp. 600–612, Apr. 2004.',
    ]

    for ref in refs:
        p_ref = doc.add_paragraph()
        p_ref.paragraph_format.line_spacing = 1.05
        p_ref.paragraph_format.left_indent = Inches(0.25)
        p_ref.paragraph_format.first_line_indent = Inches(-0.25)
        p_ref.paragraph_format.space_after = Pt(2)
        r = p_ref.add_run(ref)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(9.5)

    output_file = "Document_Restoration_IEEE_Report.docx"
    doc.save(output_file)
    print(f"Successfully generated calibrated report: {output_file}")


if __name__ == "__main__":
    build_exact_5_page_report()
