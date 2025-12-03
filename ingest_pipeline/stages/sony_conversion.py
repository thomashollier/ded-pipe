"""
Stage for converting Sony Venice 2 raw footage to DPX.
Uses Sony's command line conversion tool.
"""
import subprocess
from pathlib import Path
from typing import Optional

from .base import PipelineStage
from ..models import ProcessingResult, ShotInfo, ImageSequence
from ..config import PipelineConfig


class SonyRawConversionStage(PipelineStage):
    """
    Convert Sony Venice 2 MXF raw footage to DPX sequence.
    
    This stage extracts frames from the raw camera files and creates
    an intermediate DPX sequence for further processing.
    """
    
    def __init__(self, sony_tool_path: Optional[str] = None, **kwargs):
        """
        Initialize the Sony conversion stage.
        
        Args:
            sony_tool_path: Path to Sony conversion tool (uses config default if None)
        """
        super().__init__(**kwargs)
        self.sony_tool_path = sony_tool_path or PipelineConfig.SONY_CONVERT_TOOL
    
    def process(self, shot_info: ShotInfo, result: ProcessingResult, **kwargs):
        """
        Process Sony raw footage conversion.
        
        Args:
            shot_info: Shot information
            result: Result object to populate
            **kwargs: Additional arguments
                - output_dir: Override output directory
                - dpx_bit_depth: Bit depth for DPX (default: 16)
        """
        if not self.validate_inputs(shot_info, result):
            return
        
        # Verify source file exists
        source_file = shot_info.source_raw_path
        if not self.verify_file_exists(source_file, result):
            return
        
        # Setup output directory
        output_dir = kwargs.get('output_dir')
        if output_dir is None:
            output_dir = Path(f"/tmp/sony_conversion/{shot_info.shot_name}")
        
        output_dir = Path(output_dir)
        if not self.create_directory(output_dir, result):
            return
        
        # Calculate frame range with handles
        in_frame = shot_info.editorial_info.in_point - PipelineConfig.HEAD_HANDLE_FRAMES
        out_frame = shot_info.editorial_info.out_point + PipelineConfig.TAIL_HANDLE_FRAMES
        
        # Build output pattern
        output_pattern = output_dir / f"{shot_info.shot_name}.%04d.dpx"
        
        self.logger.info(f"Converting {source_file} to DPX")
        self.logger.info(f"Frame range: {in_frame}-{out_frame}")
        self.logger.info(f"Output pattern: {output_pattern}")
        
        # Build conversion command
        success = self._run_sony_conversion(
            source_file=source_file,
            output_pattern=output_pattern,
            in_frame=in_frame,
            out_frame=out_frame,
            bit_depth=kwargs.get('dpx_bit_depth', 16),
            result=result
        )
        
        if success:
            # Create ImageSequence object for the output
            dpx_sequence = ImageSequence(
                directory=output_dir,
                base_name=shot_info.shot_name,
                extension="dpx",
                first_frame=shot_info.first_frame,
                last_frame=shot_info.last_frame,
                frame_padding=4
            )
            
            # Verify frames were created
            existing_frames = dpx_sequence.verify_exists()
            expected_frames = dpx_sequence.total_frames
            
            if len(existing_frames) != expected_frames:
                result.add_warning(
                    f"Only {len(existing_frames)} of {expected_frames} frames were created"
                )
            
            result.data['dpx_sequence'] = dpx_sequence.to_dict()
            result.data['output_dir'] = str(output_dir)
            result.data['frames_created'] = len(existing_frames)
        
    def _run_sony_conversion(
        self,
        source_file: Path,
        output_pattern: Path,
        in_frame: int,
        out_frame: int,
        bit_depth: int,
        result: ProcessingResult
    ) -> bool:
        """
        Run the Sony conversion tool.
        
        Args:
            source_file: Source MXF file
            output_pattern: Output file pattern
            in_frame: First frame to extract
            out_frame: Last frame to extract
            bit_depth: Bit depth for DPX
            result: Result object
            
        Returns:
            True if successful, False otherwise
        """
        # Build command - this is a placeholder as the actual Sony tool
        # command structure would need to be verified
        cmd = [
            self.sony_tool_path,
            '-i', str(source_file),
            '-o', str(output_pattern),
            '-start', str(in_frame),
            '-end', str(out_frame),
            '-bit_depth', str(bit_depth),
            '-format', 'dpx',
            '-colorspace', 'linear'
        ]
        
        self.logger.debug(f"Running command: {' '.join(cmd)}")
        
        try:
            # For this example, we'll create a placeholder
            # In production, you would run the actual command:
            # process = subprocess.run(
            #     cmd,
            #     capture_output=True,
            #     text=True,
            #     check=True
            # )
            
            # Placeholder - simulate conversion
            self.logger.warning(
                "Sony conversion tool not available - using placeholder"
            )
            result.add_warning("Sony conversion tool not executed (placeholder mode)")
            
            return True
            
        except subprocess.CalledProcessError as e:
            result.add_error(f"Sony conversion failed: {e.stderr}")
            return False
        except FileNotFoundError:
            result.add_error(
                f"Sony conversion tool not found at: {self.sony_tool_path}"
            )
            return False
        except Exception as e:
            result.add_error(f"Unexpected error during Sony conversion: {str(e)}")
            return False
    
    def validate_inputs(self, shot_info: ShotInfo, result: ProcessingResult) -> bool:
        """Validate that we have the necessary input data."""
        if not super().validate_inputs(shot_info, result):
            return False
        
        if not shot_info.source_raw_path:
            result.add_error("Source raw path not specified")
            return False
        
        if not shot_info.editorial_info:
            result.add_error("Editorial info not provided")
            return False
        
        return True
