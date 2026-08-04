"""Unit tests for ingestion/service.py's document_type-tag pass-through behavior.

The docling pipeline, settings, and database are all faked so these run
without a real model, database connection, or environment configuration.
Ingestion no longer classifies PDFs at all (neither document_type nor
source_type is inferred from the PDF's declared type string, both of which
were removed from pdf.proto) — these tests confirm store_document is called
with no source_type argument, no publication_type in metadata, and that tags
(including document_type) only ever come straight from the caller's own
request.pdf.tags.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime

import pytest

import bibliophage.v1alpha3.pdf_pb2 as pdf_api
import ingestion.service as ingestion_service_module
from ingestion.service import LoadingServiceImplementation


class _FakeDoclingPipeline:
    def __init__(self, *args, **kwargs):
        pass

    def process_pdf(self, *, pdf_bytes, pdf_name, use_smart_batching, memory_per_page_mb):
        return {
            "content": "fake content",
            "processed_batches": [1],
            "successful_batches": 1,
            "total_pages": 3,
        }


@dataclass
class _FakeDb:
    calls: list = field(default_factory=list)

    async def store_document(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "document_id": "22222222-2222-2222-2222-222222222222",
            "created_at": datetime.now(tz=UTC),
            "character_count": len(kwargs["content"]),
        }


@pytest.fixture
def ingestion_service(monkeypatch):
    fake_db = _FakeDb()
    monkeypatch.setattr(ingestion_service_module, "DoclingPipeline", _FakeDoclingPipeline)
    monkeypatch.setattr(ingestion_service_module, "get_postgres_db", lambda: fake_db)
    monkeypatch.setattr(ingestion_service_module, "get_settings", lambda: None)
    service = LoadingServiceImplementation()
    return service, fake_db


def _make_request() -> pdf_api.LoadPdfRequest:
    request = pdf_api.LoadPdfRequest()
    request.pdf.name = "Test PDF"
    request.file_data = b"%PDF-1.4 fake"
    return request


@pytest.mark.unit
async def test_load_pdf_sets_no_source_type(ingestion_service):
    service, fake_db = ingestion_service

    response = await service.load_pdf(_make_request(), ctx=None)

    assert response.success
    assert len(fake_db.calls) == 1
    assert "source_type" not in fake_db.calls[0]


@pytest.mark.unit
async def test_load_pdf_metadata_has_no_publication_type(ingestion_service):
    service, fake_db = ingestion_service

    await service.load_pdf(_make_request(), ctx=None)

    metadata = fake_db.calls[0]["metadata"]
    assert "publication_type" not in metadata
    assert metadata["file_size"] == len(b"%PDF-1.4 fake")


@pytest.mark.unit
async def test_load_pdf_does_not_set_document_type_when_caller_omits_it(ingestion_service):
    service, fake_db = ingestion_service

    await service.load_pdf(_make_request(), ctx=None)

    assert fake_db.calls[0]["tags"] == []
    assert "doc_type" not in fake_db.calls[0]


@pytest.mark.unit
async def test_load_pdf_preserves_caller_supplied_document_type_tag(ingestion_service):
    service, fake_db = ingestion_service

    request = _make_request()
    tag = request.pdf.tags.add()
    tag.name = "document_type"
    tag.values.add(value="rulebook")

    await service.load_pdf(request, ctx=None)

    assert fake_db.calls[0]["tags"] == [{"name": "document_type", "values": ["rulebook"]}]


@pytest.mark.unit
async def test_load_pdf_preserves_multiple_caller_supplied_tags(ingestion_service):
    service, fake_db = ingestion_service

    request = _make_request()
    doc_type_tag = request.pdf.tags.add()
    doc_type_tag.name = "document_type"
    doc_type_tag.values.add(value="rulebook")
    canon_tag = request.pdf.tags.add()
    canon_tag.name = "canon"
    canon_tag.values.add(value="official")

    await service.load_pdf(request, ctx=None)

    assert fake_db.calls[0]["tags"] == [
        {"name": "document_type", "values": ["rulebook"]},
        {"name": "canon", "values": ["official"]},
    ]
