#!/usr/bin/env python3
"""
Setup and configuration check script for the footage ingest pipeline.

Run this script to:
1. Check for required tools
2. Verify tool versions
3. Test basic functionality
4. Configure environment
"""
import subprocess
import sys
from pathlib import Path
import shutil


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text:^80}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*80}{Colors.END}\n")


def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def check_python_version():
    """Check Python version."""
    print_header("Python Version Check")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python version: {version_str}")
        return True
    else:
        print_error(f"Python version {version_str} is too old")
        print("  Python 3.8 or later is required")
        return False


def check_tool(command, name, required=True):
    """
    Check if a command line tool is available.
    
    Args:
        command: Command to check
        name: Display name
        required: Whether tool is required
    
    Returns:
        True if found, False otherwise
    """
    path = shutil.which(command)
    
    if path:
        # Try to get version
        try:
            result = subprocess.run(
                [command, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            version = result.stdout.split('\n')[0] if result.stdout else "version unknown"
            print_success(f"{name}: {path}")
            print(f"  Version: {version}")
            return True
        except:
            print_success(f"{name}: {path}")
            return True
    else:
        if required:
            print_error(f"{name}: Not found")
        else:
            print_warning(f"{name}: Not found (optional)")
        return False


def check_tools():
    """Check all required and optional tools."""
    print_header("Tool Availability Check")
    
    results = {}
    
    # Required tools
    print(f"{Colors.BOLD}Required Tools:{Colors.END}")
    results['ffmpeg'] = check_tool('ffmpeg', 'FFmpeg', required=True)
    
    # Optional tools (would be required in production)
    print(f"\n{Colors.BOLD}Optional Tools (required for full functionality):{Colors.END}")
    results['oiiotool'] = check_tool('oiiotool', 'OpenImageIO', required=False)
    
    # Python packages
    print(f"\n{Colors.BOLD}Python Packages:{Colors.END}")
    
    try:
        import requests
        print_success(f"requests: {requests.__version__}")
        results['requests'] = True
    except ImportError:
        print_error("requests: Not installed")
        print("  Install with: pip install requests")
        results['requests'] = False
    
    return results


def check_import():
    """Check if the pipeline package can be imported."""
    print_header("Package Import Check")
    
    try:
        import ingest_pipeline
        print_success(f"ingest_pipeline package: Version {ingest_pipeline.__version__}")
        
        # Try importing key components
        from ingest_pipeline import (
            PipelineConfig,
            FootageIngestPipeline,
            ingest_shot
        )
        print_success("Core modules imported successfully")
        return True
        
    except ImportError as e:
        print_error(f"Failed to import package: {str(e)}")
        print("\nMake sure you're running this from the project root directory")
        return False


def check_directories():
    """Check directory structure."""
    print_header("Directory Structure Check")
    
    current_dir = Path.cwd()
    expected_files = [
        'ingest_pipeline/__init__.py',
        'ingest_pipeline/config.py',
        'ingest_pipeline/pipeline.py',
        'ingest_pipeline/stages/__init__.py',
        'README.md'
    ]
    
    all_found = True
    for file in expected_files:
        path = current_dir / file
        if path.exists():
            print_success(f"Found: {file}")
        else:
            print_error(f"Missing: {file}")
            all_found = False
    
    return all_found


def test_basic_functionality():
    """Test basic pipeline functionality."""
    print_header("Basic Functionality Test")
    
    try:
        from ingest_pipeline import PipelineConfig
        from ingest_pipeline.models import EditorialCutInfo, ShotInfo
        from ingest_pipeline.pipeline import PipelineBuilder
        from ingest_pipeline.stages import CleanupStage
        
        # Test config
        print_success("Configuration loaded")
        print(f"  Digital start frame: {PipelineConfig.DIGITAL_START_FRAME}")
        print(f"  Handle frames: {PipelineConfig.HEAD_HANDLE_FRAMES}")
        
        # Test models
        editorial_info = EditorialCutInfo(
            sequence="test",
            shot="100",
            source_file=Path("/tmp/test.mxf"),
            in_point=100,
            out_point=150
        )
        print_success("Models work correctly")
        
        shot_info = ShotInfo(
            project="test",
            sequence="test",
            shot="100",
            editorial_info=editorial_info
        )
        print_success("ShotInfo created successfully")
        print(f"  First frame: {shot_info.first_frame}")
        print(f"  Last frame: {shot_info.last_frame}")
        
        # Test pipeline builder
        builder = PipelineBuilder("TestPipeline")
        builder.add_stage(CleanupStage())
        pipeline = builder.build()
        print_success("Pipeline builder works")
        
        return True
        
    except Exception as e:
        print_error(f"Functionality test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def print_configuration_guide():
    """Print configuration guide."""
    print_header("Configuration Guide")
    
    print("To configure the pipeline for your environment:\n")
    
    print(f"{Colors.BOLD}1. Edit ingest_pipeline/config.py:{Colors.END}")
    print("   - Set tool paths (SONY_CONVERT_TOOL, OIIO_TOOL, FFMPEG_TOOL)")
    print("   - Adjust frame numbering if needed")
    print("   - Configure shot tree root directory")
    print("   - Set ACES version and color spaces\n")
    
    print(f"{Colors.BOLD}2. Configure Kitsu (if using):{Colors.END}")
    print("   - Set environment variables:")
    print("     export KITSU_HOST='https://your-kitsu.com/api'")
    print("     export KITSU_EMAIL='your-email'")
    print("     export KITSU_PASSWORD='your-password'\n")
    
    print(f"{Colors.BOLD}3. Test with sample shot:{Colors.END}")
    print("   - Edit process_tst100.py")
    print("   - Set the source_file path to your test footage")
    print("   - Set in_point and out_point")
    print("   - Run: python process_tst100.py\n")


def main():
    """Run all checks."""
    print(f"\n{Colors.BOLD}Footage Ingest Pipeline Setup Check{Colors.END}")
    
    results = {}
    
    # Run checks
    results['python'] = check_python_version()
    results['tools'] = check_tools()
    results['directories'] = check_directories()
    results['import'] = check_import()
    results['functionality'] = test_basic_functionality()
    
    # Print summary
    print_header("Summary")
    
    all_passed = all([
        results['python'],
        results['directories'],
        results['import'],
        results['functionality']
    ])
    
    if all_passed:
        print_success("Core setup is complete!")
        print("\nThe pipeline is ready for basic testing.")
        
        # Check tools
        if not all(results['tools'].values()):
            print_warning("\nSome tools are missing:")
            for tool, found in results['tools'].items():
                if not found:
                    print(f"  - {tool}")
            print("\nThese tools are needed for full functionality.")
    else:
        print_error("Setup is incomplete.")
        print("\nPlease resolve the issues above before using the pipeline.")
    
    # Always show configuration guide
    print_configuration_guide()
    
    # Next steps
    print_header("Next Steps")
    
    print("1. Install missing dependencies:")
    print("   pip install -r requirements.txt\n")
    
    print("2. Install external tools:")
    print("   - Sony raw converter (vendor-specific)")
    print("   - OpenImageIO with ACES support")
    print("   - FFmpeg\n")
    
    print("3. Review and edit configuration:")
    print("   - ingest_pipeline/config.py\n")
    
    print("4. Try the examples:")
    print("   - python examples.py (shows all usage patterns)")
    print("   - python process_tst100.py (process test shot)\n")
    
    print("5. Read the documentation:")
    print("   - README.md (complete guide)")
    print("   - PROJECT_STRUCTURE.md (architecture overview)\n")


if __name__ == "__main__":
    main()
