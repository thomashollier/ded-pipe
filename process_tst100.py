#!/usr/bin/env python3
"""
Process shot tst200 from camera raw to Kitsu.

This script processes a specific shot with configurable frame ranges.
All frame numbers and paths are clearly defined at the top for easy modification.
"""
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, '/home/pigeon/ded-pipe-main')

from ded_io.pipeline import PipelineBuilder
from ded_io.models import ShotInfo
from ded_io.stages.ocio_conversion import OCIOConversionStage
from ded_io.stages.proxy_generation import ProxyGenerationStage
from ded_io.stages.shot_tree_organization import ShotTreeOrganizationStage
from ded_io.stages.kitsu_integration import KitsuIntegrationStage


# ============================================================================
# SHOT CONFIGURATION - EDIT THESE VALUES
# ============================================================================

SHOT_NAME = "tst200"
SEQUENCE = "tst"

# Frame range for this shot (the actual frame numbers you want to process)
FIRST_FRAME = 993
LAST_FRAME = 1059
# These will be automatically calculated:
# TOTAL_FRAMES = 67 (1059 - 993 + 1)
# FRAME_RANGE = "993-1059"

# Source camera file
SOURCE_FILE = "/home/pigeon/Venice2/edt200_pla_mainCamera_v001_raw.mxf"

# ============================================================================


def main():
    """Process the shot."""
    
    # Calculate derived values
    total_frames = LAST_FRAME - FIRST_FRAME + 1
    frame_range = f"{FIRST_FRAME}-{LAST_FRAME}"
    
    # Validate source file exists
    source_path = Path(SOURCE_FILE)
    if not source_path.exists():
        print(f"❌ ERROR: Source file not found: {SOURCE_FILE}")
        print("\nPlease update SOURCE_FILE in this script with the correct path.")
        sys.exit(1)
    
    # Print configuration
    print("=" * 70)
    print("🎬 PROCESSING SHOT: tst200")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Shot Name:    {SHOT_NAME}")
    print(f"  Sequence:     {SEQUENCE}")
    print(f"  Frame Range:  {frame_range} ({total_frames} frames)")
    print(f"  Source File:  {source_path.name}")
    print(f"  Full Path:    {SOURCE_FILE}")
    print("=" * 70)
    print()
    
    # Create ShotInfo with frame range data
    shot_info = ShotInfo(
        shot_name=SHOT_NAME,
        sequence=SEQUENCE,
        source_raw_path=str(source_path),
        first_frame=FIRST_FRAME,        # → Used by OCIO for EXR numbering
        last_frame=LAST_FRAME,          # → Used by OCIO for EXR numbering
        total_frames=total_frames,      # → Uploaded to Kitsu metadata
        frame_range=frame_range         # → Uploaded to Kitsu metadata
    )
    
    print("🚀 Building pipeline...\n")
    
    # Build pipeline
    pipeline = (
        PipelineBuilder()
        .add_stage(OCIOConversionStage(
            input_colorspace="Sony SLog3 SGamut3.Cine",
            output_colorspace="ACEScg",
            output_format="exr"
        ))
        .add_stage(ProxyGenerationStage(
            resolution="1920x1080",
            colorspace="sRGB"
        ))
        .add_stage(ShotTreeOrganizationStage())
        .add_stage(KitsuIntegrationStage())
        .build()
    )
    
    # Execute
    print("⚙️  Executing pipeline...\n")
    result = pipeline.execute(shot_info)
    
    # Print results
    print("\n" + "=" * 70)
    if result.success:
        print("✅ PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"\n📊 Results:")
        print(f"  • Kitsu Shot:     {result.data.get('kitsu_shot_name', 'N/A')}")
        print(f"  • Shot ID:        {result.data.get('kitsu_shot_id', 'N/A')}")
        print(f"  • Proxy Uploaded: {result.data.get('proxy_uploaded', False)}")
        print(f"  • Tasks Created:  {result.data.get('tasks_created', 0)}")
        
        metadata_fields = result.data.get('metadata_updated', [])
        print(f"  • Metadata:       {len(metadata_fields)} fields updated")
        
        # Show frame range was uploaded
        if 'frame_in' in metadata_fields:
            print(f"\n📋 Frame data uploaded to Kitsu:")
            print(f"  • Frame In:    {FIRST_FRAME}")
            print(f"  • Frame Out:   {LAST_FRAME}")
            print(f"  • Frame Count: {total_frames}")
            print(f"  • Frame Range: {frame_range}")
        
        print("\n✓ Shot tst200 processed successfully!")
        print("\nNext steps:")
        print("  1. Check Kitsu for the uploaded shot")
        print("  2. Review the proxy preview")
        print("  3. Verify EXR plates in shot tree")
        
    else:
        print("❌ PIPELINE FAILED")
        print("=" * 70)
        
        if result.errors:
            print("\n🚨 Errors:")
            for error in result.errors:
                print(f"  • {error}")
        
        if result.warnings:
            print("\n⚠️  Warnings:")
            for warning in result.warnings:
                print(f"  • {warning}")
        
        print()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)