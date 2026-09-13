## Connect-RPC error handling

- https://connectrpc.com/docs/python/errors/
- https://connectrpc.com/docs/python/interceptors/

`connect-python`'s `ConnectASGIApplication` catches every exception a service method raises and converts it into a generic wire error (`Code.UNKNOWN` / HTTP 500) without ever logging it - this happens uniformly for any exception that isn't already caught by our own code before it reaches connect-python's dispatch boundary. Because the tag service is mounted as a raw ASGI sub-app, this also bypasses Starlette's/uvicorn's usual "log unhandled exceptions" safety nets, so without extra plumbing an unexpected bug in a handler shows up only as a bare 500 in the logs.

`python-server/src/logging_interceptor.py` closes this gap by hooking connect-python's own interceptor mechanism (the documented way to add cross-cutting concerns like logging) to log a full traceback before the exception is converted. It's implemented as a `MetadataInterceptor` (`on_start`/`on_end`) rather than a `UnaryInterceptor`, since connect-python only applies an interceptor to the RPC shapes it structurally implements - a unary-only interceptor is silently skipped for streaming methods such as `ChatService.StreamChat`.

Hiding internal exception details from RPC clients is intentional and correct; the interceptor only restores visibility on the server side, it doesn't change what clients receive.
