import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ChunkingStrategy(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CHUNKING_STRATEGY_UNSPECIFIED: _ClassVar[ChunkingStrategy]
    TOKEN_BASED: _ClassVar[ChunkingStrategy]
    MARKDOWN_STRUCTURE: _ClassVar[ChunkingStrategy]
    MARKDOWN_WITH_TOKEN_LIMIT: _ClassVar[ChunkingStrategy]
    PDF_PAGE_BASED: _ClassVar[ChunkingStrategy]
    USER_DEFINED: _ClassVar[ChunkingStrategy]
CHUNKING_STRATEGY_UNSPECIFIED: ChunkingStrategy
TOKEN_BASED: ChunkingStrategy
MARKDOWN_STRUCTURE: ChunkingStrategy
MARKDOWN_WITH_TOKEN_LIMIT: ChunkingStrategy
PDF_PAGE_BASED: ChunkingStrategy
USER_DEFINED: ChunkingStrategy

class MarkdownReference(_message.Message):
    __slots__ = ("heading_path", "start_heading_level")
    HEADING_PATH_FIELD_NUMBER: _ClassVar[int]
    START_HEADING_LEVEL_FIELD_NUMBER: _ClassVar[int]
    heading_path: _containers.RepeatedScalarFieldContainer[str]
    start_heading_level: int
    def __init__(self, heading_path: _Optional[_Iterable[str]] = ..., start_heading_level: _Optional[int] = ...) -> None: ...

class PdfPageReference(_message.Message):
    __slots__ = ("start_page", "end_page")
    START_PAGE_FIELD_NUMBER: _ClassVar[int]
    END_PAGE_FIELD_NUMBER: _ClassVar[int]
    start_page: int
    end_page: int
    def __init__(self, start_page: _Optional[int] = ..., end_page: _Optional[int] = ...) -> None: ...

class ChunkBoundary(_message.Message):
    __slots__ = ("chunk_id", "char_start", "char_end", "token_start", "token_end", "markdown_ref", "pdf_ref", "description", "preview")
    CHUNK_ID_FIELD_NUMBER: _ClassVar[int]
    CHAR_START_FIELD_NUMBER: _ClassVar[int]
    CHAR_END_FIELD_NUMBER: _ClassVar[int]
    TOKEN_START_FIELD_NUMBER: _ClassVar[int]
    TOKEN_END_FIELD_NUMBER: _ClassVar[int]
    MARKDOWN_REF_FIELD_NUMBER: _ClassVar[int]
    PDF_REF_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    PREVIEW_FIELD_NUMBER: _ClassVar[int]
    chunk_id: str
    char_start: int
    char_end: int
    token_start: int
    token_end: int
    markdown_ref: MarkdownReference
    pdf_ref: PdfPageReference
    description: str
    preview: str
    def __init__(self, chunk_id: _Optional[str] = ..., char_start: _Optional[int] = ..., char_end: _Optional[int] = ..., token_start: _Optional[int] = ..., token_end: _Optional[int] = ..., markdown_ref: _Optional[_Union[MarkdownReference, _Mapping]] = ..., pdf_ref: _Optional[_Union[PdfPageReference, _Mapping]] = ..., description: _Optional[str] = ..., preview: _Optional[str] = ...) -> None: ...

class ChunkingConfig(_message.Message):
    __slots__ = ("strategy", "token_chunk_size", "token_chunk_overlap", "max_heading_level", "config_version")
    STRATEGY_FIELD_NUMBER: _ClassVar[int]
    TOKEN_CHUNK_SIZE_FIELD_NUMBER: _ClassVar[int]
    TOKEN_CHUNK_OVERLAP_FIELD_NUMBER: _ClassVar[int]
    MAX_HEADING_LEVEL_FIELD_NUMBER: _ClassVar[int]
    CONFIG_VERSION_FIELD_NUMBER: _ClassVar[int]
    strategy: ChunkingStrategy
    token_chunk_size: int
    token_chunk_overlap: int
    max_heading_level: int
    config_version: str
    def __init__(self, strategy: _Optional[_Union[ChunkingStrategy, str]] = ..., token_chunk_size: _Optional[int] = ..., token_chunk_overlap: _Optional[int] = ..., max_heading_level: _Optional[int] = ..., config_version: _Optional[str] = ...) -> None: ...

class EmbeddingStatus(_message.Message):
    __slots__ = ("is_embedded", "embeddings_current", "embedded_at", "total_chunks", "embedding_model", "vector_collection")
    IS_EMBEDDED_FIELD_NUMBER: _ClassVar[int]
    EMBEDDINGS_CURRENT_FIELD_NUMBER: _ClassVar[int]
    EMBEDDED_AT_FIELD_NUMBER: _ClassVar[int]
    TOTAL_CHUNKS_FIELD_NUMBER: _ClassVar[int]
    EMBEDDING_MODEL_FIELD_NUMBER: _ClassVar[int]
    VECTOR_COLLECTION_FIELD_NUMBER: _ClassVar[int]
    is_embedded: bool
    embeddings_current: bool
    embedded_at: _timestamp_pb2.Timestamp
    total_chunks: int
    embedding_model: str
    vector_collection: str
    def __init__(self, is_embedded: bool = ..., embeddings_current: bool = ..., embedded_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., total_chunks: _Optional[int] = ..., embedding_model: _Optional[str] = ..., vector_collection: _Optional[str] = ...) -> None: ...

class ChunkProposal(_message.Message):
    __slots__ = ("boundaries", "config", "statistics")
    BOUNDARIES_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    STATISTICS_FIELD_NUMBER: _ClassVar[int]
    boundaries: _containers.RepeatedCompositeFieldContainer[ChunkBoundary]
    config: ChunkingConfig
    statistics: ChunkStatistics
    def __init__(self, boundaries: _Optional[_Iterable[_Union[ChunkBoundary, _Mapping]]] = ..., config: _Optional[_Union[ChunkingConfig, _Mapping]] = ..., statistics: _Optional[_Union[ChunkStatistics, _Mapping]] = ...) -> None: ...

class ChunkStatistics(_message.Message):
    __slots__ = ("total_chunks", "avg_chunk_size", "min_chunk_size", "max_chunk_size", "total_content_length")
    TOTAL_CHUNKS_FIELD_NUMBER: _ClassVar[int]
    AVG_CHUNK_SIZE_FIELD_NUMBER: _ClassVar[int]
    MIN_CHUNK_SIZE_FIELD_NUMBER: _ClassVar[int]
    MAX_CHUNK_SIZE_FIELD_NUMBER: _ClassVar[int]
    TOTAL_CONTENT_LENGTH_FIELD_NUMBER: _ClassVar[int]
    total_chunks: int
    avg_chunk_size: int
    min_chunk_size: int
    max_chunk_size: int
    total_content_length: int
    def __init__(self, total_chunks: _Optional[int] = ..., avg_chunk_size: _Optional[int] = ..., min_chunk_size: _Optional[int] = ..., max_chunk_size: _Optional[int] = ..., total_content_length: _Optional[int] = ...) -> None: ...

class ProposeChunksRequest(_message.Message):
    __slots__ = ("document_id", "config")
    DOCUMENT_ID_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    document_id: str
    config: ChunkingConfig
    def __init__(self, document_id: _Optional[str] = ..., config: _Optional[_Union[ChunkingConfig, _Mapping]] = ...) -> None: ...

class ProposeChunksResponse(_message.Message):
    __slots__ = ("success", "message", "proposal")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    PROPOSAL_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    proposal: ChunkProposal
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., proposal: _Optional[_Union[ChunkProposal, _Mapping]] = ...) -> None: ...

