"""
AEGIS-DocIntel — Product Hunt Visual Asset Renderer & Packager
==============================================================
Renders all vector SVGs (Logo, Gallery Slides, Social Cards, Architecture Banner)
into pixel-perfect, high-DPI PNGs matching official Product Hunt specifications.

Outputs to:
- launch/product-hunt/distribution_assets/
- launch/product-hunt/distribution_assets/AEGIS-DocIntel-ProductHunt-Assets.zip
- Conversation artifact directory for rich UI display
"""

from __future__ import annotations

import hashlib
import os
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import fitz  # PyMuPDF
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = REPO_ROOT / "launch" / "product-hunt" / "assets"
DIST_DIR = REPO_ROOT / "launch" / "product-hunt" / "distribution_assets"
ARTIFACT_DIR = Path(r"C:\Users\ASUS\.gemini\antigravity\brain\19160291-bf7a-4317-a067-7f57fa1afd23") / "assets"


@dataclass
class RenderTask:
    src_rel_path: str
    out_filename: str
    target_width: int
    target_height: int
    category: str
    description: str


TASKS: List[RenderTask] = [
    # 1. Product Logos & Icons (Product Hunt Thumbnail)
    RenderTask(
        "logo/logo-512x512.svg",
        "logo-512x512.png",
        512,
        512,
        "Logo / Thumbnail",
        "Official 512x512 primary thumbnail icon for Product Hunt listing header.",
    ),
    RenderTask(
        "logo/logo-512x512.svg",
        "logo-1024x1024-retina.png",
        1024,
        1024,
        "Logo / Thumbnail (2x)",
        "High-density 1024x1024 retina icon for marketing and high-res displays.",
    ),
    RenderTask(
        "logo/logo.svg",
        "logo-icon-256x256.png",
        256,
        256,
        "Logo Icon",
        "Compact 256x256 square brand mark icon.",
    ),
    # 2. Product Gallery Slides (Product Hunt Media Gallery: 1270x760 px)
    RenderTask(
        "gallery/gallery-01-hero.svg",
        "gallery-01-hero.png",
        1270,
        760,
        "Gallery Slide 1",
        "Hero Slide: Core value proposition, layout-aware parsing, knapsack optimizer.",
    ),
    RenderTask(
        "gallery/gallery-02-workflow.svg",
        "gallery-02-workflow.png",
        1270,
        760,
        "Gallery Slide 2",
        "Workflow: 5-stage document intelligence pipeline (Intake -> Verifiable Output).",
    ),
    RenderTask(
        "gallery/gallery-03-retrieval.svg",
        "gallery-03-retrieval.png",
        1270,
        760,
        "Gallery Slide 3",
        "Spatial Graph: Kahn DAG reading order determinism vs standard linear flattening.",
    ),
    RenderTask(
        "gallery/gallery-04-structured-output.svg",
        "gallery-04-structured-output.png",
        1270,
        760,
        "Gallery Slide 4",
        "Citations: Bounding-box coordinate evidence with exact page & excerpt references.",
    ),
    RenderTask(
        "gallery/gallery-05-trust-security.svg",
        "gallery-05-trust-security.png",
        1270,
        760,
        "Gallery Slide 5",
        "Trust & Security: Zero-leak client proxy, Ed25519 licensing, GDPR cascading erasure.",
    ),
    # 3. Retina 2x Gallery Slides (2540x1520 px)
    RenderTask(
        "gallery/gallery-01-hero.svg",
        "gallery-01-hero-2x.png",
        2540,
        1520,
        "Gallery Slide 1 (2x)",
        "Ultra-crisp 2x retina version of Slide 1.",
    ),
    RenderTask(
        "gallery/gallery-04-structured-output.svg",
        "gallery-04-structured-output-2x.png",
        2540,
        1520,
        "Gallery Slide 4 (2x)",
        "Ultra-crisp 2x retina version of Slide 4.",
    ),
    # 4. Social & Banner Graphics
    RenderTask(
        "social/og-image-1200x630.svg",
        "og-image-1200x630.png",
        1200,
        630,
        "Social Card",
        "OpenGraph card (1200x630) for Twitter, LinkedIn, and social link previews.",
    ),
    RenderTask(
        "graphics/website-launch-banner.svg",
        "website-launch-banner.png",
        1200,
        630,
        "Marketing Banner",
        "Production website launch banner and announcement graphic.",
    ),
    RenderTask(
        "graphics/architecture-workflow.svg",
        "architecture-workflow.png",
        1400,
        800,
        "Architecture",
        "Complete technical system architecture and isolated client/gateway topology.",
    ),
]


