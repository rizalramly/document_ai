"""Structure-aware text chunking for documents."""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TextChunker:
    """Split text into semantically meaningful chunks."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str, page_number: Optional[int] = None) -> list[dict]:
        """Split text into chunks, trying to respect section boundaries.

        Returns list of {chunk_text, start_char, end_char, page_number}.
        """
        if not text or len(text.strip()) < 20:
            return []

        # Try structure-aware splitting first
        sections = self._split_by_headings(text)

        if len(sections) > 1:
            chunks = []
            for section in sections:
                sub_chunks = self._split_by_size(section["text"], section["start"])
                for sc in sub_chunks:
                    sc["page_number"] = page_number
                chunks.extend(sub_chunks)
            return chunks
        else:
            # Fall back to paragraph/size-based splitting
            chunks = self._split_by_size(text, 0)
            for c in chunks:
                c["page_number"] = page_number
            return chunks

    def _split_by_headings(self, text: str) -> list[dict]:
        """Split text by heading patterns (numbered sections, CAPS headings)."""
        heading_patterns = [
            r'^#{1,4}\s+.+',                           # Markdown headings
            r'^\d+\.\d*\s+[A-Z]',                      # Numbered sections (1.1 Title)
            r'^[A-Z][A-Z\s]{5,}$',                      # ALL CAPS lines (likely headings)
            r'^(?:SECTION|CHAPTER|PART)\s+\d+',         # Section/Chapter markers
        ]
        combined = '|'.join(f'({p})' for p in heading_patterns)

        sections = []
        last_start = 0
        for match in re.finditer(combined, text, re.MULTILINE):
            if match.start() > last_start:
                section_text = text[last_start:match.start()].strip()
                if section_text:
                    sections.append({"text": section_text, "start": last_start})
            last_start = match.start()

        # Add remaining text
        remaining = text[last_start:].strip()
        if remaining:
            sections.append({"text": remaining, "start": last_start})

        return sections if len(sections) > 1 else [{"text": text, "start": 0}]

    def _split_by_size(self, text: str, offset: int = 0) -> list[dict]:
        """Split text into chunks of roughly chunk_size words with overlap."""
        words = text.split()
        if len(words) <= self.chunk_size:
            return [{
                "chunk_text": text.strip(),
                "start_char": offset,
                "end_char": offset + len(text),
            }]

        chunks = []
        i = 0
        while i < len(words):
            end = min(i + self.chunk_size, len(words))
            chunk_words = words[i:end]
            chunk_text = " ".join(chunk_words)

            # Calculate char positions approximately
            start_char = offset + text.find(chunk_words[0], sum(len(w) + 1 for w in words[:i]))
            chunks.append({
                "chunk_text": chunk_text,
                "start_char": start_char,
                "end_char": start_char + len(chunk_text),
            })

            i += self.chunk_size - self.chunk_overlap

        return chunks


text_chunker = TextChunker()
