"""
Stage for file operations like copying, moving, and organizing.
Handles copying sequences and files to shot tree locations.
"""
import shutil
from pathlib import Path
from typing import Optional, List
import os

from .base import PipelineStage
from ..models import ProcessingResult, ShotInfo, ImageSequence
from ..config import PipelineConfig


class FileCopyStage(PipelineStage):
    """
    Copy files or sequences to destination locations.
    
    Handles copying with verification and can preserve or update
    permissions.
    """
    
    def __init__(self, verify_copy: bool = True, **kwargs):
        """
        Initialize file copy stage.
        
        Args:
            verify_copy: Verify file sizes after copy
        """
        super().__init__(**kwargs)
        self.verify_copy = verify_copy
    
    def process(self, shot_info: ShotInfo, result: ProcessingResult, **kwargs):
        """
        Copy files to destination.
        
        Args:
            shot_info: Shot information
            result: Result object
            **kwargs: Additional arguments
                - source_files: List of source file paths
                - source_sequence: ImageSequence object to copy
                - destination_dir: Destination directory
                - create_structure: Create shot tree structure (default: True)
        """
        if not self.validate_inputs(shot_info, result):
            return
        
        # Determine what to copy
        source_files = kwargs.get('source_files', [])
        source_sequence = kwargs.get('source_sequence')
        
        if not source_files and not source_sequence:
            result.add_error("No source files or sequence specified")
            return
        
        # Setup destination
        destination_dir = kwargs.get('destination_dir')
        create_structure = kwargs.get('create_structure', True)
        
        if destination_dir:
            destination_dir = Path(destination_dir)
        elif create_structure:
            # Use default shot tree structure
            destination_dir = PipelineConfig.get_shot_path(
                shot_info.project,
                shot_info.sequence,
                shot_info.shot
            )
        else:
            result.add_error("No destination directory specified")
            return
        
        # Create destination directory
        if not self.create_directory(destination_dir, result):
            return
        
        # Copy files
        copied_files = []
        
        if source_sequence:
            copied_files.extend(
                self._copy_sequence(source_sequence, destination_dir, result)
            )
        
        if source_files:
            for source_file in source_files:
                dest_file = self._copy_file(Path(source_file), destination_dir, result)
                if dest_file:
                    copied_files.append(dest_file)
        
        result.data['copied_files'] = [str(f) for f in copied_files]
        result.data['files_copied'] = len(copied_files)
        result.data['destination_dir'] = str(destination_dir)
    
    def _copy_file(
        self,
        source_file: Path,
        destination_dir: Path,
        result: ProcessingResult
    ) -> Optional[Path]:
        """
        Copy a single file.
        
        Returns:
            Destination path if successful, None otherwise
        """
        if not source_file.exists():
            result.add_error(f"Source file does not exist: {source_file}")
            return None
        
        dest_file = destination_dir / source_file.name
        
        try:
            self.logger.debug(f"Copying {source_file} to {dest_file}")
            shutil.copy(source_file, dest_file)
            
            # Verify copy
            if self.verify_copy:
                if not self._verify_file_copy(source_file, dest_file, result):
                    return None
            
            return dest_file
            
        except Exception as e:
            result.add_error(f"Failed to copy {source_file}: {str(e)}")
            return None
    
    def _copy_sequence(
        self,
        source_sequence: ImageSequence,
        destination_dir: Path,
        result: ProcessingResult
    ) -> List[Path]:
        """
        Copy an entire image sequence.
        
        Returns:
            List of copied file paths
        """
        if isinstance(source_sequence, dict):
            source_sequence = ImageSequence(**source_sequence)
        
        copied_files = []
        errors = []
        
        for frame in range(source_sequence.first_frame, source_sequence.last_frame + 1):
            source_file = source_sequence.get_frame_path(frame)
            
            if not source_file.exists():
                errors.append(f"Frame {frame} does not exist: {source_file}")
                continue
            
            dest_file = destination_dir / source_file.name
            
            try:
                shutil.copy(source_file, dest_file)
                
                if self.verify_copy:
                    if not self._verify_file_copy(source_file, dest_file, result):
                        errors.append(f"Verification failed for frame {frame}")
                        continue
                
                copied_files.append(dest_file)
                
            except Exception as e:
                errors.append(f"Failed to copy frame {frame}: {str(e)}")
        
        # Report results
        self.logger.info(
            f"Copied {len(copied_files)}/{source_sequence.total_frames} frames"
        )
        
        if errors:
            for error in errors:
                result.add_warning(error)
        
        return copied_files
    
    def _verify_file_copy(
        self,
        source_file: Path,
        dest_file: Path,
        result: ProcessingResult
    ) -> bool:
        """
        Verify that file was copied correctly.
        
        Returns:
            True if verification passed, False otherwise
        """
        if not dest_file.exists():
            result.add_error(f"Destination file does not exist: {dest_file}")
            return False
        
        source_size = source_file.stat().st_size
        dest_size = dest_file.stat().st_size
        
        if source_size != dest_size:
            result.add_error(
                f"File size mismatch: {source_file} ({source_size}) vs "
                f"{dest_file} ({dest_size})"
            )
            return False
        
        return True


