format:
	buf format --write grpc-api/grpc_generated

api:
	cd web-ui && \
	yarn run api && \
	cd -
	cd python-server && \
	pixi run api
