"""Step 1: write raw pypdf text per order PDF, one file per order.

Usage (from the repo root):
  uv run -q --with pypdf --with pymupdf python -I data/scripts/extract.py
Output: data/text/<order>.txt with '=== page N' markers before each page.
No cleaning happens here.
"""
import glob
import os
from pathlib import Path

from pypdf import PdfReader

DATA = Path(__file__).resolve().parents[1]
pdf_dir, out_dir = DATA / "originals" / "orders", DATA / "text"
os.makedirs(out_dir, exist_ok=True)
ok = 0
paths = sorted(glob.glob(os.path.join(pdf_dir, "*.pdf")))
for path in paths:
    name = os.path.basename(path)
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages, 1):
        try:
            text = page.extract_text() or ""
        except Exception as e:  # keep going; the verifier looks for this marker
            text = f"[[EXTRACT_ERROR page {i}: {type(e).__name__}]]"
        pages.append(text)
    with open(os.path.join(out_dir, name[:-4] + ".txt"), "w", encoding="utf-8") as f:
        for i, text in enumerate(pages, 1):
            f.write(f"=== page {i}\n{text}\n")
    ok += 1
print(ok, "of", len(paths), "files written to data/text")
