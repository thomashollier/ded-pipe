# Command Line Interface (CLI) Documentation

The `ingest-cli.py` script provides a complete command-line interface for running the footage ingest pipeline. It combines configuration file settings with command-line arguments for maximum flexibility.

## Installation

After installing the package:

```bash
# Make the CLI executable
chmod +x ingest-cli.py

# Optionally, link it to your PATH
sudo ln -s $(pwd)/ingest-cli.py /usr/local/bin/ingest-cli
```

## Quick Start

### Single Shot

```bash
# Basic usage
python ingest-cli.py \
  --source /path/to/clip.mxf \
  --sequence tst \
  --shot 100 \
  --in 100 \
  --out 200

# With configuration file
python ingest-cli.py \
  --config my_config.json \
  --source /path/to/clip.mxf \
  --sequence tst \
  --shot 100 \
  --in 100 \
  --out 200
```

### Batch Processing

```bash
# Process multiple shots from JSON file
python ingest-cli.py --batch shots.json

# With configuration
python ingest-cli.py --config my_config.json --batch shots.json
```

## Configuration Files

### Project Configuration (`config.json`)

Store show-wide constants in a configuration file:

```json
{
  "project": "my_feature_film",
  "project_id": "kitsu_project_abc123",
  "defaults": {
    "source_fps": 24.0,
    "stop_on_error": true
  },
  "paths": {
    "shot_tree_root": "/mnt/projects",
    "temp_dir": "/mnt/temp"
  },
  "tools": {
    "sony_converter": "/usr/local/bin/sony_raw_converter",
    "oiiotool": "/usr/bin/oiiotool",
    "ffmpeg": "/usr/bin/ffmpeg"
  },
  "output": {
    "exr_compression": "dwaa:15",
    "proxy_resolution": "1920x1080",
    "proxy_crf": 18
  },
  "pipeline": {
    "skip_kitsu": false,
    "skip_cleanup": false,
    "burn_in_proxy": false
  }
}
```

