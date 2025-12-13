"""
Batch-based PDF to Markdown converter using Docling

This script processes large PDFs in batches to avoid memory exhaustion
If we try to convert heavy PDFs like the PF1E Core Rulebook in one go, we can run out of RAM
It will try to determine ideal batch sizes via chapters defined in the PDF

How it works:
1. Get total page count (lightweight operation)
2. Attempt to determine chapter boundaries for clean page separation
3. Optionally fall back to fixed boundaries
4. Process batches of N pages using page_range parameter
5. Export each batch to markdown
6. Append to output file
7. Free memory before next batch
8. Repeat until all pages processed
"""

import datetime
import gc
import logging
import time
from pathlib import Path

from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import ConversionStatus, InputFormat
from docling.datamodel.pipeline_options import ThreadedPdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from batch_size_calculator import calculate_batch_size
from pdf_outline_inspector import inspect_pdf_outline, analyze_outline_for_batching, get_pdf_page_count

_log: logging.Logger = logging.getLogger(__name__)

def convert_pdf_in_batches(
    pdf_path: Path,
    output_path: Path,
    # define fallback value
    batch_size: int = 50,
    pipeline_options: ThreadedPdfPipelineOptions = None,
    use_smart_batching: bool = True
) -> dict:
    """
    Convert a large PDF to markdown in batches to avoid OOM.

    Args:
        pdf_path: Path to input PDF
        output_path: Path to output markdown file
        batch_size: Maximum number of pages to process per batch (based on RAM)
        pipeline_options: Docling pipeline options
        use_smart_batching: If True, try to split batches at chapter boundaries

    Returns:
        dict with statistics (total_pages, total_time, etc.)
    """
    # Get total page count
    _log.info(f"Reading PDF metadata from {pdf_path.name}...")
    total_pages: int = get_pdf_page_count(pdf_path)
    _log.info(f"PDF has {total_pages} pages")

    # Try smart batching first if enabled
    batches = []
    if use_smart_batching:
        _log.info("Attempting smart batching based on PDF outline...")
        try:
            outline_result = inspect_pdf_outline(pdf_path)
            if outline_result['has_outline']:
                batches = analyze_outline_for_batching(
                    outline_result['outline_items'],
                    total_pages,
                    batch_size
                )
                if batches:
                    _log.info(f"✓ Smart batching enabled: {len(batches)} chapter-based batches")
                    _log.info(f"  Batch sizes range from {min(b[1]-b[0]+1 for b in batches)} to {max(b[1]-b[0]+1 for b in batches)} pages")
                else:
                    _log.warning("Could not create smart batches from outline")
            else:
                _log.info("PDF has no outline/bookmarks")
        except Exception as e:
            _log.warning(f"Smart batching failed: {e}")

    # Fall back to fixed-size batching
    if not batches:
        _log.info(f"Using fixed-size batching: {batch_size} pages per batch")
        batches = []
        for i in range(0, total_pages, batch_size):
            start = i + 1
            end = min(i + batch_size, total_pages)
            batches.append((start, end, f"Pages {start}-{end}"))

    num_batches = len(batches)
    _log.info(f"Will process in {num_batches} batches")

    # Initialize converter with standard pipeline
    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
            )
        }
    )

    # Initialize pipeline once (reused across batches)
    init_start: float = time.time()
    doc_converter.initialize_pipeline(InputFormat.PDF)
    init_time: float = time.time() - init_start
    _log.info(f"Pipeline initialized in {init_time:.2f} seconds")

    # Statistics tracking
    stats: dict[str, int | list[Unknown]] = {
        'total_pages': total_pages,
        'processed_pages': 0,
        'successful_batches': 0,
        'failed_batches': 0,
        'total_time': 0,
        'batch_times': []
    }

    overall_start: float = time.time()

    # Open output file once, append batches as we go
    with open(output_path, 'w', encoding='utf-8') as output_file:
        # Write document header
        output_file.write(f"# {pdf_path.name}\n\n")
        output_file.write(f"Converted: {datetime.datetime.now().isoformat()}\n\n")
        output_file.write(f"Total Pages: {total_pages}\n\n")
        output_file.write(f"Maximum Batch Size: {batch_size}\n\n")
        output_file.write(f"Smart Batching: {use_smart_batching}\n\n")
        output_file.write("---\n\n")
        output_file.flush()

        # Process each batch
        for batch_num, (start_page, end_page, description) in enumerate(batches):
            pages_in_batch: int = end_page - start_page + 1

            _log.info("=" * 60)
            _log.info(f"BATCH {batch_num + 1}/{num_batches}: Pages {start_page}-{end_page} ({pages_in_batch} pages)")
            _log.info(f"  Content: {description}")
            _log.info("=" * 60)

            batch_start: float = time.time()

            try:
                # Convert ONLY this batch of pages
                # The page_range parameter is KEY to limiting memory usage!
                conv_result = doc_converter.convert(
                    pdf_path,
                    page_range=(start_page, end_page)
                )

                if conv_result.status != ConversionStatus.SUCCESS:
                    _log.warning(f"Batch {batch_num + 1} conversion status: {conv_result.status}")
                    stats['failed_batches'] += 1
                    output_file.write(f"\n<!-- BATCH {batch_num + 1} FAILED: {conv_result.status} -->\n\n")
                    output_file.flush()
                    continue

                # Export batch to markdown
                batch_markdown = conv_result.document.export_to_markdown()

                # Write batch header with description
                output_file.write(f"\n<!-- Batch {batch_num + 1}: Pages {start_page}-{end_page} - {description} -->\n\n")

                # Write batch content
                output_file.write(batch_markdown)
                output_file.write("\n\n")

                # Batch separator
                output_file.write(f"---\n\n")

                # Flush to disk immediately
                output_file.flush()

                stats['processed_pages'] += pages_in_batch
                stats['successful_batches'] += 1

                batch_time: float = time.time() - batch_start
                stats['batch_times'].append(batch_time)

                _log.info(f"Batch {batch_num + 1} complete in {batch_time:.2f} seconds")
                _log.info(f"Progress: {stats['processed_pages']}/{total_pages} pages")

                # Free memory before next batch
                del conv_result
                del batch_markdown
                gc.collect()

                _log.info("Memory freed, ready for next batch")

            except Exception as e:
                _log.error(f"Batch {batch_num + 1} failed with error: {e}")
                stats['failed_batches'] += 1
                output_file.write(f"\n<!-- BATCH {batch_num + 1} ERROR: {e} -->\n\n")
                output_file.flush()

                # Always try to free memory
                gc.collect()

    stats['total_time'] = time.time() - overall_start

    return stats
