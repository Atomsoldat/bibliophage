"""Docling-based PDF processing pipeline.

This module isolates all Docling-specific code for PDF processing.
The service layer should only interact with this module's public API,
allowing easy replacement of the PDF processing backend.
"""

import gc
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TypedDict

from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import ConversionStatus, InputFormat
from docling.datamodel.pipeline_options import ThreadedPdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from ingestion.batch_size_calculator import calculate_batch_size
from ingestion.pdf_outline_inspector import (
    analyze_outline_for_batching,
    get_pdf_page_count,
    inspect_pdf_outline,
)

logger = logging.getLogger(__name__)


class BatchInfo(TypedDict):
    """Information about a processed batch."""

    batch_number: int
    start_page: int
    end_page: int
    description: str
    status: str
    success: bool


class PdfProcessingResult(TypedDict):
    """Result of PDF processing."""

    content: str
    total_pages: int
    processed_batches: list[BatchInfo]
    successful_batches: int
    failed_batches: int


class DoclingPipeline:
    """Encapsulates the Docling PDF processing pipeline.

    This class handles all Docling-specific logic for converting PDFs to markdown,
    including batch processing, memory management, and smart batching based on
    PDF structure.
    """

    def __init__(
        self,
        ocr_batch_size: int = 4,
        layout_batch_size: int = 64,
        table_batch_size: int = 4,
        do_ocr: bool = False,
    ):
        """Initialize the Docling pipeline.

        Args:
            ocr_batch_size: Batch size for OCR processing
            layout_batch_size: Batch size for layout analysis
            table_batch_size: Batch size for table extraction
            do_ocr: Whether to perform OCR on the PDF

        """
        self.pipeline_options = ThreadedPdfPipelineOptions(
            accelerator_options=AcceleratorOptions(
                device=AcceleratorDevice.AUTO,
            ),
            ocr_batch_size=ocr_batch_size,
            layout_batch_size=layout_batch_size,
            table_batch_size=table_batch_size,
        )
        self.pipeline_options.do_ocr = do_ocr

    def process_pdf(
        self,
        pdf_bytes: bytes,
        pdf_name: str,
        use_smart_batching: bool = True,
        memory_per_page_mb: float = 67.8,
    ) -> PdfProcessingResult:
        """Process a PDF file and return the extracted markdown content.

        Args:
            pdf_bytes: Raw PDF file data
            pdf_name: Name of the PDF file (for logging)
            use_smart_batching: If True, try to split batches at chapter boundaries
            memory_per_page_mb: Estimated memory per page for batch size calculation

        Returns:
            PdfProcessingResult with content and metadata

        """
        logger.info(f"Processing PDF: {pdf_name}")

        # Write PDF to temporary file for processing
        with NamedTemporaryFile(delete=True, suffix=".pdf") as tmp:
            tmp.write(pdf_bytes)
            tmp.flush()
            tmp_path = Path(tmp.name)
            logger.info(f"Temporary file created: {tmp_path}")

            # Calculate optimal batch size
            logger.info("Calculating optimal batch size...")
            batch_config = calculate_batch_size(memory_per_page_mb=memory_per_page_mb)
            logger.info(f"Batch configuration: {batch_config}")
            batch_size = batch_config["recommended_batch_size"]

            # Get total page count
            logger.info(f"Reading PDF metadata from {pdf_name}...")
            total_pages = get_pdf_page_count(tmp_path)
            logger.info(f"PDF has {total_pages} pages")

            # Determine batches
            batches = self._determine_batches(
                tmp_path,
                total_pages,
                batch_size,
                use_smart_batching,
            )
            num_batches = len(batches)
            logger.info(f"Will process in {num_batches} batches")

            # Process batches
            result = self._process_batches(tmp_path, batches, total_pages)

        return result

    def _determine_batches(
        self,
        pdf_path: Path,
        total_pages: int,
        batch_size: int,
        use_smart_batching: bool,
    ) -> list[tuple[int, int, str]]:
        """Determine batch boundaries for PDF processing.

        Args:
            pdf_path: Path to the PDF file
            total_pages: Total number of pages in the PDF
            batch_size: Maximum pages per batch
            use_smart_batching: Whether to use smart batching

        Returns:
            List of (start_page, end_page, description) tuples

        """
        batches = []

        if use_smart_batching:
            logger.info("Attempting smart batching based on PDF outline...")
            try:
                outline_result = inspect_pdf_outline(pdf_path)
                if outline_result["has_outline"]:
                    batches = analyze_outline_for_batching(
                        outline_result["outline_items"],
                        total_pages,
                        batch_size,
                    )
                    if batches:
                        logger.info(
                            f"✓ Smart batching enabled: {len(batches)} chapter-based batches",
                        )
                        logger.info(
                            f"  Batch sizes range from {min(b[1] - b[0] + 1 for b in batches)} to {max(b[1] - b[0] + 1 for b in batches)} pages",
                        )
                    else:
                        logger.warning("Could not create smart batches from outline")
                else:
                    logger.info("PDF has no outline/bookmarks")
            except Exception as e:
                logger.warning(f"Smart batching failed: {e}")

        # Fall back to fixed-size batching
        if not batches:
            logger.info(f"Using fixed-size batching: {batch_size} pages per batch")
            batches = []
            for i in range(0, total_pages, batch_size):
                start = i + 1
                end = min(i + batch_size, total_pages)
                batches.append((start, end, f"Pages {start}-{end}"))

        return batches

    def _process_batches(
        self,
        pdf_path: Path,
        batches: list[tuple[int, int, str]],
        total_pages: int,
    ) -> PdfProcessingResult:
        """Process PDF batches using Docling.

        Args:
            pdf_path: Path to the PDF file
            batches: List of (start_page, end_page, description) tuples
            total_pages: Total number of pages

        Returns:
            PdfProcessingResult with content and metadata

        """
        num_batches = len(batches)

        # Initialize docling converter with pipeline options
        doc_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=self.pipeline_options,
                ),
            },
        )

        # Initialize pipeline once (reused across batches)
        doc_converter.initialize_pipeline(InputFormat.PDF)
        logger.info("Pipeline initialized")

        # Process batches and collect results
        processed_batches: list[BatchInfo] = []
        successful_batches = 0
        failed_batches = 0
        markdown_parts = []

        for batch_num, (start_page, end_page, description) in enumerate(batches):
            pages_in_batch = end_page - start_page + 1

            logger.info("=" * 60)
            logger.info(
                f"BATCH {batch_num + 1}/{num_batches}: Pages {start_page}-{end_page} ({pages_in_batch} pages)",
            )
            logger.info(f"  Content: {description}")
            logger.info("=" * 60)

            try:
                # Convert this batch of pages
                conv_result = doc_converter.convert(
                    pdf_path,
                    page_range=(start_page, end_page),
                )

                if conv_result.status != ConversionStatus.SUCCESS:
                    logger.warning(
                        f"Batch {batch_num + 1} conversion status: {conv_result.status}",
                    )
                    failed_batches += 1
                    processed_batches.append(
                        BatchInfo(
                            batch_number=batch_num + 1,
                            start_page=start_page,
                            end_page=end_page,
                            description=description,
                            status=str(conv_result.status),
                            success=False,
                        ),
                    )
                    continue

                # Export batch to markdown
                batch_markdown = conv_result.document.export_to_markdown()
                markdown_parts.append(batch_markdown)

                processed_batches.append(
                    BatchInfo(
                        batch_number=batch_num + 1,
                        start_page=start_page,
                        end_page=end_page,
                        description=description,
                        status="SUCCESS",
                        success=True,
                    ),
                )

                successful_batches += 1
                logger.info(f"Batch {batch_num + 1} complete")

                # Free memory before next batch
                del conv_result
                del batch_markdown
                gc.collect()

            except Exception as e:
                logger.error(f"Batch {batch_num + 1} failed with error: {e}")
                failed_batches += 1
                processed_batches.append(
                    BatchInfo(
                        batch_number=batch_num + 1,
                        start_page=start_page,
                        end_page=end_page,
                        description=description,
                        status="ERROR",
                        success=False,
                    ),
                )
                gc.collect()

        # Concatenate markdown from all successful batches
        concatenated_content = "\n\n".join(markdown_parts)
        logger.info(
            f"Concatenated {len(markdown_parts)} batches into {len(concatenated_content)} characters of markdown",
        )

        return PdfProcessingResult(
            content=concatenated_content,
            total_pages=total_pages,
            processed_batches=processed_batches,
            successful_batches=successful_batches,
            failed_batches=failed_batches,
        )
