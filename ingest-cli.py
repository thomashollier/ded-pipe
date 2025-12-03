#!/usr/bin/env python3
"""
Command-line interface for the footage ingest pipeline.

This script allows you to run the complete ingest process from the command line,
using configuration file settings combined with shot-specific arguments.

Usage:
    ingest-cli --source /path/to/clip.mxf --sequence seq --shot 010 --in 100 --out 200
    ingest-cli --config my_config.json --source clip.mxf --sequence seq --shot 010 --in 100 --out 200
    ingest-cli --batch shots.json
"""
import argparse
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add parent directory to path for local import
sys.path.insert(0, str(Path(__file__).parent))

# Determine package name by checking what exists
PACKAGE_NAME = None
script_dir = Path(__file__).parent

# Check for common package names
for possible_name in ['ded_io', 'ingest_pipeline', 'footage_ingest']:
    if (script_dir / possible_name).exists():
        PACKAGE_NAME = possible_name
        break

if PACKAGE_NAME is None:
    print("Error: Could not find the package directory.")
    print("Expected one of: ded_io, ingest_pipeline, footage_ingest")
    print(f"In directory: {script_dir}")
    print("\nPlease ensure the package directory exists and hasn't been renamed.")
    sys.exit(1)

# Try to import the package
try:
    # Dynamic import based on package name
    if PACKAGE_NAME == 'ded_io':
        from ded_io import (
            FootageIngestPipeline,
            ingest_shot,
            PipelineConfig
        )
        from ded_io.models import EditorialCutInfo, ShotInfo
    elif PACKAGE_NAME == 'ingest_pipeline':
        from ingest_pipeline import (
            FootageIngestPipeline,
            ingest_shot,
            PipelineConfig
        )
        from ingest_pipeline.models import EditorialCutInfo, ShotInfo
    else:
        from footage_ingest import (
            FootageIngestPipeline,
            ingest_shot,
            PipelineConfig
        )
        from footage_ingest.models import EditorialCutInfo, ShotInfo
        
except ImportError as e:
    print(f"Error: Could not import from {PACKAGE_NAME} package.")
    print("Make sure you're running this script from the repository root directory.")
    print(f"\nCurrent directory: {Path.cwd()}")
    print(f"Script directory: {script_dir}")
    print(f"Looking for package: {PACKAGE_NAME}")
    print("\nOption 1: Run from repository root (no installation needed)")
    print("  cd /path/to/your-project")
    print("  python ingest-cli.py ...")
    print("\nOption 2: Rename package directory to match expected name")
    print(f"  mv old_name {PACKAGE_NAME}")
    print("\nOption 3: Install the package")
    print("  pip install -e .")
    print("\nOption 4: Set PYTHONPATH")
    print("  export PYTHONPATH=/path/to/your-project:$PYTHONPATH")
    print(f"\nImport error details: {e}")
    sys.exit(1)


