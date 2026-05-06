from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Node(_message.Message):
    __slots__ = ("id", "type_id", "properties")
    ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_ID_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    id: str
    type_id: str
    properties: _struct_pb2.Struct
    def __init__(self, id: _Optional[str] = ..., type_id: _Optional[str] = ..., properties: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class Edge(_message.Message):
    __slots__ = ("id", "relationship", "directed", "node_a", "node_b")
    ID_FIELD_NUMBER: _ClassVar[int]
    RELATIONSHIP_FIELD_NUMBER: _ClassVar[int]
    DIRECTED_FIELD_NUMBER: _ClassVar[int]
    NODE_A_FIELD_NUMBER: _ClassVar[int]
    NODE_B_FIELD_NUMBER: _ClassVar[int]
    id: str
    relationship: str
    directed: bool
    node_a: str
    node_b: str
    def __init__(self, id: _Optional[str] = ..., relationship: _Optional[str] = ..., directed: bool = ..., node_a: _Optional[str] = ..., node_b: _Optional[str] = ...) -> None: ...

class CreateNodeRequest(_message.Message):
    __slots__ = ("type_id", "properties")
    TYPE_ID_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    type_id: str
    properties: _struct_pb2.Struct
    def __init__(self, type_id: _Optional[str] = ..., properties: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class CreateNodeResponse(_message.Message):
    __slots__ = ("success", "message", "node")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    NODE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    node: Node
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., node: _Optional[_Union[Node, _Mapping]] = ...) -> None: ...

class CreateEdgeRequest(_message.Message):
    __slots__ = ("relationship", "directed", "source_node_id", "target_node_id")
    RELATIONSHIP_FIELD_NUMBER: _ClassVar[int]
    DIRECTED_FIELD_NUMBER: _ClassVar[int]
    SOURCE_NODE_ID_FIELD_NUMBER: _ClassVar[int]
    TARGET_NODE_ID_FIELD_NUMBER: _ClassVar[int]
    relationship: str
    directed: bool
    source_node_id: str
    target_node_id: str
    def __init__(self, relationship: _Optional[str] = ..., directed: bool = ..., source_node_id: _Optional[str] = ..., target_node_id: _Optional[str] = ...) -> None: ...

class CreateEdgeResponse(_message.Message):
    __slots__ = ("success", "message", "edge")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    EDGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    edge: Edge
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., edge: _Optional[_Union[Edge, _Mapping]] = ...) -> None: ...

class DeleteNodeRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class DeleteNodeResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class DeleteEdgeRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class DeleteEdgeResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...
