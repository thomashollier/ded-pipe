"""
Stage for converting Sony Venice 2 raw footage to DPX.
Uses WSL interop to call Windows Sony tool from Linux/WSL.
"""
import os
import subprocess
from pathlib import Path
from typing import Optional

from .base import PipelineStage
from ..models import ProcessingResult, ShotInfo, ImageSequence
from ..config import PipelineConfig


class SonyRawConversionStage(PipelineStage):
    """
    Convert Sony Venice 2 MXF raw footage to DPX sequence.
    
    Uses WSL interop to call the Windows-only Sony conversion tool.
    Automatically detects if running on Windows or WSL.
    """
    
    # Default Windows path to Sony tool
    DEFAULT_TOOL_PATH = r"C:\Program Files\Sony\RAW Viewer\rawexporter.exe"
    
    def __init__(self, sony_tool_path: Optional[str] = None, bake_colorspace: str = "SGAMUT3_LINEAR", **kwargs):
        """
        Initialize the Sony conversion stage.
        
        Args:
            sony_tool_path: Path to Sony conversion tool (Windows path)
            bake_colorspace: Output colorspace for bake mode. Options:
                - ALL, INPUT, SGAMUT_LINEAR, SGAMUT_SLOG2
                - ACES_LINEAR, SGAMUT3_LINEAR, SGAMUT3_SLOG3, SGAMUT3CINE_SLOG3
        """
        super().__init__(**kwargs)
        self.sony_tool_path = sony_tool_path or self.DEFAULT_TOOL_PATH
        self.bake_colorspace = bake_colorspace
        self.is_wsl = self._detect_wsl()
        
        if self.is_wsl:
            self.logger.info("Running in WSL - will use interop to call Windows tool")
    
    def _detect_wsl(self) -> bool:
        """Check if running in Windows Subsystem for Linux."""
        if os.name == 'nt':
            return False
        try:
            with open('/proc/version', 'r') as f:
                version = f.read().lower()
                return 'microsoft' in version or 'wsl' in version
        except:
            return False
    
    def _to_windows_path(self, linux_path: Path) -> str:
        """
        Convert Linux/WSL path to Windows path.
        
        /mnt/c/Users/... -> C:\\Users\\...
        /home/user/...   -> \\\\wsl$\\Ubuntu\\home\\user\\...
        """
        path_str = str(linux_path.resolve())
        
        if path_str.startswith('/mnt/'):
            # /mnt/c/... -> C:\...
            parts = path_str.split('/')
            drive = parts[2].upper()
            rest = '\\'.join(parts[3:])
            return f"{drive}:\\{rest}"
        else:
            # WSL internal path -> \\wsl$\<distro>\...
            distro = os.environ.get('WSL_DISTRO_NAME', 'Ubuntu')
            return f"\\\\wsl$\\{distro}{path_str.replace('/', '\\')}"
    
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
        frame_count = out_frame - in_frame + 1
        
        # Use pipeline frame numbering (starting at first_frame, typically 993)
        output_first_frame = shot_info.first_frame
        output_last_frame = output_first_frame + frame_count - 1
        
        # Build output pattern
        output_pattern = output_dir / f"{shot_info.shot_name}.%04d.dpx"
        
        self.logger.info(f"Converting {source_file} to DPX")
        self.logger.info(f"Source frame range: {in_frame}-{out_frame} ({frame_count} frames)")
        self.logger.info(f"Output frame range: {output_first_frame}-{output_last_frame}")
        self.logger.info(f"Output pattern: {output_pattern}")
        
        # Run conversion with start_index to match pipeline frame numbering
        success = self._run_sony_conversion(
            source_file=source_file,
            output_pattern=output_pattern,
            in_frame=in_frame,
            out_frame=out_frame,
            bit_depth=kwargs.get('dpx_bit_depth', 16),
            result=result,
            start_index=output_first_frame
        )
        
        if success:
            # Create ImageSequence object matching the output
            dpx_sequence = ImageSequence(
                directory=output_dir,
                base_name=shot_info.shot_name,
                extension="dpx",
                first_frame=output_first_frame,
                last_frame=output_last_frame,
                frame_padding=4  # We specified --digits 4
            )
            
            # Verify frames were created
            existing_frames = dpx_sequence.verify_exists()
            expected_frames = frame_count
            
            if len(existing_frames) != expected_frames:
                result.add_warning(
                    f"Only {len(existing_frames)} of {expected_frames} frames were created"
                )
            
            result.data['dpx_sequence'] = dpx_sequence.to_dict()
            result.data['output_dir'] = str(output_dir)
            result.data['frames_created'] = len(existing_frames)
            result.data['frame_mapping'] = {
                'source_in': in_frame,
                'source_out': out_frame,
                'output_first': output_first_frame,
                'output_last': output_last_frame
            }
    
    def _run_sony_conversion(
        self,
        source_file: Path,
        output_pattern: Path,
        in_frame: int,
        out_frame: int,
        bit_depth: int,
        result: ProcessingResult,
        start_index: int = 0
    ) -> bool:
        """
        Run the Sony conversion tool.
        
        Uses WSL interop if running in WSL, otherwise runs directly.
        """
        if self.is_wsl:
            return self._run_via_wsl_interop(
                source_file, output_pattern, in_frame, out_frame, bit_depth, result, start_index
            )
        else:
            return self._run_native(
                source_file, output_pattern, in_frame, out_frame, bit_depth, result, start_index
            )
    
    def _run_native(
        self,
        source_file: Path,
        output_pattern: Path,
        in_frame: int,
        out_frame: int,
        bit_depth: int,
        result: ProcessingResult,
        start_index: int = 0
    ) -> bool:
        """Run Sony tool directly (Windows native)."""
        # --output expects base name only (e.g., "sht100"), tool adds frame numbers
        output_base = output_pattern.stem.replace('.%04d', '').replace('.%d', '')
        cmd = [
            self.sony_tool_path,
            '--input', str(source_file),
            '--dir', str(output_pattern.parent),
            '--output', output_base,
            '--in', str(in_frame),
            '--out', str(out_frame),
            '--start', str(start_index),
            '--digits', '4',
            '--video', 'DPX',
            '--depth', str(bit_depth),
            '--bake', self.bake_colorspace,
            '--display', '1'
        ]
        
        self.logger.debug(f"Running: {' '.join(cmd)}")
        
        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            if process.returncode != 0:
                result.add_error(f"Sony conversion failed: {process.stderr}")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            result.add_error("Sony conversion timed out")
            return False
        except FileNotFoundError:
            result.add_error(f"Sony tool not found: {self.sony_tool_path}")
            return False
        except Exception as e:
            result.add_error(f"Conversion error: {str(e)}")
            return False
    
    def _run_via_wsl_interop(
        self,
        source_file: Path,
        output_pattern: Path,
        in_frame: int,
        out_frame: int,
        bit_depth: int,
        result: ProcessingResult,
        start_index: int = 0
    ) -> bool:
        """Run Sony tool via WSL interop (calling Windows exe from WSL)."""
        
        # Convert paths to Windows format
        win_source = self._to_windows_path(source_file)
        win_output = self._to_windows_path(output_pattern)
        
        # First check if the Sony tool exists
        check_cmd = [
            'powershell.exe',
            '-NoProfile',
            '-NonInteractive',
            '-Command',
            f'Test-Path "{self.sony_tool_path}"'
        ]
        
        try:
            check_result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=10)
            if 'False' in check_result.stdout:
                result.add_error(
                    f"Sony RAW Converter not found at: {self.sony_tool_path}\n"
                    f"Please install Sony RAW Viewer or set the correct path.\n"
                    f"Download from: https://www.sony.com/electronics/support/software/raw-viewer"
                )
                return False
        except Exception as e:
            self.logger.warning(f"Could not verify tool path: {e}")
        
        # Build PowerShell command
        # rawexporter.exe options from --help
        # --output expects base name only (e.g., "sht100"), tool adds frame numbers
        # --start controls the starting frame number in output filenames
        output_base = output_pattern.stem.replace('.%04d', '').replace('.%d', '')
        
        ps_command = (
            f'& "{self.sony_tool_path}" '
            f'--input "{win_source}" '
            f'--dir "{self._to_windows_path(output_pattern.parent)}" '
            f'--output "{output_base}" '
            f'--in {in_frame} '
            f'--out {out_frame} '
            f'--start {start_index} '
            f'--digits 4 '
            f'--video DPX '
            f'--depth {bit_depth} '
            f'--bake {self.bake_colorspace} '
            f'--display 1'
        )
        
        cmd = [
            'powershell.exe',
            '-NoProfile',
            '-NonInteractive', 
            '-Command',
            ps_command
        ]
        
        self.logger.debug(f"WSL interop (PowerShell): {ps_command}")
        
        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            if process.returncode != 0:
                error_msg = process.stderr.strip() if process.stderr else process.stdout.strip()
                result.add_error(f"Sony conversion failed: {error_msg}")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            result.add_error("Sony conversion timed out")
            return False
        except Exception as e:
            result.add_error(f"WSL interop error: {str(e)}")
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
