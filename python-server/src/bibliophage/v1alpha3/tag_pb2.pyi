from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Tag(_message.Message):
    __slots__ = ("name", "id", "colour", "values", "document_count", "value_count")
    NAME_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    COLOUR_FIELD_NUMBER: _ClassVar[int]
    VALUES_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_COUNT_FIELD_NUMBER: _ClassVar[int]
    VALUE_COUNT_FIELD_NUMBER: _ClassVar[int]
    name: str
    id: str
    colour: str
    values: _containers.RepeatedCompositeFieldContainer[TagValue]
    document_count: int
    value_count: int
    def __init__(self, name: _Optional[str] = ..., id: _Optional[str] = ..., colour: _Optional[str] = ..., values: _Optional[_Iterable[_Union[TagValue, _Mapping]]] = ..., document_count: _Optional[int] = ..., value_count: _Optional[int] = ...) -> None: ...

class TagValue(_message.Message):
    __slots__ = ("value", "document_count")
    VALUE_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_COUNT_FIELD_NUMBER: _ClassVar[int]
    value: str
    document_count: int
    def __init__(self, value: _Optional[str] = ..., document_count: _Optional[int] = ...) -> None: ...

class TagFilter(_message.Message):
    __slots__ = ("name", "value")
    NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    name: str
    value: str
    def __init__(self, name: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class StoreTagRequest(_message.Message):
    __slots__ = ("tag",)
    TAG_FIELD_NUMBER: _ClassVar[int]
    tag: Tag
    def __init__(self, tag: _Optional[_Union[Tag, _Mapping]] = ...) -> None: ...

class StoreTagResponse(_message.Message):
    __slots__ = ("success", "message", "tag")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TAG_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    tag: Tag
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., tag: _Optional[_Union[Tag, _Mapping]] = ...) -> None: ...

class GetTagRequest(_message.Message):
    __slots__ = ("id", "count_docs", "count_values")
    ID_FIELD_NUMBER: _ClassVar[int]
    COUNT_DOCS_FIELD_NUMBER: _ClassVar[int]
    COUNT_VALUES_FIELD_NUMBER: _ClassVar[int]
    id: str
    count_docs: bool
    count_values: bool
    def __init__(self, id: _Optional[str] = ..., count_docs: bool = ..., count_values: bool = ...) -> None: ...

class GetTagResponse(_message.Message):
    __slots__ = ("success", "message", "tag")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TAG_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    tag: Tag
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., tag: _Optional[_Union[Tag, _Mapping]] = ...) -> None: ...

class GetTagsRequest(_message.Message):
    __slots__ = ("name_filter", "count_docs", "count_values")
    NAME_FILTER_FIELD_NUMBER: _ClassVar[int]
    COUNT_DOCS_FIELD_NUMBER: _ClassVar[int]
    COUNT_VALUES_FIELD_NUMBER: _ClassVar[int]
    name_filter: str
    count_docs: bool
    count_values: bool
    def __init__(self, name_filter: _Optional[str] = ..., count_docs: bool = ..., count_values: bool = ...) -> None: ...

class GetTagsResponse(_message.Message):
    __slots__ = ("success", "message", "tags")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    tags: _containers.RepeatedCompositeFieldContainer[Tag]
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., tags: _Optional[_Iterable[_Union[Tag, _Mapping]]] = ...) -> None: ...

class DeleteTagRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class DeleteTagResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class RenameTagRequest(_message.Message):
    __slots__ = ("id", "name")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ...) -> None: ...

class RenameTagResponse(_message.Message):
    __slots__ = ("success", "message", "tag")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TAG_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    tag: Tag
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., tag: _Optional[_Union[Tag, _Mapping]] = ...) -> None: ...

class UpdateTagColourRequest(_message.Message):
    __slots__ = ("id", "colour")
    ID_FIELD_NUMBER: _ClassVar[int]
    COLOUR_FIELD_NUMBER: _ClassVar[int]
    id: str
    colour: str
    def __init__(self, id: _Optional[str] = ..., colour: _Optional[str] = ...) -> None: ...

class UpdateTagColourResponse(_message.Message):
    __slots__ = ("success", "message", "tag")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TAG_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    tag: Tag
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., tag: _Optional[_Union[Tag, _Mapping]] = ...) -> None: ...

class StoreTagValueRequest(_message.Message):
    __slots__ = ("tag_id", "tag_value")
    TAG_ID_FIELD_NUMBER: _ClassVar[int]
    TAG_VALUE_FIELD_NUMBER: _ClassVar[int]
    tag_id: str
    tag_value: TagValue
    def __init__(self, tag_id: _Optional[str] = ..., tag_value: _Optional[_Union[TagValue, _Mapping]] = ...) -> None: ...

class StoreTagValueResponse(_message.Message):
    __slots__ = ("success", "message", "tag_value")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TAG_VALUE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    tag_value: TagValue
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., tag_value: _Optional[_Union[TagValue, _Mapping]] = ...) -> None: ...

class DeleteTagValueRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class DeleteTagValueResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class RenameTagValueRequest(_message.Message):
    __slots__ = ("id", "name")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ...) -> None: ...

class RenameTagValueResponse(_message.Message):
    __slots__ = ("success", "message", "tag_value")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TAG_VALUE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    tag_value: TagValue
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., tag_value: _Optional[_Union[TagValue, _Mapping]] = ...) -> None: ...
