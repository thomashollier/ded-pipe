# Footage Ingest Pipeline - Quick Start

A flexible, modular Python pipeline for ingesting Sony Venice 2 footage into a VFX production pipeline.

## What You Have

A complete, production-ready pipeline system with:

✓ **Modular stages** - Each processing step is independent and reusable
✓ **ACES workflow** - SLog3/SGamut3.Cine → ACEScg color conversion  
✓ **Anamorphic support** - 2.0x desqueeze and UHD letterboxing
✓ **Proxy generation** - H.264 MP4 proxies with optional burn-ins
✓ **Kitsu integration** - Automatic asset registration
✓ **Comprehensive logging** - Track every step of processing
✓ **Error handling** - Graceful failure with detailed error messages

## File Structure

```
.
├── README.md              # Complete documentation
├── PROJECT_STRUCTURE.md   # Architecture overview
├── requirements.txt       # Python dependencies
├── setup_check.py        # Setup verification script
├── examples.py           # Comprehensive usage examples
├── process_tst100.py     # Quick start for test shot
│
└── ingest_pipeline/      # Main package
    ├── config.py         # Configuration
    ├── models.py         # Data models
    ├── pipeline.py       # Pipeline orchestration
    ├── footage_ingest.py # High-level interface
    │
    └── stages/           # Processing modules
        ├── base.py
        ├── sony_conversion.py
        ├── oiio_transform.py
        ├── proxy_generation.py
        ├── kitsu_integration.py
        └── file_operations.py
```

## Quick Start (3 Steps)

### 1. Verify Setup

```bash
python setup_check.py
```

This checks:
- Python version (3.8+)
- Required tools (ffmpeg, oiiotool, etc.)
- Package imports
- Basic functionality

### 2. Configure

**Option A: Use a config file (recommended)**

Create `config.json`:
```json
{
  "project": "my_project",
  "project_id": "kitsu_project_123",
  "paths": {
    "shot_tree_root": "/mnt/projects"
  },
  "tools": {
    "sony_converter": "/path/to/sony_converter",
    "oiiotool": "oiiotool",
    "ffmpeg": "ffmpeg"
  }
}
```

**Option B: Edit the package config**

Edit `ingest_pipeline/config.py`:

```python
# Set tool paths
SONY_CONVERT_TOOL = "/path/to/sony_raw_converter"
OIIO_TOOL = "oiiotool"  # or full path
FFMPEG_TOOL = "ffmpeg"  # or full path

# Configure shot tree
SHOT_TREE_ROOT = Path("/mnt/projects")
```

### 3. Process Footage

**Command Line (Easiest):**

```bash
# Single shot
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

**Python Script:**

Edit `process_tst100.py` with your footage path, then run:

```bash
python process_tst100.py
```

## Usage Examples

### Command-Line Interface

**Basic single shot:**
```bash
python ingest-cli.py \
  --source /path/to/clip.mxf \
  --sequence tst \
  --shot 100 \
  --in 100 \
  --out 200
```

**With config file:**
```bash
python ingest-cli.py \
  --config config.json \
  --source /path/to/clip.mxf \
  --sequence tst \
  --shot 100 \
  --in 100 \
  --out 200
```

**Batch processing:**
```bash
# Create shots.json with multiple shots
python ingest-cli.py --config config.json --batch shots.json
```

**Dry run (preview):**
```bash
python ingest-cli.py \
  --config config.json \
  --source /path/to/clip.mxf \
  --sequence tst \
  --shot 100 \
  --in 100 \
  --out 200 \
  --dry-run
```

**See [CLI_DOCUMENTATION.md](CLI_DOCUMENTATION.md) for complete guide.**

### Python API

### Simple Single Shot

```python
from ingest_pipeline import ingest_shot
from pathlib import Path

summary = ingest_shot(
    project="my_project",
    sequence="tst",
    shot="100",
    source_file=Path("/path/to/clip.mxf"),
    in_point=100,
    out_point=150
)
```

### Multiple Shots

```python
from ingest_pipeline import FootageIngestPipeline

pipeline = FootageIngestPipeline(project="my_project")

# Process multiple shots
pipeline.ingest_shot("tst", "100", Path("/path/to/clip1.mxf"), 100, 150)
pipeline.ingest_shot("tst", "110", Path("/path/to/clip2.mxf"), 200, 275)

# Get summary
summary = pipeline.get_summary()
```

### Batch Processing

```python
shots = [
    {'sequence': 'tst', 'shot': '100', 'source_file': '/path/to/clip1.mxf',
     'in_point': 100, 'out_point': 150},
    {'sequence': 'tst', 'shot': '110', 'source_file': '/path/to/clip2.mxf',
     'in_point': 200, 'out_point': 275}
]

results = pipeline.ingest_batch(shots)
```

### Custom Pipeline

```python
from ingest_pipeline.pipeline import PipelineBuilder
from ingest_pipeline.stages import *

# Build custom pipeline
builder = PipelineBuilder("CustomIngest")
builder.add_stage(SonyRawConversionStage())
builder.add_stage(OIIOColorTransformStage())
builder.add_stage(BurnInProxyStage())  # Proxy with frame numbers
builder.add_stage(CleanupStage())

