import pytest
from pathlib import Path
import subprocess
import os


# this decorator allows tests to use this function as an argument
# the function is automatically called and returns the path to our pdf
# tmp_path is a fixture built into pytest, which handles the creation and cleanup for us
@pytest.fixture
def sample_pdf(tmp_path):
    """Generate PDF from markdown fixture."""
    fixture_dir = Path(__file__).parent / "data"
    md_file = fixture_dir / "bestiary_sample.md"
    pdf_file = tmp_path / "bestiary_sample.pdf"
    
    subprocess.run(['pandoc', str(md_file), '-o', str(pdf_file)], check=True)
    return pdf_file

def test_pdf_creation(sample_pdf):
    assert os.path.exists(sample_pdf)
