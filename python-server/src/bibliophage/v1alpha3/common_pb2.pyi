from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

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
