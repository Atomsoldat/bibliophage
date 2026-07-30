import datetime

from bibliophage.v1alpha3 import common_pb2 as _common_pb2
from bibliophage.v1alpha3 import embedding_pb2 as _embedding_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SourceType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SOURCE_TYPE_UNSPECIFIED: _ClassVar[SourceType]
    CORE: _ClassVar[SourceType]
    SUPPLEMENT: _ClassVar[SourceType]
    GM_NOTES: _ClassVar[SourceType]
    PLAYER_NOTES: _ClassVar[SourceType]
    SESSION_LOG_RECORD: _ClassVar[SourceType]
    GENERATED: _ClassVar[SourceType]
    COMMUNITY: _ClassVar[SourceType]
SOURCE_TYPE_UNSPECIFIED: SourceType
CORE: SourceType
SUPPLEMENT: SourceType
GM_NOTES: SourceType
PLAYER_NOTES: SourceType
SESSION_LOG_RECORD: SourceType
GENERATED: SourceType
COMMUNITY: SourceType

class PdfData(_message.Message):
    __slots__ = ("loading_batch_count", "vector_chunk_count", "page_count")
    LOADING_BATCH_COUNT_FIELD_NUMBER: _ClassVar[int]
    VECTOR_CHUNK_COUNT_FIELD_NUMBER: _ClassVar[int]
    PAGE_COUNT_FIELD_NUMBER: _ClassVar[int]
    loading_batch_count: int
    vector_chunk_count: int
    page_count: int
    def __init__(self, loading_batch_count: _Optional[int] = ..., vector_chunk_count: _Optional[int] = ..., page_count: _Optional[int] = ...) -> None: ...

class Metadata(_message.Message):
    __slots__ = ("file_size", "publication_type", "pdf")
    FILE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PUBLICATION_TYPE_FIELD_NUMBER: _ClassVar[int]
    PDF_FIELD_NUMBER: _ClassVar[int]
    file_size: int
    publication_type: str
    pdf: PdfData
    def __init__(self, file_size: _Optional[int] = ..., publication_type: _Optional[str] = ..., pdf: _Optional[_Union[PdfData, _Mapping]] = ...) -> None: ...

class Document(_message.Message):
    __slots__ = ("id", "name", "source_type", "metadata", "content", "created_at", "updated_at", "tags", "character_count")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    SOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_COUNT_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    source_type: SourceType
    metadata: Metadata
    content: str
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    tags: _containers.RepeatedCompositeFieldContainer[_common_pb2.Tag]
    character_count: int
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., source_type: _Optional[_Union[SourceType, str]] = ..., metadata: _Optional[_Union[Metadata, _Mapping]] = ..., content: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., tags: _Optional[_Iterable[_Union[_common_pb2.Tag, _Mapping]]] = ..., character_count: _Optional[int] = ...) -> None: ...

class DocumentListItem(_message.Message):
    __slots__ = ("id", "name", "source_type", "metadata", "content_snippet", "created_at", "updated_at", "tags", "character_count", "embedding_status")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    SOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    CONTENT_SNIPPET_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_COUNT_FIELD_NUMBER: _ClassVar[int]
    EMBEDDING_STATUS_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    source_type: SourceType
    metadata: Metadata
    content_snippet: str
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    tags: _containers.RepeatedCompositeFieldContainer[_common_pb2.Tag]
    character_count: int
    embedding_status: _embedding_pb2.EmbeddingStatus
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., source_type: _Optional[_Union[SourceType, str]] = ..., metadata: _Optional[_Union[Metadata, _Mapping]] = ..., content_snippet: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., tags: _Optional[_Iterable[_Union[_common_pb2.Tag, _Mapping]]] = ..., character_count: _Optional[int] = ..., embedding_status: _Optional[_Union[_embedding_pb2.EmbeddingStatus, _Mapping]] = ...) -> None: ...

class StoreDocumentRequest(_message.Message):
    __slots__ = ("document",)
    DOCUMENT_FIELD_NUMBER: _ClassVar[int]
    document: Document
    def __init__(self, document: _Optional[_Union[Document, _Mapping]] = ...) -> None: ...

class StoreDocumentResponse(_message.Message):
    __slots__ = ("success", "message", "document")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    document: Document
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., document: _Optional[_Union[Document, _Mapping]] = ...) -> None: ...

class GetDocumentRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class GetDocumentResponse(_message.Message):
    __slots__ = ("success", "message", "document")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    document: Document
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., document: _Optional[_Union[Document, _Mapping]] = ...) -> None: ...

class UpdateDocumentRequest(_message.Message):
    __slots__ = ("document",)
    DOCUMENT_FIELD_NUMBER: _ClassVar[int]
    document: Document
    def __init__(self, document: _Optional[_Union[Document, _Mapping]] = ...) -> None: ...

class UpdateDocumentResponse(_message.Message):
    __slots__ = ("success", "message", "document")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    document: Document
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., document: _Optional[_Union[Document, _Mapping]] = ...) -> None: ...

class DocumentFilter(_message.Message):
    __slots__ = ("name_query", "content_query", "tag_filters")
    NAME_QUERY_FIELD_NUMBER: _ClassVar[int]
    CONTENT_QUERY_FIELD_NUMBER: _ClassVar[int]
    TAG_FILTERS_FIELD_NUMBER: _ClassVar[int]
    name_query: str
    content_query: str
    tag_filters: _containers.RepeatedCompositeFieldContainer[_common_pb2.TagFilter]
    def __init__(self, name_query: _Optional[str] = ..., content_query: _Optional[str] = ..., tag_filters: _Optional[_Iterable[_Union[_common_pb2.TagFilter, _Mapping]]] = ...) -> None: ...

class SearchDocumentsRequest(_message.Message):
    __slots__ = ("filter", "page_size", "page_number", "sort_order")
    FILTER_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    SORT_ORDER_FIELD_NUMBER: _ClassVar[int]
    filter: DocumentFilter
    page_size: int
    page_number: int
    sort_order: _common_pb2.SortOrder
    def __init__(self, filter: _Optional[_Union[DocumentFilter, _Mapping]] = ..., page_size: _Optional[int] = ..., page_number: _Optional[int] = ..., sort_order: _Optional[_Union[_common_pb2.SortOrder, str]] = ...) -> None: ...

class SearchDocumentsResponse(_message.Message):
    __slots__ = ("success", "message", "matches", "total_count", "page_number", "has_more")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    MATCHES_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    PAGE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    HAS_MORE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    matches: _containers.RepeatedCompositeFieldContainer[DocumentListItem]
    total_count: int
    page_number: int
    has_more: bool
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., matches: _Optional[_Iterable[_Union[DocumentListItem, _Mapping]]] = ..., total_count: _Optional[int] = ..., page_number: _Optional[int] = ..., has_more: bool = ...) -> None: ...

class DeleteDocumentRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class DeleteDocumentResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...