class ShotTreeOrganizationStage(PipelineStage):
    """
    Organize files into a standardized shot tree structure.
    
    Creates the complete directory structure following the naming convention:
    {shot}/
      {task}/
        {shot}_{task}_{element}_v{version}/
          {rep}_{colorspace}/
            {shot}_{task}_{element}_v{version}_{rep}_{colorspace}.####.ext
          {shot}_{task}_{element}_v{version}_{rep}_{colorspace}.mov
    """
    
    def process(self, shot_info: ShotInfo, result: ProcessingResult, **kwargs):
        """
        Organize files into shot tree with new naming convention.
        
        Args:
            shot_info: Shot information
            result: Result object
            **kwargs: Additional arguments
                - plates_sequence: Plates ImageSequence to organize
                - proxy_file: Proxy file path to organize
                - colorspace: Colorspace for plates (default: ACEScg)
        """
        if not self.validate_inputs(shot_info, result):
            return
        
        colorspace = kwargs.get('colorspace', PipelineConfig.COLORSPACE_ACESCG)
        
        # Create directory structure
        # shot_root = /mnt/projects/sht100
        shot_root = PipelineConfig.get_shot_path(shot_info.shot_name)
        
        # task_dir = /mnt/projects/sht100/pla
        task_dir = PipelineConfig.get_task_path(
            shot_info.shot_name,
            shot_info.task_type
        )
        
        # version_dir = /mnt/projects/sht100/pla/sht100_pla_rawPlate_v001
        version_dir = PipelineConfig.get_version_path(
            shot_info.shot_name,
            shot_info.task_type,
            shot_info.element_name,
            shot_info.version
        )
        
        # colorspace_dir = /mnt/projects/sht100/pla/sht100_pla_rawPlate_v001/main_ACEScg
        colorspace_dir = PipelineConfig.get_colorspace_path(
            shot_info.shot_name,
            shot_info.task_type,
            shot_info.element_name,
            shot_info.version,
            shot_info.representation,
            colorspace
        )
        
        self.logger.info(f"Creating shot tree structure:")
        self.logger.info(f"  Shot root: {shot_root}")
        self.logger.info(f"  Task dir: {task_dir}")
        self.logger.info(f"  Version container: {version_dir}")
        self.logger.info(f"  Colorspace dir: {colorspace_dir}")
        
        # Create all directories
        directories_created = []
        for directory in [shot_root, task_dir, version_dir, colorspace_dir]:
            if self.create_directory(directory, result):
                directories_created.append(str(directory))
            else:
                result.add_error(f"Failed to create directory: {directory}")
                return
        
        result.data['directories_created'] = directories_created
        
        # Store paths in shot_info
        shot_info.version_container_path = version_dir
        shot_info.output_sequence_path = colorspace_dir
        
        # Organize plates sequence
        plates_sequence = kwargs.get('plates_sequence')
        if plates_sequence:
            if isinstance(plates_sequence, dict):
                plates_sequence = ImageSequence(**plates_sequence)
            
            self.logger.info(f"Organizing plates sequence to: {colorspace_dir}")
            
            # Copy sequence to colorspace directory with new naming
            organized_files = self._organize_sequence(
                plates_sequence,
                colorspace_dir,
                shot_info,
                colorspace,
                result
            )
            
            if organized_files:
                result.data['plates_organized'] = len(organized_files)
                result.data['plates_directory'] = str(colorspace_dir)
        
        # Organize proxy
        proxy_file = kwargs.get('proxy_file')
        if proxy_file:
            proxy_file = Path(proxy_file)
            self.logger.info(f"Organizing proxy file to: {version_dir}")
            
            organized_proxy = self._organize_proxy(
                proxy_file,
                version_dir,
                shot_info,
                result
            )
            
            if organized_proxy:
                shot_info.output_proxy_path = organized_proxy
                result.data['proxy_file'] = str(organized_proxy)
        
        result.message = f"Organized shot files into: {version_dir}"
    
    def _organize_sequence(
        self,
        source_sequence: ImageSequence,
        dest_dir: Path,
        shot_info: ShotInfo,
        colorspace: str,
        result: ProcessingResult
    ) -> List[Path]:
        """
        Copy sequence files to destination with new naming.
        
        Args:
            source_sequence: Source image sequence
            dest_dir: Destination directory (colorspace directory)
            shot_info: Shot information
            colorspace: Colorspace name
            result: Result object
            
        Returns:
            List of organized file paths
        """
        organized_files = []
        errors = []
        
        for frame in range(source_sequence.first_frame, source_sequence.last_frame + 1):
            try:
                source_file = source_sequence.get_frame_path(frame)
                
                if not source_file.exists():
                    errors.append(f"Source frame does not exist: {source_file}")
                    continue
                
                # Generate new filename using naming convention
                new_filename = shot_info.get_sequence_filename(
                    frame,
                    colorspace,
                    source_sequence.extension
                )
                
                dest_file = dest_dir / new_filename
                
                # Copy file
                shutil.copy(source_file, dest_file)
                organized_files.append(dest_file)
                
            except Exception as e:
                errors.append(f"Failed to organize frame {frame}: {str(e)}")
        
        # Report results
        self.logger.info(
            f"Organized {len(organized_files)}/{source_sequence.total_frames} frames"
        )
        
        if errors:
            for error in errors:
                result.add_warning(error)
        
        return organized_files
    
    def _organize_proxy(
        self,
        source_proxy: Path,
        dest_dir: Path,
        shot_info: ShotInfo,
        result: ProcessingResult
    ) -> Optional[Path]:
        """
        Copy proxy file to destination with new naming.
        
        Args:
            source_proxy: Source proxy file
            dest_dir: Destination directory (version container)
            shot_info: Shot information
            result: Result object
            
        Returns:
            Path to organized proxy file
        """
        if not source_proxy.exists():
            result.add_error(f"Source proxy does not exist: {source_proxy}")
            return None
        
        # Generate new filename using naming convention
        proxy_filename = shot_info.get_proxy_filename(
            colorspace=PipelineConfig.COLORSPACE_SRGB,
            extension=source_proxy.suffix.lstrip('.')
        )
        
        dest_file = dest_dir / proxy_filename
        
        try:
            # Use binary read/write to avoid any permission/metadata issues
            # when copying between Linux and Windows filesystems (WSL)
            with open(source_proxy, 'rb') as src:
                with open(dest_file, 'wb') as dst:
                    dst.write(src.read())
            self.logger.info(f"Organized proxy: {dest_file}")
            return dest_file
            
        except Exception as e:
            result.add_error(f"Failed to organize proxy: {str(e)}")
            return None
        
        result.data['shot_tree_root'] = str(shot_root)
        result.data['directories_created'] = directories_created
        result.data['plates_path'] = str(shot_info.output_plates_path) if shot_info.output_plates_path else None
        result.data['proxy_path'] = str(shot_info.output_proxy_path) if shot_info.output_proxy_path else None
        
        self.logger.info(f"Shot tree organized at: {shot_root}")


