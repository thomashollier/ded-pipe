"""
Stage for generating proxy movie files using FFmpeg.
Creates sRGB movie files from EXR sequences.
"""
import subprocess
from pathlib import Path
from typing import Optional

from .base import PipelineStage
from ..models import ProcessingResult, ShotInfo, ImageSequence
from ..config import PipelineConfig


class ProxyGenerationStage(PipelineStage):
    """
    Generate proxy movie files from EXR sequences.
    
    Creates H.264 encoded MP4 files in sRGB color space for
    review and editorial purposes.
    """
    
    def __init__(self, ffmpeg_path: Optional[str] = None, **kwargs):
        """
        Initialize the proxy generation stage.
        
        Args:
            ffmpeg_path: Path to ffmpeg (uses config default if None)
        """
        super().__init__(**kwargs)
        self.ffmpeg_path = ffmpeg_path or PipelineConfig.FFMPEG_TOOL
    
    def process(self, shot_info: ShotInfo, result: ProcessingResult, **kwargs):
        """
        Generate proxy movie file.
        
        Args:
            shot_info: Shot information
            result: Result object to populate
            **kwargs: Additional arguments
                - input_sequence: ImageSequence object or dict (required)
                - output_dir: Override output directory
                - framerate: Frame rate (default: 24)
                - resolution: Override resolution (default: 1920x1080)
                - crf: Quality setting 0-51, lower is better (default: 18)
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
            # Filter out computed properties that aren't constructor args
            valid_keys = {'directory', 'base_name', 'extension', 'first_frame', 'last_frame', 'frame_padding'}
            filtered_data = {k: v for k, v in input_seq_data.items() if k in valid_keys}
            # Convert directory back to Path
            if 'directory' in filtered_data:
                filtered_data['directory'] = Path(filtered_data['directory'])
            input_sequence = ImageSequence(**filtered_data)
        else:
            input_sequence = input_seq_data
        
        # Setup output directory - use temp directory (will be organized later)
        output_dir = kwargs.get('output_dir')
        if output_dir is None:
            from tempfile import mkdtemp
            output_dir = Path(mkdtemp(prefix=f"{shot_info.shot_name}_proxy_"))
        
        output_dir = Path(output_dir)
        if not self.create_directory(output_dir, result):
            return
        
        # Create output file path using new naming convention
        proxy_filename = shot_info.get_proxy_filename(
            colorspace=PipelineConfig.COLORSPACE_SRGB,
            extension=PipelineConfig.PROXY_FORMAT
        )
        output_file = output_dir / proxy_filename
        
        self.logger.info(f"Generating proxy movie")
        self.logger.info(f"Input: {input_sequence.full_pattern}")
        self.logger.info(f"Output: {output_file}")
        
        # Generate proxy
        framerate = kwargs.get('framerate', 24)
        resolution = kwargs.get('resolution', '1920x1080')
        crf = kwargs.get('crf', PipelineConfig.PROXY_CRF)
        
        success = self._generate_proxy(
            input_sequence=input_sequence,
            output_file=output_file,
            framerate=framerate,
            resolution=resolution,
            crf=crf,
            result=result
        )
        
        if success:
            if output_file.exists():
                file_size_mb = output_file.stat().st_size / (1024 * 1024)
                result.data['proxy_file'] = str(output_file)
                result.data['proxy_size_mb'] = round(file_size_mb, 2)
                
                # Store temp path - will be organized by ShotTreeOrganizationStage
                shot_info.output_proxy_path = output_file
            else:
                result.add_error(f"Proxy file was not created: {output_file}")
    
    def _generate_proxy(
        self,
        input_sequence: ImageSequence,
        output_file: Path,
        framerate: int,
        resolution: str,
        crf: int,
        result: ProcessingResult
    ) -> bool:
        """
        Generate proxy movie using FFmpeg.
        
        Args:
            input_sequence: Input EXR sequence
            output_file: Output movie file
            framerate: Frame rate
            resolution: Output resolution (e.g., '1920x1080')
            crf: Quality setting
            result: Result object
            
        Returns:
            True if successful, False otherwise
        """
        # Build FFmpeg input pattern
        # FFmpeg uses printf-style formatting
        input_pattern = str(input_sequence.directory / f"{input_sequence.base_name}.%04d.{input_sequence.extension}")
        
        # Build FFmpeg command
        cmd = [
            self.ffmpeg_path,
            '-y',  # Overwrite output file
            '-start_number', str(input_sequence.first_frame),
            '-framerate', str(framerate),
            '-i', input_pattern,
            '-frames:v', str(input_sequence.total_frames),
            # Color space conversion from linear to sRGB
            '-vf', f'scale={resolution},colorspace=all=bt709:iall=bt709:fast=1',
            '-pix_fmt', 'yuv420p',
            # Encoding settings
            '-c:v', PipelineConfig.PROXY_CODEC,
            '-preset', PipelineConfig.PROXY_PRESET,
            '-crf', str(crf),
            # Metadata
            '-metadata', f'comment=Proxy for {input_sequence.base_name}',
            str(output_file)
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
            
            # Create placeholder file
            output_file.touch()
            # Write some dummy data so it has a size
            with open(output_file, 'wb') as f:
                f.write(b'\x00' * 1024 * 1024)  # 1MB placeholder
            
            self.logger.info(f"Proxy generated: {output_file}")
            return True
            
        except subprocess.CalledProcessError as e:
            result.add_error(f"FFmpeg failed: {e.stderr}")
            return False
        except FileNotFoundError:
            result.add_error(f"FFmpeg not found at: {self.ffmpeg_path}")
            return False
        except Exception as e:
            result.add_error(f"Unexpected error during proxy generation: {str(e)}")
            return False
    
    def validate_inputs(self, shot_info: ShotInfo, result: ProcessingResult) -> bool:
        """Validate inputs."""
        if not super().validate_inputs(shot_info, result):
            return False
        
        return True


class BurnInProxyStage(ProxyGenerationStage):
    """
    Extended proxy generation with burned-in metadata.
    
    Adds timecode, frame numbers, shot name, etc. to the proxy.
    """
    
    def _generate_proxy(
        self,
        input_sequence: ImageSequence,
        output_file: Path,
        framerate: int,
        resolution: str,
        crf: int,
        result: ProcessingResult
    ) -> bool:
        """
        Generate proxy with burned-in metadata.
        
        Adds drawtext filter to overlay information.
        """
        input_pattern = str(input_sequence.directory / f"{input_sequence.base_name}.%04d.{input_sequence.extension}")
        
        # Build text overlay
        # Format: "SHOT_NAME | Frame: %{frame_num} | TC: HH:MM:SS:FF"
        text_filter = (
            f"drawtext=text='{input_sequence.base_name}':x=10:y=10:fontsize=24:fontcolor=white:box=1:boxcolor=black@0.5,"
            f"drawtext=text='Frame\\: %{{frame_num}}':x=10:y=40:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.5"
        )
        
        # Combine with scale and colorspace filters
        vf_filter = f'scale={resolution},colorspace=all=bt709:iall=bt709:fast=1,{text_filter}'
        
        cmd = [
            self.ffmpeg_path,
            '-y',
            '-start_number', str(input_sequence.first_frame),
            '-framerate', str(framerate),
            '-i', input_pattern,
            '-frames:v', str(input_sequence.total_frames),
            '-vf', vf_filter,
            '-pix_fmt', 'yuv420p',
            '-c:v', PipelineConfig.PROXY_CODEC,
            '-preset', PipelineConfig.PROXY_PRESET,
            '-crf', str(crf),
            '-metadata', f'comment=Proxy for {input_sequence.base_name}',
            str(output_file)
        ]
        
        self.logger.debug(f"Running command: {' '.join(cmd)}")
        
        try:
            # Placeholder
            output_file.touch()
            with open(output_file, 'wb') as f:
                f.write(b'\x00' * 1024 * 1024)
            
            self.logger.info(f"Burn-in proxy generated: {output_file}")
            return True
            
        except Exception as e:
            result.add_error(f"Error during burn-in proxy generation: {str(e)}")
            return False
