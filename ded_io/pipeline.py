"""
Pipeline orchestrator for chaining stages together.
Provides the main execution framework for running complete pipelines.
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime

from .models import ShotInfo, ProcessingResult
from .stages.base import PipelineStage


class Pipeline:
    """
    Main pipeline orchestrator.
    
    Chains together multiple stages and executes them in sequence,
    handling data flow and error management.
    """
    
    def __init__(
        self,
        name: str,
        stages: Optional[List[PipelineStage]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize pipeline.
        
        Args:
            name: Pipeline name
            stages: List of pipeline stages (can be added later)
            logger: Logger instance
        """
        self.name = name
        self.stages = stages or []
        self.logger = logger or self._create_logger()
        self.results: List[ProcessingResult] = []
    
    def _create_logger(self) -> logging.Logger:
        """Create logger for this pipeline."""
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
    
    def add_stage(self, stage: PipelineStage):
        """
        Add a stage to the pipeline.
        
        Args:
            stage: Pipeline stage to add
        """
        self.stages.append(stage)
        self.logger.debug(f"Added stage: {stage.name}")
    
    def execute(
        self,
        shot_info: ShotInfo,
        stop_on_error: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the complete pipeline.
        
        Args:
            shot_info: Shot information object
            stop_on_error: Stop execution if a stage fails
            **kwargs: Additional arguments passed to all stages
            
        Returns:
            Dictionary with execution summary
        """
        self.logger.info(f"Starting pipeline: {self.name}")
        self.logger.info(f"Processing shot: {shot_info.shot_name}")
        self.results = []
        
        start_time = datetime.now()
        shot_info.processing_status = "processing"
        
        # Accumulated data from previous stages
        pipeline_data = dict(kwargs)
        
        # Execute each stage
        for i, stage in enumerate(self.stages):
            self.logger.info(f"Executing stage {i+1}/{len(self.stages)}: {stage.name}")
            
            # Execute stage with accumulated pipeline data
            result = stage.execute(shot_info, **pipeline_data)
            self.results.append(result)
            
            # Accumulate data from this stage for next stages
            if result.data:
                # Map known outputs to expected inputs for next stages
                if 'dpx_sequence' in result.data:
                    pipeline_data['input_sequence'] = result.data['dpx_sequence']
                if 'output_sequence' in result.data:
                    pipeline_data['input_sequence'] = result.data['output_sequence']
                if 'proxy_file' in result.data:
                    pipeline_data['proxy_file'] = result.data['proxy_file']
                # Also store all data under stage name for explicit access
                pipeline_data[f'{stage.name}_output'] = result.data
            
            # Check for errors
            if not result.success:
                shot_info.processing_status = "error"
                
                if stop_on_error:
                    self.logger.error(
                        f"Pipeline stopped due to error in stage: {stage.name}"
                    )
                    break
                else:
                    self.logger.warning(
                        f"Stage {stage.name} failed but continuing pipeline"
                    )
        
        # Update final status
        if shot_info.processing_status != "error":
            shot_info.processing_status = "complete"
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Build summary
        summary = self._build_summary(shot_info, duration)
        
        self.logger.info(f"Pipeline {self.name} completed in {duration:.2f} seconds")
        self.logger.info(f"Status: {shot_info.processing_status}")
        
        return summary
    
    def _build_summary(self, shot_info: ShotInfo, duration: float) -> Dict[str, Any]:
        """
        Build execution summary.
        
        Args:
            shot_info: Shot information
            duration: Total execution time in seconds
            
        Returns:
            Summary dictionary
        """
        total_stages = len(self.stages)
        successful_stages = sum(1 for r in self.results if r.success)
        failed_stages = total_stages - successful_stages
        
        return {
            'pipeline_name': self.name,
            'shot_info': shot_info.to_dict(),
            'duration_seconds': duration,
            'total_stages': total_stages,
            'successful_stages': successful_stages,
            'failed_stages': failed_stages,
            'overall_success': shot_info.processing_status == "complete",
            'stage_results': [r.to_dict() for r in self.results]
        }
    
    def save_report(self, output_path: Path):
        """
        Save execution report to file.
        
        Args:
            output_path: Path to save report JSON
        """
        if not self.results:
            self.logger.warning("No results to save")
            return
        
        summary = {
            'pipeline_name': self.name,
            'execution_time': datetime.now().isoformat(),
            'stage_results': [r.to_dict() for r in self.results]
        }
        
        try:
            with open(output_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            self.logger.info(f"Report saved to: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save report: {str(e)}")


class PipelineBuilder:
    """
    Builder class for constructing pipelines.
    
    Provides a fluent interface for building pipelines.
    """
    
    def __init__(self, name: str):
        """
        Initialize builder.
        
        Args:
            name: Pipeline name
        """
        self.pipeline = Pipeline(name)
    
    def add_stage(self, stage: PipelineStage) -> 'PipelineBuilder':
        """
        Add a stage to the pipeline.
        
        Args:
            stage: Stage to add
            
        Returns:
            Self for chaining
        """
        self.pipeline.add_stage(stage)
        return self
    
    def build(self) -> Pipeline:
        """
        Build and return the pipeline.
        
        Returns:
            Constructed pipeline
        """
        return self.pipeline


class ConditionalPipeline(Pipeline):
    """
    Pipeline that can skip stages based on conditions.
    
    Useful for creating flexible pipelines that adapt based
    on input data or previous stage results.
    """
    
    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)
        self.stage_conditions = {}
    
    def add_conditional_stage(
        self,
        stage: PipelineStage,
        condition_fn: callable
    ):
        """
        Add a stage with a condition function.
        
        Args:
            stage: Pipeline stage
            condition_fn: Function that takes (shot_info, previous_results)
                         and returns True if stage should run
        """
        self.add_stage(stage)
        self.stage_conditions[stage.name] = condition_fn
    
    def execute(self, shot_info: ShotInfo, stop_on_error: bool = True, **kwargs):
        """Execute with conditional stage execution."""
        self.logger.info(f"Starting conditional pipeline: {self.name}")
        self.results = []
        
        start_time = datetime.now()
        shot_info.processing_status = "processing"
        
        for i, stage in enumerate(self.stages):
            # Check condition if exists
            if stage.name in self.stage_conditions:
                condition_fn = self.stage_conditions[stage.name]
                should_run = condition_fn(shot_info, self.results)
                
                if not should_run:
                    self.logger.info(
                        f"Skipping stage {i+1}/{len(self.stages)}: {stage.name} "
                        f"(condition not met)"
                    )
                    
                    # Create a skipped result
                    result = ProcessingResult(
                        stage_name=stage.name,
                        success=True,
                        message="Stage skipped (condition not met)"
                    )
                    self.results.append(result)
                    continue
            
            # Execute stage
            self.logger.info(f"Executing stage {i+1}/{len(self.stages)}: {stage.name}")
            result = stage.execute(shot_info, **kwargs)
            self.results.append(result)
            
            if not result.success:
                shot_info.processing_status = "error"
                if stop_on_error:
                    break
        
        if shot_info.processing_status != "error":
            shot_info.processing_status = "complete"
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return self._build_summary(shot_info, duration)
