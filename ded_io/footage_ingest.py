"""
Footage ingest pipeline implementation.
Specific pipeline for ingesting Venice 2 footage into the production pipeline.
"""
from pathlib import Path
from typing import Optional
import logging

from .pipeline import Pipeline, PipelineBuilder
from .models import ShotInfo, EditorialCutInfo
from .config import PipelineConfig
from .stages import (
    SonyRawConversionStage,
    OIIOColorTransformStage,
    ProxyGenerationStage,
    ShotTreeOrganizationStage,
    KitsuIntegrationStage,
    CleanupStage
)


def create_ingest_pipeline(
    logger: Optional[logging.Logger] = None
) -> Pipeline:
    """
    Create the standard footage ingest pipeline.
    
    Pipeline stages:
    1. Sony raw conversion (MXF to DPX)
    2. Color transform and scaling (DPX to EXR with ACES)
    3. Proxy generation (EXR to MP4)
    4. Shot tree organization
    5. Kitsu integration
    6. Cleanup
    
    Args:
        logger: Optional logger instance
        
    Returns:
        Configured Pipeline object
    """
    builder = PipelineBuilder("FootageIngest")
    
    # Stage 1: Convert Sony raw to DPX
    builder.add_stage(
        SonyRawConversionStage(logger=logger)
    )
    
    # Stage 2: Apply color transform and scale to EXR
    builder.add_stage(
        OIIOColorTransformStage(logger=logger)
    )
    
    # Stage 3: Generate proxy
    builder.add_stage(
        ProxyGenerationStage(logger=logger)
    )
    
    # Stage 4: Organize into shot tree
    builder.add_stage(
        ShotTreeOrganizationStage(logger=logger)
    )
    
    # Stage 5: Register in Kitsu
    builder.add_stage(
        KitsuIntegrationStage(logger=logger)
    )
    
    # Stage 6: Clean up temporary files
    builder.add_stage(
        CleanupStage(logger=logger)
    )
    
    return builder.build()


def ingest_shot(
    project: str,
    sequence: str,
    shot: str,
    source_file: Path,
    in_point: int,
    out_point: int,
    source_fps: float = 24.0,
    task_type: str = "pla",
    element_name: str = "rawPlate",
    version: int = 1,
    project_id: Optional[str] = None,
    logger: Optional[logging.Logger] = None
) -> dict:
    """
    Ingest a single shot through the complete pipeline.
    
    This is the main entry point for processing footage.
    
    Args:
        project: Project name
        sequence: Sequence name (e.g., "sht")
        shot: Shot number (e.g., "100")
        source_file: Path to source raw footage file
        in_point: Editorial in point (frame number)
        out_point: Editorial out point (frame number)
        source_fps: Source footage frame rate
        task_type: Task type abbreviation (default: "pla" for plates)
        element_name: Element identifier (default: "rawPlate")
        version: Version number (default: 1)
        project_id: Kitsu project ID (optional)
        logger: Optional logger instance
        
    Returns:
        Pipeline execution summary
    """
    # Create editorial info
    editorial_info = EditorialCutInfo(
        sequence=sequence,
        shot=shot,
        source_file=Path(source_file),
        in_point=in_point,
        out_point=out_point,
        source_fps=source_fps
    )
    
    # Create shot info with naming convention fields
    shot_info = ShotInfo(
        project=project,
        sequence=sequence,
        shot=shot,
        editorial_info=editorial_info,
        source_raw_path=Path(source_file),
        task_type=task_type,
        element_name=element_name,
        version=version
    )
    
    # Create pipeline
    pipeline = create_ingest_pipeline(logger=logger)
    
    # Execute pipeline
    summary = pipeline.execute(
        shot_info=shot_info,
        stop_on_error=True,
        project_id=project_id
    )
    
    return summary


