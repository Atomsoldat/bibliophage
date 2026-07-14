"""Unit tests for proto_converters.py.

These tests touch only the protobuf message types — no database, no services.
"""

from datetime import UTC, datetime

import pytest
from google.protobuf import timestamp_pb2

import bibliophage.v1alpha3.common_pb2 as common_api
import bibliophage.v1alpha3.document_pb2 as document_api
from proto_converters import (
    datetime_to_proto_ts,
    metadata_dict_to_proto,
    metadata_proto_to_dict,
    row_to_proto_document,
)


def _make_row(**overrides):
    """Return a minimal complete row dict for row_to_proto_document, with overrides applied."""
    row = {
        "document_id": "11111111-1111-1111-1111-111111111111",
        "title": "Test Doc",
        "character_count": 42,
        "content": "hello world",
        "document_type": "RULEBOOK",
        "source_type": "CORE",
        "created_at": datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC),
        "updated_at": datetime(2024, 1, 2, 3, 4, 6, tzinfo=UTC),
    }
    row.update(overrides)
    return row


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


# ── datetime_to_proto_ts ────────────────────────────────────────────────


@pytest.mark.unit
def test_datetime_to_proto_ts_returns_timestamp_instance():
    ts = datetime_to_proto_ts(datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC))

    assert isinstance(ts, timestamp_pb2.Timestamp)


@pytest.mark.unit
def test_datetime_to_proto_ts_preserves_value_via_roundtrip():
    # FromDatetime/ToDatetime is the contract we care about. Use aware UTC
    # to match the timezone treatment FromDatetime applies internally.
    original = datetime(2026, 5, 23, 14, 30, 45, tzinfo=UTC)

    ts = datetime_to_proto_ts(original)

    assert ts.ToDatetime(tzinfo=UTC) == original


@pytest.mark.unit
def test_datetime_to_proto_ts_seconds_match_unix_epoch():
    # 2024-01-01T00:00:00Z = 1704067200 seconds since the unix epoch.
    ts = datetime_to_proto_ts(datetime(2024, 1, 1, tzinfo=UTC))

    assert ts.seconds == 1704067200
    assert ts.nanos == 0


@pytest.mark.unit
def test_datetime_to_proto_ts_independent_calls_dont_alias():
    # Each call must return a fresh Timestamp — mutating one must not affect another.
    a = datetime_to_proto_ts(datetime(2024, 1, 1, tzinfo=UTC))
    b = datetime_to_proto_ts(datetime(2025, 1, 1, tzinfo=UTC))

    assert a.seconds != b.seconds
    assert a is not b


# ── row_to_proto_document ───────────────────────────────────────────────


@pytest.mark.unit
def test_row_to_proto_document_default_class_is_document_with_full_content():
    proto = row_to_proto_document(_make_row())

    assert isinstance(proto, document_api.Document)
    assert proto.id == "11111111-1111-1111-1111-111111111111"
    assert proto.name == "Test Doc"
    assert proto.character_count == 42
    assert proto.content == "hello world"
    assert proto.type == document_api.RULEBOOK
    assert proto.source_type == document_api.CORE


@pytest.mark.unit
def test_row_to_proto_document_list_item_uses_content_snippet():
    row = _make_row(content_snippet="hello...")
    # DocumentListItem doesn't carry full content, only content_snippet.

    proto = row_to_proto_document(row, document_api.DocumentListItem)

    assert isinstance(proto, document_api.DocumentListItem)
    assert proto.content_snippet == "hello..."


@pytest.mark.unit
def test_row_to_proto_document_unknown_enum_falls_back_to_unspecified():
    row = _make_row(document_type="NOT_A_REAL_ENUM_VALUE")

    proto = row_to_proto_document(row)

    assert proto.type == document_api.DOCUMENT_TYPE_UNSPECIFIED


@pytest.mark.unit
def test_row_to_proto_document_missing_source_type_defaults_to_unspecified():
    row = _make_row()
    del row["source_type"]

    proto = row_to_proto_document(row)

    assert proto.source_type == document_api.SOURCE_TYPE_UNSPECIFIED


@pytest.mark.unit
def test_row_to_proto_document_with_metadata_populates_proto_metadata():
    row = _make_row(metadata={
        "file_size": 1024,
        "publication_type": "supplement",
        "pdf": {"loading_batch_count": 2, "vector_chunk_count": 50, "page_count": 100},
    })

    proto = row_to_proto_document(row)

    assert proto.HasField("metadata")
    assert proto.metadata.file_size == 1024
    assert proto.metadata.HasField("publication_type")
    assert proto.metadata.publication_type == "supplement"
    assert proto.metadata.HasField("pdf")
    assert proto.metadata.pdf.page_count == 100


@pytest.mark.unit
def test_row_to_proto_document_missing_metadata_leaves_proto_metadata_unset():
    proto = row_to_proto_document(_make_row(metadata=None))

    assert not proto.HasField("metadata")


@pytest.mark.unit
def test_row_to_proto_document_timestamps_match_row_values():
    row = _make_row(
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        updated_at=datetime(2024, 2, 1, tzinfo=UTC),
    )

    proto = row_to_proto_document(row)

    assert proto.created_at.seconds == 1704067200  # 2024-01-01T00:00:00Z
    assert proto.updated_at.seconds == 1706745600  # 2024-02-01T00:00:00Z


@pytest.mark.unit
def test_row_to_proto_document_systems_populated():
    row = _make_row(systems=["D&D 5e", "Pathfinder 2e"])

    proto = row_to_proto_document(row)

    assert list(proto.systems) == ["D&D 5e", "Pathfinder 2e"]


@pytest.mark.unit
def test_row_to_proto_document_systems_absent_yields_empty():
    proto = row_to_proto_document(_make_row())

    assert list(proto.systems) == []


@pytest.mark.unit
def test_row_to_proto_document_tags_populated():
    row = _make_row(tags=[
        {"name": "edition", "values": ["5e", "2024"]},
        {"name": "genre", "values": ["fantasy"]},
    ])

    proto = row_to_proto_document(row)

    assert len(proto.tags) == 2
    assert isinstance(proto.tags[0], common_api.Tag)
    assert proto.tags[0].name == "edition"
    assert list(proto.tags[0].values) == ["5e", "2024"]
    assert proto.tags[1].name == "genre"
    assert list(proto.tags[1].values) == ["fantasy"]


@pytest.mark.unit
def test_row_to_proto_document_tags_absent_yields_empty():
    proto = row_to_proto_document(_make_row())

    assert list(proto.tags) == []


@pytest.mark.unit
def test_row_to_proto_document_tag_with_no_values():
    row = _make_row(tags=[{"name": "solo", "values": []}])

    proto = row_to_proto_document(row)

    assert len(proto.tags) == 1
    assert proto.tags[0].name == "solo"
    assert list(proto.tags[0].values) == []
