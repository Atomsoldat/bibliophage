import os
import subprocess
from pathlib import Path

import pytest

import bibliophage.v1alpha3.pdf_pb2 as pdf_api


# this decorator allows tests to use this function as an argument
# the function is automatically called and returns the path to our pdf
# tmp_path is a fixture built into pytest, which handles the creation and cleanup for us
@pytest.fixture
def sample_pdf(tmp_path):
    """Generate PDF from markdown fixture."""
    fixture_dir = Path(__file__).parent / "data"
    md_file = fixture_dir / "bestiary_sample.md"
    pdf_file = tmp_path / "bestiary_sample.pdf"

    subprocess.run(["pandoc", str(md_file), "-o", str(pdf_file)], check=True)
    return pdf_file

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
