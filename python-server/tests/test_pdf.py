import os
import subprocess
from pathlib import Path

import pytest

import bibliophage.v1alpha3.pdf_pb2 as pdf_api


# TODO: is this the correct marker here? we are basically testing a test...
@pytest.mark.integration
def test_pdf_creation(sample_pdf):
    assert os.path.exists(sample_pdf)


# This decorator tells pytest that the function is asynchronous
# pytest will run the function in an event loop
# asynchronous functions just return a coroutine object when invoked, which does not
# cause the function itself to be executed
@pytest.mark.asyncio
async def test_load_pdf_integration(sample_pdf, pdf_client):
    """Integration test: Load a PDF via the PDF service API."""
    # Read PDF bytes
    with Path.open(sample_pdf, "rb") as f:
        pdf_bytes = f.read()

    request = pdf_api.LoadPdfRequest()
    request.pdf.name = "Test Bestiary"
    request.pdf.systems.append("Fantasy RPG")
    request.pdf.type = "BESTIARY"
    request.file_data = pdf_bytes

    # Call service
    response = await pdf_client.load_pdf(request)

    assert response.success
    assert response.pdf.page_count > 0
    assert response.pdf.name == "Test Bestiary"
