#!/bin/bash

  nix  --experimental-features develop path:. --command protoc \
    --proto_path=submodules/arcadedb/grpc/src/main/proto \
    --go_out=./src/arcadedb --go_opt=paths=source_relative \
    --go_opt=Marcadedb-server.proto=lichturm.de/bibliophage/flansch/arcadedb \
    --go-grpc_out=./src/arcadedb --go-grpc_opt=paths=source_relative \
    --go-grpc_opt=Marcadedb-server.proto=lichturm.de/bibliophage/flansch/arcadedb \
    submodules/arcadedb/grpc/src/main/proto/arcadedb-server.proto
