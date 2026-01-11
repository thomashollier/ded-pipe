# DED-IO: Digital Editorial Data - Input/Output

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A production-ready Python pipeline for ingesting Sony Venice 2 raw camera footage into a VFX production workflow. Handles the complete journey from MXF raw files to organized, color-corrected EXR sequences with proxies, ready for compositing.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Pipeline Architecture](#pipeline-architecture)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Technical Details](#technical-details)
- [Extending the Pipeline](#extending-the-pipeline)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)

---

## Overview

DED-IO automates the complex process of ingesting camera-original footage into a VFX pipeline. Given a raw MXF clip from a Sony Venice 2 camera and editorial cut information, it:

1. Extracts the required frame range from the camera original
2. Converts from camera raw to DPX
3. Applies ACES color transformation (S-Log3/S-Gamut3.Cine to ACEScg)
4. Corrects for 2x anamorphic squeeze and scales to UHD
5. Generates H.264 proxy movies for review
6. Organizes files into a standardized shot tree structure
7. Registers assets in Kitsu (optional)

The pipeline is modular - each stage can be used independently, combined into custom pipelines, or run as a complete end-to-end workflow.

---

## Features

### Core Capabilities

- **Sony Venice 2 Support**: Native handling of MXF raw footage from Venice 2 cameras
- **ACES Color Workflow**: Converts from S-Log3/S-Gamut3.Cine to ACEScg using ACES 1.3
- **Anamorphic Correction**: 2.0x desqueeze with UHD letterboxing
- **Proxy Generation**: H.264 MP4 proxies with optional burn-in overlays
- **Shot Tree Organization**: Standardized VFX directory structure and naming
- **Kitsu Integration**: Automatic asset registration, proxy upload, and output file tracking
- **WSL/Windows Support**: Seamless integration between WSL and Windows tools

### Pipeline Features

- **Modular Design**: Each processing stage is independent and reusable
- **Multiple Interfaces**: Command-line (CLI) and Python API
- **Batch Processing**: Process multiple shots from JSON manifests
- **Dry Run Mode**: Preview operations without executing
- **Comprehensive Logging**: Detailed logging at every stage
- **Error Recovery**: Graceful failure handling with detailed error reporting
- **Parallel Processing**: Multi-threaded frame processing where applicable

---

## Pipeline Architecture

### Processing Flow

```
                    ┌──────────────────────────────────────────────────────────────┐
                    │                    EDITORIAL INPUT                           │
                    │  MXF Raw File + In/Out Points + Shot/Sequence Info           │
                    └───────────────────────────┬──────────────────────────────────┘
                                                │
                    ┌───────────────────────────▼──────────────────────────────────┐
                    │              STAGE 1: Sony Raw Conversion                    │
                    │  MXF → DPX (via Sony rawexporter.exe)                        │
                    │  Extracts frame range with handles                           │
                    └───────────────────────────┬──────────────────────────────────┘
                                                │
                    ┌───────────────────────────▼──────────────────────────────────┐
                    │              STAGE 2: OIIO Color Transform                   │
                    │  DPX → EXR (via oiiotool)                                    │
                    │  • S-Log3/S-Gamut3.Cine → ACEScg color conversion            │
                    │  • 2.0x anamorphic desqueeze                                 │
                    │  • UHD (3840x2160) letterbox/scale                           │
                    │  • DWAA compression, 16-bit float                            │
                    └───────────────────────────┬──────────────────────────────────┘
                                                │
                    ┌───────────────────────────▼──────────────────────────────────┐
                    │              STAGE 3: Proxy Generation                       │
                    │  EXR → MP4 (via ffmpeg)                                      │
                    │  • H.264 encoding, 1920x1080                                 │
                    │  • ACEScg → sRGB conversion                                  │
                    │  • Optional frame number burn-in                             │
                    └───────────────────────────┬──────────────────────────────────┘
                                                │
                    ┌───────────────────────────▼──────────────────────────────────┐
                    │              STAGE 4: Shot Tree Organization                 │
                    │  Copy files to standardized directory structure              │
                    │  {shot}/{task}/{version_container}/{colorspace}/             │
                    └───────────────────────────┬──────────────────────────────────┘
                                                │
                    ┌───────────────────────────▼──────────────────────────────────┐
                    │              STAGE 5: Kitsu Integration (Optional)           │
                    │  • Create/update shot in Kitsu                               │
                    │  • Upload proxy for review                                   │
                    │  • Register output file records                              │
                    └───────────────────────────┬──────────────────────────────────┘
                                                │
                    ┌───────────────────────────▼──────────────────────────────────┐
                    │              STAGE 6: Cleanup                                │
                    │  Remove temporary files from /tmp                            │
                    └──────────────────────────────────────────────────────────────┘
```

### Frame Numbering

The pipeline uses a standardized frame numbering scheme:

| Concept | Value | Description |
|---------|-------|-------------|
| Digital Start Frame | 1001 | All shots start at frame 1001 |
| Head Handle | 8 frames | Frames before editorial in point |
| Tail Handle | 8 frames | Frames after editorial out point |
| Sequence Start | 993 | First frame = 1001 - 8 |

**Example**: For editorial in=100, out=150 (51 frames):
- Total frames with handles: 51 + 8 + 8 = 67 frames
- Frame range: 993-1059
- Frame 1001 corresponds to editorial frame 100

### Directory Structure

```
{shot_tree_root}/
└── sht100/                                         # Shot root
    └── pla/                                        # Task (plates)
        └── sht100_pla_rawPlate_v001/              # Version container
            ├── main_ACEScg/                        # Colorspace directory
            │   ├── sht100_pla_rawPlate_v001_main_ACEScg.0993.exr
            │   ├── sht100_pla_rawPlate_v001_main_ACEScg.0994.exr
            │   └── ...
            └── sht100_pla_rawPlate_v001_proxy_sRGB.mp4
```

### Naming Convention

Files follow standard VFX naming:
```
{shot}_{task}_{element}_v{version}_{rep}_{colorspace}.{frame}.{ext}
```

| Component | Example | Description |
|-----------|---------|-------------|
| shot | sht100 | Sequence + shot number |
| task | pla | Task type (pla=plates, rnd=render, cmp=comp) |
| element | rawPlate | Element name (rawPlate, cleanPlate, finalComp) |
| version | v001 | Version with 3-digit padding |
| rep | main | Representation (main, proxy) |
| colorspace | ACEScg | Color space identifier |
| frame | 0993 | Frame number with 4-digit padding |
| ext | exr | File extension |

---

## Requirements

### Python

- **Python 3.8+** (tested on 3.8, 3.9, 3.10, 3.11, 3.12)

### External Tools

| Tool | Purpose | Platform | Notes |
|------|---------|----------|-------|
| **Sony RAW Viewer / rawexporter.exe** | MXF to DPX conversion | Windows only | [Download from Sony](https://www.sony.com/electronics/support/downloads) |
| **OpenImageIO (oiiotool)** | Color transforms, format conversion | Linux/macOS/Windows | Requires ACES 1.3 OCIO config |
| **FFmpeg** | Proxy generation | Linux/macOS/Windows | H.264 encoding support required |

### ACES Configuration

The pipeline requires ACES 1.3 OpenColorIO configuration:
- **Studio Config** (recommended): Includes camera input transforms for Sony Venice
- **CG Config**: Lighter config without camera transforms

Download from: [OpenColorIO-Config-ACES releases](https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES/releases)

### Python Dependencies

```
requests>=2.28.0    # Kitsu API integration
```

Optional development dependencies:
```
pytest>=7.0.0       # Testing
black>=22.0.0       # Code formatting
mypy>=0.990         # Type checking
flake8>=5.0.0       # Linting
```

---

## Installation

### Option 1: Standard Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ded-io.git
cd ded-io

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .

# Verify installation
python setup_check.py
```

### Option 2: Manual Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Ensure external tools are available
which oiiotool    # Should return path
which ffmpeg      # Should return path
```

### Option 3: WSL/Debian Automated Setup

For Windows users running WSL, an automated setup script is provided:

```bash
# Navigate to setup directory
cd WSL_setup

# Run the setup script
chmod +x debian-wsl-setup.sh
./debian-wsl-setup.sh

# Reload shell
source ~/.bashrc
```

This script installs:
- Homebrew for Linux
- pyenv with Python 3.12
- OpenColorIO and OpenImageIO
- FFmpeg
- ACES 1.3 configuration (at `C:\ACES\aces_1.3\`)
- MediaInfo

**Sony RAW Viewer** must be installed separately on Windows:
1. Download from [Sony Support](https://www.sony.com/electronics/support/downloads)
2. Install on Windows
3. The pipeline automatically handles WSL ↔ Windows path conversion

### Verifying Installation

```bash
# Run the setup checker
python setup_check.py

# Expected output:
# [OK] Python version 3.x.x
# [OK] oiiotool found
# [OK] ffmpeg found
# [OK] All imports successful
```

---

## Configuration

### Configuration Hierarchy

Configuration is applied in this order (later overrides earlier):

1. **Package defaults** (`ded_io/config.py`)
2. **JSON config file** (`--config config.json`)
3. **CLI arguments** (`--source`, `--sequence`, etc.)

### JSON Configuration File

Create a `config.json` based on `config.example.json`:

```json
{
  "project": "my_feature_film",
  "project_id": "kitsu_project_abc123",

  "defaults": {
    "source_fps": 24.0,
    "stop_on_error": true
  },

  "paths": {
    "shot_tree_root": "/mnt/projects/my_film/shots",
    "temp_dir": "/tmp/ded_io"
  },

  "tools": {
    "sony_converter": "C:\\Program Files\\Sony\\RAW Viewer\\rawexporter.exe",
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

### Core Configuration Options

#### Frame Numbering

```python
# In ded_io/config.py
DIGITAL_START_FRAME = 1001     # Shots start at frame 1001
HEAD_HANDLE_FRAMES = 8         # 8 frames before cut
TAIL_HANDLE_FRAMES = 8         # 8 frames after cut
```

#### Color Pipeline

```python
SOURCE_COLORSPACE = "Input - Sony - S-Log3 - Venice S-Gamut3.Cine"
TARGET_COLORSPACE = "ACEScg"
ACES_VERSION = "1.3"
```

#### Output Format

```python
OUTPUT_FORMAT = "exr"
OUTPUT_COMPRESSION = "dwaa:15"   # DWAA with quality 15
OUTPUT_BIT_DEPTH = "half"        # 16-bit float
```

#### Anamorphic Settings

```python
ANAMORPHIC_SQUEEZE = 2.0         # 2x anamorphic
TARGET_WIDTH = 3840              # UHD width
TARGET_HEIGHT = 2160             # UHD height
LETTERBOX = True                 # Center and letterbox
```

#### Proxy Settings

```python
PROXY_FORMAT = "mp4"
PROXY_CODEC = "libx264"
PROXY_COLORSPACE = "sRGB"
PROXY_CRF = 18                   # Quality (lower = better)
```

### Kitsu Configuration

Set via environment variables or edit `ded_io/config.py`:

```bash
export KITSU_HOST="https://your-instance.cg-wire.com/api"
export KITSU_EMAIL="your-email@example.com"
export KITSU_PASSWORD="your-password"
export KITSU_PROJECT="ProjectName"
```

### OCIO Configuration

Set the OCIO environment variable:

```bash
# Linux/WSL
export OCIO="/mnt/c/ACES/aces_1.3/config.ocio"

# macOS
export OCIO="/path/to/aces_1.3/config.ocio"

# Windows
set OCIO=C:\ACES\aces_1.3\config.ocio
```

---

## Usage

### Command-Line Interface

#### Basic Single Shot

```bash
python ingest-cli.py \
  --source /path/to/clip.mxf \
  --sequence sht \
  --shot 100 \
  --in 100 \
  --out 200
```

#### With Configuration File

```bash
python ingest-cli.py \
  --config config.json \
  --source /path/to/clip.mxf \
  --sequence sht \
  --shot 100 \
  --in 100 \
  --out 200
```

#### Batch Processing

Create a `shots.json` file:

```json
[
  {
    "sequence": "sht",
    "shot": "100",
    "source_file": "/path/to/clip_001.mxf",
    "in_point": 100,
    "out_point": 200,
    "notes": "Opening shot"
  },
  {
    "sequence": "sht",
    "shot": "110",
    "source_file": "/path/to/clip_002.mxf",
    "in_point": 50,
    "out_point": 175
  }
]
```

Run batch:

```bash
python ingest-cli.py --config config.json --batch shots.json
```

#### Dry Run (Preview)

```bash
python ingest-cli.py \
  --config config.json \
  --source /path/to/clip.mxf \
  --sequence sht \
  --shot 100 \
  --in 100 \
  --out 200 \
  --dry-run
```

#### Common CLI Options

| Option | Description |
|--------|-------------|
| `--source PATH` | Source MXF file path |
| `--sequence NAME` | Sequence name (e.g., "sht") |
| `--shot NUM` | Shot number (e.g., "100") |
| `--in FRAME` | Editorial in point |
| `--out FRAME` | Editorial out point |
| `--config FILE` | JSON configuration file |
| `--batch FILE` | Batch shots JSON file |
| `--dry-run` | Preview without executing |
| `--skip-kitsu` | Skip Kitsu integration |
| `--skip-cleanup` | Keep temporary files |
| `--burn-in` | Add frame numbers to proxy |
| `--verbose` | Verbose logging |

See [CLI_DOCUMENTATION.md](CLI_DOCUMENTATION.md) for complete reference.

### Python API

#### Simple Single Shot

```python
from ded_io import ingest_shot
from pathlib import Path

summary = ingest_shot(
    project="my_project",
    sequence="sht",
    shot="100",
    source_file=Path("/path/to/clip.mxf"),
    in_point=100,
    out_point=150
)

print(f"Success: {summary['overall_success']}")
print(f"Duration: {summary['duration_seconds']:.2f}s")
```

#### Using Pipeline Object

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
    sequence="sht",
    shot="100",
    source_file=Path("/path/to/clip_001.mxf"),
    in_point=100,
    out_point=150
)

pipeline.ingest_shot(
    sequence="sht",
    shot="110",
    source_file=Path("/path/to/clip_002.mxf"),
    in_point=200,
    out_point=275
)

# Get summary
summary = pipeline.get_summary()
print(f"Processed: {summary['total_shots_processed']}")
print(f"Successful: {summary['successful_shots']}")
```

#### Batch Processing

```python
from ded_io import FootageIngestPipeline

pipeline = FootageIngestPipeline(project="my_project")

shots = [
    {
        'sequence': 'sht',
        'shot': '100',
        'source_file': '/path/to/clip_001.mxf',
        'in_point': 100,
        'out_point': 150
    },
    {
        'sequence': 'sht',
        'shot': '110',
        'source_file': '/path/to/clip_002.mxf',
        'in_point': 200,
        'out_point': 275
    }
]

results = pipeline.ingest_batch(shots)
```

#### Custom Pipeline

```python
from ded_io.pipeline import PipelineBuilder
from ded_io.stages import (
    SonyRawConversionStage,
    OIIOColorTransformStage,
    BurnInProxyStage,
    ShotTreeOrganizationStage,
    CleanupStage
)

# Build custom pipeline (no Kitsu, with burn-in proxy)
builder = PipelineBuilder("CustomIngest")
builder.add_stage(SonyRawConversionStage())
builder.add_stage(OIIOColorTransformStage())
builder.add_stage(BurnInProxyStage())  # Proxy with frame numbers
builder.add_stage(ShotTreeOrganizationStage())
builder.add_stage(CleanupStage())

pipeline = builder.build()
summary = pipeline.execute(shot_info)
```

#### Using Individual Stages

```python
from ded_io.stages import OIIOColorTransformStage
from ded_io.models import ShotInfo, EditorialCutInfo, ImageSequence
from pathlib import Path

# Create stage
color_stage = OIIOColorTransformStage()

# Set up shot info
editorial_info = EditorialCutInfo(
    sequence="sht",
    shot="100",
    source_file=Path("/path/to/clip.mxf"),
    in_point=100,
    out_point=150
)

shot_info = ShotInfo(
    project="my_project",
    sequence="sht",
    shot="100",
    editorial_info=editorial_info
)

# Input from previous stage
input_sequence = ImageSequence(
    directory=Path("/tmp/dpx_output"),
    base_name="sht100",
    extension="dpx",
    first_frame=993,
    last_frame=1058
)

# Execute single stage
result = color_stage.execute(
    shot_info=shot_info,
    input_sequence=input_sequence,
    output_dir=Path("/output/path")
)

print(f"Success: {result.success}")
```

---

## Technical Details

### Stage Details

#### SonyRawConversionStage

Converts Sony Venice 2 MXF files to DPX sequences.

- **Input**: MXF raw file path
- **Output**: DPX image sequence in temp directory
- **Tool**: Sony RAW Viewer rawexporter.exe
- **Notes**:
  - Windows-only tool, automatically handles WSL path conversion
  - Extracts exact frame range with handles
  - Preserves full camera sensor data

#### OIIOColorTransformStage

Applies color transformation and geometric corrections.

- **Input**: DPX sequence
- **Output**: EXR sequence in ACEScg
- **Tool**: OpenImageIO oiiotool
- **Operations**:
  - Color: S-Log3/S-Gamut3.Cine → ACEScg
  - Desqueeze: 2.0x anamorphic correction
  - Scale: Fit to UHD (3840x2160) with letterbox
  - Format: 16-bit float EXR with DWAA compression
- **Performance**: Parallel processing (4 jobs default)

#### ProxyGenerationStage / BurnInProxyStage

Generates H.264 proxy movies for review.

- **Input**: EXR sequence
- **Output**: MP4 file
- **Tool**: FFmpeg
- **Settings**:
  - Resolution: 1920x1080
  - Codec: libx264
  - Quality: CRF 18
  - Color: ACEScg → sRGB
- **BurnInProxyStage**: Adds frame number overlay

#### ShotTreeOrganizationStage

Organizes files into standardized directory structure.

- **Input**: EXR sequence + proxy file
- **Output**: Files in shot tree
- **Operations**:
  - Creates directory structure
  - Copies files with verification
  - Maintains naming convention

#### KitsuIntegrationStage

Registers assets in Kitsu production tracking.

- **Operations**:
  - Create/find shot entity
  - Create plate task
  - Upload proxy for review
  - Create output file records
- **API**: Uses Kitsu REST API

#### CleanupStage

Removes temporary processing files.

- **Removes**: `/tmp/*_sony_conversion`, `/tmp/*_oiio_*`, `/tmp/*_proxy_*`

### Data Models

| Model | Purpose |
|-------|---------|
| `EditorialCutInfo` | Editorial cut information (source, in/out points, timecode) |
| `ShotInfo` | Complete shot metadata and paths |
| `ProcessingResult` | Stage execution result with errors/warnings |
| `ImageSequence` | Represents image sequence with frame range |

### Error Handling

```python
summary = pipeline.execute(shot_info, stop_on_error=True)

if not summary['overall_success']:
    for stage_result in summary['stage_results']:
        if not stage_result['success']:
            print(f"Stage {stage_result['stage_name']} failed:")
            for error in stage_result['errors']:
                print(f"  - {error}")
```

### Logging

```python
import logging

# Set log level
logging.basicConfig(level=logging.DEBUG)

# Or use custom logger
custom_logger = logging.getLogger("my_pipeline")
pipeline = FootageIngestPipeline(
    project="my_project",
    logger=custom_logger
)
```

---

## Extending the Pipeline

### Creating a Custom Stage

```python
from ded_io.stages.base import PipelineStage
from ded_io.models import ProcessingResult, ShotInfo

class MyCustomStage(PipelineStage):
    """Custom processing stage."""

    def __init__(self, custom_param: str = "default"):
        super().__init__("MyCustomStage")
        self.custom_param = custom_param

    def process(self, shot_info: ShotInfo, result: ProcessingResult, **kwargs):
        """Implement stage-specific logic."""

        # Validate inputs
        if not self.validate_inputs(shot_info, result):
            return

        try:
            self.logger.info(f"Processing with param: {self.custom_param}")

            # Your processing logic here
            output_path = self.do_work(shot_info)

            # Update result
            result.data['output_path'] = str(output_path)
            result.success = True

        except Exception as e:
            result.add_error(f"Processing failed: {str(e)}")
            result.success = False
```

### Adding to a Pipeline

```python
from ded_io.pipeline import PipelineBuilder

builder = PipelineBuilder("ExtendedPipeline")
builder.add_stage(SonyRawConversionStage())
builder.add_stage(OIIOColorTransformStage())
builder.add_stage(MyCustomStage(custom_param="value"))
builder.add_stage(ProxyGenerationStage())
builder.add_stage(CleanupStage())

pipeline = builder.build()
```

---

## Troubleshooting

### Common Issues

#### "oiiotool not found"

```bash
# Check if oiiotool is in PATH
which oiiotool

# If using Homebrew on Linux/WSL
brew install openimageio

# Add to PATH if needed
export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
```

#### "OCIO config not found"

```bash
# Set OCIO environment variable
export OCIO="/mnt/c/ACES/aces_1.3/config.ocio"

# Verify config exists
ls -la "$OCIO"

# Test with oiiotool
oiiotool --colorconfig
```

#### "Sony converter failed"

- Ensure Sony RAW Viewer is installed on Windows
- Check the path in config matches your installation
- For WSL: paths are auto-converted (e.g., `/mnt/c/...` → `C:\...`)

#### "Kitsu connection failed"

```bash
# Verify credentials
export KITSU_HOST="https://your-instance.cg-wire.com/api"
export KITSU_EMAIL="email@example.com"
export KITSU_PASSWORD="password"

# Test connection
python -c "from ded_io.stages import KitsuIntegrationStage; print('OK')"
```

#### WSL Path Issues

The pipeline automatically converts between WSL and Windows paths:
- WSL: `/mnt/c/path/to/file` ↔ Windows: `C:\path\to\file`

If issues persist, check:
```bash
# Verify WSL can access Windows drives
ls /mnt/c/

# Check Windows tool is accessible
/mnt/c/Program\ Files/Sony/RAW\ Viewer/rawexporter.exe --help
```

### Debug Mode

```bash
# Run with verbose output
python ingest-cli.py --verbose ...

# Keep temp files for inspection
python ingest-cli.py --skip-cleanup ...
```

---

## Project Structure

```
ded-io/
├── README.md                  # This file
├── QUICKSTART.md              # Quick start guide
├── CLI_DOCUMENTATION.md       # Complete CLI reference
├── CLI_QUICK_REFERENCE.md     # One-page CLI reference
├── PROJECT_STRUCTURE.md       # Architecture overview
├── COMPLETE_GUIDE.md          # Detailed workflow guide
├── FLOWCHARTS.md              # Data flow diagrams
│
├── requirements.txt           # Python dependencies
├── setup.py                   # Package setup
├── setup_check.py             # Installation verification
│
├── ingest-cli.py              # Command-line interface
├── examples.py                # Usage examples
├── process_tst100.py          # Quick test script
│
├── config.example.json        # Example configuration
├── batch.example.json         # Example batch file
│
├── ded_io/                    # Main package
│   ├── __init__.py            # Package exports
│   ├── config.py              # Configuration classes
│   ├── models.py              # Data models
│   ├── pipeline.py            # Pipeline orchestration
│   ├── footage_ingest.py      # High-level ingest interface
│   │
│   └── stages/                # Processing stages
│       ├── __init__.py
│       ├── base.py            # Base stage class
│       ├── sony_conversion.py # MXF → DPX
│       ├── oiio_transform.py  # Color/geometric transforms
│       ├── proxy_generation.py# Proxy creation
│       ├── kitsu_integration.py # Kitsu API
│       └── file_operations.py # File handling
│
├── WSL_setup/                 # WSL/Debian setup
│   ├── debian-wsl-setup.sh    # Automated setup script
│   └── create_instance.md     # WSL instance creation
│
└── debug_scripts/             # Development/debug utilities
    ├── test_data.py
    ├── setup_kitsu_file_tree.py
    └── ...
```

---

## Future Enhancements

- EDL/XML parsing for automated batch ingests
- Support for additional camera formats (ARRI, RED, Canon)
- GPU-accelerated color processing
- Distributed processing across multiple machines
- Real-time status dashboard
- Automated QC checks
- Integration with additional asset management systems

---

## License

MIT License - See LICENSE file for details.

---

## Support

For issues and feature requests, please use the GitHub issue tracker.
