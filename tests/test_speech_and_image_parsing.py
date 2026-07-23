'''
AEGIS-DocIntel / AMDI-OS — Speech & Multimodal Image Parsing Test Suite
========================================================================
Verifies speech audio ingestion, STT transcription, speaker diarization,
audio quality metrics, visual document image layout decomposition, sharpness score,
and REST API endpoints.
'''
from __future__ import annotations

import io
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from src.core.document_object import DocumentFormat
from src.ingestion.speech_loader import SpeechLoader
from src.ingestion.image_parser import AdvancedImageParser
from src.ingestion.service import IngestionService
from ui.src.pages.speech_image_dashboard import (
    SpeechImageDashboard,
    AudioMetadataViewData,
    AudioTranscriptViewData,
    ImageQualityViewData,
    ImageLayoutRegionViewData,
)
from src.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_speech_loader_direct():
    loader = SpeechLoader()
    # Dummy RIFF WAV header
    wav_header = b"RIFF____WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data____" + (b"\x00" * 32000)
    
    assert loader.validate(wav_header) is True
    doc = await loader.load(wav_header, filename="meeting_recording.wav")

    assert doc.format == DocumentFormat.SPEECH
    assert doc.metadata["sample_rate"] == 16000
    assert doc.metadata["duration_seconds"] > 0.0
    assert len(doc.text_content) > 0


def test_advanced_image_parser_direct():
    img = Image.new("RGB", (600, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 580, 80], fill=(200, 200, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    parser = AdvancedImageParser(blur_threshold=50.0)
    res = parser.parse_image(buf.getvalue())

    assert res.width == 600
    assert res.height == 800
    assert res.sharpness_score >= 0.0
    assert len(res.layout_regions) >= 4
    assert res.detected_tables_count >= 1
    assert len(res.visual_feature_vector) == 128


@pytest.mark.asyncio
async def test_ingestion_service_speech_routing():
    service = IngestionService()
    wav_header = b"RIFF____WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data____" + (b"\x00" * 16000)
    
    doc = await service.ingest(wav_header, filename="interview.wav")
    assert doc.format == DocumentFormat.SPEECH


def test_api_parse_speech_endpoint():
    resp = client.post(
        "/v1/advanced/ingestion/parse-speech",
        json={"filename": "interview_session.wav"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["format"] == "speech"
    assert "transcript" in data


def test_api_parse_image_layout_endpoint():
    resp = client.post(
        "/v1/advanced/ingestion/parse-image-layout",
        json={"filename": "doc_scan.png", "blur_threshold": 100.0},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["width"] == 800
    assert data["height"] == 1000
    assert "layout_regions" in data


def test_speech_image_dashboard_ui():
    db = SpeechImageDashboard()
    doc_id = "doc_speech_1"

    db.set_audio_metadata(doc_id, AudioMetadataViewData("audio.wav", 120.0, 1, 16000, 256, 28.5, 2, "en"))
    db.add_transcript_segment(doc_id, AudioTranscriptViewData(0, 0.0, 5.0, "Speaker 1", "Hello world"))
    db.set_image_quality(doc_id, ImageQualityViewData(800, 1000, 150.0, 0.25, False, 1))
    db.add_layout_region(doc_id, ImageLayoutRegionViewData("r1", "heading", [0.1, 0.1, 0.8, 0.1], 0.98, "Title"))

    rendered = db.render_dashboard(doc_id)
    assert rendered["document_id"] == doc_id
    assert rendered["audio_metadata"]["speaker_count"] == 2
    assert len(rendered["transcript_segments"]) == 1
    assert rendered["image_quality"]["sharpness_score"] == 150.0
    assert len(rendered["layout_regions"]) == 1
