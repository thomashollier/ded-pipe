"""
Configuration module for the footage ingest pipeline.
Contains all constants and settings used across the pipeline.
"""
import os
from pathlib import Path
from typing import Dict, Any


class PipelineConfig:
    """Central configuration for the ingest pipeline."""
    
    # Frame numbering
    DIGITAL_START_FRAME = 1001
    HEAD_HANDLE_FRAMES = 8
    TAIL_HANDLE_FRAMES = 8
    SEQUENCE_START_FRAME = DIGITAL_START_FRAME - HEAD_HANDLE_FRAMES  # 993
    
    # Camera and color settings
    CAMERA_TYPE = "Venice2"
    SOURCE_COLORSPACE = "SLog3-SGamut3.Cine"
    TARGET_COLORSPACE = "ACES - ACEScg"
    ACES_VERSION = "1.3"
    
    # Image format settings
    OUTPUT_FORMAT = "exr"
    OUTPUT_COMPRESSION = "dwaa:15"  # DWAA compression with quality 15
    OUTPUT_BIT_DEPTH = "half"  # 16-bit float
    
    # Anamorphic and resolution settings
    ANAMORPHIC_SQUEEZE = 2.0
    TARGET_WIDTH = 3840  # UHD width
    TARGET_HEIGHT = 2160  # UHD height
    LETTERBOX = True
    
    # Proxy settings
    PROXY_FORMAT = "mp4"
    PROXY_CODEC = "libx264"
    PROXY_COLORSPACE = "sRGB"
    PROXY_CRF = 18  # Quality setting for H.264
    PROXY_PRESET = "medium"
    
    # Asset management
    ASSET_TYPE = "plate"
    
    # Tools paths (these should be customized per environment)
    SONY_CONVERT_TOOL = "sony_raw_converter"  # Placeholder
    OIIO_TOOL = "oiiotool"
    FFMPEG_TOOL = "ffmpeg"
    
    # Directory structure
    SHOT_TREE_ROOT = Path("/mnt/projects")
    SEQUENCE_SUBDIR = "sequences"
    PLATES_SUBDIR = "plates"
    PROXY_SUBDIR = "proxy"
    
    @classmethod
    def get_shot_path(cls, project: str, sequence: str, shot: str) -> Path:
        """Generate the shot directory path."""
        return cls.SHOT_TREE_ROOT / project / cls.SEQUENCE_SUBDIR / sequence / shot
    
    @classmethod
    def get_plates_path(cls, project: str, sequence: str, shot: str) -> Path:
        """Generate the plates directory path."""
        return cls.get_shot_path(project, sequence, shot) / cls.PLATES_SUBDIR
    
    @classmethod
    def get_proxy_path(cls, project: str, sequence: str, shot: str) -> Path:
        """Generate the proxy directory path."""
        return cls.get_shot_path(project, sequence, shot) / cls.PROXY_SUBDIR
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            key: value for key, value in cls.__dict__.items()
            if not key.startswith('_') and not callable(value)
        }


class KitsuConfig:
    """Configuration for Kitsu API integration."""
    
    # These should be set via environment variables or a secure config file
    KITSU_HOST = os.getenv("KITSU_HOST", "https://kitsu.example.com/api")
    KITSU_EMAIL = os.getenv("KITSU_EMAIL")
    KITSU_PASSWORD = os.getenv("KITSU_PASSWORD")
    
    # Timeouts
    CONNECTION_TIMEOUT = 30
    READ_TIMEOUT = 120