**See:** [config.example.json](computer:///home/claude/config.example.json) for complete example

### Batch File (`shots.json`)

Process multiple shots with a single command:

```json
[
  {
    "sequence": "seq010",
    "shot": "010",
    "source_file": "/path/to/clip_001.mxf",
    "in_point": 100,
    "out_point": 250,
    "source_fps": 24.0,
    "notes": "Opening shot"
  },
  {
    "sequence": "seq010",
    "shot": "020",
    "source_file": "/path/to/clip_002.mxf",
    "in_point": 300,
    "out_point": 450,
    "source_fps": 24.0,
    "notes": "Medium shot"
  }
]
```

**See:** [batch.example.json](computer:///home/claude/batch.example.json) for complete example

## Command-Line Arguments

### Required Arguments (Single Shot Mode)

```bash
--source, -s PATH       # Path to source raw footage file
--sequence NAME         # Sequence name (e.g., "tst")
--shot NAME            # Shot number/name (e.g., "100")
--in, -i FRAME         # Editorial in point (frame number)
--out, -o FRAME        # Editorial out point (frame number)
```

### Configuration

```bash
--config, -c PATH      # Path to JSON configuration file
```

### Batch Processing

```bash
--batch, -b PATH       # Path to JSON file with batch shot data
```

### Optional Shot Data

```bash
--fps FLOAT            # Source frame rate (default: 24.0)
--timecode TC          # Source timecode start (optional)
```

### Project Settings

```bash
--project, -p NAME     # Project name
--project-id ID        # Kitsu project ID
```

### Output Options

```bash
--output-dir PATH      # Override output directory
--report PATH          # Save execution report to file
```

### Pipeline Options

```bash
--skip-kitsu           # Skip Kitsu integration stage
--skip-cleanup         # Skip cleanup stage (preserve temp files)
--burn-in              # Use burn-in proxy instead of regular proxy
```

### Execution Options

```bash
--dry-run              # Print what would be done without executing
--stop-on-error        # Stop pipeline on first error (default)
--continue-on-error    # Continue pipeline even if stages fail
```

### Logging

```bash
-v, --verbose          # Verbose output (DEBUG level)
-q, --quiet            # Quiet output (ERROR level only)
--log-file PATH        # Write log to file
```

## Usage Examples

### Example 1: Basic Single Shot

```bash
python ingest-cli.py \
  --source /mnt/raw/2024-01-15/clip_001.mxf \
  --sequence seq010 \
  --shot 010 \
  --in 100 \
  --out 250
```

### Example 2: With Configuration File

```bash
# config.json contains project name, Kitsu ID, tool paths, etc.
python ingest-cli.py \
  --config config.json \
  --source /mnt/raw/clip_001.mxf \
  --sequence seq010 \
  --shot 010 \
  --in 100 \
  --out 250
```

### Example 3: Batch Processing

```bash
# Process all shots defined in batch.json
python ingest-cli.py --config config.json --batch shots.json
```

### Example 4: Verbose with Report

```bash
python ingest-cli.py \
  --config config.json \
  --source /mnt/raw/clip_001.mxf \
  --sequence seq010 \
  --shot 010 \
  --in 100 \
  --out 250 \
  --verbose \
  --report shot_010_report.json
```

### Example 5: Dry Run (Preview)

```bash
# See what would be done without processing
python ingest-cli.py \
  --config config.json \
  --source /mnt/raw/clip_001.mxf \
  --sequence seq010 \
  --shot 010 \
  --in 100 \
  --out 250 \
  --dry-run
```

### Example 6: Skip Kitsu Integration

```bash
python ingest-cli.py \
  --config config.json \
  --source /mnt/raw/clip_001.mxf \
  --sequence seq010 \
  --shot 010 \
  --in 100 \
  --out 250 \
  --skip-kitsu
```

### Example 7: Burn-in Proxy with Debug Logging

```bash
python ingest-cli.py \
  --config config.json \
  --source /mnt/raw/clip_001.mxf \
  --sequence seq010 \
  --shot 010 \
  --in 100 \
  --out 250 \
  --burn-in \
  --verbose \
  --log-file debug.log
```

### Example 8: Keep Temp Files for Debugging

```bash
python ingest-cli.py \
  --config config.json \
  --source /mnt/raw/clip_001.mxf \
  --sequence seq010 \
  --shot 010 \
  --in 100 \
  --out 250 \
  --skip-cleanup \
  --verbose
```

## Output

### Console Output

The CLI provides formatted output showing progress:

```
================================================================================
                            SHOT INFORMATION                                
================================================================================
Sequence:      seq010
Shot:          010
Source:        /mnt/raw/clip_001.mxf
In Point:      100
Out Point:     250
Duration:      151 frames
FPS:           24.0

Digital Frames:
  First Frame: 993
  Last Frame:  1158
  Total:       166 frames
================================================================================

2024-12-02 10:30:00 - ingest_cli - INFO - Processing shot: seq010010
2024-12-02 10:30:01 - ingest_cli - INFO - Starting stage: SonyRawConversion
...

================================================================================
                           EXECUTION SUMMARY                                
================================================================================

Status: SUCCESS ✓
Duration: 125.43 seconds
Stages: 6/6 completed

Stage Results:
  ✓ SonyRawConversionStage: Stage completed successfully
  ✓ OIIOColorTransformStage: Stage completed successfully
  ✓ ProxyGenerationStage: Stage completed successfully
  ✓ ShotTreeOrganizationStage: Stage completed successfully
  ✓ KitsuIntegrationStage: Stage completed successfully
  ✓ CleanupStage: Stage completed successfully
================================================================================
```

### Report File

When using `--report`, a JSON file is created:

```json
{
  "pipeline_name": "FootageIngest",
  "shot_info": {
    "shot_name": "seq010010",
    "frame_range": "993-1158",
    "total_frames": 166,
    "output_plates_path": "/mnt/projects/my_film/sequences/seq010/seq010010/plates",
    "output_proxy_path": "/mnt/projects/my_film/sequences/seq010/seq010010/proxy/seq010010.mp4"
  },
  "duration_seconds": 125.43,
  "total_stages": 6,
  "successful_stages": 6,
  "failed_stages": 0,
  "overall_success": true,
  "stage_results": [
    {
      "stage_name": "SonyRawConversionStage",
      "success": true,
      "message": "Stage completed successfully",
      "duration_seconds": 45.2
    }
  ]
}
```

## Integration with Other Tools

### Shell Scripts

```bash
#!/bin/bash
# process_dailies.sh

CONFIG="production_config.json"
RAW_DIR="/mnt/raw_footage/$(date +%Y-%m-%d)"

for clip in "$RAW_DIR"/*.mxf; do
    echo "Processing: $clip"
    
    python ingest-cli.py \
        --config "$CONFIG" \
        --source "$clip" \
        --sequence "dailies" \
        --shot "$(basename $clip .mxf)" \
        --in 0 \
        --out 100 \
        --report "reports/$(basename $clip .mxf).json"
done
```

### Makefile

```makefile
# Makefile

CONFIG = config.json

shot-%:
	python ingest-cli.py \
		--config $(CONFIG) \
		--source $(SOURCE) \
		--sequence $(SEQ) \
		--shot $* \
		--in $(IN) \
		--out $(OUT)

batch:
	python ingest-cli.py --config $(CONFIG) --batch $(BATCH_FILE)

dry-run:
	python ingest-cli.py \
		--config $(CONFIG) \
		--source $(SOURCE) \
		--sequence $(SEQ) \
		--shot $(SHOT) \
		--in $(IN) \
		--out $(OUT) \
		--dry-run
```

Usage:
```bash
make shot-010 SOURCE=clip.mxf SEQ=seq010 IN=100 OUT=200
make batch BATCH_FILE=shots.json
```

### Python Scripts

```python
#!/usr/bin/env python3
import subprocess
import json

# Load shot data from database or other source
shots = get_shots_from_database()

for shot in shots:
    cmd = [
        'python', 'ingest-cli.py',
        '--config', 'config.json',
        '--source', shot['source_file'],
        '--sequence', shot['sequence'],
        '--shot', shot['shot'],
        '--in', str(shot['in_point']),
        '--out', str(shot['out_point']),
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    
    if result.returncode != 0:
        print(f"Failed: {shot['shot']}")
    else:
        print(f"Success: {shot['shot']}")
```

## Configuration Precedence

Settings are applied in this order (later overrides earlier):

1. **Package defaults** (from `PipelineConfig`)
2. **Configuration file** (`--config`)
3. **Command-line arguments**

Example:
```bash
# config.json has: "project": "film_A"
# Command line overrides it:
python ingest-cli.py --config config.json --project film_B ...
# Result: Uses "film_B"
```

## Error Handling

### Exit Codes

- `0` - Success
- `1` - General error
- `130` - Interrupted by user (Ctrl+C)

### Common Errors

**Missing required arguments:**
```
Error: Missing required arguments: source, in_point
```

**Source file not found:**
```
Error: Source file not found: /path/to/clip.mxf
```

**Invalid frame range:**
```
Error: In point (200) must be less than out point (100)
```

**Invalid config file:**
```
Error: Invalid JSON in config file: Expecting ',' delimiter: line 5 column 3
```

## Best Practices

### 1. Use Configuration Files

Store show constants in config files:
```bash
# Good
python ingest-cli.py --config my_show.json --source clip.mxf ...

# Instead of repeating arguments every time
python ingest-cli.py --project my_show --project-id abc123 --source clip.mxf ...
```

### 2. Use Batch Processing

For multiple shots, use batch files:
```bash
# Good
python ingest-cli.py --batch shots.json

# Instead of multiple commands
python ingest-cli.py --source clip1.mxf ...
python ingest-cli.py --source clip2.mxf ...
python ingest-cli.py --source clip3.mxf ...
```

### 3. Dry Run First

Preview before processing:
```bash
python ingest-cli.py --config config.json --source clip.mxf --dry-run
```

### 4. Save Reports

Keep records of processing:
```bash
python ingest-cli.py ... --report shot_010_$(date +%Y%m%d_%H%M%S).json
```

### 5. Use Verbose for Debugging

When troubleshooting:
```bash
python ingest-cli.py ... --verbose --log-file debug.log
```

### 6. Preserve Temp Files When Debugging

If a stage fails:
```bash
python ingest-cli.py ... --skip-cleanup --verbose
```

## Tips & Tricks

### Process Today's Dailies

```bash
#!/bin/bash
TODAY=$(date +%Y-%m-%d)
RAW_DIR="/mnt/raw_footage/$TODAY"

python ingest-cli.py \
    --config config.json \
    --batch <(ls "$RAW_DIR"/*.mxf | jq -R -s 'split("\n")[:-1] | map({
        sequence: "dailies",
        shot: (split("/")[-1] | split(".")[0]),
        source_file: .,
        in_point: 0,
        out_point: 100,
        source_fps: 24.0
    })')
```

### Watch Directory for New Files

```bash
#!/bin/bash
inotifywait -m -e create /mnt/raw_footage --format '%w%f' |
while read file; do
    if [[ "$file" == *.mxf ]]; then
        python ingest-cli.py --config config.json --source "$file" ...
    fi
done
```

### Parallel Processing

```bash
# Process multiple shots in parallel (use with caution!)
cat shots.txt | parallel -j 4 "python ingest-cli.py --config config.json {}"
```

## Troubleshooting

### CLI Not Found

```bash
# Make executable
chmod +x ingest-cli.py

# Or use python explicitly
python ingest-cli.py ...
```

### Import Errors

```bash
# Install package first
pip install -e .

# Or set PYTHONPATH
export PYTHONPATH=/path/to/footage-ingest-pipeline:$PYTHONPATH
```

### Configuration Not Loading

```bash
# Check JSON syntax
python -m json.tool config.json

# Use absolute paths
python ingest-cli.py --config /full/path/to/config.json ...
```

## See Also

- [examples.py](computer:///home/claude/examples.py) - Python API examples
- [process_tst100.py](computer:///home/claude/process_tst100.py) - Simple test script
- [config.example.json](computer:///home/claude/config.example.json) - Example config
- [batch.example.json](computer:///home/claude/batch.example.json) - Example batch file
- [README.md](computer:///home/claude/README.md) - Main documentation
