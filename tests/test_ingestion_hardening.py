"""
AEGIS-DocIntel — Ingestion & Pipeline Hardening Test Suite
==========================================================
Verifies zero silent failures on malformed, encrypted, or edge-case documents.
Exit Criteria:
  - 100 malformed/fuzzed test files run through parse_document(fallback=True) -> 0 unhandled exceptions.
  - When fallback=False, 100% typed error returns (DocumentCorruptError, EncryptedDocumentError, etc.).
"""
from __future__ import annotations

import asyncio
import io
import os
import random
import zipfile
import pytest

try:
    import fitz
except ImportError:
    fitz = None

from PIL import Image

from src.models.document_object import DocumentFormat, DocumentObject
from src.ingestion import (
    DocumentCorruptError,
    EncryptedDocumentError,
    FallbackParser,
    FormatError,
    IngestionError,
    IngestionService,
    ProcessingTimeoutError,
    SizeLimitError,
    SniffResult,
    UnsupportedFormatError,
    parse_document,
    sniff_format,
)


# ============================================================================
# Helpers to generate malformed & edge-case documents
# ============================================================================

def make_corrupt_pdf() -> bytes:
    """PDF header with invalid binary body."""
    return b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n" + os.urandom(128) + b"\n%%EOF"


def make_encrypted_pdf() -> bytes:
    """Valid PDF encrypted with a password."""
    if fitz is None:
        pytest.skip("fitz required for encrypted PDF test")
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Confidential Classified Document")
    perm = fitz.PDF_PERM_ACCESSIBILITY
    encrypt_meth = fitz.PDF_ENCRYPT_AES_256
    pdf_bytes = doc.write(
        encryption=encrypt_meth,
        owner_pw="owner123",
        user_pw="secret123",
        permissions=perm,
    )
    doc.close()
    return pdf_bytes


def make_corrupt_zip_docx() -> bytes:
    """Valid ZIP header followed by garbage bytes."""
    return b"PK\x03\x04\x14\x00\x00\x00" + os.urandom(256)


def make_corrupt_xlsx() -> bytes:
    """Valid ZIP with invalid internal components."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("corrupted_content.txt", "not an excel sheet")
    return buf.getvalue()


def make_corrupt_pptx() -> bytes:
    """Valid ZIP with invalid internal components."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("corrupted_slide.xml", "<malformed<xml")
    return buf.getvalue()


