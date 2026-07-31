import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ChunkType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CHUNK_TYPE_UNSPECIFIED: _ClassVar[ChunkType]
    TOKEN: _ClassVar[ChunkType]
    METADATA: _ClassVar[ChunkType]
    ERROR: _ClassVar[ChunkType]
    DONE: _ClassVar[ChunkType]
CHUNK_TYPE_UNSPECIFIED: ChunkType
TOKEN: ChunkType
METADATA: ChunkType
ERROR: ChunkType
DONE: ChunkType

class ChatRequest(_message.Message):
    __slots__ = ("message", "context_document_ids", "system_prompt", "conversation_history", "enable_auto_retrieval", "retrieval_top_k")
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_DOCUMENT_IDS_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_PROMPT_FIELD_NUMBER: _ClassVar[int]
    CONVERSATION_HISTORY_FIELD_NUMBER: _ClassVar[int]
    ENABLE_AUTO_RETRIEVAL_FIELD_NUMBER: _ClassVar[int]
    RETRIEVAL_TOP_K_FIELD_NUMBER: _ClassVar[int]
    message: str
    context_document_ids: _containers.RepeatedScalarFieldContainer[str]
    system_prompt: str
    conversation_history: _containers.RepeatedCompositeFieldContainer[ChatMessage]
    enable_auto_retrieval: bool
    retrieval_top_k: int
    def __init__(self, message: _Optional[str] = ..., context_document_ids: _Optional[_Iterable[str]] = ..., system_prompt: _Optional[str] = ..., conversation_history: _Optional[_Iterable[_Union[ChatMessage, _Mapping]]] = ..., enable_auto_retrieval: bool = ..., retrieval_top_k: _Optional[int] = ...) -> None: ...

class ChatMessage(_message.Message):
    __slots__ = ("role", "content", "timestamp")
    ROLE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    role: str
    content: str
    timestamp: _timestamp_pb2.Timestamp
    def __init__(self, role: _Optional[str] = ..., content: _Optional[str] = ..., timestamp: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ChatResponseChunk(_message.Message):
    __slots__ = ("type", "content", "metadata")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    type: ChunkType
    content: str
    metadata: ChunkMetadata
    def __init__(self, type: _Optional[_Union[ChunkType, str]] = ..., content: _Optional[str] = ..., metadata: _Optional[_Union[ChunkMetadata, _Mapping]] = ...) -> None: ...

class ChunkMetadata(_message.Message):
    __slots__ = ("model", "context_documents", "retrieved_chunks")
    MODEL_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_DOCUMENTS_FIELD_NUMBER: _ClassVar[int]
    RETRIEVED_CHUNKS_FIELD_NUMBER: _ClassVar[int]
    model: str
    context_documents: _containers.RepeatedCompositeFieldContainer[ContextDocumentInfo]
    retrieved_chunks: _containers.RepeatedCompositeFieldContainer[RetrievedChunk]
    def __init__(self, model: _Optional[str] = ..., context_documents: _Optional[_Iterable[_Union[ContextDocumentInfo, _Mapping]]] = ..., retrieved_chunks: _Optional[_Iterable[_Union[RetrievedChunk, _Mapping]]] = ...) -> None: ...

class ContextDocumentInfo(_message.Message):
    __slots__ = ("id", "name")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ...) -> None: ...

class RetrievedChunk(_message.Message):
    __slots__ = ("chunk_id", "document_id", "document_name", "content", "similarity")
    CHUNK_ID_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_ID_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_NAME_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    SIMILARITY_FIELD_NUMBER: _ClassVar[int]
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    similarity: float
    def __init__(self, chunk_id: _Optional[str] = ..., document_id: _Optional[str] = ..., document_name: _Optional[str] = ..., content: _Optional[str] = ..., similarity: _Optional[float] = ...) -> None: ...