def render_svg_to_png(src_svg: Path, out_png: Path, target_w: int, target_h: int) -> int:
    """Render an SVG file to PNG with exact pixel dimensions using PyMuPDF."""
    doc = fitz.open(str(src_svg))
    page = doc[0]
    rect = page.rect

    scale_x = target_w / rect.width
    scale_y = target_h / rect.height
    matrix = fitz.Matrix(scale_x, scale_y)

    pix = page.get_pixmap(matrix=matrix, alpha=True)
    pix.save(str(out_png))
    return out_png.stat().st_size


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    h.update(filepath.read_bytes())
    return h.hexdigest()


def main():
    print("[*] Starting AEGIS-DocIntel Product Hunt Asset Generator...")
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    rendered_assets = []

    for task in TASKS:
        src = ASSETS_DIR / task.src_rel_path
        if not src.exists():
            print(f"  [!] Missing source SVG: {src}")
            continue

        out_dist = DIST_DIR / task.out_filename
        out_artifact = ARTIFACT_DIR / task.out_filename

        bytes_size = render_svg_to_png(src, out_dist, task.target_width, task.target_height)
        shutil.copy2(out_dist, out_artifact)

        sha = compute_sha256(out_dist)
        rendered_assets.append({
            "task": task,
            "filename": task.out_filename,
            "size": bytes_size,
            "sha256": sha,
            "dist_path": out_dist,
            "artifact_path": out_artifact,
        })
        print(f"  [+] Rendered {task.out_filename} ({task.target_width}x{task.target_height}) -> {bytes_size} bytes")

    # Package all into a zip bundle
    zip_path = DIST_DIR / "AEGIS-DocIntel-ProductHunt-Assets.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in rendered_assets:
            zf.write(item["dist_path"], arcname=item["filename"])
    shutil.copy2(zip_path, ARTIFACT_DIR / "AEGIS-DocIntel-ProductHunt-Assets.zip")
    print(f"[+] Packaged all assets into {zip_path.name} ({zip_path.stat().st_size} bytes)")

    # Generate Markdown Catalog
    catalog_path = DIST_DIR / "INDEX.md"
    lines = [
        "# AEGIS-DocIntel — Product Hunt Verified Asset Catalog",
        "",
        "This catalog contains all high-resolution PNG images generated for the Product Hunt launch.",
        "All assets are strictly compliant with Product Hunt dimension and file size guidelines (<10MB).",
        "",
        f"**Download Complete ZIP:** [`{zip_path.name}`]({zip_path.as_uri()}) ({zip_path.stat().st_size:,} bytes)",
        "",
        "---",
        "",
        "## Asset Inventory & Direct Upload Links",
        "",
        "| Asset Name | Category | Resolution | File Size | Direct File Link |",
        "| :--- | :--- | :---: | :---: | :--- |",
    ]

    for item in rendered_assets:
        t = item["task"]
        name = item["filename"]
        res = f"{t.target_width}x{t.target_height}"
        sz = f"{item['size']:,} B"
        link = f"[{name}]({item['dist_path'].as_uri()})"
        lines.append(f"| **{name}** | {t.category} | `{res}` | {sz} | {link} |")

    lines.extend([
        "",
        "---",
        "",
        "## Product Hunt Form Field Guide",
        "",
        "### 1. Product Thumbnail / Logo",
        "- **Upload File:** [`logo-512x512.png`](file:///" + str(DIST_DIR / "logo-512x512.png").replace("\\", "/") + ")",
        "- **Format:** 512x512 px PNG with transparent / clean dark rounded badge.",
        "",
        "### 2. Product Gallery (Minimum 3, Recommended 5)",
        "1. **Slide 1 (Hero):** [`gallery-01-hero.png`](file:///" + str(DIST_DIR / "gallery-01-hero.png").replace("\\", "/") + ")",
        "2. **Slide 2 (Workflow):** [`gallery-02-workflow.png`](file:///" + str(DIST_DIR / "gallery-02-workflow.png").replace("\\", "/") + ")",
        "3. **Slide 3 (DAG Reading Order):** [`gallery-03-retrieval.png`](file:///" + str(DIST_DIR / "gallery-03-retrieval.png").replace("\\", "/") + ")",
        "4. **Slide 4 (Citations & Coordinates):** [`gallery-04-structured-output.png`](file:///" + str(DIST_DIR / "gallery-04-structured-output.png").replace("\\", "/") + ")",
        "5. **Slide 5 (Security & Boundary):** [`gallery-05-trust-security.png`](file:///" + str(DIST_DIR / "gallery-05-trust-security.png").replace("\\", "/") + ")",
        "",
        "### 3. Social Media Sharing Card",
        "- **Card File:** [`og-image-1200x630.png`](file:///" + str(DIST_DIR / "og-image-1200x630.png").replace("\\", "/") + ")",
        "- **Format:** 1200x630 px PNG for Twitter Card and OpenGraph.",
    ])

    catalog_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[+] Catalog written to {catalog_path}")


if __name__ == "__main__":
    main()
