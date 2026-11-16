---
name: academic-figure-studio
description: Assemble microscopy and other scientific images into academic figures with metadata-footer cropping, calibrated scale bars, interactive canvas layouts, and linked zoom insets. Use for academic figure preparation for papers or slides.
---

# Academic Figure Studio

The plugin exposes the academic figure workbench through Codex's embedded browser surface when available. The plugin root is two directories above this file. Start its local renderer with `sh <plugin-root>/scripts/launch.sh --port 8765` using a persistent terminal. First check `http://127.0.0.1:8765/api/health`; reuse it only if its `name` is `Academic Figure Studio`, otherwise use an available port. Open the selected localhost URL in the embedded Codex browser panel and keep the workbench in that plugin surface; if panel control is unavailable, provide the URL and explain that the embedded panel could not be opened.

The editor supports automatic TIFF physical-pixel calibration, multi-file import, crop-line adjustment, two-point scale calibration, canvas dragging/resizing, grid layouts, ROI selection, connected insets, local autosave, portable `.figstudio` project files, and PNG/TIFF/PDF/SVG/PPTX exports. Importing a project restores its original image bytes and all calibration/ROI settings.

If runtime dependencies are missing, run `npm ci` at the plugin root and install `requirements.txt` into a virtual environment. The launcher can use the Codex bundled Python runtime. `FIGURE_PYTHON` selects another Python. `FIGURE_FONT_PATH` selects a Source Han Sans OTF file; by default it uses `~/Library/Fonts/SourceHanSansCN-Regular.otf`. Optional local Tesseract OCR supplies scale candidates; manual calibration remains available without it.

## Scientific invariants

- Retain original files. Footer removal is a reversible crop, not inpainting. Do not use image generation to alter scientific images.
- Footer detection is heuristic. Inspect the proposed crop line, especially on images with large black/white regions or an embedded information overlay.
- Automatically use recognized TIFF specimen-space metadata for calibration and scale bars; do not require manual confirmation for a valid metadata calibration. Display its source. If metadata is absent, invalid, conflicting, or unsupported, use the full uncropped original (including the instrument scale bar) for manual two-point calibration. Never treat ordinary print DPI as specimen calibration. Manual calibration requires a physical length and corresponding original-image pixel distance. Do not infer it solely from magnification, image DPI, or screen size. OCR suggestions require user verification. If the user supplies a verified nm/px value, it may be entered directly.
- All insets derive from original source pixels and inherit their source calibration. Scale bar display length equals physical length / nm-per-source-pixel × display-width / source-crop-width. Preserve image aspect ratios.
- Scale bars and their labels have a contrasting outline by default; preserve this in all exported formats. Use Source Han Sans for generated annotations. PDF exports embed the font. PPTX keeps annotations editable and refers to the installed Source Han Sans CN font. Native text within original instrument images remains unchanged.
- The demo uses explicitly marked synthetic textures for interface testing; never represent it as experimental data.

## Working with the user

Help import images and explain the shortest relevant workflow: verify crop → use TIFF metadata or manually calibrate on the full original → arrange → select ROI → export. Use the UI for freehand selections. Do not invent region coordinates when the scientific feature of interest is unspecified; let the user select it. For known coordinates, preserve their reference to source image pixels.
While dragging a panel, edge alignment guides appear against other panels and positions within the snap threshold lock to the matched edge. Horizontal and vertical snapping are evaluated independently.

The application binds to loopback only. It writes original images to `.sem-data/` under the plugin root and autosaves project state in the browser. Do not claim it is published or installed into Codex merely because the local plugin package exists. See the root `README.md` for launch and plugin installation options.
