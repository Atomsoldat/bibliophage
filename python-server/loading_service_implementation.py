import logging
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
import gc

from google.protobuf import timestamp_pb2
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import ConversionStatus, InputFormat
from docling.datamodel.pipeline_options import ThreadedPdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
import motor.motor_asyncio

import bibliophage.v1alpha2.pdf_pb2 as api
from config import get_settings
from batch_size_calculator import calculate_batch_size
from pdf_outline_inspector import inspect_pdf_outline, analyze_outline_for_batching, get_pdf_page_count

logger = logging.getLogger(__name__)


class LoadingServiceImplementation:
    """
    Loading service implementation using Docling for PDF processing.

    This replaces the legacy chunking approach with docling's batch-based
    PDF processing pipeline, storing full documents in FerretDB instead
    of chunked embeddings in pgvector.
    """

    def __init__(self):
        """Initialize the loading service with configuration from environment variables."""
        settings = get_settings()

        # Initialize FerretDB/MongoDB connection for document storage
        self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(str(settings.database.doc_db_url))
        # Use 'bibliophage' database and 'documents' collection
        self.db = self.mongo_client.bibliophage
        self.documents_collection = self.db.documents

        # Initialize docling pipeline options
        # TODO: Make these configurable via environment variables or request parameters
        self.pipeline_options = ThreadedPdfPipelineOptions(
            accelerator_options=AcceleratorOptions(
                device=AcceleratorDevice.CUDA,
            ),
            ocr_batch_size=4,
            layout_batch_size=64,
            table_batch_size=4,
        )
        self.pipeline_options.do_ocr = False

        logger.info("Loading service initialized with Docling pipeline and FerretDB storage")

    async def load_pdf(self, request: api.LoadPdfRequest, ctx):
        """
        Load a PDF using docling's batch processing pipeline.

        This method:
        1. Writes PDF bytes to a temporary file
        2. Calculates optimal batch size based on system memory
        3. Processes PDF pages in batches using docling's DocumentConverter
        4. Stores the full document with batches in FerretDB
        5. Returns LoadPdfResponse with metadata

        Args:
            request: LoadPdfRequest containing PDF metadata and file data
            ctx: gRPC context (unused)

        Returns:
            LoadPdfResponse with stored document metadata
        """
        try:
            logger.info(f"Received LoadPdf request for file: {request.pdf.name}")

            pdf_bytes = request.file_data

            # Write PDF to temporary file for processing
            # Using 'with' ensures cleanup after processing
            with NamedTemporaryFile(delete=True, suffix=".pdf") as tmp:
                tmp.write(pdf_bytes)
                tmp.flush()
                tmp_path = Path(tmp.name)
                logger.info(f"Temporary file created: {tmp_path}")

                # Calculate optimal batch size based on system memory
                # For table-heavy PDFs: 67.8 MB/page (default)
                # For text-heavy PDFs: use 40.0 MB/page
                # For image-heavy PDFs: use 100.0 MB/page
                logger.info("Calculating optimal batch size...")
                batch_config = calculate_batch_size(memory_per_page_mb=67.8)
                logger.info(f"Batch configuration: {batch_config}")
                batch_size = batch_config['recommended_batch_size']

                # Get total page count
                logger.info(f"Reading PDF metadata from {request.pdf.name}...")
                total_pages = get_pdf_page_count(tmp_path)
                logger.info(f"PDF has {total_pages} pages")

                # Try smart batching based on PDF outline
                # TODO: Make configurable
                batches = []
                use_smart_batching = True

                if use_smart_batching:
                    logger.info("Attempting smart batching based on PDF outline...")
                    try:
                        outline_result = inspect_pdf_outline(tmp_path)
                        if outline_result['has_outline']:
                            batches = analyze_outline_for_batching(
                                outline_result['outline_items'],
                                total_pages,
                                batch_size
                            )
                            if batches:
                                logger.info(f"✓ Smart batching enabled: {len(batches)} chapter-based batches")
                                logger.info(f"  Batch sizes range from {min(b[1]-b[0]+1 for b in batches)} to {max(b[1]-b[0]+1 for b in batches)} pages")
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

                num_batches = len(batches)
                logger.info(f"Will process in {num_batches} batches")

                # Initialize docling converter with pipeline options
                doc_converter = DocumentConverter(
                    format_options={
                        InputFormat.PDF: PdfFormatOption(
                            pipeline_options=self.pipeline_options,
                        )
                    }
                )

                # Initialize pipeline once (reused across batches)
                doc_converter.initialize_pipeline(InputFormat.PDF)
                logger.info("Pipeline initialized")

                # Process batches and collect results
                processed_batches = []
                successful_batches = 0
                failed_batches = 0

                for batch_num, (start_page, end_page, description) in enumerate(batches):
                    pages_in_batch = end_page - start_page + 1

                    logger.info("=" * 60)
                    logger.info(f"BATCH {batch_num + 1}/{num_batches}: Pages {start_page}-{end_page} ({pages_in_batch} pages)")
                    logger.info(f"  Content: {description}")
                    logger.info("=" * 60)

                    try:
                        # Convert this batch of pages
                        conv_result = doc_converter.convert(
                            tmp_path,
                            page_range=(start_page, end_page)
                        )

                        if conv_result.status != ConversionStatus.SUCCESS:
                            logger.warning(f"Batch {batch_num + 1} conversion status: {conv_result.status}")
                            failed_batches += 1
                            processed_batches.append({
                                'batch_number': batch_num + 1,
                                'start_page': start_page,
                                'end_page': end_page,
                                'description': description,
                                'status': str(conv_result.status),
                                'markdown': None,
                                'success': False
                            })
                            continue

                        # Export batch to markdown
                        batch_markdown = conv_result.document.export_to_markdown()

                        processed_batches.append({
                            'batch_number': batch_num + 1,
                            'start_page': start_page,
                            'end_page': end_page,
                            'description': description,
                            'status': 'SUCCESS',
                            'markdown': batch_markdown,
                            'success': True
                        })

                        successful_batches += 1
                        logger.info(f"Batch {batch_num + 1} complete")

                        # Free memory before next batch
                        del conv_result
                        del batch_markdown
                        gc.collect()

                    except Exception as e:
                        logger.error(f"Batch {batch_num + 1} failed with error: {e}")
                        failed_batches += 1
                        processed_batches.append({
                            'batch_number': batch_num + 1,
                            'start_page': start_page,
                            'end_page': end_page,
                            'description': description,
                            'status': 'ERROR',
                            'error': str(e),
                            'success': False
                        })
                        gc.collect()

            # Create document to store in FerretDB
            document_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)

            document = {
                '_id': document_id,
                'name': request.pdf.name,
                'system': request.pdf.system,
                'type': request.pdf.type,
                'origin_path': request.pdf.origin_path,
                'page_count': total_pages,
                'file_size': len(pdf_bytes),
                'batch_count': len(processed_batches),
                'successful_batches': successful_batches,
                'failed_batches': failed_batches,
                'batches': processed_batches,
                'batch_config': batch_config,
                'use_smart_batching': use_smart_batching,
                'created_at': now,
                'updated_at': now,
                'tags': list(request.pdf.tags) if request.pdf.tags else []
            }

            # Store document in FerretDB
            await self.documents_collection.insert_one(document)
            logger.info(f"Document stored in FerretDB with ID: {document_id}")

            # Create response matching LoadPdfResponse structure
            stored_pdf = api.Pdf()
            stored_pdf.CopyFrom(request.pdf)
            stored_pdf.id = document_id
            stored_pdf.page_count = total_pages
            # For API compatibility, set chunk_count to batch_count
            # (API expects chunk_count, but we're storing batches now)
            stored_pdf.chunk_count = len(processed_batches)
            stored_pdf.file_size = len(pdf_bytes)

            # Set timestamps
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(now)
            stored_pdf.created_at.CopyFrom(timestamp)
            stored_pdf.updated_at.CopyFrom(timestamp)

            return api.LoadPdfResponse(
                success=True,
                message=f"PDF {request.pdf.name} processed successfully ({successful_batches}/{len(processed_batches)} batches)",
                pdf=stored_pdf,
            )

        except Exception as e:
            logger.error(f"Exception in load_pdf: {e}\n{traceback.format_exc()}")
            raise

    async def search_pdfs(
        self, request: api.SearchPdfsRequest, ctx,
    ) -> api.SearchPdfsResponse:
        """
        Search for PDFs in FerretDB.

        TODO: Implement actual search functionality using MongoDB queries.
        """
        logger.info("Received SearchPdfsRequest")

        # TODO: Implement actual PDF search against FerretDB
        # Example query structure:
        # query = {}
        # if request.title_query:
        #     query['name'] = {'$regex': request.title_query, '$options': 'i'}
        # if request.system_filter:
        #     query['system'] = request.system_filter
        # if request.type_filter:
        #     query['type'] = request.type_filter
        #
        # cursor = self.documents_collection.find(query)
        # documents = await cursor.to_list(length=request.page_size)

        return api.SearchPdfsResponse(
            success=False,
            message="Search not yet implemented",
            pdfs=[],
            total_count=0,
            page_number=request.page_size if request.page_number else 0,
            has_more=False,
        )

    async def get_pdf(
        self, request: api.GetPdfRequest, ctx,
    ) -> api.GetPdfResponse:
        """
        Retrieve a specific PDF by ID from FerretDB.

        TODO: Implement actual PDF retrieval from FerretDB.
        """
        logger.info(f"Received GetPdfRequest for ID: {request.id}")

        # TODO: Implement actual PDF retrieval
        # document = await self.documents_collection.find_one({'_id': request.id})
        # if document:
        #     # Convert document to api.Pdf
        #     pass

        return api.GetPdfResponse(
            success=False,
            message="PDF retrieval not yet implemented",
        )
