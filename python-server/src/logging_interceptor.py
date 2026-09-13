"""Connect-RPC interceptor that logs unhandled exceptions.

`ConnectASGIApplication` (connectrpc/_server_async.py) catches every exception
raised by a service method and converts it straight into a generic wire
error/500 response without ever logging it - see `_handle_error` and
`_handle_stream` in that module. Without this interceptor, any exception that
isn't deliberately translated into a `ConnectError`/domain exception by the
service layer just vanishes, leaving a bare 500 in the logs with no
traceback.

Implemented as a `MetadataInterceptor` (`on_start`/`on_end`) rather than a
`UnaryInterceptor`. connect-python only applies an interceptor to the RPC
shapes it structurally implements (see `_apply_interceptors` in
`connectrpc/_server_async.py`) - a `UnaryInterceptor` is silently skipped for
streaming methods such as `ChatService.StreamChat`. A `MetadataInterceptor`
is automatically wrapped (`MetadataInterceptorInvoker`) into all four RPC
shapes, so this one implementation covers unary and streaming calls alike.
"""

import logging
import sys

logger = logging.getLogger(__name__)


class LoggingInterceptor:
    """Logs the full traceback of any exception before it reaches connect-python's handler."""

    async def on_start(self, ctx):
        return None

    async def on_end(self, token, ctx):
        if sys.exc_info()[1] is None:
            return
        method = ctx.method()
        logger.exception(
            "Unhandled exception in %s/%s",
            method.service_name,
            method.name,
        )
