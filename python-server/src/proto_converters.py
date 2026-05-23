"""Conversions between protobuf messages and the dict / row shapes used by the DB.

Centralizing these here keeps the service implementations focused on RPC
orchestration. New conversions accumulate as more proto types touch the DB.
"""

from __future__ import annotations

from typing import Any

import bibliophage.v1alpha3.document_pb2 as document_api


def metadata_dict_to_proto(d: dict[str, Any]) -> document_api.Metadata:
    """Build a Metadata proto from a JSONB metadata dict (as returned by Postgres).

    Missing keys default to the proto's zero values. The optional `publication_type`
    and `pdf` fields are only set when present in the dict, so HasField reports
    them accurately on the resulting proto.
    """
    metadata = document_api.Metadata()
    metadata.file_size = d.get("file_size", 0)
    if "publication_type" in d:
        metadata.publication_type = d["publication_type"]
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

    Optional fields (`publication_type`, `pdf`) are only included when set on
    the proto, matching how the read-side converter interprets them.
    """
    d: dict[str, Any] = {"file_size": m.file_size}
    if m.HasField("publication_type"):
        d["publication_type"] = m.publication_type
    if m.HasField("pdf"):
        d["pdf"] = {
            "loading_batch_count": m.pdf.loading_batch_count,
            "vector_chunk_count": m.pdf.vector_chunk_count,
            "page_count": m.pdf.page_count,
        }
    return d
