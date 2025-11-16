from grpc_generated.api_connect import LoadingService
import grpc_generated.api_pb2 as api

# this class implements the interface that our generated connect RPC code defines
# it does that by having all the methods of the interface class
class LoadingServiceImplementation:
    async def load_p_d_f(self, request: api.PdfLoadRequest, ctx):

        # TODO: actually do stuff with the request
        print("Received PDF:", request.pdf_name)

        # dummy response for now
        return api.PdfLoadResponse(
            success=True,
            message="Loaded successfully via Connect RPC",
            chunks_created=0,
            document_id="12345",
        )