class CleanupStage(PipelineStage):
    """
    Clean up temporary files and directories.
    
    Removes intermediate processing files after successful completion.
    """
    
    def __init__(self, remove_temp_dirs: bool = True, **kwargs):
        """
        Initialize cleanup stage.
        
        Args:
            remove_temp_dirs: Remove temporary directories
        """
        super().__init__(**kwargs)
        self.remove_temp_dirs = remove_temp_dirs
    
    def process(self, shot_info: ShotInfo, result: ProcessingResult, **kwargs):
        """
        Clean up temporary files.
        
        Args:
            shot_info: Shot information
            result: Result object
            **kwargs: Additional arguments
                - temp_dirs: List of temporary directories to remove
                - temp_files: List of temporary files to remove
                - keep_on_error: Don't clean up if there were errors
        """
        keep_on_error = kwargs.get('keep_on_error', True)
        
        # Check if we should skip cleanup
        if keep_on_error and shot_info.processing_status == 'error':
            self.logger.info("Skipping cleanup due to processing errors")
            result.add_warning("Cleanup skipped - preserving files for debugging")
            return
        
        removed_items = []
        errors = []
        
        # Clean up temporary directories
        temp_dirs = kwargs.get('temp_dirs', [])
        if self.remove_temp_dirs:
            for temp_dir in temp_dirs:
                temp_dir = Path(temp_dir)
                if temp_dir.exists() and temp_dir.is_dir():
                    try:
                        shutil.rmtree(temp_dir)
                        removed_items.append(str(temp_dir))
                        self.logger.info(f"Removed temporary directory: {temp_dir}")
                    except Exception as e:
                        errors.append(f"Failed to remove {temp_dir}: {str(e)}")
        
        # Clean up temporary files
        temp_files = kwargs.get('temp_files', [])
        for temp_file in temp_files:
            temp_file = Path(temp_file)
            if temp_file.exists() and temp_file.is_file():
                try:
                    temp_file.unlink()
                    removed_items.append(str(temp_file))
                    self.logger.debug(f"Removed temporary file: {temp_file}")
                except Exception as e:
                    errors.append(f"Failed to remove {temp_file}: {str(e)}")
        
        result.data['removed_items'] = removed_items
        result.data['items_removed'] = len(removed_items)
        
        if errors:
            for error in errors:
                result.add_warning(error)
