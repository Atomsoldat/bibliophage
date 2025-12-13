from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DocumentType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DOCUMENT_TYPE_UNSPECIFIED: _ClassVar[DocumentType]
    NOTE: _ClassVar[DocumentType]
    LORE_FRAGMENT: _ClassVar[DocumentType]
    CHARACTER: _ClassVar[DocumentType]
    LOCATION: _ClassVar[DocumentType]
    OBJECT: _ClassVar[DocumentType]
DOCUMENT_TYPE_UNSPECIFIED: DocumentType
NOTE: DocumentType
LORE_FRAGMENT: DocumentType
CHARACTER: DocumentType
LOCATION: DocumentType
OBJECT: DocumentType

class DocumentStoreRequest(_message.Message):
    __slots__ = ("document_name", "content", "document_type")
    DOCUMENT_NAME_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    document_name: str
    content: str
    document_type: DocumentType
    def __init__(self, document_name: _Optional[str] = ..., content: _Optional[str] = ..., document_type: _Optional[_Union[DocumentType, str]] = ...) -> None: ...

class DocumentStoreResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...
