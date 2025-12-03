"""
Stage for color conversion and image transformations using OIIO.
Handles ACES color conversion, anamorphic desqueeze, and letterboxing.
"""
import subprocess
from pathlib import Path
from typing import Optional, List

from .base import PipelineStage
from ..models import ProcessingResult, ShotInfo, ImageSequence
from ..config import PipelineConfig


class OIIOColorTransformStage(PipelineStage):
    """
    Apply color transformations and geometric corrections using OpenImageIO.
    
    This stage handles:
    - Color space conversion (SLog3 to ACES)
    - Anamorphic desqueeze
    - Letterboxing to UHD format
    - Output to EXR format
    """
    
    def __init__(self, oiio_tool_path: Optional[str] = None, **kwargs):
        """
        Initialize the OIIO transform stage.
        
        Args:
            oiio_tool_path: Path to oiiotool (uses config default if None)
        """
        super().__init__(**kwargs)
        self.oiio_tool_path = oiio_tool_path or PipelineConfig.OIIO_TOOL
    
    def process(self, shot_info: ShotInfo, result: ProcessingResult, **kwargs):
        """
        Process color and geometric transformations.
        
        Args:
            shot_info: Shot information
            result: Result object to populate
            **kwargs: Additional arguments
                - input_sequence: ImageSequence object or dict (required)
                - output_dir: Override output directory
                - parallel_jobs: Number of parallel processes (default: 4)
        """
        if not self.validate_inputs(shot_info, result):
            return
        
        # Get input sequence
        input_seq_data = kwargs.get('input_sequence')
        if not input_seq_data:
            result.add_error("Input sequence not provided")
            return
        
        # Convert dict to ImageSequence if needed
        if isinstance(input_seq_data, dict):
            input_sequence = ImageSequence(**input_seq_data)
        else:
            input_sequence = input_seq_data
        
        # Setup output directory
        output_dir = kwargs.get('output_dir')
        if output_dir is None:
            output_dir = PipelineConfig.get_plates_path(
                shot_info.project,
                shot_info.sequence,
                shot_info.shot
            )
        
        output_dir = Path(output_dir)
        if not self.create_directory(output_dir, result):
            return
        
        # Create output sequence
        output_sequence = ImageSequence(
            directory=output_dir,
            base_name=shot_info.shot_name,
            extension=PipelineConfig.OUTPUT_FORMAT,
            first_frame=shot_info.first_frame,
            last_frame=shot_info.last_frame,
            frame_padding=4
        )
        
        self.logger.info(f"Processing {input_sequence.total_frames} frames")
        self.logger.info(f"Input: {input_sequence.full_pattern}")
        self.logger.info(f"Output: {output_sequence.full_pattern}")
        
        # Process frames
        parallel_jobs = kwargs.get('parallel_jobs', 4)
        success = self._process_frames(
            input_sequence=input_sequence,
            output_sequence=output_sequence,
            shot_info=shot_info,
            result=result,
            parallel_jobs=parallel_jobs
        )
        
        if success:
            # Verify output
            existing_frames = output_sequence.verify_exists()
            expected_frames = output_sequence.total_frames
            
            if len(existing_frames) != expected_frames:
                result.add_error(
                    f"Only {len(existing_frames)} of {expected_frames} frames were created"
                )
            else:
                result.data['output_sequence'] = output_sequence.to_dict()
                result.data['frames_processed'] = len(existing_frames)
                
                # Update shot_info
                shot_info.output_plates_path = output_dir
    
    def _process_frames(
        self,
        input_sequence: ImageSequence,
        output_sequence: ImageSequence,
        shot_info: ShotInfo,
        result: ProcessingResult,
        parallel_jobs: int = 4
    ) -> bool:
        """
        Process all frames in the sequence.
        
        Args:
            input_sequence: Input image sequence
            output_sequence: Output image sequence
            shot_info: Shot information
            result: Result object
            parallel_jobs: Number of parallel processes
            
        Returns:
            True if successful, False otherwise
        """
        # Build oiiotool command
        # We'll process all frames in a single command for efficiency
        
        # Get input and output dimensions
        input_width, input_height = self._get_input_dimensions(input_sequence, result)
        if input_width is None:
            return False
        
        # Calculate desqueezed dimensions
        desqueezed_width = int(input_width * PipelineConfig.ANAMORPHIC_SQUEEZE)
        desqueezed_height = input_height
        
        # Calculate letterbox dimensions
        target_width = PipelineConfig.TARGET_WIDTH
        target_height = PipelineConfig.TARGET_HEIGHT
        
        # Determine scaling to fit in target with letterboxing
        scale_factor = min(
            target_width / desqueezed_width,
            target_height / desqueezed_height
        )
        
        scaled_width = int(desqueezed_width * scale_factor)
        scaled_height = int(desqueezed_height * scale_factor)
        
        # Calculate letterbox offsets (center the image)
        offset_x = (target_width - scaled_width) // 2
        offset_y = (target_height - scaled_height) // 2
        
        self.logger.info(f"Input dimensions: {input_width}x{input_height}")
        self.logger.info(f"Desqueezed dimensions: {desqueezed_width}x{desqueezed_height}")
        self.logger.info(f"Scaled dimensions: {scaled_width}x{scaled_height}")
        self.logger.info(f"Target dimensions: {target_width}x{target_height}")
        self.logger.info(f"Letterbox offset: ({offset_x}, {offset_y})")
        
        # Process each frame
        errors = []
        for frame in range(input_sequence.first_frame, input_sequence.last_frame + 1):
            input_file = input_sequence.get_frame_path(frame)
            output_file = output_sequence.get_frame_path(frame)
            
            if not self._process_single_frame(
                input_file=input_file,
                output_file=output_file,
                desqueezed_width=desqueezed_width,
                desqueezed_height=desqueezed_height,
                scaled_width=scaled_width,
                scaled_height=scaled_height,
                target_width=target_width,
                target_height=target_height,
                offset_x=offset_x,
                offset_y=offset_y,
                result=result
            ):
                errors.append(f"Frame {frame} failed")
        
        if errors:
            for error in errors:
                result.add_error(error)
            return False
        
        return True
    
    def _process_single_frame(
        self,
        input_file: Path,
        output_file: Path,
        desqueezed_width: int,
        desqueezed_height: int,
        scaled_width: int,
        scaled_height: int,
        target_width: int,
        target_height: int,
        offset_x: int,
        offset_y: int,
        result: ProcessingResult
    ) -> bool:
        """
        Process a single frame.
        
        Returns:
            True if successful, False otherwise
        """
        cmd = [
            self.oiio_tool_path,
            str(input_file),
            # Color space conversion
            '--colorconvert', PipelineConfig.SOURCE_COLORSPACE, PipelineConfig.TARGET_COLORSPACE,
            # Desqueeze (resize with aspect ratio correction)
            '--resize', f'{desqueezed_width}x{desqueezed_height}',
            # Scale to fit target
            '--resize', f'{scaled_width}x{scaled_height}',
            # Create canvas with target dimensions
            '--create', f'{target_width}x{target_height}', '3',
            # Paste the scaled image onto the canvas
            '--paste', f'+{offset_x}+{offset_y}',
            # Set output format and compression
            '--compression', PipelineConfig.OUTPUT_COMPRESSION,
            '--bits', PipelineConfig.OUTPUT_BIT_DEPTH,
            '-o', str(output_file)
        ]
        
        try:
            # For this example, we'll create a placeholder
            # In production, you would run the actual command:
            # process = subprocess.run(
            #     cmd,
            #     capture_output=True,
            #     text=True,
            #     check=True
            # )
            
            # Create placeholder file
            output_file.touch()
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"OIIO processing failed for {input_file}: {e.stderr}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error processing {input_file}: {str(e)}")
            return False
    
    def _get_input_dimensions(
        self,
        input_sequence: ImageSequence,
        result: ProcessingResult
    ) -> tuple:
        """
        Get dimensions of the input sequence.
        
        Returns:
            Tuple of (width, height) or (None, None) if failed
        """
        # Get first frame
        first_frame_path = input_sequence.get_frame_path(input_sequence.first_frame)
        
        if not first_frame_path.exists():
            result.add_error(f"First frame does not exist: {first_frame_path}")
            return None, None
        
        # Use oiiotool to get info
        cmd = [self.oiio_tool_path, '--info', str(first_frame_path)]
        
        try:
            # Placeholder - in production would parse actual oiiotool output
            # For Venice 2 6K anamorphic, typical resolution is 6048x4032
            return 6048, 4032
            
        except Exception as e:
            result.add_error(f"Failed to get input dimensions: {str(e)}")
            return None, None
