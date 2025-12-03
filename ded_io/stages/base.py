"""
Base stage class for pipeline operations.
All processing stages inherit from this base class.
"""
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pathlib import Path

from ..models import ProcessingResult, ShotInfo


class PipelineStage(ABC):
    """
    Abstract base class for all pipeline stages.
    
    Provides common functionality like logging, error handling,
    and result reporting.
    """
    
    def __init__(self, name: Optional[str] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize the pipeline stage.
        
        Args:
            name: Stage name (defaults to class name)
            logger: Logger instance (creates new one if not provided)
        """
        self.name = name or self.__class__.__name__
        self.logger = logger or self._create_logger()
        self._start_time = None
        self._end_time = None
    
    def _create_logger(self) -> logging.Logger:
        """Create a logger for this stage."""
        logger = logging.getLogger(f"pipeline.{self.name}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def execute(self, shot_info: ShotInfo, **kwargs) -> ProcessingResult:
        """
        Execute the pipeline stage with timing and error handling.
        
        Args:
            shot_info: Shot information object
            **kwargs: Additional arguments specific to the stage
            
        Returns:
            ProcessingResult object with execution details
        """
        self.logger.info(f"Starting stage: {self.name} for shot {shot_info.shot_name}")
        self._start_time = time.time()
        
        result = ProcessingResult(
            stage_name=self.name,
            success=True,
            message=""
        )
        
        try:
            # Call the stage-specific processing
            self.process(shot_info, result, **kwargs)
            
            if result.success:
                result.message = f"Stage {self.name} completed successfully"
                self.logger.info(result.message)
            else:
                result.message = f"Stage {self.name} completed with errors"
                self.logger.error(result.message)
                for error in result.errors:
                    self.logger.error(f"  - {error}")
        
        except Exception as e:
            result.success = False
            error_msg = f"Stage {self.name} failed with exception: {str(e)}"
            result.add_error(error_msg)
            result.message = error_msg
            self.logger.exception(error_msg)
        
        finally:
            self._end_time = time.time()
            result.duration_seconds = self._end_time - self._start_time
            self.logger.info(
                f"Stage {self.name} completed in {result.duration_seconds:.2f} seconds"
            )
            
            # Log warnings if any
            for warning in result.warnings:
                self.logger.warning(f"  - {warning}")
        
        return result
    
    @abstractmethod
    def process(self, shot_info: ShotInfo, result: ProcessingResult, **kwargs):
        """
        Stage-specific processing logic.
        
        This method must be implemented by each stage subclass.
        
        Args:
            shot_info: Shot information object
            result: ProcessingResult object to populate
            **kwargs: Additional stage-specific arguments
        """
        pass
    
    def validate_inputs(self, shot_info: ShotInfo, result: ProcessingResult) -> bool:
        """
        Validate inputs before processing.
        
        Args:
            shot_info: Shot information object
            result: ProcessingResult object to add errors to
            
        Returns:
            True if inputs are valid, False otherwise
        """
        # Base validation - can be overridden by subclasses
        if not shot_info:
            result.add_error("Shot info is None")
            return False
        
        return True
    
    def create_directory(self, path: Path, result: ProcessingResult) -> bool:
        """
        Create a directory if it doesn't exist.
        
        Args:
            path: Directory path to create
            result: ProcessingResult object to add errors to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Created directory: {path}")
            return True
        except Exception as e:
            result.add_error(f"Failed to create directory {path}: {str(e)}")
            return False
    
    def verify_file_exists(self, path: Path, result: ProcessingResult) -> bool:
        """
        Verify that a file exists.
        
        Args:
            path: File path to check
            result: ProcessingResult object to add errors to
            
        Returns:
            True if file exists, False otherwise
        """
        if not path.exists():
            result.add_error(f"File does not exist: {path}")
            return False
        
        if not path.is_file():
            result.add_error(f"Path is not a file: {path}")
            return False
        
        return True
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        from ..config import PipelineConfig
        return getattr(PipelineConfig, key, default)


class ValidationStage(PipelineStage):
    """
    Special stage for validating data before or after processing.
    """
    
    @abstractmethod
    def validate(self, shot_info: ShotInfo, result: ProcessingResult, **kwargs) -> bool:
        """
        Perform validation.
        
        Args:
            shot_info: Shot information object
            result: ProcessingResult object to populate
            **kwargs: Additional validation-specific arguments
            
        Returns:
            True if validation passes, False otherwise
        """
        pass
    
    def process(self, shot_info: ShotInfo, result: ProcessingResult, **kwargs):
        """Execute validation."""
        is_valid = self.validate(shot_info, result, **kwargs)
        result.data['is_valid'] = is_valid
        
        if not is_valid:
            result.success = False
            result.message = f"Validation failed: {self.name}"
        else:
            result.message = f"Validation passed: {self.name}"
