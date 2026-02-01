#!/bin/bash

# Generate ArcadeDB Go code (from submodule)
nix --extra-experimental-features "nix-command flakes" develop path:. --command protoc \
  --proto_path=submodules/arcadedb/grpc/src/main/proto \
  --go_out=./src/arcadedb --go_opt=paths=source_relative \
  --go_opt=Marcadedb-server.proto=lichturm.de/bibliophage/flansch/arcadedb \
  --go-grpc_out=./src/arcadedb --go-grpc_opt=paths=source_relative \
  --go-grpc_opt=Marcadedb-server.proto=lichturm.de/bibliophage/flansch/arcadedb \
  submodules/arcadedb/grpc/src/main/proto/arcadedb-server.proto

# Generate Bibliophage Go code (from ../api)
nix --extra-experimental-features "nix-command flakes" develop path:. --command protoc \
  --proto_path=../api \
  --go_out=./src/bibliophage --go_opt=paths=source_relative \
  --go_opt=Mbibliophage/v1alpha3/graph.proto=lichturm.de/bibliophage/flansch/bibliophage \
  --go-grpc_out=./src/bibliophage --go-grpc_opt=paths=source_relative \
  --go-grpc_opt=Mbibliophage/v1alpha3/graph.proto=lichturm.de/bibliophage/flansch/bibliophage \
  ../api/bibliophage/v1alpha3/graph.proto
