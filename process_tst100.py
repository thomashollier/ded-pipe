#!/usr/bin/env python3
"""
Quick start script for processing the test shot tst100.

This demonstrates how to process the specific shot mentioned in the requirements:
- Sequence: tst
- Shot: 100
- Digital shot name: tst100
"""
from pathlib import Path
from ded_io import ingest_shot

def process_tst100(source_file: str, in_point: int, out_point: int):
    """
    Process the test shot tst100.
    
    Args:
        source_file: Path to the Venice 2 raw MXF file
        in_point: Editorial in point (frame number in source)
        out_point: Editorial out point (frame number in source)
    
    Example:
        process_tst100(
            source_file="/path/to/venice2/clip.mxf",
            in_point=100,
            out_point=150
        )
    """
    
    print("="*80)
    print("Processing Test Shot: tst100")
    print("="*80)
    print(f"\nSource File: {source_file}")
    print(f"Editorial In Point: {in_point}")
    print(f"Editorial Out Point: {out_point}")
    print(f"Duration (editorial): {out_point - in_point + 1} frames")
    print(f"\nWith handles (8 frames head + tail):")
    print(f"  First frame: 993")
    print(f"  Last frame: {993 + (out_point - in_point) + 8 + 8}")
    print(f"  Total frames: {(out_point - in_point + 1) + 16}")
    print()
    
    # Run the ingest
    summary = ingest_shot(
        project="test_project",
        sequence="tst",
        shot="100",
        source_file=Path(source_file),
        in_point=in_point,
        out_point=out_point,
        source_fps=24.0,
        project_id="kitsu_test_project"
    )
    
    # Print results
    print("\n" + "="*80)
    print("PROCESSING RESULTS")
    print("="*80)
    
    print(f"\nOverall Status: {'SUCCESS ✓' if summary['overall_success'] else 'FAILED ✗'}")
    print(f"Total Duration: {summary['duration_seconds']:.2f} seconds")
    print(f"Stages Completed: {summary['successful_stages']}/{summary['total_stages']}")
    
    # Print shot info
    shot_info = summary['shot_info']
    print(f"\nShot Information:")
    print(f"  Shot Name: {shot_info['shot_name']}")
    print(f"  Frame Range: {shot_info['frame_range']}")
    print(f"  Total Frames: {shot_info['total_frames']}")
    
    if shot_info.get('output_plates_path'):
        print(f"  Plates Path: {shot_info['output_plates_path']}")
    if shot_info.get('output_proxy_path'):
        print(f"  Proxy Path: {shot_info['output_proxy_path']}")
    
    # Print stage details
    print(f"\nStage Details:")
    for i, stage in enumerate(summary['stage_results'], 1):
        status = "✓" if stage['success'] else "✗"
        duration = stage.get('duration_seconds', 0)
        print(f"  {i}. {status} {stage['stage_name']}")
        print(f"     Duration: {duration:.2f}s")
        print(f"     {stage['message']}")
        
        # Show errors
        if stage['errors']:
            print(f"     Errors:")
            for error in stage['errors']:
                print(f"       - {error}")
        
        # Show warnings
        if stage['warnings']:
            print(f"     Warnings:")
            for warning in stage['warnings']:
                print(f"       - {warning}")
        
        # Show key data
        if stage['data']:
            interesting_keys = ['frames_processed', 'frames_created', 'proxy_size_mb', 
                              'files_copied', 'kitsu_shot_id']
            for key in interesting_keys:
                if key in stage['data']:
                    print(f"     {key}: {stage['data'][key]}")
        print()
    
    print("="*80)
    
    return summary


def main():
    """
    Main function for quick testing.
    
    IMPORTANT: Update the source_file path with your actual raw footage location.
    """
    
    # CONFIGURE THESE VALUES
    # =====================
    
    # Path to your Venice 2 raw MXF file
    source_file = "/path/to/your/venice2/clip.mxf"
    
    # Editorial cut points (adjust based on your actual footage)
    in_point = 100   # Where your shot starts in the raw footage
    out_point = 150  # Where your shot ends in the raw footage
    
    # =====================
    
    # Validate
    if not Path(source_file).exists():
        print(f"ERROR: Source file not found: {source_file}")
        print("\nPlease update the source_file variable in this script with")
        print("the actual path to your Venice 2 raw footage file.")
        return
    
    # Process the shot
    summary = process_tst100(source_file, in_point, out_point)
    
    # Save report
    if summary.get('overall_success'):
        print("\n✓ Shot tst100 processed successfully!")
        print("\nNext steps:")
        print("  1. Check the plates in the shot tree")
        print("  2. Review the proxy movie")
        print("  3. Verify the Kitsu entry")
    else:
        print("\n✗ Shot processing encountered errors.")
        print("\nTroubleshooting:")
        print("  1. Check the error messages above")
        print("  2. Verify tool paths in config.py")
        print("  3. Check source file format and location")
        print("  4. Review log output for details")


if __name__ == "__main__":
    main()
