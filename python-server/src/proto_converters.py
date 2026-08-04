"""Conversions between protobuf messages and the dict / row shapes used by the DB.

Centralizing these here keeps the service implementations focused on RPC
orchestration. New conversions accumulate as more proto types touch the DB.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from google.protobuf import timestamp_pb2

import bibliophage.v1alpha3.document_pb2 as document_api
import bibliophage.v1alpha3.tag_pb2 as tag_api


def datetime_to_proto_ts(dt: datetime) -> timestamp_pb2.Timestamp:
    """Build a google.protobuf.Timestamp from a Python datetime.

    Wraps the two-step `Timestamp()` + `.FromDatetime(dt)` dance that protobuf
    requires (direct assignment to `.created_at = dt` does not work).
    """
    ts = timestamp_pb2.Timestamp()
    ts.FromDatetime(dt)
    return ts


def row_to_proto_document(
    row: dict[str, Any],
    proto_class: type = document_api.Document,
) -> document_api.Document | document_api.DocumentListItem:
    """Convert a DB row from the documents table to a proto Document or DocumentListItem.

    Handles column renames (document_id→id, title→name),
    metadata JSONB→proto, and timestamp conversion.
    """
    proto = proto_class()
    proto.id = str(row["document_id"])
    proto.name = row["title"]
    proto.character_count = row["character_count"]

    # Content field: Document has full content, DocumentListItem has content_snippet
    if proto_class == document_api.Document:
        proto.content = row["content"]
    else:
        proto.content_snippet = row.get("content_snippet", "")

    # Metadata JSONB → proto
    metadata_dict = row.get("metadata") or {}
    if metadata_dict:
        proto.metadata.CopyFrom(metadata_dict_to_proto(metadata_dict))

    for tag_data in row.get("tags", []):
        tag = tag_api.Tag()
        tag.name = tag_data.get("name", "")
        # DB read-side enrichment (_hydrate_document_tags) does not yet return
        # tag_value_id alongside the value string, so TagValue.id is left unset here.
        tag.values.extend(
            tag_api.TagValue(value=v) for v in tag_data.get("values", [])
        )
        proto.tags.append(tag)

    # Timestamps
    proto.created_at.CopyFrom(datetime_to_proto_ts(row["created_at"]))
    proto.updated_at.CopyFrom(datetime_to_proto_ts(row["updated_at"]))

    return proto


def metadata_dict_to_proto(d: dict[str, Any]) -> document_api.Metadata:
    """Build a Metadata proto from a JSONB metadata dict (as returned by Postgres).

    Missing keys default to the proto's zero values. The optional `pdf` field
    is only set when present in the dict, so HasField reports it accurately
    on the resulting proto.
    """
    metadata = document_api.Metadata()
    metadata.file_size = d.get("file_size", 0)
    if "pdf" in d:
        pdf = d["pdf"]
        metadata.pdf.CopyFrom(
            document_api.PdfData(
                loading_batch_count=pdf.get("loading_batch_count", 0),
                vector_chunk_count=pdf.get("vector_chunk_count", 0),
                page_count=pdf.get("page_count", 0),
            ),
        )
    return metadata


def metadata_proto_to_dict(m: document_api.Metadata) -> dict[str, Any]:
    """Serialize a Metadata proto into a dict suitable for JSONB storage.

    The optional `pdf` field is only included when set on the proto, matching
    how the read-side converter interprets it.
    """
    d: dict[str, Any] = {"file_size": m.file_size}
    if m.HasField("pdf"):
        d["pdf"] = {
            "loading_batch_count": m.pdf.loading_batch_count,
            "vector_chunk_count": m.pdf.vector_chunk_count,
            "page_count": m.pdf.page_count,
        }
    return d
