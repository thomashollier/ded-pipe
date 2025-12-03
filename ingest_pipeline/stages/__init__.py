"""
Footage Ingest Pipeline

A flexible, modular pipeline for ingesting camera footage into
a VFX production pipeline.

Main components:
- config: Configuration settings
- models: Data models for shots and results
- stages: Individual processing stages
- pipeline: Pipeline orchestration
- footage_ingest: High-level ingest interface
"""

__version__ = '0.1.0'

from .config import PipelineConfig, KitsuConfig
from .models import ShotInfo, EditorialCutInfo, ProcessingResult, ImageSequence
from .pipeline import Pipeline, PipelineBuilder, ConditionalPipeline
from .footage_ingest import (
    FootageIngestPipeline,
    ingest_shot,
    quick_ingest,
    create_ingest_pipeline
)

__all__ = [
    # Config
    'PipelineConfig',
    'KitsuConfig',
    
    # Models
    'ShotInfo',
    'EditorialCutInfo',
    'ProcessingResult',
    'ImageSequence',
    
    # Pipeline
    'Pipeline',
    'PipelineBuilder',
    'ConditionalPipeline',
    
    # Footage Ingest
    'FootageIngestPipeline',
    'ingest_shot',
    'quick_ingest',
    'create_ingest_pipeline',
]