class IngestCLI:
    """Command-line interface for footage ingest."""
    
    def __init__(self):
        """Initialize CLI."""
        self.parser = self._create_parser()
        self.logger = self._setup_logging()
        self.config = {}
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            description='Footage Ingest Pipeline - Command Line Interface',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Ingest a single shot
  %(prog)s --source /path/to/clip.mxf --sequence tst --shot 100 --in 100 --out 200
  
  # Use custom config file
  %(prog)s --config my_config.json --source clip.mxf --sequence tst --shot 100 --in 100 --out 200
  
  # Batch process from JSON file
  %(prog)s --batch shots.json
  
  # Dry run to preview settings
  %(prog)s --source clip.mxf --sequence tst --shot 100 --in 100 --out 200 --dry-run
  
  # Verbose output
  %(prog)s --source clip.mxf --sequence tst --shot 100 --in 100 --out 200 -v
            """
        )
        
        # Configuration
        config_group = parser.add_argument_group('Configuration')
        config_group.add_argument(
            '--config', '-c',
            type=str,
            help='Path to JSON configuration file (overrides defaults)'
        )
        
        # Shot data (for single shot processing)
        shot_group = parser.add_argument_group('Shot Data (required for single shot)')
        shot_group.add_argument(
            '--source', '-s',
            type=str,
            help='Path to source raw footage file'
        )
        shot_group.add_argument(
            '--sequence',
            type=str,
            help='Sequence name (e.g., "tst")'
        )
        shot_group.add_argument(
            '--shot',
            type=str,
            help='Shot number/name (e.g., "100")'
        )
        shot_group.add_argument(
            '--in', '-i',
            dest='in_point',
            type=int,
            help='Editorial in point (frame number)'
        )
        shot_group.add_argument(
            '--out', '-o',
            dest='out_point',
            type=int,
            help='Editorial out point (frame number)'
        )
        
        # Optional shot data
        shot_group.add_argument(
            '--fps',
            type=float,
            default=24.0,
            help='Source frame rate (default: 24.0)'
        )
        shot_group.add_argument(
            '--timecode',
            type=str,
            help='Source timecode start (optional)'
        )
        
        # Batch processing
        batch_group = parser.add_argument_group('Batch Processing')
        batch_group.add_argument(
            '--batch', '-b',
            type=str,
            help='Path to JSON file with batch shot data'
        )
        
        # Project settings
        project_group = parser.add_argument_group('Project Settings')
        project_group.add_argument(
            '--project', '-p',
            type=str,
            help='Project name (default: from config or "default")'
        )
        project_group.add_argument(
            '--project-id',
            type=str,
            help='Kitsu project ID (optional)'
        )
        
        # Output options
        output_group = parser.add_argument_group('Output Options')
        output_group.add_argument(
            '--output-dir',
            type=str,
            help='Override output directory'
        )
        output_group.add_argument(
            '--report',
            type=str,
            help='Save execution report to file'
        )
        
        # Pipeline options
        pipeline_group = parser.add_argument_group('Pipeline Options')
        pipeline_group.add_argument(
            '--skip-kitsu',
            action='store_true',
            help='Skip Kitsu integration stage'
        )
        pipeline_group.add_argument(
            '--skip-cleanup',
            action='store_true',
            help='Skip cleanup stage (preserve temp files)'
        )
        pipeline_group.add_argument(
            '--burn-in',
            action='store_true',
            help='Use burn-in proxy instead of regular proxy'
        )
        
        # Execution options
        exec_group = parser.add_argument_group('Execution Options')
        exec_group.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be done without executing'
        )
        exec_group.add_argument(
            '--stop-on-error',
            action='store_true',
            default=True,
            help='Stop pipeline on first error (default: True)'
        )
        exec_group.add_argument(
            '--continue-on-error',
            action='store_true',
            help='Continue pipeline even if stages fail'
        )
        
        # Logging
        log_group = parser.add_argument_group('Logging')
        log_group.add_argument(
            '-v', '--verbose',
            action='store_true',
            help='Verbose output (DEBUG level)'
        )
        log_group.add_argument(
            '-q', '--quiet',
            action='store_true',
            help='Quiet output (ERROR level only)'
        )
        log_group.add_argument(
            '--log-file',
            type=str,
            help='Write log to file'
        )
        
        # Version
        parser.add_argument(
            '--version',
            action='version',
            version='%(prog)s 0.1.0'
        )
        
        return parser
    
    def _setup_logging(self, verbose=False, quiet=False, log_file=None) -> logging.Logger:
        """Setup logging configuration."""
        if quiet:
            level = logging.ERROR
        elif verbose:
            level = logging.DEBUG
        else:
            level = logging.INFO
        
        # Create logger
        logger = logging.getLogger('ingest_cli')
        logger.setLevel(level)
        
        # Remove existing handlers
        logger.handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)  # Always debug in file
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Path to config file
            
        Returns:
            Configuration dictionary
        """
        if not config_path:
            return {}
        
        config_file = Path(config_path)
        if not config_file.exists():
            self.logger.error(f"Config file not found: {config_path}")
            sys.exit(1)
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            self.logger.info(f"Loaded configuration from: {config_path}")
            return config
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in config file: {str(e)}")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Failed to load config: {str(e)}")
            sys.exit(1)
    
    def load_batch_file(self, batch_path: str) -> List[Dict[str, Any]]:
        """
        Load batch shot data from JSON file.
        
        Args:
            batch_path: Path to batch file
            
        Returns:
            List of shot data dictionaries
        """
        batch_file = Path(batch_path)
        if not batch_file.exists():
            self.logger.error(f"Batch file not found: {batch_path}")
            sys.exit(1)
        
        try:
            with open(batch_file, 'r') as f:
                batch_data = json.load(f)
            
            # Validate format
            if not isinstance(batch_data, list):
                self.logger.error("Batch file must contain a JSON array")
                sys.exit(1)
            
            self.logger.info(f"Loaded {len(batch_data)} shots from: {batch_path}")
            return batch_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in batch file: {str(e)}")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Failed to load batch file: {str(e)}")
            sys.exit(1)
    
    def validate_shot_data(self, args: argparse.Namespace) -> bool:
        """
        Validate that required shot data is provided.
        
        Args:
            args: Parsed arguments
            
        Returns:
            True if valid, False otherwise
        """
        required = ['source', 'sequence', 'shot', 'in_point', 'out_point']
        missing = [field for field in required if not getattr(args, field, None)]
        
        if missing:
            self.logger.error(f"Missing required arguments: {', '.join(missing)}")
            return False
        
        # Validate source file exists
        source_path = Path(args.source)
        if not source_path.exists():
            self.logger.error(f"Source file not found: {args.source}")
            return False
        
        # Validate frame numbers
        if args.in_point >= args.out_point:
            self.logger.error(
                f"In point ({args.in_point}) must be less than out point ({args.out_point})"
            )
            return False
        
        return True
    
    def print_shot_info(self, shot_data: Dict[str, Any]):
        """
        Print shot information.
        
        Args:
            shot_data: Shot data dictionary
        """
        print("\n" + "="*80)
        print("SHOT INFORMATION")
        print("="*80)
        print(f"Sequence:      {shot_data.get('sequence')}")
        print(f"Shot:          {shot_data.get('shot')}")
        print(f"Source:        {shot_data.get('source_file')}")
        print(f"In Point:      {shot_data.get('in_point')}")
        print(f"Out Point:     {shot_data.get('out_point')}")
        print(f"Duration:      {shot_data.get('out_point') - shot_data.get('in_point') + 1} frames")
        print(f"FPS:           {shot_data.get('source_fps', 24.0)}")
        
        # Calculate digital frame range
        duration = shot_data.get('out_point') - shot_data.get('in_point') + 1
        first_frame = PipelineConfig.DIGITAL_START_FRAME - PipelineConfig.HEAD_HANDLE_FRAMES
        last_frame = first_frame + duration + PipelineConfig.HEAD_HANDLE_FRAMES + PipelineConfig.TAIL_HANDLE_FRAMES - 1
        
        print(f"\nDigital Frames:")
        print(f"  First Frame: {first_frame}")
        print(f"  Last Frame:  {last_frame}")
        print(f"  Total:       {last_frame - first_frame + 1} frames")
        print("="*80 + "\n")
    
    def process_single_shot(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        Process a single shot.
        
        Args:
            args: Parsed arguments
            
        Returns:
            Pipeline execution summary
        """
        # Validate
        if not self.validate_shot_data(args):
            sys.exit(1)
        
        # Build shot data
        shot_data = {
            'source_file': args.source,
            'sequence': args.sequence,
            'shot': args.shot,
            'in_point': args.in_point,
            'out_point': args.out_point,
            'source_fps': args.fps,
        }
        
        if args.timecode:
            shot_data['source_timecode_start'] = args.timecode
        
        # Get project name
        project = args.project or self.config.get('project', 'default')
        project_id = args.project_id or self.config.get('project_id')
        
        # Print info
        self.print_shot_info(shot_data)
        
        # Dry run
        if args.dry_run:
            print("DRY RUN - No processing will occur")
            print(f"\nWould process shot: {args.sequence}{args.shot}")
            print(f"Project: {project}")
            if project_id:
                print(f"Kitsu Project ID: {project_id}")
            print(f"Stop on error: {not args.continue_on_error}")
            return {'dry_run': True}
        
        # Process
        self.logger.info(f"Processing shot: {args.sequence}{args.shot}")
        
        summary = ingest_shot(
            project=project,
            sequence=args.sequence,
            shot=args.shot,
            source_file=Path(args.source),
            in_point=args.in_point,
            out_point=args.out_point,
            source_fps=args.fps,
            project_id=project_id,
            logger=self.logger
        )
        
        return summary
    
    def process_batch(self, args: argparse.Namespace) -> List[Dict[str, Any]]:
        """
        Process multiple shots from batch file.
        
        Args:
            args: Parsed arguments
            
        Returns:
            List of pipeline execution summaries
        """
        # Load batch data
        batch_data = self.load_batch_file(args.batch)
        
        # Get project settings
        project = args.project or self.config.get('project', 'default')
        project_id = args.project_id or self.config.get('project_id')
        
        # Dry run
        if args.dry_run:
            print("DRY RUN - No processing will occur")
            print(f"\nWould process {len(batch_data)} shots:")
            for i, shot_data in enumerate(batch_data, 1):
                print(f"  {i}. {shot_data.get('sequence')}{shot_data.get('shot')}")
            return [{'dry_run': True}]
        
        # Create pipeline
        pipeline = FootageIngestPipeline(
            project=project,
            project_id=project_id,
            logger=self.logger
        )
        
        # Process batch
        self.logger.info(f"Processing {len(batch_data)} shots in batch mode")
        results = pipeline.ingest_batch(batch_data)
        
        return results
    
    def print_summary(self, summary: Dict[str, Any]):
        """
        Print execution summary.
        
        Args:
            summary: Pipeline execution summary
        """
        if summary.get('dry_run'):
            return
        
        print("\n" + "="*80)
        print("EXECUTION SUMMARY")
        print("="*80)
        
        success = summary.get('overall_success', False)
        status = "SUCCESS ✓" if success else "FAILED ✗"
        print(f"\nStatus: {status}")
        print(f"Duration: {summary.get('duration_seconds', 0):.2f} seconds")
        print(f"Stages: {summary.get('successful_stages', 0)}/{summary.get('total_stages', 0)} completed")
        
        # Stage details
        print("\nStage Results:")
        for result in summary.get('stage_results', []):
            status_icon = "✓" if result['success'] else "✗"
            print(f"  {status_icon} {result['stage_name']}: {result['message']}")
            
            # Errors
            if result.get('errors'):
                for error in result['errors']:
                    print(f"      ERROR: {error}")
            
            # Warnings
            if result.get('warnings'):
                for warning in result['warnings']:
                    print(f"      WARNING: {warning}")
        
        print("="*80 + "\n")
    
    def save_report(self, summary: Dict[str, Any], report_path: str):
        """
        Save execution report to file.
        
        Args:
            summary: Pipeline execution summary
            report_path: Path to save report
        """
        try:
            with open(report_path, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            self.logger.info(f"Report saved to: {report_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save report: {str(e)}")
    
    def run(self, argv=None):
        """
        Run the CLI.
        
        Args:
            argv: Command line arguments (for testing)
        """
        args = self.parser.parse_args(argv)
        
        # Update logging
        self.logger = self._setup_logging(
            verbose=args.verbose,
            quiet=args.quiet,
            log_file=args.log_file
        )
        
        # Load configuration
        self.config = self.load_config(args.config)
        
        # Determine mode
        if args.batch:
            # Batch mode
            results = self.process_batch(args)
            
            # Print summary for each shot
            for result in results:
                self.print_summary(result)
            
            # Save report if requested
            if args.report:
                self.save_report({'batch_results': results}, args.report)
        
        elif args.source:
            # Single shot mode
            summary = self.process_single_shot(args)
            
            # Print summary
            self.print_summary(summary)
            
            # Save report if requested
            if args.report:
                self.save_report(summary, args.report)
        
        else:
            # No mode specified
            self.parser.print_help()
            sys.exit(1)


def main():
    """Main entry point."""
    cli = IngestCLI()
    try:
        cli.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
