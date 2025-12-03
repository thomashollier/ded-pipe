#!/usr/bin/env python3
"""
Example script demonstrating footage ingest pipeline usage.

This shows how to use the pipeline to ingest Venice 2 footage
for the test shot 'tst100'.
"""
import sys
from pathlib import Path
import logging

# Add the parent directory to the path so we can import the pipeline
sys.path.insert(0, str(Path(__file__).parent))

from ingest_pipeline.footage_ingest import (
    FootageIngestPipeline,
    ingest_shot,
    quick_ingest
)
from ingest_pipeline.config import PipelineConfig


def setup_logging():
    """Setup logging for the example."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def example_single_shot():
    """
    Example 1: Ingest a single shot using the simple function.
    """
    print("\n" + "="*80)
    print("Example 1: Single Shot Ingest")
    print("="*80 + "\n")
    
    # Define shot parameters
    source_file = Path("/path/to/venice2/raw/clip_001.mxf")
    sequence = "tst"
    shot = "100"
    in_point = 100  # Frame 100 in the raw footage
    out_point = 150  # Frame 150 in the raw footage
    project = "test_project"
    
    # Run ingest
    summary = ingest_shot(
        project=project,
        sequence=sequence,
        shot=shot,
        source_file=source_file,
        in_point=in_point,
        out_point=out_point,
        source_fps=24.0
    )
    
    # Print results
    print(f"\nPipeline Status: {summary['overall_success']}")
    print(f"Total Stages: {summary['total_stages']}")
    print(f"Successful Stages: {summary['successful_stages']}")
    print(f"Failed Stages: {summary['failed_stages']}")
    print(f"Duration: {summary['duration_seconds']:.2f} seconds")
    
    # Print stage details
    print("\nStage Results:")
    for stage_result in summary['stage_results']:
        status = "✓" if stage_result['success'] else "✗"
        print(f"  {status} {stage_result['stage_name']}: {stage_result['message']}")
        
        if stage_result['errors']:
            for error in stage_result['errors']:
                print(f"      Error: {error}")
        
        if stage_result['warnings']:
            for warning in stage_result['warnings']:
                print(f"      Warning: {warning}")


def example_pipeline_object():
    """
    Example 2: Use the FootageIngestPipeline object for managing multiple shots.
    """
    print("\n" + "="*80)
    print("Example 2: Pipeline Object with Multiple Shots")
    print("="*80 + "\n")
    
    # Create pipeline instance
    pipeline = FootageIngestPipeline(
        project="test_project",
        project_id="kitsu_project_123"
    )
    
    # Process first shot
    print("Processing tst100...")
    result1 = pipeline.ingest_shot(
        sequence="tst",
        shot="100",
        source_file=Path("/path/to/venice2/raw/clip_001.mxf"),
        in_point=100,
        out_point=150
    )
    
    # Process second shot
    print("\nProcessing tst110...")
    result2 = pipeline.ingest_shot(
        sequence="tst",
        shot="110",
        source_file=Path("/path/to/venice2/raw/clip_002.mxf"),
        in_point=200,
        out_point=275
    )
    
    # Get overall summary
    summary = pipeline.get_summary()
    print(f"\n{'='*80}")
    print("Overall Summary")
    print(f"{'='*80}")
    print(f"Project: {summary['project']}")
    print(f"Total Shots Processed: {summary['total_shots_processed']}")
    print(f"Successful: {summary['successful_shots']}")
    print(f"Failed: {summary['failed_shots']}")


def example_batch_ingest():
    """
    Example 3: Batch ingest from a list of shots.
    """
    print("\n" + "="*80)
    print("Example 3: Batch Ingest")
    print("="*80 + "\n")
    
    # Create pipeline
    pipeline = FootageIngestPipeline(project="test_project")
    
    # Define batch of shots
    shots = [
        {
            'sequence': 'tst',
            'shot': '100',
            'source_file': '/path/to/venice2/raw/clip_001.mxf',
            'in_point': 100,
            'out_point': 150,
            'source_fps': 24.0
        },
        {
            'sequence': 'tst',
            'shot': '110',
            'source_file': '/path/to/venice2/raw/clip_002.mxf',
            'in_point': 200,
            'out_point': 275,
            'source_fps': 24.0
        },
        {
            'sequence': 'tst',
            'shot': '120',
            'source_file': '/path/to/venice2/raw/clip_003.mxf',
            'in_point': 50,
            'out_point': 125,
            'source_fps': 24.0
        }
    ]
    
    # Process batch
    results = pipeline.ingest_batch(shots)
    
    # Print results
    print(f"\nProcessed {len(results)} shots")
    for result in results:
        shot_name = result.get('shot_info', {}).get('shot_name', 'unknown')
        success = result.get('overall_success', False)
        status = "✓" if success else "✗"
        print(f"  {status} {shot_name}")


def example_custom_pipeline():
    """
    Example 4: Create a custom pipeline with different stages.
    """
    print("\n" + "="*80)
    print("Example 4: Custom Pipeline")
    print("="*80 + "\n")
    
    from ingest_pipeline.pipeline import PipelineBuilder
    from ingest_pipeline.stages import (
        SonyRawConversionStage,
        OIIOColorTransformStage,
        BurnInProxyStage,  # Using burn-in version instead of regular proxy
        ShotTreeOrganizationStage
    )
    from ingest_pipeline.models import ShotInfo, EditorialCutInfo
    
    # Build custom pipeline (without Kitsu, with burn-in proxy)
    builder = PipelineBuilder("CustomIngest")
    builder.add_stage(SonyRawConversionStage())
    builder.add_stage(OIIOColorTransformStage())
    builder.add_stage(BurnInProxyStage())  # Proxy with frame numbers burned in
    builder.add_stage(ShotTreeOrganizationStage())
    
    custom_pipeline = builder.build()
    
    # Create shot info
    editorial_info = EditorialCutInfo(
        sequence="tst",
        shot="100",
        source_file=Path("/path/to/venice2/raw/clip_001.mxf"),
        in_point=100,
        out_point=150
    )
    
    shot_info = ShotInfo(
        project="test_project",
        sequence="tst",
        shot="100",
        editorial_info=editorial_info,
        source_raw_path=Path("/path/to/venice2/raw/clip_001.mxf")
    )
    
    # Execute custom pipeline
    summary = custom_pipeline.execute(shot_info)
    
    print(f"Custom pipeline completed: {summary['overall_success']}")


def example_stage_usage():
    """
    Example 5: Using individual stages independently.
    """
    print("\n" + "="*80)
    print("Example 5: Using Individual Stages")
    print("="*80 + "\n")
    
    from ingest_pipeline.stages import OIIOColorTransformStage
    from ingest_pipeline.models import ShotInfo, EditorialCutInfo, ImageSequence
    
    # Create a stage
    color_stage = OIIOColorTransformStage()
    
    # Create shot info
    editorial_info = EditorialCutInfo(
        sequence="tst",
        shot="100",
        source_file=Path("/path/to/venice2/raw/clip_001.mxf"),
        in_point=100,
        out_point=150
    )
    
    shot_info = ShotInfo(
        project="test_project",
        sequence="tst",
        shot="100",
        editorial_info=editorial_info
    )
    
    # Create input sequence info (from a previous stage)
    input_sequence = ImageSequence(
        directory=Path("/tmp/dpx_output"),
        base_name="tst100",
        extension="dpx",
        first_frame=993,
        last_frame=1058,
        frame_padding=4
    )
    
    # Execute just this stage
    result = color_stage.execute(
        shot_info=shot_info,
        input_sequence=input_sequence,
        output_dir=Path("/tmp/exr_output")
    )
    
    print(f"Stage completed: {result.success}")
    print(f"Message: {result.message}")
    
    if result.data:
        print("\nStage Data:")
        for key, value in result.data.items():
            print(f"  {key}: {value}")


def main():
    """Run all examples."""
    setup_logging()
    
    print("\n" + "="*80)
    print("Footage Ingest Pipeline Examples")
    print("="*80)
    
    # Note: These examples use placeholder paths
    # In production, you would use actual file paths
    
    print("\nNote: These examples use placeholder data and will show warnings")
    print("about tools not being available. In production, you would configure")
    print("the actual tool paths and provide real source files.\n")
    
    try:
        # Run examples
        example_single_shot()
        example_pipeline_object()
        example_batch_ingest()
        example_custom_pipeline()
        example_stage_usage()
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
    except Exception as e:
        print(f"\n\nError running examples: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
