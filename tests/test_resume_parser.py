"""Unit tests for resume text extraction."""

import os
import pytest
from matcher.matcher import extract_resume_text


class TestExtractResumeText:
    """Tests for extract_resume_text function."""

    def test_file_not_found_raises_error(self, tmp_path):
        """Raises FileNotFoundError when PDF path doesn't exist."""
        fake_path = str(tmp_path / "nonexistent.pdf")
        with pytest.raises(FileNotFoundError, match="Resume PDF not found"):
            extract_resume_text(fake_path)

    def test_corrupted_pdf_raises_value_error(self, tmp_path):
        """Raises ValueError when PDF is corrupted/unreadable."""
        corrupted = tmp_path / "corrupted.pdf"
        corrupted.write_bytes(b"this is not a valid pdf file content")
        with pytest.raises(ValueError, match="corrupted or unreadable"):
            extract_resume_text(str(corrupted))

    def test_empty_pdf_raises_value_error(self, tmp_path):
        """Raises ValueError when PDF has no extractable text."""
        # Create a minimal valid PDF with no text content
        from PyPDF2 import PdfWriter

        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        empty_pdf = tmp_path / "empty.pdf"
        with open(empty_pdf, "wb") as f:
            writer.write(f)

        with pytest.raises(ValueError, match="No extractable text"):
            extract_resume_text(str(empty_pdf))

    def test_valid_pdf_returns_text(self, tmp_path):
        """Returns extracted text from a valid PDF with text content."""
        from PyPDF2 import PdfWriter
        from PyPDF2.generic import AnnotationBuilder
        import io
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.pagesizes import letter

        # Use reportlab if available, otherwise create a simple PDF with PyPDF2
        try:
            # Create a PDF with actual text using reportlab
            buf = io.BytesIO()
            c = rl_canvas.Canvas(buf, pagesize=letter)
            c.drawString(72, 720, "John Doe")
            c.drawString(72, 700, "Software Engineer")
            c.drawString(72, 680, "Python, Machine Learning")
            c.save()
            buf.seek(0)

            pdf_path = tmp_path / "resume.pdf"
            pdf_path.write_bytes(buf.read())

            result = extract_resume_text(str(pdf_path))
            assert "John Doe" in result
            assert "Software Engineer" in result
            assert "Python" in result
        except ImportError:
            # If reportlab is not available, test with the actual resume file
            resume_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "resume", "resume.pdf"
            )
            if os.path.exists(resume_path):
                result = extract_resume_text(resume_path)
                assert isinstance(result, str)
                assert len(result) > 0

    def test_actual_resume_extraction(self):
        """Tests extraction on the actual resume file if it exists."""
        resume_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "resume", "resume.pdf"
        )
        if not os.path.exists(resume_path):
            pytest.skip("No resume.pdf found at resume/resume.pdf")

        result = extract_resume_text(resume_path)
        assert isinstance(result, str)
        assert len(result) > 0
        # Text should contain newlines from page separation
        # (only if multi-page, but at minimum it should be non-empty)

    def test_returns_string_type(self, tmp_path):
        """Return type is always a string."""
        resume_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "resume", "resume.pdf"
        )
        if not os.path.exists(resume_path):
            pytest.skip("No resume.pdf found at resume/resume.pdf")

        result = extract_resume_text(resume_path)
        assert isinstance(result, str)