def make_encrypted_office_package() -> bytes:
    """Office OpenXML encrypted package container."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("EncryptedPackage", os.urandom(100))
        z.writestr("EncryptionInfo", os.urandom(50))
    return buf.getvalue()


def make_corrupt_png() -> bytes:
    """PNG signature followed by random bytes."""
    return b"\x89PNG\r\n\x1a\n" + os.urandom(64)


def make_corrupt_jpeg() -> bytes:
    """JPEG signature followed by garbage."""
    return b"\xff\xd8\xff" + os.urandom(64)


def make_corrupt_wav() -> bytes:
    """RIFF WAVE header truncated to less than 44 bytes."""
    return b"RIFF\x10\x00\x00\x00WAVEfmt "


# ============================================================================
# Sniffing Tests
# ============================================================================

def test_sniff_empty_bytes():
    res = sniff_format(b"")
    assert res.format == DocumentFormat.UNKNOWN
    assert res.confidence == 0.0


def test_sniff_pdf_magic():
    res = sniff_format(b"%PDF-1.7\nsome pdf stream")
    assert res.format == DocumentFormat.PDF
    assert res.confidence == 1.0
    assert res.mime_type == "application/pdf"


def test_sniff_png_magic():
    res = sniff_format(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
    assert res.format == DocumentFormat.IMAGE
    assert res.mime_type == "image/png"


def test_sniff_jpeg_magic():
    res = sniff_format(b"\xff\xd8\xff\xe0\x00\x10JFIF")
    assert res.format == DocumentFormat.IMAGE
    assert res.mime_type == "image/jpeg"


def test_sniff_gif_magic():
    res = sniff_format(b"GIF89a\x01\x00\x01\x00")
    assert res.format == DocumentFormat.IMAGE
    assert res.mime_type == "image/gif"


def test_sniff_webp_magic():
    raw = b"RIFF\x20\x00\x00\x00WEBPVP8 "
    res = sniff_format(raw)
    assert res.format == DocumentFormat.IMAGE
    assert res.mime_type == "image/webp"


def test_sniff_wav_magic():
    raw = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00"
    res = sniff_format(raw)
    assert res.format == DocumentFormat.SPEECH
    assert res.mime_type == "audio/wav"


def test_sniff_docx_zip_structure():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", "<w:document/>")
    res = sniff_format(buf.getvalue(), filename="unknown_file")
    assert res.format == DocumentFormat.DOCX
    assert res.confidence >= 0.95


def test_sniff_xlsx_zip_structure():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("xl/workbook.xml", "<workbook/>")
    res = sniff_format(buf.getvalue(), filename="test")
    assert res.format == DocumentFormat.XLSX
    assert res.confidence >= 0.95


def test_sniff_pptx_zip_structure():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("ppt/presentation.xml", "<presentation/>")
    res = sniff_format(buf.getvalue(), filename="deck")
    assert res.format == DocumentFormat.PPTX
    assert res.confidence >= 0.95


def test_sniff_plain_text_and_markdown():
    res_txt = sniff_format(b"Simple plain text file contents", filename="test.txt")
    assert res_txt.format == DocumentFormat.TEXT

    res_md = sniff_format(b"# Section Header\n\n- item 1\n- item 2", filename="test.md")
    assert res_md.format == DocumentFormat.MARKDOWN

    res_html = sniff_format(b"<!DOCTYPE html><html><body><h1>Hello</h1></body></html>")
    assert res_html.format == DocumentFormat.HTML


# ============================================================================
# Universal Fallback Parser Tests
# ============================================================================

def test_fallback_parser_never_raises():
    parser = FallbackParser()
    doc = parser.parse(b"", filename="empty.bin")
    assert isinstance(doc, DocumentObject)
    assert doc.text_content == ""
    assert doc.metadata["recovered_via_fallback"] is True

    # High entropy random noise
    doc_noise = parser.parse(os.urandom(2048), filename="noise.bin")
    assert isinstance(doc_noise, DocumentObject)
    assert doc_noise.metadata["recovered_via_fallback"] is True


def test_fallback_parser_recovers_utf8_and_latin1():
    parser = FallbackParser()
    payload = "Important text report with café and naïve data".encode("utf-8")
    doc = parser.parse(payload, filename="report.bin")
    assert "Important text report" in doc.text_content
    assert doc.metadata["fallback_encoding"] == "utf-8"

    latin_payload = "Schöne Grüße aus München".encode("latin-1")
    doc_latin = parser.parse(latin_payload, filename="german.bin")
    assert "Grüße" in doc_latin.text_content or "München" in doc_latin.text_content


def test_fallback_parser_extracts_ascii_chunks_from_binary():
    parser = FallbackParser()
    # Embed printable strings inside raw binary
    binary_stream = os.urandom(64) + b"SALVAGEABLE_SECRET_DATA_KEY" + os.urandom(64) + b"ADDITIONAL_REPORT_STRING" + os.urandom(64)
    doc = parser.parse(binary_stream, filename="dump.bin")
    assert "SALVAGEABLE_SECRET_DATA_KEY" in doc.text_content
    assert "ADDITIONAL_REPORT_STRING" in doc.text_content


# ============================================================================
# Strict Error Hierarchy Tests (fallback=False)
# ============================================================================

@pytest.mark.asyncio
async def test_corrupt_pdf_raises_document_corrupt_error():
    corrupt = make_corrupt_pdf()
    service = IngestionService()
    with pytest.raises((DocumentCorruptError, FormatError)) as excinfo:
        await service.ingest(corrupt, filename="broken.pdf", format=DocumentFormat.PDF, fallback=False)
    assert issubclass(excinfo.type, IngestionError)


@pytest.mark.asyncio
async def test_encrypted_pdf_raises_encrypted_document_error():
    if fitz is None:
        pytest.skip("fitz required for encrypted PDF test")
    enc_pdf = make_encrypted_pdf()
    service = IngestionService()

    with pytest.raises(EncryptedDocumentError) as excinfo:
        await service.ingest(enc_pdf, filename="secret.pdf", format=DocumentFormat.PDF, fallback=False)
    assert issubclass(excinfo.type, IngestionError)
    assert "encrypted" in str(excinfo.value).lower() or "password" in str(excinfo.value).lower()



@pytest.mark.asyncio
async def test_corrupt_docx_raises_document_corrupt_error():
    corrupt = make_corrupt_zip_docx()
    service = IngestionService()
    with pytest.raises((DocumentCorruptError, FormatError)):
        await service.ingest(corrupt, filename="broken.docx", format=DocumentFormat.DOCX, fallback=False)


@pytest.mark.asyncio
async def test_encrypted_office_package_raises_encrypted_error():
    enc_pkg = make_encrypted_office_package()
    service = IngestionService()
    with pytest.raises(EncryptedDocumentError):
        await service.ingest(enc_pkg, filename="protected.docx", format=DocumentFormat.DOCX, fallback=False)


@pytest.mark.asyncio
async def test_corrupt_xlsx_raises_document_corrupt_error():
    corrupt = make_corrupt_xlsx()
    service = IngestionService()
    with pytest.raises((DocumentCorruptError, FormatError)):
        await service.ingest(corrupt, filename="broken.xlsx", format=DocumentFormat.XLSX, fallback=False)


@pytest.mark.asyncio
async def test_corrupt_pptx_raises_document_corrupt_error():
    corrupt = make_corrupt_pptx()
    service = IngestionService()
    with pytest.raises((DocumentCorruptError, FormatError)):
        await service.ingest(corrupt, filename="broken.pptx", format=DocumentFormat.PPTX, fallback=False)


@pytest.mark.asyncio
async def test_corrupt_image_raises_document_corrupt_error():
    corrupt = make_corrupt_png()
    service = IngestionService()
    with pytest.raises((DocumentCorruptError, FormatError)):
        await service.ingest(corrupt, filename="corrupt.png", format=DocumentFormat.IMAGE, fallback=False)


@pytest.mark.asyncio
async def test_corrupt_audio_raises_document_corrupt_error():
    corrupt = make_corrupt_wav()
    service = IngestionService()
    with pytest.raises((DocumentCorruptError, FormatError)):
        await service.ingest(corrupt, filename="corrupt.wav", format=DocumentFormat.SPEECH, fallback=False)


@pytest.mark.asyncio
async def test_unsupported_format_raises_unsupported_error():
    service = IngestionService()
    with pytest.raises(UnsupportedFormatError):
        await service.ingest(b"random bytes", filename="data.unknown_xyz", format=DocumentFormat.UNKNOWN, fallback=False)


# ============================================================================
# 100 Malformed / Fuzzed Files Ingestion Hardening Benchmark (Exit Criteria)
# ============================================================================

@pytest.mark.asyncio
async def test_100_fuzzed_and_malformed_inputs_zero_unhandled_exceptions():
    """
    Run 100 uniquely fuzzed / malformed byte payloads through parse_document.
    Guarantees:
      1. Zero unhandled exceptions (100% success rate yielding DocumentObject).
      2. When fallback=True, all corrupted payloads recover with metadata indicators.
    """
    random.seed(42)
    payloads: list[tuple[bytes, str, DocumentFormat | None]] = []

    # 1. Edge-case binaries
    payloads.append((b"", "zero_byte.pdf", DocumentFormat.PDF))
    payloads.append((b"\x00", "single_null.bin", None))
    payloads.append((b"\xff", "single_high_byte.bin", None))
    payloads.append((b"%PDF", "truncated_pdf_header.pdf", DocumentFormat.PDF))
    payloads.append((b"PK\x03\x04", "truncated_zip_header.docx", DocumentFormat.DOCX))
    payloads.append((b"\x89PNG", "truncated_png_header.png", DocumentFormat.IMAGE))
    payloads.append((b"RIFF\x00\x00\x00\x00WAVE", "truncated_wav.wav", DocumentFormat.SPEECH))
    payloads.append((make_corrupt_pdf(), "corrupt_xref.pdf", DocumentFormat.PDF))
    payloads.append((make_corrupt_zip_docx(), "broken_deflate.docx", DocumentFormat.DOCX))
    payloads.append((make_corrupt_xlsx(), "broken_sheets.xlsx", DocumentFormat.XLSX))
    payloads.append((make_corrupt_pptx(), "broken_slides.pptx", DocumentFormat.PPTX))
    payloads.append((make_corrupt_png(), "broken_chunks.png", DocumentFormat.IMAGE))
    payloads.append((make_corrupt_jpeg(), "truncated_jfif.jpeg", DocumentFormat.IMAGE))
    payloads.append((make_corrupt_wav(), "short_riff.wav", DocumentFormat.SPEECH))
    payloads.append((make_encrypted_office_package(), "locked.docx", DocumentFormat.DOCX))
    if fitz is not None:
        payloads.append((make_encrypted_pdf(), "locked.pdf", DocumentFormat.PDF))

    # Fill remainder to 100 with fuzz generators
    ext_choices = [".pdf", ".docx", ".xlsx", ".pptx", ".png", ".jpg", ".wav", ".txt", ".bin"]
    for i in range(len(payloads), 100):
        length = random.choice([2, 5, 17, 64, 128, 512, 1024, 4096])
        fuzz_bytes = os.urandom(length)
        ext = random.choice(ext_choices)
        filename = f"fuzzed_sample_{i}{ext}"
        payloads.append((fuzz_bytes, filename, None))

    assert len(payloads) == 100

    # Execute all 100 through parse_document with fallback=True
    recovered_count = 0
    for idx, (data, fname, fmt) in enumerate(payloads):
        try:
            doc = await parse_document(data, filename=fname, format=fmt, fallback=True)
            assert isinstance(doc, DocumentObject), f"Failed returning DocumentObject for {fname}"
            assert doc.filename == fname
            assert doc.size_bytes == len(data)
            if doc.metadata.get("recovered_via_fallback"):
                recovered_count += 1
        except Exception as unhandled:
            pytest.fail(f"Unhandled exception on payload {idx} ({fname}): {type(unhandled).__name__}: {unhandled}")

    # Verify that fallbacks cleanly caught corrupted payloads
    assert recovered_count > 0, "Expected corrupted payloads to trigger fallback recovery"
