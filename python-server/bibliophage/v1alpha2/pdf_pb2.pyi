import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from bibliophage.v1alpha2 import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Pdf(_message.Message):
    __slots__ = ("id", "name", "system", "type", "page_count", "origin_path", "created_at", "updated_at", "file_size", "chunk_count", "tags")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    PAGE_COUNT_FIELD_NUMBER: _ClassVar[int]
    ORIGIN_PATH_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    FILE_SIZE_FIELD_NUMBER: _ClassVar[int]
    CHUNK_COUNT_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    system: str
    type: str
    page_count: int
    origin_path: str
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    file_size: int
    chunk_count: int
    tags: _containers.RepeatedCompositeFieldContainer[_common_pb2.Tag]
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., system: _Optional[str] = ..., type: _Optional[str] = ..., page_count: _Optional[int] = ..., origin_path: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., file_size: _Optional[int] = ..., chunk_count: _Optional[int] = ..., tags: _Optional[_Iterable[_Union[_common_pb2.Tag, _Mapping]]] = ...) -> None: ...

class PdfListItem(_message.Message):
    __slots__ = ("id", "name", "system", "type", "page_count", "origin_path", "created_at", "updated_at", "file_size", "chunk_count", "tags")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    PAGE_COUNT_FIELD_NUMBER: _ClassVar[int]
    ORIGIN_PATH_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    FILE_SIZE_FIELD_NUMBER: _ClassVar[int]
    CHUNK_COUNT_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    system: str
    type: str
    page_count: int
    origin_path: str
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    file_size: int
    chunk_count: int
    tags: _containers.RepeatedCompositeFieldContainer[_common_pb2.Tag]
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., system: _Optional[str] = ..., type: _Optional[str] = ..., page_count: _Optional[int] = ..., origin_path: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., file_size: _Optional[int] = ..., chunk_count: _Optional[int] = ..., tags: _Optional[_Iterable[_Union[_common_pb2.Tag, _Mapping]]] = ...) -> None: ...

class LoadPdfRequest(_message.Message):
    __slots__ = ("pdf", "file_data", "chunking_config")
    PDF_FIELD_NUMBER: _ClassVar[int]
    FILE_DATA_FIELD_NUMBER: _ClassVar[int]
    CHUNKING_CONFIG_FIELD_NUMBER: _ClassVar[int]
    pdf: Pdf
    file_data: bytes
    chunking_config: ChunkingConfig
    def __init__(self, pdf: _Optional[_Union[Pdf, _Mapping]] = ..., file_data: _Optional[bytes] = ..., chunking_config: _Optional[_Union[ChunkingConfig, _Mapping]] = ...) -> None: ...

class ChunkingConfig(_message.Message):
    __slots__ = ("chunk_size", "chunk_overlap")
    CHUNK_SIZE_FIELD_NUMBER: _ClassVar[int]
    CHUNK_OVERLAP_FIELD_NUMBER: _ClassVar[int]
    chunk_size: int
    chunk_overlap: int
    def __init__(self, chunk_size: _Optional[int] = ..., chunk_overlap: _Optional[int] = ...) -> None: ...

class LoadPdfResponse(_message.Message):
    __slots__ = ("success", "message", "pdf")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    PDF_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    pdf: Pdf
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., pdf: _Optional[_Union[Pdf, _Mapping]] = ...) -> None: ...

class SearchPdfsRequest(_message.Message):
    __slots__ = ("title_query", "system_filter", "type_filter", "tag_filters", "page_size", "page_number", "sort_order")
    TITLE_QUERY_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_FILTER_FIELD_NUMBER: _ClassVar[int]
    TYPE_FILTER_FIELD_NUMBER: _ClassVar[int]
    TAG_FILTERS_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    SORT_ORDER_FIELD_NUMBER: _ClassVar[int]
    title_query: str
    system_filter: str
    type_filter: str
    tag_filters: _containers.RepeatedCompositeFieldContainer[_common_pb2.TagFilter]
    page_size: int
    page_number: int
    sort_order: _common_pb2.SortOrder
    def __init__(self, title_query: _Optional[str] = ..., system_filter: _Optional[str] = ..., type_filter: _Optional[str] = ..., tag_filters: _Optional[_Iterable[_Union[_common_pb2.TagFilter, _Mapping]]] = ..., page_size: _Optional[int] = ..., page_number: _Optional[int] = ..., sort_order: _Optional[_Union[_common_pb2.SortOrder, str]] = ...) -> None: ...

class SearchPdfsResponse(_message.Message):
    __slots__ = ("success", "message", "pdfs", "total_count", "page_number", "has_more")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    PDFS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    PAGE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    HAS_MORE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    pdfs: _containers.RepeatedCompositeFieldContainer[PdfListItem]
    total_count: int
    page_number: int
    has_more: bool
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., pdfs: _Optional[_Iterable[_Union[PdfListItem, _Mapping]]] = ..., total_count: _Optional[int] = ..., page_number: _Optional[int] = ..., has_more: bool = ...) -> None: ...

class GetPdfRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class GetPdfResponse(_message.Message):
    __slots__ = ("success", "message", "pdf")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    PDF_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    pdf: Pdf
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., pdf: _Optional[_Union[Pdf, _Mapping]] = ...) -> None: ...
