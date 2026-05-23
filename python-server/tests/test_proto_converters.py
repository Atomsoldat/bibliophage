"""Unit tests for proto_converters.py.

These tests touch only the protobuf message types — no database, no services.
"""

import pytest

import bibliophage.v1alpha3.document_pb2 as document_api
from proto_converters import metadata_dict_to_proto, metadata_proto_to_dict


# ── metadata_dict_to_proto ──────────────────────────────────────────────


@pytest.mark.unit
def test_dict_to_proto_empty_dict_yields_default_metadata():
    proto = metadata_dict_to_proto({})

    assert proto.file_size == 0
    assert not proto.HasField("publication_type")
    assert not proto.HasField("pdf")


@pytest.mark.unit
def test_dict_to_proto_file_size_only():
    proto = metadata_dict_to_proto({"file_size": 12345})

    assert proto.file_size == 12345
    assert not proto.HasField("publication_type")
    assert not proto.HasField("pdf")


@pytest.mark.unit
def test_dict_to_proto_publication_type_only():
    proto = metadata_dict_to_proto({"publication_type": "rulebook"})

    assert proto.HasField("publication_type")
    assert proto.publication_type == "rulebook"
    assert not proto.HasField("pdf")


@pytest.mark.unit
def test_dict_to_proto_pdf_full():
    proto = metadata_dict_to_proto({
        "pdf": {
            "loading_batch_count": 4,
            "vector_chunk_count": 200,
            "page_count": 320,
        },
    })

    assert proto.HasField("pdf")
    assert proto.pdf.loading_batch_count == 4
    assert proto.pdf.vector_chunk_count == 200
    assert proto.pdf.page_count == 320


@pytest.mark.unit
def test_dict_to_proto_pdf_partial_defaults_missing_fields():
    # Only page_count provided — the other two pdf fields default to 0.
    proto = metadata_dict_to_proto({"pdf": {"page_count": 7}})

    assert proto.HasField("pdf")
    assert proto.pdf.page_count == 7
    assert proto.pdf.loading_batch_count == 0
    assert proto.pdf.vector_chunk_count == 0


# ── metadata_proto_to_dict ──────────────────────────────────────────────


@pytest.mark.unit
def test_proto_to_dict_default_metadata():
    proto = document_api.Metadata()

    d = metadata_proto_to_dict(proto)

    assert d == {"file_size": 0}


@pytest.mark.unit
def test_proto_to_dict_with_publication_type():
    proto = document_api.Metadata(file_size=100, publication_type="adventure")

    d = metadata_proto_to_dict(proto)

    assert d == {"file_size": 100, "publication_type": "adventure"}


@pytest.mark.unit
def test_proto_to_dict_with_pdf():
    proto = document_api.Metadata(file_size=500)
    proto.pdf.CopyFrom(document_api.PdfData(
        loading_batch_count=2,
        vector_chunk_count=50,
        page_count=120,
    ))

    d = metadata_proto_to_dict(proto)

    assert d == {
        "file_size": 500,
        "pdf": {
            "loading_batch_count": 2,
            "vector_chunk_count": 50,
            "page_count": 120,
        },
    }


# ── round-trips ─────────────────────────────────────────────────────────


@pytest.mark.unit
def test_roundtrip_full_metadata():
    original_dict = {
        "file_size": 9876,
        "publication_type": "supplement",
        "pdf": {
            "loading_batch_count": 8,
            "vector_chunk_count": 1000,
            "page_count": 450,
        },
    }

    proto = metadata_dict_to_proto(original_dict)
    roundtripped = metadata_proto_to_dict(proto)

    assert roundtripped == original_dict


@pytest.mark.unit
def test_roundtrip_proto_with_file_size_only():
    original = document_api.Metadata(file_size=42)

    d = metadata_proto_to_dict(original)
    rebuilt = metadata_dict_to_proto(d)

    assert rebuilt.file_size == 42
    assert not rebuilt.HasField("publication_type")
    assert not rebuilt.HasField("pdf")
