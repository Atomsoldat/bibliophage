import datetime

from bibliophage.v1alpha3 import common_pb2 as _common_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Pdf(_message.Message):
    __slots__ = ("id", "name", "systems", "type", "page_count", "created_at", "updated_at", "file_size", "batch_count", "vector_chunk_count", "tags", "content")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    SYSTEMS_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    PAGE_COUNT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    FILE_SIZE_FIELD_NUMBER: _ClassVar[int]
    BATCH_COUNT_FIELD_NUMBER: _ClassVar[int]
    VECTOR_CHUNK_COUNT_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    systems: _containers.RepeatedScalarFieldContainer[str]
    type: str
    page_count: int
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    file_size: int
    batch_count: int
    vector_chunk_count: int
    tags: _containers.RepeatedCompositeFieldContainer[_common_pb2.Tag]
    content: str
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., systems: _Optional[_Iterable[str]] = ..., type: _Optional[str] = ..., page_count: _Optional[int] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., file_size: _Optional[int] = ..., batch_count: _Optional[int] = ..., vector_chunk_count: _Optional[int] = ..., tags: _Optional[_Iterable[_Union[_common_pb2.Tag, _Mapping]]] = ..., content: _Optional[str] = ...) -> None: ...

class PdfListItem(_message.Message):
    __slots__ = ("id", "name", "systems", "type", "page_count", "created_at", "updated_at", "file_size", "batch_count", "vector_chunk_count", "tags")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    SYSTEMS_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    PAGE_COUNT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    FILE_SIZE_FIELD_NUMBER: _ClassVar[int]
    BATCH_COUNT_FIELD_NUMBER: _ClassVar[int]
    VECTOR_CHUNK_COUNT_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    systems: _containers.RepeatedScalarFieldContainer[str]
    type: str
    page_count: int
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    file_size: int
    batch_count: int
    vector_chunk_count: int
    tags: _containers.RepeatedCompositeFieldContainer[_common_pb2.Tag]
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., systems: _Optional[_Iterable[str]] = ..., type: _Optional[str] = ..., page_count: _Optional[int] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., file_size: _Optional[int] = ..., batch_count: _Optional[int] = ..., vector_chunk_count: _Optional[int] = ..., tags: _Optional[_Iterable[_Union[_common_pb2.Tag, _Mapping]]] = ...) -> None: ...

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