class EmbedDocumentRequest(_message.Message):
    __slots__ = ("document_id", "config", "desired_boundaries")
    DOCUMENT_ID_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    DESIRED_BOUNDARIES_FIELD_NUMBER: _ClassVar[int]
    document_id: str
    config: ChunkingConfig
    desired_boundaries: _containers.RepeatedCompositeFieldContainer[ChunkBoundary]
    def __init__(self, document_id: _Optional[str] = ..., config: _Optional[_Union[ChunkingConfig, _Mapping]] = ..., desired_boundaries: _Optional[_Iterable[_Union[ChunkBoundary, _Mapping]]] = ...) -> None: ...

class EmbedDocumentResponse(_message.Message):
    __slots__ = ("success", "message", "embedding_status")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    EMBEDDING_STATUS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    embedding_status: EmbeddingStatus
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., embedding_status: _Optional[_Union[EmbeddingStatus, _Mapping]] = ...) -> None: ...

class GetChunkBoundariesRequest(_message.Message):
    __slots__ = ("document_id",)
    DOCUMENT_ID_FIELD_NUMBER: _ClassVar[int]
    document_id: str
    def __init__(self, document_id: _Optional[str] = ...) -> None: ...

class GetChunkBoundariesResponse(_message.Message):
    __slots__ = ("success", "message", "boundaries", "config", "embedding_status")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    BOUNDARIES_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    EMBEDDING_STATUS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    boundaries: _containers.RepeatedCompositeFieldContainer[ChunkBoundary]
    config: ChunkingConfig
    embedding_status: EmbeddingStatus
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., boundaries: _Optional[_Iterable[_Union[ChunkBoundary, _Mapping]]] = ..., config: _Optional[_Union[ChunkingConfig, _Mapping]] = ..., embedding_status: _Optional[_Union[EmbeddingStatus, _Mapping]] = ...) -> None: ...

class DeleteEmbeddingsRequest(_message.Message):
    __slots__ = ("document_id",)
    DOCUMENT_ID_FIELD_NUMBER: _ClassVar[int]
    document_id: str
    def __init__(self, document_id: _Optional[str] = ...) -> None: ...

class DeleteEmbeddingsResponse(_message.Message):
    __slots__ = ("success", "message", "chunks_deleted")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    CHUNKS_DELETED_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    chunks_deleted: int
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., chunks_deleted: _Optional[int] = ...) -> None: ...
