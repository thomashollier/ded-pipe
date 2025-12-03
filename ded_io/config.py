"""
Configuration module for the footage ingest pipeline.
Contains all constants and settings used across the pipeline.

Updated to follow standard VFX naming convention:
{shot}_{task}_{element}_v{version}_{rep}_{colorspace}.####.ext
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
    
    # ============================================================================
    # NAMING CONVENTION - Standard VFX Format
    # ============================================================================
    
    # Task type abbreviations (3-letter codes)
    TASK_TYPE_PLATES = "pla"      # Raw plates, clean plates, paint-fixed plates
    TASK_TYPE_OUTPUT = "out"      # Final comp outputs
    TASK_TYPE_RENDER = "rnd"      # CG renders
    TASK_TYPE_MAYA = "mya"        # Maya scenes
    TASK_TYPE_ASSET = "ast"       # Assets (ABC, FBX, USD)
    TASK_TYPE_COMP = "cmp"        # Comp scripts (Nuke)
    TASK_TYPE_REFERENCE = "ref"   # Reference images/photos
    
    # Default element names by task type
    ELEMENT_RAW_PLATE = "rawPlate"
    ELEMENT_CLEAN_PLATE = "cleanPlate"
    ELEMENT_BG_PLATE = "bgPlate"
    ELEMENT_FINAL_COMP = "finalComp"
    
    # Representation types
    REP_MAIN = "main"        # Main/hero representation
    REP_PROXY = "proxy"      # Proxy/preview representation
    
    # Colorspace names (for filenames and directories)
    COLORSPACE_ACESCG = "ACEScg"
    COLORSPACE_SRGB = "sRGB"
    
    # Padding
    VERSION_PADDING = 3      # v001, v002, v003
    FRAME_PADDING = 4        # 0993, 0994, 0995
    
    # Directory structure (new convention)
    # Root: {shot}/
    #   Task: {task}/
    #     Version: {shot}_{task}_{element}_v{version}/
    #       Colorspace: {rep}_{colorspace}/ (for sequences only)
    #         Files: {shot}_{task}_{element}_v{version}_{rep}_{colorspace}.####.ext
    #       Proxy: {shot}_{task}_{element}_v{version}_{rep}_{colorspace}.mov (at version level)
    
    SHOT_TREE_ROOT = Path("/mnt/projects")
    
    @classmethod
    def format_shot_name(cls, sequence: str, shot: str) -> str:
        """
        Format shot name from sequence and shot number.
        
        Args:
            sequence: Sequence name (e.g., "sht")
            shot: Shot number (e.g., "100")
            
        Returns:
            Shot name (e.g., "sht100")
        """
        return f"{sequence}{shot}"
    
    @classmethod
    def format_version(cls, version: int) -> str:
        """
        Format version number with padding.
        
        Args:
            version: Version number (e.g., 1)
            
        Returns:
            Formatted version (e.g., "v001")
        """
        return f"v{version:0{cls.VERSION_PADDING}d}"
    
    @classmethod
    def format_frame(cls, frame: int) -> str:
        """
        Format frame number with padding.
        
        Args:
            frame: Frame number (e.g., 993)
            
        Returns:
            Formatted frame (e.g., "0993")
        """
        return f"{frame:0{cls.FRAME_PADDING}d}"
    
    @classmethod
    def get_version_container_name(cls, shot_name: str, task: str, element: str, version: int) -> str:
        """
        Generate version container directory name.
        
        Args:
            shot_name: Shot name (e.g., "sht100")
            task: Task type (e.g., "pla")
            element: Element name (e.g., "rawPlate")
            version: Version number (e.g., 1)
            
        Returns:
            Version container name (e.g., "sht100_pla_rawPlate_v001")
        """
        return f"{shot_name}_{task}_{element}_{cls.format_version(version)}"
    
    @classmethod
    def get_base_filename(cls, shot_name: str, task: str, element: str, version: int, 
                         rep: str, colorspace: str) -> str:
        """
        Generate base filename (without frame number and extension).
        
        Args:
            shot_name: Shot name (e.g., "sht100")
            task: Task type (e.g., "pla")
            element: Element name (e.g., "rawPlate")
            version: Version number (e.g., 1)
            rep: Representation (e.g., "main")
            colorspace: Colorspace (e.g., "ACEScg")
            
        Returns:
            Base filename (e.g., "sht100_pla_rawPlate_v001_main_ACEScg")
        """
        version_str = cls.format_version(version)
        return f"{shot_name}_{task}_{element}_{version_str}_{rep}_{colorspace}"
    
    @classmethod
    def get_sequence_filename(cls, shot_name: str, task: str, element: str, version: int,
                              rep: str, colorspace: str, frame: int, extension: str) -> str:
        """
        Generate full filename for image sequence frame.
        
        Args:
            shot_name: Shot name (e.g., "sht100")
            task: Task type (e.g., "pla")
            element: Element name (e.g., "rawPlate")
            version: Version number (e.g., 1)
            rep: Representation (e.g., "main")
            colorspace: Colorspace (e.g., "ACEScg")
            frame: Frame number (e.g., 993)
            extension: File extension without dot (e.g., "exr")
            
        Returns:
            Full filename (e.g., "sht100_pla_rawPlate_v001_main_ACEScg.0993.exr")
        """
        base = cls.get_base_filename(shot_name, task, element, version, rep, colorspace)
        frame_str = cls.format_frame(frame)
        return f"{base}.{frame_str}.{extension}"
    
    @classmethod
    def get_movie_filename(cls, shot_name: str, task: str, element: str, version: int,
                          rep: str, colorspace: str, extension: str = "mov") -> str:
        """
        Generate filename for movie file (proxy, etc.).
        
        Args:
            shot_name: Shot name (e.g., "sht100")
            task: Task type (e.g., "pla")
            element: Element name (e.g., "rawPlate")
            version: Version number (e.g., 1)
            rep: Representation (e.g., "proxy")
            colorspace: Colorspace (e.g., "sRGB")
            extension: File extension without dot (default: "mov")
            
        Returns:
            Full filename (e.g., "sht100_pla_rawPlate_v001_proxy_sRGB.mov")
        """
        base = cls.get_base_filename(shot_name, task, element, version, rep, colorspace)
        return f"{base}.{extension}"
    
    @classmethod
    def get_shot_path(cls, shot_name: str) -> Path:
        """
        Generate the shot root directory path.
        
        Args:
            shot_name: Shot name (e.g., "sht100")
            
        Returns:
            Path to shot root (e.g., "/mnt/projects/sht100")
        """
        return cls.SHOT_TREE_ROOT / shot_name
    
    @classmethod
    def get_task_path(cls, shot_name: str, task: str) -> Path:
        """
        Generate the task directory path.
        
        Args:
            shot_name: Shot name (e.g., "sht100")
            task: Task type (e.g., "pla")
            
        Returns:
            Path to task directory (e.g., "/mnt/projects/sht100/pla")
        """
        return cls.get_shot_path(shot_name) / task
    
    @classmethod
    def get_version_path(cls, shot_name: str, task: str, element: str, version: int) -> Path:
        """
        Generate the version container directory path.
        
        Args:
            shot_name: Shot name (e.g., "sht100")
            task: Task type (e.g., "pla")
            element: Element name (e.g., "rawPlate")
            version: Version number (e.g., 1)
            
        Returns:
            Path to version container (e.g., "/mnt/projects/sht100/pla/sht100_pla_rawPlate_v001")
        """
        container_name = cls.get_version_container_name(shot_name, task, element, version)
        return cls.get_task_path(shot_name, task) / container_name
    
    @classmethod
    def get_colorspace_path(cls, shot_name: str, task: str, element: str, version: int,
                           rep: str, colorspace: str) -> Path:
        """
        Generate the colorspace directory path (for image sequences).
        
        Args:
            shot_name: Shot name (e.g., "sht100")
            task: Task type (e.g., "pla")
            element: Element name (e.g., "rawPlate")
            version: Version number (e.g., 1)
            rep: Representation (e.g., "main")
            colorspace: Colorspace (e.g., "ACEScg")
            
        Returns:
            Path to colorspace directory (e.g., "/mnt/projects/sht100/pla/sht100_pla_rawPlate_v001/main_ACEScg")
        """
        version_path = cls.get_version_path(shot_name, task, element, version)
        return version_path / f"{rep}_{colorspace}"
    
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
