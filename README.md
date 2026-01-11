# DED-IO: Digital Editorial Data - Input/Output

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A flexible, modular Python pipeline for ingesting camera footage into a VFX production pipeline. Designed for Sony Venice 2 raw footage with support for ACES color workflow, anamorphic correction, and integration with Kitsu asset management.

**✨ Production-ready • 🎬 VFX-focused • 🔧 Highly configurable • 📦 Modular design**

## Features

- **Modular Architecture**: Each processing stage is independent and reusable
- **Sony Venice 2 Support**: Handles MXF raw footage from Venice 2 cameras
- **ACES Color Workflow**: Converts from S-Log3/S-Gamut3.Cine to ACEScg
- **Anamorphic Correction**: Desqueeze and letterbox anamorphic footage
- **Proxy Generation**: Creates sRGB proxy movies with optional burn-ins
- **Shot Tree Management**: Organizes footage into standardized directory structures
- **Kitsu Integration**: Automatically registers plates and metadata in Kitsu
- **Flexible Execution**: Can run complete pipelines or individual stages
- **Scripted WSL Install**: Scripted environment install on WSL/Debian

## Architecture

### Directory Structure

```
ded_io/
├── __init__.py              # Package initialization
├── config.py                # Configuration and constants
├── models.py                # Data models (ShotInfo, EditorialCutInfo, etc.)
├── pipeline.py              # Pipeline orchestration
├── footage_ingest.py        # High-level ingest interface
└── stages/                  # Processing stages
    ├── __init__.py
    ├── base.py              # Base stage class
    ├── sony_conversion.py   # Sony raw to DPX conversion
    ├── oiio_transform.py    # Color and geometric transforms
    ├── proxy_generation.py  # Proxy movie generation
    ├── kitsu_integration.py # Kitsu API integration
    └── file_operations.py   # File copying and organization
```

### Core Components

#### 1. Configuration (`config.py`)
- `PipelineConfig`: All pipeline settings (frame numbering, color spaces, formats)
- `KitsuConfig`: Kitsu API connection settings

#### 2. Data Models (`models.py`)
- `EditorialCutInfo`: Editorial cut list information
- `ShotInfo`: Complete shot information including paths and status
- `ProcessingResult`: Result from each pipeline stage
- `ImageSequence`: Represents an image sequence with frame range

#### 3. Pipeline Stages (`stages/`)
Each stage inherits from `PipelineStage` and implements specific functionality:
- `SonyRawConversionStage`: Converts MXF to DPX using Sony tools
- `OIIOColorTransformStage`: ACES color conversion and anamorphic correction
- `ProxyGenerationStage`: Creates H.264 proxy movies
- `BurnInProxyStage`: Creates proxies with metadata burn-in
- `KitsuIntegrationStage`: Registers assets in Kitsu
- `FileCopyStage`: Copies files with verification
- `ShotTreeOrganizationStage`: Organizes files into shot tree
- `CleanupStage`: Removes temporary files

#### 4. Pipeline Orchestration (`pipeline.py`)
- `Pipeline`: Executes stages in sequence with error handling
- `PipelineBuilder`: Fluent interface for building pipelines
- `ConditionalPipeline`: Pipeline with conditional stage execution

#### 5. Footage Ingest (`footage_ingest.py`)
High-level interface for common ingest operations:
- `FootageIngestPipeline`: Object-oriented interface
- `ingest_shot()`: Function to ingest a single shot
- `create_ingest_pipeline()`: Creates standard ingest pipeline

## Installation

### Requirements

- Python 3.8+
- Sony's command line conversion tool
- OIIO (OpenImageIO) with ACES 1.3 support
- FFmpeg
- Kitsu API credentials (optional)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/ded-io.git
cd ded-io

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"

# Verify installation
python setup_check.py
```

### Manual Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Ensure tools are in PATH or configure in config.py:
# - Sony raw converter
# - oiiotool
# - ffmpeg
```

## Usage

### Command-Line Interface (Recommended)

The easiest way to use the pipeline is through the command-line interface:

```bash
# Single shot
python ingest-cli.py \
  --source /path/to/clip.mxf \
  --sequence tst \
  --shot 100 \
  --in 100 \
  --out 200

# With configuration file
python ingest-cli.py \
  --config config.json \
  --source /path/to/clip.mxf \
  --sequence tst \
  --shot 100 \
  --in 100 \
  --out 200

# Batch processing
python ingest-cli.py --config config.json --batch shots.json
```