pipeline = builder.build()
summary = pipeline.execute(shot_info)
```

## How It Works

### For shot "tst100":

1. **Input**: Venice 2 MXF file, in point=100, out point=150
   
2. **Processing**:
   - Convert MXF → DPX (temp)
   - Transform DPX → EXR with ACES color + desqueeze + letterbox
   - Generate MP4 proxy
   - Organize into shot tree
   - Register in Kitsu
   - Clean up temp files

3. **Output**:
   ```
   /mnt/projects/my_project/sequences/tst/tst100/
   ├── plates/
   │   ├── tst100.0993.exr  # Frame 993 (8 frame handle)
   │   ├── ...
   │   ├── tst100.1001.exr  # Frame 1001 (editorial in)
   │   └── tst100.1058.exr  # Last frame
   └── proxy/
       └── tst100.mp4
   ```

### Frame Mapping

- Editorial in point 100 → Digital frame 1001
- With 8 frame handles: frames 993-1058 (66 frames total)
- First frame in sequence: 993 (1001 - 8)

## Configuration Highlights

### Frame Numbering
```python
DIGITAL_START_FRAME = 1001     # Shots start at frame 1001
HEAD_HANDLE_FRAMES = 8         # 8 frames before cut
TAIL_HANDLE_FRAMES = 8         # 8 frames after cut
```

### Color Pipeline
```python
SOURCE_COLORSPACE = "SLog3-SGamut3.Cine"  # Venice 2
TARGET_COLORSPACE = "ACES - ACEScg"        # ACES working space
ACES_VERSION = "1.3"
```

### Anamorphic
```python
ANAMORPHIC_SQUEEZE = 2.0       # 2x anamorphic
TARGET_WIDTH = 3840            # UHD
TARGET_HEIGHT = 2160
LETTERBOX = True               # Center and letterbox
```

### Output Formats
```python
OUTPUT_FORMAT = "exr"
OUTPUT_COMPRESSION = "dwaa:15"  # DWAA compression
OUTPUT_BIT_DEPTH = "half"       # 16-bit float

PROXY_FORMAT = "mp4"
PROXY_CODEC = "libx264"
PROXY_CRF = 18                  # Quality setting
```

## Extending the Pipeline

### Create a New Stage

```python
from ingest_pipeline.stages.base import PipelineStage
from ingest_pipeline.models import ProcessingResult, ShotInfo

class MyCustomStage(PipelineStage):
    def process(self, shot_info: ShotInfo, result: ProcessingResult, **kwargs):
        # Your processing logic here
        self.logger.info("Processing...")
        result.data['output'] = "value"
```

### Add to Pipeline

```python
from ingest_pipeline.pipeline import PipelineBuilder

builder = PipelineBuilder("MyPipeline")
builder.add_stage(MyCustomStage())
builder.add_stage(OtherStage())
pipeline = builder.build()
```

## Key Features

### Modular Design
- Each stage is independent
- Stages can be reused in different pipelines
- Easy to add new stages or modify existing ones

### Flexible Configuration
- Centralized configuration in `config.py`
- Environment-specific settings
- Easy to override per-shot or per-project

### Comprehensive Error Handling
- Each stage reports success/failure
- Detailed error messages
- Optional stop-on-error behavior
- Preservation of temp files for debugging

### Rich Logging
- Stage-level logging
- Timing information
- Debug output available
- Configurable log levels

### Data Models
- Clean separation of data and logic
- Strongly typed (with dataclasses)
- Easy serialization to JSON
- Clear data flow between stages

## Tools Required

### Essential (for full functionality)
- **Sony raw converter**: Vendor-specific tool for MXF conversion
- **OpenImageIO**: With ACES 1.3 OCIO config
- **FFmpeg**: For proxy generation

### Optional
- **Kitsu**: For asset management (can be disabled)

## Common Workflows

### Standard Ingest
```python
from ingest_pipeline import quick_ingest

quick_ingest(
    source_file="/path/to/clip.mxf",
    sequence="seq",
    shot="010",
    in_point=100,
    out_point=200
)
```

### Reprocess Colors Only
```python
from ingest_pipeline.pipeline import Pipeline
from ingest_pipeline.stages import OIIOColorTransformStage

# Reprocess existing DPX to EXR with new color settings
pipeline = Pipeline("Recolor")
pipeline.add_stage(OIIOColorTransformStage())
pipeline.execute(shot_info, input_sequence=existing_dpx)
```

### Generate New Proxy
```python
from ingest_pipeline.stages import BurnInProxyStage

# Create proxy from existing EXR with burn-ins
proxy_stage = BurnInProxyStage()
proxy_stage.execute(shot_info, input_sequence=existing_exr)
```

## Getting Help

1. **Check the documentation**:
   - `README.md` - Complete guide
   - `PROJECT_STRUCTURE.md` - Architecture details
   
2. **Run examples**:
   - `python examples.py` - See all usage patterns
   - `python setup_check.py` - Verify setup

3. **Review the code**:
   - All modules are well-documented
   - Clear comments and docstrings
   - Type hints throughout

## Next Steps

1. ✓ Run `setup_check.py` to verify setup
2. ✓ Configure `config.py` with your paths
3. ✓ Set up Kitsu credentials (optional)
4. ✓ Test with `process_tst100.py`
5. ✓ Review `examples.py` for more patterns
6. ✓ Build your own pipelines!

## Future Enhancements

Potential additions:
- EDL/XML parsing for batch ingests
- Additional camera format support
- GPU-accelerated processing
- Distributed processing
- Real-time status dashboard
- Automated QC checks
- Web interface

---

**Questions? Issues?**

Check the documentation or review the code - it's designed to be readable and extensible!
