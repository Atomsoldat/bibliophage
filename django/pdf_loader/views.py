from django.shortcuts import render
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import tempfile

from .forms import PdfUploadForm
from .grpc_client import GrpcClient


def index(request):
    """Main view for PDF upload and loading"""

    output_text = ''

    if request.method == 'POST':
        form = PdfUploadForm(request.POST, request.FILES)

        if form.is_valid():
            # Get form data
            server_address = form.cleaned_data['server_address']
            server_port = form.cleaned_data['server_port']
            pdf_file = form.cleaned_data['pdf_file']
            pdf_name = form.cleaned_data['pdf_name']
            rpg_system = form.cleaned_data['rpg_system']
            publication_type = form.cleaned_data['publication_type']
            chunk_size = form.cleaned_data['chunk_size']
            chunk_overlap = form.cleaned_data['chunk_overlap']

            output_text = f'Connecting to server at {server_address}:{server_port}...\n'

            try:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    for chunk in pdf_file.chunks():
                        tmp_file.write(chunk)
                    tmp_file_path = tmp_file.name

                output_text += 'Sending LoadPDF request...\n'

                # Create gRPC client and send request
                with GrpcClient(server_address, server_port) as client:
                    response = client.load_pdf(
                        pdf_path=tmp_file_path,
                        pdf_name=pdf_name,
                        rpg_system=rpg_system,
                        publication_type=publication_type,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap
                    )

                # Clean up temporary file
                os.unlink(tmp_file_path)

                # Process response
                if response['success']:
                    output_text += '\nSUCCESS!\n'
                    output_text += f"Message: {response['message']}\n"
                    output_text += f"Chunks created: {response['chunks_created']}\n"
                    output_text += f"Document ID: {response['document_id']}\n"
                    messages.success(request, 'PDF loaded successfully!')
                else:
                    output_text += '\nFAILED!\n'
                    output_text += f"Message: {response['message']}\n"
                    messages.error(request, 'Failed to load PDF')

            except Exception as e:
                output_text += f'\nERROR: {str(e)}\n'
                messages.error(request, f'Error: {str(e)}')

                # Clean up temporary file if it exists
                if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
    else:
        form = PdfUploadForm()

    context = {
        'form': form,
        'output_text': output_text,
    }

    return render(request, 'pdf_loader/index.html', context)
