"""PDF text and metadata extraction using PyMuPDF."""

import base64
import logging
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract text, metadata, and render pages from PDF files."""

    def extract_metadata(self, pdf_path: str) -> dict:
        """Extract basic PDF metadata."""
        doc = fitz.open(pdf_path)
        meta = doc.metadata or {}
        result = {
            "page_count": len(doc),
            "title": meta.get("title", ""),
            "author": meta.get("author", ""),
            "subject": meta.get("subject", ""),
            "creator": meta.get("creator", ""),
            "creation_date": meta.get("creationDate", ""),
            "mod_date": meta.get("modDate", ""),
        }
        doc.close()
        return result

    def extract_text_per_page(self, pdf_path: str) -> list[dict]:
        """Extract text from each page. Returns list of {page_number, text, has_text}."""
        doc = fitz.open(pdf_path)
        pages = []
        for i, page in enumerate(doc):
            text = page.get_text("text").strip()
            pages.append({
                "page_number": i + 1,
                "text": text,
                "has_text": len(text) > 50,  # Threshold for "has meaningful text"
                "width": page.rect.width,
                "height": page.rect.height,
            })
        doc.close()
        return pages

    def render_page_to_png(self, pdf_path: str, page_number: int,
                           output_path: str, dpi: int = 150) -> str:
        """Render a specific page to PNG. Returns the output path."""
        doc = fitz.open(pdf_path)
        page = doc[page_number - 1]  # 0-indexed
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        pix.save(output_path)
        doc.close()
        return output_path

    def render_page_to_base64(self, pdf_path: str, page_number: int,
                               dpi: int = 150) -> str:
        """Render page to base64 PNG for VLM input."""
        doc = fitz.open(pdf_path)
        page = doc[page_number - 1]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        doc.close()
        return base64.b64encode(img_bytes).decode("utf-8")

    def render_all_pages(self, pdf_path: str, output_dir: str,
                         dpi: int = 150) -> list[str]:
        """Render all pages to PNG files. Returns list of output paths."""
        doc = fitz.open(pdf_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for i in range(len(doc)):
            out_path = str(output_dir / f"page_{i + 1}.png")
            page = doc[i]
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)
            pix.save(out_path)
            paths.append(out_path)
        doc.close()
        return paths


pdf_extractor = PDFExtractor()