class FootageIngestPipeline:
    """
    High-level interface for footage ingest operations.
    
    Provides a more object-oriented interface with state management.
    """
    
    def __init__(
        self,
        project: str,
        project_id: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize footage ingest pipeline.
        
        Args:
            project: Project name
            project_id: Kitsu project ID
            logger: Optional logger instance
        """
        self.project = project
        self.project_id = project_id
        self.logger = logger or self._create_logger()
        self.pipeline = create_ingest_pipeline(logger=self.logger)
        self.processed_shots = []
    
    def _create_logger(self) -> logging.Logger:
        """Create logger."""
        logger = logging.getLogger(f"FootageIngest.{self.project}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def ingest_shot(
        self,
        sequence: str,
        shot: str,
        source_file: Path,
        in_point: int,
        out_point: int,
        source_fps: float = 24.0,
        task_type: str = "pla",
        element_name: str = "rawPlate",
        version: int = 1
    ) -> dict:
        """
        Ingest a single shot.
        
        Args:
            sequence: Sequence name (e.g., "sht")
            shot: Shot number (e.g., "100")
            source_file: Path to source raw footage file
            in_point: Editorial in point
            out_point: Editorial out point
            source_fps: Frame rate
            task_type: Task type abbreviation (default: "pla")
            element_name: Element identifier (default: "rawPlate")
            version: Version number (default: 1)
            
        Returns:
            Pipeline execution summary
        """
        summary = ingest_shot(
            project=self.project,
            sequence=sequence,
            shot=shot,
            source_file=source_file,
            in_point=in_point,
            out_point=out_point,
            source_fps=source_fps,
            task_type=task_type,
            element_name=element_name,
            version=version,
            project_id=self.project_id,
            logger=self.logger
        )
        
        self.processed_shots.append(summary)
        return summary
    
    def ingest_from_edl(self, edl_file: Path):
        """
        Ingest multiple shots from an EDL file.
        
        This would parse the EDL and process each shot.
        
        Args:
            edl_file: Path to EDL file
        """
        # Placeholder - would implement EDL parsing
        self.logger.info(f"EDL processing not yet implemented: {edl_file}")
        raise NotImplementedError("EDL parsing to be implemented")
    
    def ingest_batch(self, shots_data: list):
        """
        Ingest multiple shots from a list of shot data.
        
        Args:
            shots_data: List of dictionaries with shot information
                       Each dict should contain: sequence, shot, source_file,
                       in_point, out_point, source_fps (optional)
                       Optional: task_type, element_name, version
        """
        results = []
        
        for shot_data in shots_data:
            try:
                result = self.ingest_shot(
                    sequence=shot_data['sequence'],
                    shot=shot_data['shot'],
                    source_file=Path(shot_data['source_file']),
                    in_point=shot_data['in_point'],
                    out_point=shot_data['out_point'],
                    source_fps=shot_data.get('source_fps', 24.0),
                    task_type=shot_data.get('task_type', 'pla'),
                    element_name=shot_data.get('element_name', 'rawPlate'),
                    version=shot_data.get('version', 1)
                )
                results.append(result)
                
            except Exception as e:
                self.logger.error(
                    f"Failed to process shot {shot_data.get('shot')}: {str(e)}"
                )
                results.append({
                    'shot': shot_data.get('shot'),
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def get_summary(self) -> dict:
        """
        Get summary of all processed shots.
        
        Returns:
            Summary dictionary
        """
        total_shots = len(self.processed_shots)
        successful_shots = sum(
            1 for s in self.processed_shots if s.get('overall_success')
        )
        
        return {
            'project': self.project,
            'total_shots_processed': total_shots,
            'successful_shots': successful_shots,
            'failed_shots': total_shots - successful_shots,
            'shots': self.processed_shots
        }


# Convenience functions for common operations

def quick_ingest(
    source_file: str,
    sequence: str,
    shot: str,
    in_point: int,
    out_point: int,
    project: str = "default",
    task_type: str = "pla",
    element_name: str = "rawPlate",
    version: int = 1
) -> dict:
    """
    Quick ingest function for simple use cases.
    
    Args:
        source_file: Path to source file
        sequence: Sequence name (e.g., "sht")
        shot: Shot number (e.g., "100")
        in_point: In point frame
        out_point: Out point frame
        project: Project name
        task_type: Task type abbreviation (default: "pla")
        element_name: Element identifier (default: "rawPlate")
        version: Version number (default: 1)
        
    Returns:
        Pipeline summary
    """
    return ingest_shot(
        project=project,
        sequence=sequence,
        shot=shot,
        source_file=Path(source_file),
        in_point=in_point,
        out_point=out_point,
        task_type=task_type,
        element_name=element_name,
        version=version
    )
