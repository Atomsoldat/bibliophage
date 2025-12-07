from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class SortOrder(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SORT_ORDER_UNSPECIFIED: _ClassVar[SortOrder]
    NAME_ASC: _ClassVar[SortOrder]
    NAME_DESC: _ClassVar[SortOrder]
    CREATED_AT_ASC: _ClassVar[SortOrder]
    CREATED_AT_DESC: _ClassVar[SortOrder]
SORT_ORDER_UNSPECIFIED: SortOrder
NAME_ASC: SortOrder
NAME_DESC: SortOrder
CREATED_AT_ASC: SortOrder
CREATED_AT_DESC: SortOrder

class Tag(_message.Message):
    __slots__ = ("name", "values")
    NAME_FIELD_NUMBER: _ClassVar[int]
    VALUES_FIELD_NUMBER: _ClassVar[int]
    name: str
    values: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, name: _Optional[str] = ..., values: _Optional[_Iterable[str]] = ...) -> None: ...

class TagFilter(_message.Message):
    __slots__ = ("name", "value")
    NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    name: str
    value: str
    def __init__(self, name: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
