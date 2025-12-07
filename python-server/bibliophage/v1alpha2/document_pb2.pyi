from google.protobuf import timestamp_pb2 as _timestamp_pb2
from bibliophage.v1alpha2 import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DocumentType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DOCUMENT_TYPE_UNSPECIFIED: _ClassVar[DocumentType]
    NOTE: _ClassVar[DocumentType]
    LORE_FRAGMENT: _ClassVar[DocumentType]
    CHARACTER: _ClassVar[DocumentType]
    LOCATION: _ClassVar[DocumentType]
    OBJECT: _ClassVar[DocumentType]
    QUEST: _ClassVar[DocumentType]
    SESSION_LOG: _ClassVar[DocumentType]
DOCUMENT_TYPE_UNSPECIFIED: DocumentType
NOTE: DocumentType
LORE_FRAGMENT: DocumentType
CHARACTER: DocumentType
LOCATION: DocumentType
OBJECT: DocumentType
QUEST: DocumentType
SESSION_LOG: DocumentType

class Document(_message.Message):
    __slots__ = ("id", "name", "content", "type", "created_at", "updated_at", "tags", "character_count")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_COUNT_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    content: str
    type: DocumentType
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    tags: _containers.RepeatedCompositeFieldContainer[_common_pb2.Tag]
    character_count: int
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., content: _Optional[str] = ..., type: _Optional[_Union[DocumentType, str]] = ..., created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., tags: _Optional[_Iterable[_Union[_common_pb2.Tag, _Mapping]]] = ..., character_count: _Optional[int] = ...) -> None: ...

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

class SearchDocumentsRequest(_message.Message):
    __slots__ = ("name_query", "content_query", "type_filter", "tag_filters", "page_size", "page_number", "sort_order")
    NAME_QUERY_FIELD_NUMBER: _ClassVar[int]
    CONTENT_QUERY_FIELD_NUMBER: _ClassVar[int]
    TYPE_FILTER_FIELD_NUMBER: _ClassVar[int]
    TAG_FILTERS_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    SORT_ORDER_FIELD_NUMBER: _ClassVar[int]
    name_query: str
    content_query: str
    type_filter: DocumentType
    tag_filters: _containers.RepeatedCompositeFieldContainer[_common_pb2.TagFilter]
    page_size: int
    page_number: int
    sort_order: _common_pb2.SortOrder
    def __init__(self, name_query: _Optional[str] = ..., content_query: _Optional[str] = ..., type_filter: _Optional[_Union[DocumentType, str]] = ..., tag_filters: _Optional[_Iterable[_Union[_common_pb2.TagFilter, _Mapping]]] = ..., page_size: _Optional[int] = ..., page_number: _Optional[int] = ..., sort_order: _Optional[_Union[_common_pb2.SortOrder, str]] = ...) -> None: ...

class SearchDocumentsResponse(_message.Message):
    __slots__ = ("success", "message", "documents", "total_count", "page_number", "has_more")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    DOCUMENTS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    PAGE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    HAS_MORE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    documents: _containers.RepeatedCompositeFieldContainer[Document]
    total_count: int
    page_number: int
    has_more: bool
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., documents: _Optional[_Iterable[_Union[Document, _Mapping]]] = ..., total_count: _Optional[int] = ..., page_number: _Optional[int] = ..., has_more: bool = ...) -> None: ...

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
