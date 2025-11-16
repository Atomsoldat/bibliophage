format:
	buf format --write grpc-api/grpc_generated

# .PHONY tells make that this target does not generate a file called api
.PHONY: api
api:
	cd web-ui && \
	yarn run api && \
	cd -
	cd python-server && \
	pixi run api