**See [CLI_DOCUMENTATION.md](CLI_DOCUMENTATION.md) for complete CLI guide.**

### Python API

### Example 1: Simple Single Shot Ingest

```python
from ded_io import ingest_shot
from pathlib import Path

# Ingest a single shot
summary = ingest_shot(
    project="my_project",
    sequence="tst",
    shot="100",
    source_file=Path("/path/to/raw/clip_001.mxf"),
    in_point=100,      # Frame 100 in raw footage
    out_point=150,     # Frame 150 in raw footage
    source_fps=24.0
)

print(f"Success: {summary['overall_success']}")
print(f"Duration: {summary['duration_seconds']:.2f}s")
```

### Example 2: Using the Pipeline Object

```python
from ded_io import FootageIngestPipeline
from pathlib import Path

# Create pipeline instance
pipeline = FootageIngestPipeline(
    project="my_project",
    project_id="kitsu_project_123"
)

# Process multiple shots
pipeline.ingest_shot(
    sequence="tst",
    shot="100",
    source_file=Path("/path/to/raw/clip_001.mxf"),
    in_point=100,
    out_point=150
)

pipeline.ingest_shot(
    sequence="tst",
    shot="110",
    source_file=Path("/path/to/raw/clip_002.mxf"),
    in_point=200,
    out_point=275
)

# Get summary
summary = pipeline.get_summary()
print(f"Processed {summary['total_shots_processed']} shots")
print(f"Success rate: {summary['successful_shots']}/{summary['total_shots_processed']}")
```

### Example 3: Batch Processing

```python
from ded_io import FootageIngestPipeline

pipeline = FootageIngestPipeline(project="my_project")

shots = [
    {
        'sequence': 'tst',
        'shot': '100',
        'source_file': '/path/to/raw/clip_001.mxf',
        'in_point': 100,
        'out_point': 150
    },
    {
        'sequence': 'tst',
        'shot': '110',
        'source_file': '/path/to/raw/clip_002.mxf',
        'in_point': 200,
        'out_point': 275
    }
]

results = pipeline.ingest_batch(shots)
```

### Example 4: Custom Pipeline

```python
from ded_io.pipeline import PipelineBuilder
from ded_io.stages import (
    SonyRawConversionStage,
    OIIOColorTransformStage,
    BurnInProxyStage,
    ShotTreeOrganizationStage
)

# Build custom pipeline (no Kitsu, with burn-in proxy)
builder = PipelineBuilder("CustomIngest")
builder.add_stage(SonyRawConversionStage())
builder.add_stage(OIIOColorTransformStage())
builder.add_stage(BurnInProxyStage())  # Proxy with frame numbers
builder.add_stage(ShotTreeOrganizationStage())

custom_pipeline = builder.build()

# Execute
summary = custom_pipeline.execute(shot_info)
```

### Example 5: Using Individual Stages

```python
from ded_io.stages import OIIOColorTransformStage
from ded_io.models import ShotInfo, EditorialCutInfo, ImageSequence
from pathlib import Path

# Create a single stage
color_stage = OIIOColorTransformStage()

# Set up shot info
editorial_info = EditorialCutInfo(
    sequence="tst",
    shot="100",
    source_file=Path("/path/to/raw/clip.mxf"),
    in_point=100,
    out_point=150
)

shot_info = ShotInfo(
    project="my_project",
    sequence="tst",
    shot="100",
    editorial_info=editorial_info
)

# Define input sequence (from previous stage)
input_sequence = ImageSequence(
    directory=Path("/tmp/dpx_output"),
    base_name="tst100",
    extension="dpx",
    first_frame=993,
    last_frame=1058
)

# Execute just this stage
result = color_stage.execute(
    shot_info=shot_info,
    input_sequence=input_sequence,
    output_dir=Path("/output/path")
)

print(f"Stage completed: {result.success}")
```

## Configuration

### Frame Numbering

```python
from ded_io.config import PipelineConfig

# Default configuration
PipelineConfig.DIGITAL_START_FRAME = 1001  # Shot starts at frame 1001
PipelineConfig.HEAD_HANDLE_FRAMES = 8      # 8 frames before cut in
PipelineConfig.TAIL_HANDLE_FRAMES = 8      # 8 frames after cut out
# First frame = 1001 - 8 = 993
```

