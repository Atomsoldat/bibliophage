"""
gRPC client for communicating with the Bibliophage PDF loading service.
"""

import grpc
from typing import Dict, Any
from grpc_generated import api_pb2
from grpc_generated import api_pb2_grpc


class GrpcClient:
    """Client for the Bibliophage LoadingService"""

    # Enum mappings
    RPG_SYSTEM_MAP = {
        'DND_35': api_pb2.RpgSystem.DND_35,
        'PATHFINDER_1E': api_pb2.RpgSystem.PATHFINDER_1E,
        'PATHFINDER_2E': api_pb2.RpgSystem.PATHFINDER_2E,
    }

    PUBLICATION_TYPE_MAP = {
        'CORE_RULEBOOK': api_pb2.PublicationType.CORE_RULEBOOK,
        'BESTIARY': api_pb2.PublicationType.BESTIARY,
        'SUPPLEMENT': api_pb2.PublicationType.SUPPLEMENT,
        'ADVENTURE': api_pb2.PublicationType.ADVENTURE,
        'SETTING': api_pb2.PublicationType.SETTING,
    }

    def __init__(self, server_address: str, server_port: int):
        """
        Initialize the gRPC client.

        Args:
            server_address: The server hostname or IP address
            server_port: The server port number
        """
        self.target = f'{server_address}:{server_port}'
        self.channel = None
        self.stub = None

    def connect(self):
        """Establish connection to the gRPC server"""
        self.channel = grpc.insecure_channel(self.target)
        self.stub = api_pb2_grpc.LoadingServiceStub(self.channel)

    def load_pdf(
        self,
        pdf_path: str,
        pdf_name: str,
        rpg_system: str,
        publication_type: str,
        chunk_size: int = 600,
        chunk_overlap: int = 50
    ) -> Dict[str, Any]:
        """
        Send a LoadPDF request to the server.

        Args:
            pdf_path: Filesystem path to the PDF file
            pdf_name: Human-readable name for the PDF
            rpg_system: RPG system identifier (e.g., 'PATHFINDER_1E')
            publication_type: Publication type (e.g., 'BESTIARY')
            chunk_size: Size of text chunks (default: 600)
            chunk_overlap: Overlap between chunks (default: 50)

        Returns:
            Dictionary with response data:
            {
                'success': bool,
                'message': str,
                'chunks_created': int,
                'document_id': str
            }
        """
        if not self.channel:
            self.connect()

        # Build the protobuf request
        request = api_pb2.LoadRequest(
            pdf_origin_path=pdf_path,
            pdf_name=pdf_name,
            pdf_system=self.RPG_SYSTEM_MAP.get(rpg_system, api_pb2.RpgSystem.DND_35),
            pdf_type=self.PUBLICATION_TYPE_MAP.get(publication_type, api_pb2.PublicationType.SUPPLEMENT),
            pdf_page_count=0,  # Will be calculated by server
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        try:
            response = self.stub.LoadPDF(request)
            return {
                'success': response.success,
                'message': response.message,
                'chunks_created': response.chunks_created,
                'document_id': response.document_id if response.document_id else 'N/A'
            }
        except grpc.RpcError as e:
            raise Exception(f'gRPC error: {e.code()} - {e.details()}')

    def close(self):
        """Close the gRPC channel"""
        if self.channel:
            self.channel.close()
            self.channel = None
            self.stub = None

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
