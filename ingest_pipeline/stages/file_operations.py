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
            shutil.copy2(source_file, dest_file)
            
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
                shutil.copy2(source_file, dest_file)
                
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
    
    Creates the complete directory structure and organizes
    all shot-related files into appropriate locations.
    """
    
    def process(self, shot_info: ShotInfo, result: ProcessingResult, **kwargs):
        """
        Organize files into shot tree.
        
        Args:
            shot_info: Shot information
            result: Result object
            **kwargs: Additional arguments
                - plates_sequence: Plates ImageSequence to organize
                - proxy_file: Proxy file path to organize
                - additional_files: Dict of additional files {subdir: [files]}
        """
        if not self.validate_inputs(shot_info, result):
            return
        
        # Create shot tree structure
        shot_root = PipelineConfig.get_shot_path(
            shot_info.project,
            shot_info.sequence,
            shot_info.shot
        )
        
        if not self.create_directory(shot_root, result):
            return
        
        # Create subdirectories
        plates_dir = PipelineConfig.get_plates_path(
            shot_info.project,
            shot_info.sequence,
            shot_info.shot
        )
        proxy_dir = PipelineConfig.get_proxy_path(
            shot_info.project,
            shot_info.sequence,
            shot_info.shot
        )
        
        directories_created = []
        
        for directory in [plates_dir, proxy_dir]:
            if self.create_directory(directory, result):
                directories_created.append(str(directory))
        
        # Organize plates
        plates_sequence = kwargs.get('plates_sequence')
        if plates_sequence:
            if isinstance(plates_sequence, dict):
                plates_sequence = ImageSequence(**plates_sequence)
            
            # If plates aren't already in the correct location, copy them
            if plates_sequence.directory != plates_dir:
                copy_stage = FileCopyStage(logger=self.logger)
                copy_result = copy_stage.execute(
                    shot_info,
                    source_sequence=plates_sequence,
                    destination_dir=plates_dir,
                    create_structure=False
                )
                
                if not copy_result.success:
                    result.add_error("Failed to copy plates to shot tree")
                    result.errors.extend(copy_result.errors)
                    return
            
            shot_info.output_plates_path = plates_dir
        
        # Organize proxy
        proxy_file = kwargs.get('proxy_file')
        if proxy_file:
            proxy_file = Path(proxy_file)
            
            if proxy_file.exists() and proxy_file.parent != proxy_dir:
                dest_proxy = proxy_dir / proxy_file.name
                
                try:
                    shutil.copy2(proxy_file, dest_proxy)
                    shot_info.output_proxy_path = dest_proxy
                except Exception as e:
                    result.add_error(f"Failed to copy proxy: {str(e)}")
        
        # Organize additional files
        additional_files = kwargs.get('additional_files', {})
        for subdir, files in additional_files.items():
            subdir_path = shot_root / subdir
            if self.create_directory(subdir_path, result):
                for file_path in files:
                    file_path = Path(file_path)
                    if file_path.exists():
                        try:
                            shutil.copy2(file_path, subdir_path / file_path.name)
                        except Exception as e:
                            result.add_warning(
                                f"Failed to copy {file_path}: {str(e)}"
                            )
        
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
