import grpc
# futures has loads of stuff in it for parallel execution
from concurrent import futures
# reflection is used by clients to figure out what API endpoints there are
from grpc_reflection.v1alpha import reflection
import api_pb2
import api_pb2_grpc
import logging


class LoadingServiceServicer(api_pb2_grpc.LoadingServiceServicer):
    def LoadPDF(self, request, context):
        
        # this is where the program could be doing work, if
        # we had implemented that (:
        # request will be the LoadRequest from the client
        # we should access the fields in the request and do stuff with it
        # like setting metadata
        
        # then we also have to do the pdf loading and store it in our DB

        # when that's done, we return a LoadResponse
        # dummy for now
        return api_pb2.LoadResponse(
            success=True,
            message="PDF loaded successfully",
            chunks_created=42,
            document_id="some-uuid"
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # register our Servicer class at the grpc server
    # if a client requests a service that the Servicer can Service
    # the grpc server will send it that way
    api_pb2_grpc.add_LoadingServiceServicer_to_server(
        LoadingServiceServicer(), server
    )

    # Clients can use reflection to figure out which services the server offers through
    # another, standardised service
    # https://grpc.io/docs/guides/reflection/
    # TODO: This may lower the security of a given API by allowing people to see which
    # services exist.  Although releasing the code to the public probably does the same
    # so i think this is not an issue to worry about atm
    #
    # apparently this bit where  we have to tell the reflection service
    # which services are floating around in our server is not necessary in the
    # implementation of other languages, so that is something to look forward to (:
    SERVICE_NAMES = (
        api_pb2.DESCRIPTOR.services_by_name["LoadingService"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

# if our python file is executed as the main program
if __name__ == "__main__":
    logging.basicConfig()
    serve()