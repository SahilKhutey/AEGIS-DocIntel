"""
Speech & Multimodal Image Intelligence Dashboard Page
======================================================
Backend API contract and view data structures for the Speech & Image Parsing Dashboard:
  1. Speech-to-Text (STT) Transcription & Speaker Diarization
  2. Audio Signal Metrics (SNR, channels, bitrate, duration)
  3. Visual Document Layout Decomposition (bounding box regions, layout types)
  4. Image Quality Assessment (sharpness, blur detection, contrast)
  5. Multimodal Visual Embeddings (ColPali / ViT vectors)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AudioTranscriptViewData:
    segment_id: int
    start_time: float
    end_time: float
    speaker: str
    text: str
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            "segment_id": self.segment_id,
            "start_time": round(self.start_time, 2),
            "end_time": round(self.end_time, 2),
            "speaker": self.speaker,
            "text": self.text,
            "confidence": round(self.confidence, 4),
        }


@dataclass
class AudioMetadataViewData:
    filename: str
    duration_seconds: float
    channels: int
    sample_rate: int
    bitrate_kbps: int
    snr_db: float
    speaker_count: int = 1
    language: str = "en"

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "duration_seconds": round(self.duration_seconds, 2),
            "channels": self.channels,
            "sample_rate": self.sample_rate,
            "bitrate_kbps": self.bitrate_kbps,
            "snr_db": round(self.snr_db, 1),
            "speaker_count": self.speaker_count,
            "language": self.language,
        }


@dataclass
class ImageLayoutRegionViewData:
    region_id: str
    region_type: str
    bbox: List[float]  # [x, y, w, h]
    confidence: float
    text_content: str = ""

    def to_dict(self) -> dict:
        return {
            "region_id": self.region_id,
            "region_type": self.region_type,
            "bbox": [round(c, 4) for c in self.bbox],
            "confidence": round(self.confidence, 4),
            "text_content": self.text_content,
        }


@dataclass
class ImageQualityViewData:
    width: int
    height: int
    sharpness_score: float
    contrast_ratio: float
    is_blurry: bool
    tables_count: int = 0

    def to_dict(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "sharpness_score": round(self.sharpness_score, 2),
            "contrast_ratio": round(self.contrast_ratio, 4),
            "is_blurry": self.is_blurry,
            "tables_count": self.tables_count,
        }


@dataclass
class SpeechImageData:
    document_id: str
    audio_metadata: Optional[AudioMetadataViewData] = None
    transcript_segments: List[AudioTranscriptViewData] = field(default_factory=list)
    image_quality: Optional[ImageQualityViewData] = None
    layout_regions: List[ImageLayoutRegionViewData] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "audio_metadata": self.audio_metadata.to_dict() if self.audio_metadata else None,
            "transcript_segments": [t.to_dict() for t in self.transcript_segments],
            "image_quality": self.image_quality.to_dict() if self.image_quality else None,
            "layout_regions": [r.to_dict() for r in self.layout_regions],
        }


class SpeechImageDashboard:
    """Speech & Image Intelligence Dashboard Backend API."""

    def __init__(self) -> None:
        self.dashboards: Dict[str, SpeechImageData] = {}

    def get_or_create(self, document_id: str) -> SpeechImageData:
        if document_id not in self.dashboards:
            self.dashboards[document_id] = SpeechImageData(document_id=document_id)
        return self.dashboards[document_id]

    def set_audio_metadata(self, document_id: str, meta: AudioMetadataViewData) -> None:
        dash = self.get_or_create(document_id)
        dash.audio_metadata = meta

    def add_transcript_segment(self, document_id: str, seg: AudioTranscriptViewData) -> None:
        dash = self.get_or_create(document_id)
        dash.transcript_segments.append(seg)

    def set_image_quality(self, document_id: str, quality: ImageQualityViewData) -> None:
        dash = self.get_or_create(document_id)
        dash.image_quality = quality

    def add_layout_region(self, document_id: str, region: ImageLayoutRegionViewData) -> None:
        dash = self.get_or_create(document_id)
        dash.layout_regions.append(region)

    def render_dashboard(self, document_id: str) -> dict:
        dash = self.get_or_create(document_id)
        return dash.to_dict()
