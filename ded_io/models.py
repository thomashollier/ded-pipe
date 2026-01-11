"""
Data models for the footage ingest pipeline.
Defines the structure of data passed between pipeline stages.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class EditorialCutInfo:
    """Represents editorial cut information for a shot."""
    sequence: str
    shot: str
    source_file: Path
    in_point: int  # Frame number or timecode
    out_point: int  # Frame number or timecode
    source_timecode_start: Optional[str] = None
    source_fps: float = 24.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_frames(self) -> int:
        """Calculate duration in frames."""
        return self.out_point - self.in_point + 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'sequence': self.sequence,
            'shot': self.shot,
            'source_file': str(self.source_file),
            'in_point': self.in_point,
            'out_point': self.out_point,
            'source_timecode_start': self.source_timecode_start,
            'source_fps': self.source_fps,
            'duration_frames': self.duration_frames,
            'metadata': self.metadata
        }


@dataclass
class ShotInfo:
    """Complete shot information including editorial and processing details."""
    project: str
    sequence: str
    shot: str
    editorial_info: EditorialCutInfo
    
    # Naming convention fields (new)
    task_type: str = "pla"  # Task type abbreviation (pla, rnd, cmp, etc.)
    element_name: str = "rawPlate"  # Element identifier
    version: int = 1  # Version number
    representation: str = "main"  # Representation (main, proxy, etc.)
    
    # Processing information
    first_frame: int = 993  # Default from config
    last_frame: Optional[int] = None
    total_frames: Optional[int] = None
    
    # Paths (updated for new structure)
    source_raw_path: Optional[Path] = None
    output_sequence_path: Optional[Path] = None  # Path to colorspace directory
    output_proxy_path: Optional[Path] = None  # Path to proxy file
    version_container_path: Optional[Path] = None  # Path to version container
    
    # Status
    processing_status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Calculate frame ranges after initialization."""
        if self.last_frame is None:
            # Calculate based on editorial info and handles
            from .config import PipelineConfig
            duration = self.editorial_info.duration_frames
            handles = PipelineConfig.HEAD_HANDLE_FRAMES + PipelineConfig.TAIL_HANDLE_FRAMES
            self.total_frames = duration + handles
            self.last_frame = self.first_frame + self.total_frames - 1
    
    @property
    def shot_name(self) -> str:
        """Get full shot name (e.g., 'sht100')."""
        from .config import PipelineConfig
        return PipelineConfig.format_shot_name(self.sequence, self.shot)
    
    @property
    def version_string(self) -> str:
        """Get formatted version string (e.g., 'v001')."""
        from .config import PipelineConfig
        return PipelineConfig.format_version(self.version)
    
    @property
    def version_container_name(self) -> str:
        """
        Get version container directory name.
        
        Returns:
            Version container name (e.g., 'sht100_pla_rawPlate_v001')
        """
        from .config import PipelineConfig
        return PipelineConfig.get_version_container_name(
            self.shot_name, self.task_type, self.element_name, self.version
        )
    
    @property
    def frame_range(self) -> str:
        """Get frame range as string."""
        return f"{self.first_frame}-{self.last_frame}"
    
    def get_base_filename(self, colorspace: str) -> str:
        """
        Get base filename for this shot.
        
        Args:
            colorspace: Colorspace name (e.g., 'ACEScg')
            
        Returns:
            Base filename (e.g., 'sht100_pla_rawPlate_v001_main_ACEScg')
        """
        from .config import PipelineConfig
        return PipelineConfig.get_base_filename(
            self.shot_name, self.task_type, self.element_name,
            self.version, self.representation, colorspace
        )
    
    def get_sequence_filename(self, frame: int, colorspace: str, extension: str) -> str:
        """
        Get filename for a specific frame.
        
        Args:
            frame: Frame number
            colorspace: Colorspace name
            extension: File extension (without dot)
            
        Returns:
            Full filename (e.g., 'sht100_pla_rawPlate_v001_main_ACEScg.0993.exr')
        """
        from .config import PipelineConfig
        return PipelineConfig.get_sequence_filename(
            self.shot_name, self.task_type, self.element_name,
            self.version, self.representation, colorspace, frame, extension
        )
    
    def get_proxy_filename(self, colorspace: str = "sRGB", extension: str = "mov") -> str:
        """
        Get proxy filename.
        
        Args:
            colorspace: Colorspace name (default: 'sRGB')
            extension: File extension (default: 'mov')
            
        Returns:
            Proxy filename (e.g., 'sht100_pla_rawPlate_v001_proxy_sRGB.mov')
        """
        from .config import PipelineConfig
        return PipelineConfig.get_movie_filename(
            self.shot_name, self.task_type, self.element_name,
            self.version, "proxy", colorspace, extension
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'project': self.project,
            'sequence': self.sequence,
            'shot': self.shot,
            'shot_name': self.shot_name,
            'task_type': self.task_type,
            'element_name': self.element_name,
            'version': self.version,
            'version_string': self.version_string,
            'version_container_name': self.version_container_name,
            'representation': self.representation,
            'first_frame': self.first_frame,
            'last_frame': self.last_frame,
            'total_frames': self.total_frames,
            'frame_range': self.frame_range,
            'source_raw_path': str(self.source_raw_path) if self.source_raw_path else None,
            'output_sequence_path': str(self.output_sequence_path) if self.output_sequence_path else None,
            'output_proxy_path': str(self.output_proxy_path) if self.output_proxy_path else None,
            'version_container_path': str(self.version_container_path) if self.version_container_path else None,
            'processing_status': self.processing_status,
            'editorial_info': self.editorial_info.to_dict(),
            'created_at': self.created_at.isoformat()
        }


@dataclass
class ProcessingResult:
    """Result of a pipeline processing stage."""
    stage_name: str
    success: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration_seconds: Optional[float] = None
    
    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'stage_name': self.stage_name,
            'success': self.success,
            'message': self.message,
            'data': self.data,
            'errors': self.errors,
            'warnings': self.warnings,
            'duration_seconds': self.duration_seconds
        }


@dataclass
class ImageSequence:
    """Represents an image sequence."""
    directory: Path
    base_name: str
    extension: str
    first_frame: int
    last_frame: int
    frame_padding: int = 4
    
    @property
    def total_frames(self) -> int:
        """Get total number of frames."""
        return self.last_frame - self.first_frame + 1
    
    @property
    def pattern(self) -> str:
        """Get the sequence pattern (e.g., 'shot.%04d.exr')."""
        return f"{self.base_name}.%0{self.frame_padding}d.{self.extension}"
    
    @property
    def full_pattern(self) -> Path:
        """Get full path pattern."""
        return self.directory / self.pattern
    
    def get_frame_path(self, frame: int) -> Path:
        """Get path for a specific frame."""
        frame_str = str(frame).zfill(self.frame_padding)
        return self.directory / f"{self.base_name}.{frame_str}.{self.extension}"
    
    def verify_exists(self) -> List[int]:
        """Verify which frames exist on disk."""
        existing_frames = []
        for frame in range(self.first_frame, self.last_frame + 1):
            if self.get_frame_path(frame).exists():
                existing_frames.append(frame)
        return existing_frames
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'directory': str(self.directory),
            'base_name': self.base_name,
            'extension': self.extension,
            'first_frame': self.first_frame,
            'last_frame': self.last_frame,
            'total_frames': self.total_frames,
            'pattern': self.pattern,
            'full_pattern': str(self.full_pattern)
        }
