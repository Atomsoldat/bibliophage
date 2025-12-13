"""
Integration tests for the docling_batched module.

These tests verify the batch PDF conversion functionality, including:
- Fixed-size batching
- Smart batching with chapter boundaries
- Memory management and statistics tracking
- Error handling and recovery
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from docling.datamodel.base_models import ConversionStatus
from docling.datamodel.pipeline_options import ThreadedPdfPipelineOptions

from docling_batched import convert_pdf_in_batches


class TestConvertPdfInBatches:
    """Test suite for convert_pdf_in_batches function."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_pdf_path(self):
        """Create a mock PDF path."""
        return Path("/mock/path/test.pdf")

    @pytest.fixture
    def mock_pipeline_options(self):
        """Create mock pipeline options."""
        return ThreadedPdfPipelineOptions()

    @pytest.fixture
    def mock_converter(self):
        """Create a mock DocumentConverter."""
        with patch('docling_batched.DocumentConverter') as MockConverter:
            converter_instance = MockConverter.return_value

            # Mock successful conversion result
            mock_result = Mock()
            mock_result.status = ConversionStatus.SUCCESS
            mock_result.document.export_to_markdown.return_value = "# Test Markdown\n\nContent here."

            converter_instance.convert.return_value = mock_result
            converter_instance.initialize_pipeline.return_value = None

            yield converter_instance

    def test_fixed_size_batching_basic(
        self,
        mock_pdf_path,
        temp_output_dir,
        mock_converter
    ):
        """Test basic fixed-size batching with a small PDF."""
        output_path = temp_output_dir / "output.md"

        # Mock a 10-page PDF
        with patch('docling_batched.get_pdf_page_count', return_value=10):
            with patch('docling_batched.DocumentConverter', return_value=mock_converter):
                stats = convert_pdf_in_batches(
                    pdf_path=mock_pdf_path,
                    output_path=output_path,
                    batch_size=5,
                    use_smart_batching=False
                )

        # Verify statistics
        assert stats['total_pages'] == 10
        assert stats['processed_pages'] == 10
        assert stats['successful_batches'] == 2  # 10 pages / 5 per batch
        assert stats['failed_batches'] == 0
        assert len(stats['batch_times']) == 2

        # Verify output file was created
        assert output_path.exists()

        # Verify content structure
        content = output_path.read_text()
        assert "test.pdf" in content
        assert "Total Pages: 10" in content
        assert "Maximum Batch Size: 5" in content
        assert "Smart Batching: False" in content

    def test_smart_batching_with_outline(
        self,
        mock_pdf_path,
        temp_output_dir,
        mock_converter
    ):
        """Test smart batching using PDF outline/bookmarks."""
        output_path = temp_output_dir / "output.md"

        # Mock outline data with chapters
        mock_outline_result = {
            'has_outline': True,
            'outline_items': [
                {'title': 'Chapter 1', 'page': 1},
                {'title': 'Chapter 2', 'page': 6},
                {'title': 'Chapter 3', 'page': 11},
            ]
        }

        # Mock batches from outline analysis
        mock_batches = [
            (1, 5, 'Chapter 1'),
            (6, 10, 'Chapter 2'),
            (11, 15, 'Chapter 3'),
        ]

        with patch('docling_batched.get_pdf_page_count', return_value=15):
            with patch('docling_batched.inspect_pdf_outline', return_value=mock_outline_result):
                with patch('docling_batched.analyze_outline_for_batching', return_value=mock_batches):
                    with patch('docling_batched.DocumentConverter', return_value=mock_converter):
                        stats = convert_pdf_in_batches(
                            pdf_path=mock_pdf_path,
                            output_path=output_path,
                            batch_size=10,  # Max batch size
                            use_smart_batching=True
                        )

        # Verify smart batching was used
        assert stats['successful_batches'] == 3  # Chapter-based batches
        assert stats['total_pages'] == 15

        # Verify chapter information in output
        content = output_path.read_text()
        assert "Chapter 1" in content
        assert "Chapter 2" in content
        assert "Chapter 3" in content

    def test_smart_batching_fallback_to_fixed(
        self,
        mock_pdf_path,
        temp_output_dir,
        mock_converter
    ):
        """Test fallback to fixed-size batching when outline is unavailable."""
        output_path = temp_output_dir / "output.md"

        # Mock no outline
        mock_outline_result = {'has_outline': False, 'outline_items': []}

        with patch('docling_batched.get_pdf_page_count', return_value=12):
            with patch('docling_batched.inspect_pdf_outline', return_value=mock_outline_result):
                with patch('docling_batched.DocumentConverter', return_value=mock_converter):
                    stats = convert_pdf_in_batches(
                        pdf_path=mock_pdf_path,
                        output_path=output_path,
                        batch_size=5,
                        use_smart_batching=True  # Requested but will fallback
                    )

        # Should fall back to fixed-size batching: 5, 5, 2 pages
        assert stats['successful_batches'] == 3
        assert stats['total_pages'] == 12

    def test_partial_batch_failure(
        self,
        mock_pdf_path,
        temp_output_dir
    ):
        """Test handling of partial batch failures."""
        output_path = temp_output_dir / "output.md"

        with patch('docling_batched.get_pdf_page_count', return_value=10):
            with patch('docling_batched.DocumentConverter') as MockConverter:
                converter = MockConverter.return_value

                # First batch succeeds, second fails
                success_result = Mock()
                success_result.status = ConversionStatus.SUCCESS
                success_result.document.export_to_markdown.return_value = "Success content"

                failure_result = Mock()
                failure_result.status = ConversionStatus.FAILURE

                converter.convert.side_effect = [success_result, failure_result]

                stats = convert_pdf_in_batches(
                    pdf_path=mock_pdf_path,
                    output_path=output_path,
                    batch_size=5,
                    use_smart_batching=False
                )

        # Verify partial success
        assert stats['successful_batches'] == 1
        assert stats['failed_batches'] == 1
        assert stats['processed_pages'] == 5  # Only first batch

        # Verify failure marker in output
        content = output_path.read_text()
        assert "BATCH 2 FAILED" in content

    def test_batch_exception_handling(
        self,
        mock_pdf_path,
        temp_output_dir
    ):
        """Test handling of exceptions during batch processing."""
        output_path = temp_output_dir / "output.md"

        with patch('docling_batched.get_pdf_page_count', return_value=10):
            with patch('docling_batched.DocumentConverter') as MockConverter:
                converter = MockConverter.return_value

                # First batch succeeds, second raises exception
                success_result = Mock()
                success_result.status = ConversionStatus.SUCCESS
                success_result.document.export_to_markdown.return_value = "Success"

                converter.convert.side_effect = [
                    success_result,
                    Exception("Processing error")
                ]

                stats = convert_pdf_in_batches(
                    pdf_path=mock_pdf_path,
                    output_path=output_path,
                    batch_size=5,
                    use_smart_batching=False
                )

        # Should continue after exception
        assert stats['successful_batches'] == 1
        assert stats['failed_batches'] == 1

        # Verify error marker in output
        content = output_path.read_text()
        assert "BATCH 2 ERROR" in content
        assert "Processing error" in content

    def test_batch_size_edge_cases(
        self,
        mock_pdf_path,
        temp_output_dir,
        mock_converter
    ):
        """Test edge cases with batch sizes."""
        output_path = temp_output_dir / "output.md"

        # Test batch size larger than total pages
        with patch('docling_batched.get_pdf_page_count', return_value=5):
            with patch('docling_batched.DocumentConverter', return_value=mock_converter):
                stats = convert_pdf_in_batches(
                    pdf_path=mock_pdf_path,
                    output_path=output_path,
                    batch_size=100,
                    use_smart_batching=False
                )

        # Should process all pages in one batch
        assert stats['successful_batches'] == 1
        assert stats['total_pages'] == 5
        assert stats['processed_pages'] == 5

    def test_batch_size_one_page(
        self,
        mock_pdf_path,
        temp_output_dir,
        mock_converter
    ):
        """Test batch size of 1 (page-by-page processing)."""
        output_path = temp_output_dir / "output.md"

        with patch('docling_batched.get_pdf_page_count', return_value=3):
            with patch('docling_batched.DocumentConverter', return_value=mock_converter):
                stats = convert_pdf_in_batches(
                    pdf_path=mock_pdf_path,
                    output_path=output_path,
                    batch_size=1,
                    use_smart_batching=False
                )

        # Should process 3 separate batches
        assert stats['successful_batches'] == 3
        assert len(stats['batch_times']) == 3

    def test_memory_cleanup_called(
        self,
        mock_pdf_path,
        temp_output_dir,
        mock_converter
    ):
        """Test that garbage collection is called between batches."""
        output_path = temp_output_dir / "output.md"

        with patch('docling_batched.get_pdf_page_count', return_value=10):
            with patch('docling_batched.DocumentConverter', return_value=mock_converter):
                with patch('docling_batched.gc.collect') as mock_gc:
                    convert_pdf_in_batches(
                        pdf_path=mock_pdf_path,
                        output_path=output_path,
                        batch_size=5,
                        use_smart_batching=False
                    )

                    # gc.collect should be called after each batch (2 batches)
                    assert mock_gc.call_count >= 2

    def test_statistics_tracking(
        self,
        mock_pdf_path,
        temp_output_dir,
        mock_converter
    ):
        """Test that all statistics are properly tracked."""
        output_path = temp_output_dir / "output.md"

        with patch('docling_batched.get_pdf_page_count', return_value=15):
            with patch('docling_batched.DocumentConverter', return_value=mock_converter):
                stats = convert_pdf_in_batches(
                    pdf_path=mock_pdf_path,
                    output_path=output_path,
                    batch_size=7,
                    use_smart_batching=False
                )

        # Verify all required statistics fields
        assert 'total_pages' in stats
        assert 'processed_pages' in stats
        assert 'successful_batches' in stats
        assert 'failed_batches' in stats
        assert 'total_time' in stats
        assert 'batch_times' in stats

        # Verify values make sense
        assert stats['total_pages'] == 15
        assert stats['successful_batches'] == 3  # 7, 7, 1
        assert stats['total_time'] > 0
        assert len(stats['batch_times']) == 3

    def test_output_file_structure(
        self,
        mock_pdf_path,
        temp_output_dir,
        mock_converter
    ):
        """Test that output file has correct structure and metadata."""
        output_path = temp_output_dir / "output.md"

        with patch('docling_batched.get_pdf_page_count', return_value=6):
            with patch('docling_batched.DocumentConverter', return_value=mock_converter):
                convert_pdf_in_batches(
                    pdf_path=mock_pdf_path,
                    output_path=output_path,
                    batch_size=3,
                    use_smart_batching=True
                )

        content = output_path.read_text()

        # Verify header metadata
        assert "# test.pdf" in content
        assert "Converted:" in content
        assert "Total Pages: 6" in content
        assert "Maximum Batch Size: 3" in content
        assert "Smart Batching: True" in content

        # Verify batch markers
        assert "<!-- Batch 1:" in content
        assert "<!-- Batch 2:" in content

        # Verify separators
        assert content.count("---") >= 2  # Initial separator + batch separators

    def test_pipeline_initialization(
        self,
        mock_pdf_path,
        temp_output_dir
    ):
        """Test that pipeline is initialized once and reused."""
        output_path = temp_output_dir / "output.md"

        with patch('docling_batched.get_pdf_page_count', return_value=10):
            with patch('docling_batched.DocumentConverter') as MockConverter:
                converter = MockConverter.return_value

                mock_result = Mock()
                mock_result.status = ConversionStatus.SUCCESS
                mock_result.document.export_to_markdown.return_value = "Content"
                converter.convert.return_value = mock_result

                convert_pdf_in_batches(
                    pdf_path=mock_pdf_path,
                    output_path=output_path,
                    batch_size=5,
                    use_smart_batching=False
                )

                # Pipeline should be initialized once
                converter.initialize_pipeline.assert_called_once()

                # But convert should be called twice (2 batches)
                assert converter.convert.call_count == 2
