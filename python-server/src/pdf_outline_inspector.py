"""
PDF Outline/Bookmark Inspector

This script extracts the table of contents (bookmarks/outlines) from a PDF
to understand its structure. This information can be used to split batches
at chapter boundaries instead of arbitrary page counts.

Uses PyMuPDF (fitz) for accurate page numbers and outline extraction.
"""

import logging
from pathlib import Path
from typing import Any

import fitz  # pymupdf

_log = logging.getLogger(__name__)


def extract_outline(pdf_path: Path) -> list[dict[str, Any]]:
    """
    Extract PDF outline/bookmarks using PyMuPDF (fitz).

    Returns a flat list of outline items with:
    - title: Bookmark title
    - page: Page number (1-indexed to match Docling)
    - level: Nesting level (0 = top level)
    """
    outline_items = []

    with fitz.open(pdf_path) as doc:
      toc = doc.get_toc()  # Returns [[level, title, page], ...]

      if not toc:
          _log.warning("PDF has no table of contents")
          doc.close()
          return outline_items

      for level, title, page in toc:
          outline_items.append({
              'title': title,
              'page': page,  # PyMuPDF uses 1-indexed pages (matches Docling!)
              'level': level - 1  # Convert to 0-indexed levels for consistency
          })
      return outline_items


def get_pdf_page_count(pdf_path: Path) -> int:
    """
    Get the total number of pages in a PDF using PyMuPDF.

    This is a lightweight operation that only reads PDF metadata.
    """
    with fitz.open(pdf_path) as doc:
      page_count = doc.page_count
      return page_count


def get_top_level_chapters(outline_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Extract top-level chapters from outline items.

    Tries level 0 first (top-level), falls back to level 1 if none found.
    Returns chapters sorted by page number.

    Args:
        outline_items: List of outline items with 'level' and 'page' keys

    Returns:
        List of chapter items sorted by page number, or empty list if none found
    """
    chapters = [item for item in outline_items if item['level'] == 0 and item['page'] is not None]

    if not chapters:
        _log.info("No top-level chapters found, trying level 1")
        chapters = [item for item in outline_items if item['level'] == 1 and item['page'] is not None]

    return sorted(chapters, key=lambda x: x['page'])


def analyze_outline_for_batching(outline_items: list[dict[str, Any]], total_pages: int, max_batch_size: int) -> list[tuple[int, int, str]]:
    """
    Analyze outline to create smart batch boundaries.

    Args:
        outline_items: List of outline items from extract_outline_*
        total_pages: Total number of pages in PDF
        max_batch_size: Maximum pages per batch (based on RAM)

    Returns:
        List of (start_page, end_page, description) tuples
    """
    if not outline_items:
        _log.info("No outline available, falling back to fixed batch size")
        return []

    chapters = get_top_level_chapters(outline_items)

    if not chapters:
        _log.warning("No usable chapters found in outline")
        return []

    # Create batches based on chapters
    batches = []
    current_start = 1
    current_chapters = []

    for i, chapter in enumerate(chapters):
        chapter_start = chapter['page']

        # Determine chapter end (start of next chapter or end of PDF)
        if i + 1 < len(chapters):
            chapter_end = chapters[i + 1]['page'] - 1
        else:
            chapter_end = total_pages

        chapter_size = chapter_end - chapter_start + 1

        # If this chapter alone exceeds max batch size, split it
        if chapter_size > max_batch_size:
            # Finalise any pending batch first
            if current_chapters:
                prev_end = chapter_start - 1
                desc = " + ".join(c['title'] for c in current_chapters)
                batches.append((current_start, prev_end, desc))
                current_chapters = []

            # Split large chapter into fixed-size batches
            _log.info(f"Chapter '{chapter['title']}' is {chapter_size} pages, splitting into sub-batches")
            for sub_start in range(chapter_start, chapter_end + 1, max_batch_size):
                sub_end = min(sub_start + max_batch_size - 1, chapter_end)
                batches.append((sub_start, sub_end, f"{chapter['title']} (part)"))

            current_start = chapter_end + 1
            continue

        # Check if adding this chapter would exceed max batch size
        current_size = (chapter_end - current_start + 1)

        if current_size > max_batch_size:
            # Finalise current batch without this chapter
            prev_end = chapter_start - 1
            desc = " + ".join(c['title'] for c in current_chapters)
            batches.append((current_start, prev_end, desc))

            # Start new batch with this chapter
            current_start = chapter_start
            current_chapters = [chapter]
        else:
            # Add chapter to current batch
            current_chapters.append(chapter)

    # Finalize last batch
    if current_chapters:
        desc = " + ".join(c['title'] for c in current_chapters)
        batches.append((current_start, total_pages, desc))

    return batches


def inspect_pdf_outline(pdf_path: Path) -> dict[str, Any]:
    """
    Inspect PDF outline and provide detailed information.

    Returns dict with:
    - outline_items: Full outline structure
    - chapters: Top-level chapters with page ranges
    - has_outline: Whether PDF has usable outline
    """
    _log.info(f"Inspecting outline for: {pdf_path.name}")

    # Extract outline using PyMuPDF
    outline_items = extract_outline(pdf_path)

    if not outline_items:
        return {
            'has_outline': False,
            'outline_items': [],
            'chapters': []
        }

    # Get total pages
    total_pages = get_pdf_page_count(pdf_path)

    # Extract chapter information using helper function
    top_level = get_top_level_chapters(outline_items)
    chapters = []

    for i, chapter in enumerate(top_level):
        start = chapter['page']
        end = top_level[i + 1]['page'] - 1 if i + 1 < len(top_level) else total_pages
        pages = end - start + 1

        chapters.append({
            'title': chapter['title'],
            'start_page': start,
            'end_page': end,
            'num_pages': pages
        })

    return {
        'has_outline': True,
        'outline_items': outline_items,
        'chapters': chapters
    }