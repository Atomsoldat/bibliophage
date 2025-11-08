format:
	buf format --write grpc-api/grpc_generated

api:
	cd vue-ui && \
	yarn exec protoc --proto_path=../grpc-api/grpc_generated \
		--es_out src/api \
		--es_opt target=ts \
		--connect-es_out src/api \
		--connect-es_opt target=ts \
		../grpc-api/grpc_generated/api.proto
