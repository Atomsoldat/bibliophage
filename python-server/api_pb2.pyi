from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RpgSystem(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RPG_SYSTEM_UNSPECIFIED: _ClassVar[RpgSystem]
    DND_35: _ClassVar[RpgSystem]
    PATHFINDER_1E: _ClassVar[RpgSystem]
    PATHFINDER_2E: _ClassVar[RpgSystem]

class PublicationType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PUBLICATION_TYPE_UNSPECIFIED: _ClassVar[PublicationType]
    CORE_RULEBOOK: _ClassVar[PublicationType]
    BESTIARY: _ClassVar[PublicationType]
    SUPPLEMENT: _ClassVar[PublicationType]
    ADVENTURE: _ClassVar[PublicationType]
    SETTING: _ClassVar[PublicationType]
RPG_SYSTEM_UNSPECIFIED: RpgSystem
DND_35: RpgSystem
PATHFINDER_1E: RpgSystem
PATHFINDER_2E: RpgSystem
PUBLICATION_TYPE_UNSPECIFIED: PublicationType
CORE_RULEBOOK: PublicationType
BESTIARY: PublicationType
SUPPLEMENT: PublicationType
ADVENTURE: PublicationType
SETTING: PublicationType

class LoadRequest(_message.Message):
    __slots__ = ("pdf_origin_path", "pdf_name", "pdf_system", "pdf_type", "pdf_page_count", "chunk_size", "chunk_overlap")
    PDF_ORIGIN_PATH_FIELD_NUMBER: _ClassVar[int]
    PDF_NAME_FIELD_NUMBER: _ClassVar[int]
    PDF_SYSTEM_FIELD_NUMBER: _ClassVar[int]
    PDF_TYPE_FIELD_NUMBER: _ClassVar[int]
    PDF_PAGE_COUNT_FIELD_NUMBER: _ClassVar[int]
    CHUNK_SIZE_FIELD_NUMBER: _ClassVar[int]
    CHUNK_OVERLAP_FIELD_NUMBER: _ClassVar[int]
    pdf_origin_path: str
    pdf_name: str
    pdf_system: RpgSystem
    pdf_type: PublicationType
    pdf_page_count: int
    chunk_size: int
    chunk_overlap: int
    def __init__(self, pdf_origin_path: _Optional[str] = ..., pdf_name: _Optional[str] = ..., pdf_system: _Optional[_Union[RpgSystem, str]] = ..., pdf_type: _Optional[_Union[PublicationType, str]] = ..., pdf_page_count: _Optional[int] = ..., chunk_size: _Optional[int] = ..., chunk_overlap: _Optional[int] = ...) -> None: ...

class LoadResponse(_message.Message):
    __slots__ = ("success", "message", "chunks_created", "document_id")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    CHUNKS_CREATED_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_ID_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    chunks_created: int
    document_id: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., chunks_created: _Optional[int] = ..., document_id: _Optional[str] = ...) -> None: ...
