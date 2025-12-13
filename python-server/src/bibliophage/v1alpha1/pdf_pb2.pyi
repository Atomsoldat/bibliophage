from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class PdfLoadRequest(_message.Message):
    __slots__ = ("pdf_origin_path", "pdf_name", "pdf_system", "pdf_type", "pdf_page_count", "chunk_size", "chunk_overlap", "file_data")
    PDF_ORIGIN_PATH_FIELD_NUMBER: _ClassVar[int]
    PDF_NAME_FIELD_NUMBER: _ClassVar[int]
    PDF_SYSTEM_FIELD_NUMBER: _ClassVar[int]
    PDF_TYPE_FIELD_NUMBER: _ClassVar[int]
    PDF_PAGE_COUNT_FIELD_NUMBER: _ClassVar[int]
    CHUNK_SIZE_FIELD_NUMBER: _ClassVar[int]
    CHUNK_OVERLAP_FIELD_NUMBER: _ClassVar[int]
    FILE_DATA_FIELD_NUMBER: _ClassVar[int]
    pdf_origin_path: str
    pdf_name: str
    pdf_system: str
    pdf_type: str
    pdf_page_count: int
    chunk_size: int
    chunk_overlap: int
    file_data: bytes
    def __init__(self, pdf_origin_path: _Optional[str] = ..., pdf_name: _Optional[str] = ..., pdf_system: _Optional[str] = ..., pdf_type: _Optional[str] = ..., pdf_page_count: _Optional[int] = ..., chunk_size: _Optional[int] = ..., chunk_overlap: _Optional[int] = ..., file_data: _Optional[bytes] = ...) -> None: ...

class PdfLoadResponse(_message.Message):
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