### Color Settings

```python
PipelineConfig.SOURCE_COLORSPACE = "SLog3-SGamut3.Cine"
PipelineConfig.TARGET_COLORSPACE = "ACES - ACEScg"
PipelineConfig.ACES_VERSION = "1.3"
```

### Output Formats

```python
PipelineConfig.OUTPUT_FORMAT = "exr"
PipelineConfig.OUTPUT_COMPRESSION = "dwaa:15"
PipelineConfig.OUTPUT_BIT_DEPTH = "half"  # 16-bit float
```

### Anamorphic Settings

```python
PipelineConfig.ANAMORPHIC_SQUEEZE = 2.0
PipelineConfig.TARGET_WIDTH = 3840  # UHD
PipelineConfig.TARGET_HEIGHT = 2160
PipelineConfig.LETTERBOX = True
```

### Shot Tree Structure

```python
# Default structure:
# /mnt/projects/{project}/sequences/{sequence}/{shot}/
#   ├── plates/     # EXR sequences
#   └── proxy/      # MP4 proxy files
```

## Pipeline Flow

For the test shot `tst100`:

1. **Editorial Input**
   - Raw file: `/path/to/venice2/clip.mxf`
   - In point: Frame 100
   - Out point: Frame 150
   - Duration: 51 frames (including handles)

2. **Frame Mapping**
   - Editorial frame 100 → Digital frame 1001
   - With 8-frame handles: frames 993-1058
   - Total frames: 66 (51 + 8 + 8 - 1)

3. **Processing Stages**
   1. Convert MXF → DPX (temp directory)
   2. DPX → EXR with color conversion and scaling
   3. Generate MP4 proxy from EXR
   4. Copy to shot tree structure
   5. Register in Kitsu
   6. Clean up temp files

4. **Output Structure**
   ```
   /mnt/projects/test_project/sequences/tst/tst100/
   ├── plates/
   │   ├── tst100.0993.exr
   │   ├── tst100.0994.exr
   │   └── ...
   │   └── tst100.1058.exr
   └── proxy/
       └── tst100.mp4
   ```

## Extending the Pipeline

### Creating a New Stage

```python
from ded_io.stages.base import PipelineStage
from ded_io.models import ProcessingResult, ShotInfo

class MyCustomStage(PipelineStage):
    """Custom processing stage."""
    
    def process(self, shot_info: ShotInfo, result: ProcessingResult, **kwargs):
        """
        Implement stage-specific logic.
        
        Args:
            shot_info: Shot information
            result: Result object to populate
            **kwargs: Stage-specific arguments
        """
        # Validate inputs
        if not self.validate_inputs(shot_info, result):
            return
        
        try:
            # Do processing
            self.logger.info("Processing...")
            
            # Update result
            result.data['output'] = "some_value"
            
        except Exception as e:
            result.add_error(f"Processing failed: {str(e)}")
```

### Adding to a Pipeline

```python
from ingest_pipeline.pipeline import PipelineBuilder

builder = PipelineBuilder("CustomPipeline")
builder.add_stage(MyCustomStage())
builder.add_stage(OtherStage())
pipeline = builder.build()
```

## Error Handling

The pipeline provides comprehensive error handling:

```python
summary = pipeline.execute(shot_info, stop_on_error=True)

if not summary['overall_success']:
    print("Pipeline failed")
    
    for stage_result in summary['stage_results']:
        if not stage_result['success']:
            print(f"Stage {stage_result['stage_name']} failed:")
            for error in stage_result['errors']:
                print(f"  - {error}")
```

## Logging

All stages and pipelines include comprehensive logging:

```python
import logging

# Configure logging level
logging.basicConfig(level=logging.DEBUG)

# Or use custom logger
custom_logger = logging.getLogger("my_pipeline")
pipeline = FootageIngestPipeline(
    project="my_project",
    logger=custom_logger
)
```

## Testing

Run the examples script to see the pipeline in action:

```bash
python examples.py
```

## Future Enhancements

- EDL/XML parsing for batch ingests
- Support for additional camera formats
- GPU-accelerated processing
- Distributed processing across multiple machines
- Real-time status dashboard
- Automated QC checks
- Integration with additional asset management systems

## License

[Your License Here]

## Contact

[Your Contact Information]
