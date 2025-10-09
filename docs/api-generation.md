## Reading Material

- https://grpc.io/docs/guides/reflection/
- This has some good info on the Python side: https://github.com/grpc/grpc/blob/master/doc/python/server_reflection.md

## How This All Kind of Sort of Works

- First, we define our API in a `.proto`-file
- Then we use that file together with the protobuf compiler, to generate the request and response classes as well as the service and stub classes, that the client and server will use to talk to each other

```
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. api.proto
```


The generated stuff in `api_pb2.py` contains a variable called `DESCRIPTOR` which is a `FileDescriptor` representing our API-Schema. This contains all types of messages, enums, services and their names and some additional metadata.

The builder object underneath that is then used for calling builder functions that create the necessary classes for services and enums and whatever else during import time, using that `DESCRIPTOR` variable, containing a representation of the API schema.

Here's how to get the list of available classes
```bash
pixi run python -c "import api_pb2; print('Available classes and enums:'); print([name for name in dir(api_pb2) if not                  │
│   name.startswith('_')])"
```

And here's how to get all the services
```bash
pixi run python -c "
import api_pb2

# Show all services in the descriptor
print('Services in this proto file:')
for service_name in api_pb2.DESCRIPTOR.services_by_name:
    service = api_pb2.DESCRIPTOR.services_by_name[service_name]
    print(f'  Key: {service_name}')
    print(f'  Full name: {service.full_name}')
"
```


**tl;dr** all the funny bits in the generated Python files originate from `api.proto`. That's also where we can see what name our services have, if we want to register them for the reflection service (so that `grpcurl` can figure out how our API works). Reflection is some funny voodoo that a client can do with a server to figure out what API endpoints that server has, without needing to previously be made aware of them.
