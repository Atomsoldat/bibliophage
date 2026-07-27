import datetime

from bibliophage.v1alpha3 import common_pb2 as _common_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Canon(_message.Message):
    __slots__ = ("id", "name", "created_at", "updated_at", "tags")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    tags: _containers.RepeatedCompositeFieldContainer[_common_pb2.Tag]
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., tags: _Optional[_Iterable[_Union[_common_pb2.Tag, _Mapping]]] = ...) -> None: ...

class StoreCanonRequest(_message.Message):
    __slots__ = ("canon",)
    CANON_FIELD_NUMBER: _ClassVar[int]
    canon: Canon
    def __init__(self, canon: _Optional[_Union[Canon, _Mapping]] = ...) -> None: ...

class StoreCanonResponse(_message.Message):
    __slots__ = ("success", "message", "canon")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    CANON_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    canon: Canon
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., canon: _Optional[_Union[Canon, _Mapping]] = ...) -> None: ...

class GetCanonRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class GetCanonResponse(_message.Message):
    __slots__ = ("success", "message", "canon")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    CANON_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    canon: Canon
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., canon: _Optional[_Union[Canon, _Mapping]] = ...) -> None: ...

class UpdateCanonRequest(_message.Message):
    __slots__ = ("canon",)
    CANON_FIELD_NUMBER: _ClassVar[int]
    canon: Canon
    def __init__(self, canon: _Optional[_Union[Canon, _Mapping]] = ...) -> None: ...

class UpdateCanonResponse(_message.Message):
    __slots__ = ("success", "message", "canon")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    CANON_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    canon: Canon
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., canon: _Optional[_Union[Canon, _Mapping]] = ...) -> None: ...

class CanonFilter(_message.Message):
    __slots__ = ("name_query", "tag_filters")
    NAME_QUERY_FIELD_NUMBER: _ClassVar[int]
    TAG_FILTERS_FIELD_NUMBER: _ClassVar[int]
    name_query: str
    tag_filters: _containers.RepeatedCompositeFieldContainer[_common_pb2.TagFilter]
    def __init__(self, name_query: _Optional[str] = ..., tag_filters: _Optional[_Iterable[_Union[_common_pb2.TagFilter, _Mapping]]] = ...) -> None: ...

class SearchCanonsRequest(_message.Message):
    __slots__ = ("filter", "page_size", "page_number", "sort_order")
    FILTER_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    SORT_ORDER_FIELD_NUMBER: _ClassVar[int]
    filter: CanonFilter
    page_size: int
    page_number: int
    sort_order: _common_pb2.SortOrder
    def __init__(self, filter: _Optional[_Union[CanonFilter, _Mapping]] = ..., page_size: _Optional[int] = ..., page_number: _Optional[int] = ..., sort_order: _Optional[_Union[_common_pb2.SortOrder, str]] = ...) -> None: ...

class SearchCanonsResponse(_message.Message):
    __slots__ = ("success", "message", "matches", "total_count", "page_number", "has_more")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    MATCHES_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    PAGE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    HAS_MORE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    matches: _containers.RepeatedCompositeFieldContainer[Canon]
    total_count: int
    page_number: int
    has_more: bool
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., matches: _Optional[_Iterable[_Union[Canon, _Mapping]]] = ..., total_count: _Optional[int] = ..., page_number: _Optional[int] = ..., has_more: bool = ...) -> None: ...

class DeleteCanonRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class DeleteCanonResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...
