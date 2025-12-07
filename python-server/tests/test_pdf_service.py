"""Tests for PdfService v1alpha2 implementation.

Note: These tests are basic structural tests for the API.
Full integration tests require a running PostgreSQL database with pgvector extension.
"""

import pytest
import bibliophage.v1alpha2.pdf_pb2 as api
from bibliophage.v1alpha2.common_pb2 import Tag


def test_load_pdf_request_structure():
    """Test that LoadPdfRequest can be constructed with proper structure."""
    pdf = api.Pdf()
    pdf.name = "Test PDF"
    pdf.system = "D&D 5e"
    pdf.type = "Core Rulebook"
    pdf.origin_path = "/path/to/test.pdf"

    # Add tags
    tag = pdf.tags.add()
    tag.name = "genre"
    tag.values.extend(["fantasy", "adventure"])

    chunking_config = api.ChunkingConfig()
    chunking_config.chunk_size = 600
    chunking_config.chunk_overlap = 50

    request = api.LoadPdfRequest(
        pdf=pdf,
        file_data=b"fake pdf data",
        chunking_config=chunking_config
    )

    assert request.pdf.name == "Test PDF"
    assert request.pdf.system == "D&D 5e"
    assert request.chunking_config.chunk_size == 600
    assert len(request.file_data) > 0


def test_load_pdf_response_structure():
    """Test that LoadPdfResponse can be constructed properly."""
    pdf = api.Pdf()
    pdf.id = "test-uuid-123"
    pdf.name = "Test PDF"
    pdf.page_count = 100
    pdf.chunk_count = 50
    pdf.file_size = 1024000

    response = api.LoadPdfResponse(
        success=True,
        message="PDF loaded successfully",
        pdf=pdf
    )

    assert response.success is True
    assert response.pdf.id == "test-uuid-123"
    assert response.pdf.page_count == 100
    assert response.pdf.chunk_count == 50


def test_search_pdfs_request_structure():
    """Test that SearchPdfsRequest can be constructed with filters."""
    from bibliophage.v1alpha2.common_pb2 import TagFilter, SortOrder

    tag_filter = TagFilter()
    tag_filter.name = "genre"
    tag_filter.value = "fantasy"

    request = api.SearchPdfsRequest(
        title_query="Player's Handbook",
        system_filter="D&D 5e",
        type_filter="Core Rulebook",
        tag_filters=[tag_filter],
        page_size=20,
        page_number=0,
        sort_order=SortOrder.NAME_ASC
    )

    assert request.title_query == "Player's Handbook"
    assert request.system_filter == "D&D 5e"
    assert len(request.tag_filters) == 1
    assert request.tag_filters[0].name == "genre"


def test_search_pdfs_response_structure():
    """Test that SearchPdfsResponse can be constructed properly."""
    pdf1 = api.Pdf()
    pdf1.id = "pdf-1"
    pdf1.name = "PDF 1"

    pdf2 = api.Pdf()
    pdf2.id = "pdf-2"
    pdf2.name = "PDF 2"

    response = api.SearchPdfsResponse(
        success=True,
        message="Found 2 PDFs",
        pdfs=[pdf1, pdf2],
        total_count=2,
        page_number=0,
        has_more=False
    )

    assert response.success is True
    assert len(response.pdfs) == 2
    assert response.total_count == 2
    assert response.has_more is False


def test_get_pdf_request_structure():
    """Test that GetPdfRequest can be constructed."""
    request = api.GetPdfRequest(id="test-pdf-id-123")

    assert request.id == "test-pdf-id-123"


def test_get_pdf_response_structure():
    """Test that GetPdfResponse can be constructed."""
    pdf = api.Pdf()
    pdf.id = "test-id"
    pdf.name = "Test PDF"

    response = api.GetPdfResponse(
        success=True,
        message="PDF retrieved",
        pdf=pdf
    )

    assert response.success is True
    assert response.pdf.id == "test-id"


def test_pdf_with_multiple_tags():
    """Test that PDF can have multiple tags with multiple values."""
    pdf = api.Pdf()
    pdf.name = "Tagged PDF"

    # Add genre tags
    genre_tag = pdf.tags.add()
    genre_tag.name = "genre"
    genre_tag.values.extend(["fantasy", "horror", "adventure"])

    # Add campaign tag
    campaign_tag = pdf.tags.add()
    campaign_tag.name = "campaign"
    campaign_tag.values.append("curse-of-strahd")

    # Add system tag
    system_tag = pdf.tags.add()
    system_tag.name = "edition"
    system_tag.values.extend(["5e", "5.5e"])

    assert len(pdf.tags) == 3
    assert list(pdf.tags[0].values) == ["fantasy", "horror", "adventure"]
    assert list(pdf.tags[1].values) == ["curse-of-strahd"]
    assert list(pdf.tags[2].values) == ["5e", "5.5e"]


def test_chunking_config_defaults():
    """Test ChunkingConfig with default values."""
    config = api.ChunkingConfig()

    # Protobuf default values are 0 for integers
    assert config.chunk_size == 0
    assert config.chunk_overlap == 0

    # Set actual values
    config.chunk_size = 800
    config.chunk_overlap = 100

    assert config.chunk_size == 800
    assert config.chunk_overlap == 100


def test_common_tag_structure():
    """Test that Tag from common.proto works correctly."""
    tag = Tag()
    tag.name = "test-tag"
    tag.values.extend(["value1", "value2", "value3"])

    assert tag.name == "test-tag"
    assert len(tag.values) == 3
    assert list(tag.values) == ["value1", "value2", "value3"]
