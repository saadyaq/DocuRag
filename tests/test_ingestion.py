from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest

from src.ingestion.pdf_loader import PDFLoader


class TestPDFLoaderInit:
    def test_raises_file_not_found_for_missing_file(self, tmp_path):
        fake_path = tmp_path / "nonexistent.pdf"
        with pytest.raises(FileNotFoundError, match="File not found"):
            PDFLoader(fake_path)

    def test_raises_value_error_for_non_pdf_file(self, tmp_path):
        txt_file = tmp_path / "file.txt"
        txt_file.write_text("hello")
        with pytest.raises(ValueError, match="Not a PDF file"):
            PDFLoader(txt_file)

    def test_accepts_valid_pdf_path(self, tmp_path):
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake content")
        loader = PDFLoader(pdf_file)
        assert loader.file_path == pdf_file

    def test_accepts_uppercase_pdf_extension(self, tmp_path):
        pdf_file = tmp_path / "test.PDF"
        pdf_file.write_bytes(b"%PDF-1.4 fake content")
        loader = PDFLoader(pdf_file)
        assert loader.file_path == pdf_file

    def test_accepts_string_path(self, tmp_path):
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake content")
        loader = PDFLoader(str(pdf_file))
        assert loader.file_path == pdf_file


class TestPDFLoaderLoad:
    @patch("src.ingestion.pdf_loader.fitz")
    def test_load_returns_pages_with_text(self, mock_fitz, tmp_path):
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        mock_page = MagicMock()
        mock_page.get_text.return_value = "Hello world"

        mock_doc = MagicMock()
        mock_doc.__len__ = lambda self: 1
        mock_doc.__getitem__ = lambda self, idx: mock_page
        mock_fitz.open.return_value = mock_doc

        loader = PDFLoader(pdf_file)
        pages = loader.load()

        assert len(pages) == 1
        assert pages[0]["text"] == "Hello world"
        assert pages[0]["page_number"] == 0
        assert pages[0]["source"] == str(pdf_file.resolve())
        mock_doc.close.assert_called_once()

    @patch("src.ingestion.pdf_loader.fitz")
    def test_load_skips_empty_pages(self, mock_fitz, tmp_path):
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        page_with_text = MagicMock()
        page_with_text.get_text.return_value = "Content here"

        empty_page = MagicMock()
        empty_page.get_text.return_value = "   \n  "

        mock_doc = MagicMock()
        mock_doc.__len__ = lambda self: 2
        mock_doc.__getitem__ = lambda self, idx: [page_with_text, empty_page][idx]
        mock_fitz.open.return_value = mock_doc

        loader = PDFLoader(pdf_file)
        pages = loader.load()

        assert len(pages) == 1
        assert pages[0]["page_number"] == 0

    @patch("src.ingestion.pdf_loader.fitz")
    def test_load_multiple_pages(self, mock_fitz, tmp_path):
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        pages_data = ["Page one", "Page two", "Page three"]
        mock_pages = []
        for text in pages_data:
            p = MagicMock()
            p.get_text.return_value = text
            mock_pages.append(p)

        mock_doc = MagicMock()
        mock_doc.__len__ = lambda self: 3
        mock_doc.__getitem__ = lambda self, idx: mock_pages[idx]
        mock_fitz.open.return_value = mock_doc

        loader = PDFLoader(pdf_file)
        pages = loader.load()

        assert len(pages) == 3
        assert [p["page_number"] for p in pages] == [0, 1, 2]
        assert [p["text"] for p in pages] == pages_data

    @patch("src.ingestion.pdf_loader.fitz")
    def test_load_raises_value_error_on_corrupt_file(self, mock_fitz, tmp_path):
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        mock_fitz.open.side_effect = Exception("corrupt")

        loader = PDFLoader(pdf_file)
        with pytest.raises(ValueError, match="Error opening file"):
            loader.load()

    @patch("src.ingestion.pdf_loader.fitz")
    def test_load_returns_empty_list_for_all_empty_pages(self, mock_fitz, tmp_path):
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        empty_page = MagicMock()
        empty_page.get_text.return_value = ""

        mock_doc = MagicMock()
        mock_doc.__len__ = lambda self: 2
        mock_doc.__getitem__ = lambda self, idx: empty_page
        mock_fitz.open.return_value = mock_doc

        loader = PDFLoader(pdf_file)
        pages = loader.load()

        assert pages == []
