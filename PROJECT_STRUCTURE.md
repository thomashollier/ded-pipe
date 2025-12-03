# Project Structure

```
footage-ingest-pipeline/
│
├── README.md                          # Complete documentation
├── requirements.txt                   # Python dependencies
├── examples.py                        # Usage examples for all features
├── process_tst100.py                  # Quick start script for test shot
│
└── ingest_pipeline/                   # Main package
    │
    ├── __init__.py                    # Package exports
    ├── config.py                      # Configuration (PipelineConfig, KitsuConfig)
    ├── models.py                      # Data models
    │                                  #   - EditorialCutInfo
    │                                  #   - ShotInfo
    │                                  #   - ProcessingResult
    │                                  #   - ImageSequence
    │
    ├── pipeline.py                    # Pipeline orchestration
    │                                  #   - Pipeline (main orchestrator)
    │                                  #   - PipelineBuilder (fluent interface)
    │                                  #   - ConditionalPipeline (with conditions)
    │
    ├── footage_ingest.py              # High-level ingest interface
    │                                  #   - FootageIngestPipeline (OOP interface)
    │                                  #   - ingest_shot() (simple function)
    │                                  #   - create_ingest_pipeline()
    │
    └── stages/                        # Processing stages
        │
        ├── __init__.py                # Stage exports
        │
        ├── base.py                    # Base classes
        │                              #   - PipelineStage (abstract base)
        │                              #   - ValidationStage (validation base)
        │
        ├── sony_conversion.py         # Sony Venice 2 conversion
        │                              #   - SonyRawConversionStage
        │
        ├── oiio_transform.py          # OIIO color & transform
        │                              #   - OIIOColorTransformStage
        │
        ├── proxy_generation.py        # Proxy movie generation
        │                              #   - ProxyGenerationStage
        │                              #   - BurnInProxyStage (with metadata)
        │
        ├── kitsu_integration.py       # Kitsu API integration
        │                              #   - KitsuIntegrationStage
        │                              #   - KitsuQueryStage
        │
        └── file_operations.py         # File operations
                                       #   - FileCopyStage
                                       #   - ShotTreeOrganizationStage
                                       #   - CleanupStage
```

## File Descriptions

### Root Level

**README.md**
- Complete documentation with examples
- Installation instructions
- Configuration guide
- Usage patterns

**requirements.txt**
- Python package dependencies
- Currently only requires `requests` for Kitsu integration

**examples.py**
- Comprehensive examples showing different usage patterns
- Single shot ingest
- Batch processing
- Custom pipelines
- Individual stage usage

**process_tst100.py**
- Quick start script specifically for the test shot
- Demonstrates processing shot "tst100" from sequence "tst"
- Includes helpful output formatting

### Package: ingest_pipeline/

**__init__.py**
- Package initialization
- Exports main classes and functions
- Version info

**config.py**
- `PipelineConfig`: All pipeline settings
  - Frame numbering (start at 1001, 8 frame handles)
  - Color spaces (SLog3 to ACES)
  - Output formats (EXR, MP4)
  - Anamorphic settings (2.0 squeeze, UHD target)
  - Tool paths
  - Directory structure
- `KitsuConfig`: Kitsu API settings

**models.py**
- `EditorialCutInfo`: Editorial cut data (in/out points, source file)
- `ShotInfo`: Complete shot info (paths, status, frame ranges)
- `ProcessingResult`: Results from pipeline stages
- `ImageSequence`: Represents image sequences with frame ranges

**pipeline.py**
- `Pipeline`: Main orchestrator, executes stages in sequence
- `PipelineBuilder`: Fluent interface for building pipelines
- `ConditionalPipeline`: Pipeline with conditional stage execution

**footage_ingest.py**
- `FootageIngestPipeline`: High-level OOP interface
- `ingest_shot()`: Simple function for single shots
- `create_ingest_pipeline()`: Factory for standard pipeline
- Batch processing utilities

### Package: ingest_pipeline/stages/

**base.py**
- `PipelineStage`: Abstract base class for all stages
  - Common functionality (logging, timing, error handling)
  - Template method pattern
- `ValidationStage`: Base class for validation stages

**sony_conversion.py**
- `SonyRawConversionStage`: Convert Venice 2 MXF to DPX
  - Calls Sony's command line tool
  - Handles frame range extraction with handles
  - Outputs intermediate DPX sequence

**oiio_transform.py**
- `OIIOColorTransformStage`: Color and geometric transforms
  - ACES color conversion (SLog3 → ACEScg)
  - Anamorphic desqueeze (2.0x)
  - Letterbox to UHD (3840x2160)
  - Output to EXR with DWAA compression

**proxy_generation.py**
- `ProxyGenerationStage`: Create MP4 proxy movies
  - H.264 encoding
  - sRGB color space
  - Configurable resolution and quality
- `BurnInProxyStage`: Proxy with burned-in metadata
  - Frame numbers
  - Shot name
  - Timecode

**kitsu_integration.py**
- `KitsuIntegrationStage`: Register assets in Kitsu
  - Create/update shot entries
  - Register plate sequences
  - Store metadata (frame ranges, paths, etc.)
- `KitsuQueryStage`: Query data from Kitsu

**file_operations.py**
- `FileCopyStage`: Copy files with verification
  - Single files or sequences
  - Size verification
- `ShotTreeOrganizationStage`: Organize into shot tree
  - Create directory structure
  - Copy plates and proxies to proper locations
- `CleanupStage`: Remove temporary files
  - Clean up after successful processing
  - Optional preservation on errors

## Pipeline Data Flow

```
Editorial Cut List
        ↓
    ShotInfo
        ↓
[Sony Conversion]  ───→  DPX Sequence (temp)
        ↓
[OIIO Transform]   ───→  EXR Sequence (plates dir)
        ↓
[Proxy Generation] ───→  MP4 File (proxy dir)
        ↓
[Shot Tree Org]    ───→  Organized structure
        ↓
[Kitsu Integration]───→  Database entry
        ↓
[Cleanup]          ───→  Remove temp files
        ↓
    Complete!
```

## Output Structure

For shot `tst100`:

```
/mnt/projects/test_project/sequences/tst/tst100/
├── plates/
│   ├── tst100.0993.exr    # Frame 993 (first handle frame)
│   ├── tst100.0994.exr
│   ├── ...
│   ├── tst100.1001.exr    # Frame 1001 (shot start)
│   ├── ...
│   └── tst100.1058.exr    # Last frame
└── proxy/
    └── tst100.mp4          # Proxy movie
```

## Key Design Principles

1. **Modularity**: Each stage is independent and reusable
2. **Flexibility**: Stages can be mixed and matched in pipelines
3. **Extensibility**: Easy to add new stages or customize existing ones
4. **Error Handling**: Comprehensive error capture and reporting
5. **Logging**: Detailed logging at every step
6. **Data Flow**: Clear data models passed between stages
7. **Configuration**: Centralized configuration management

## Stage Reusability

Stages can be used in multiple pipelines:

```python
# Standard ingest pipeline
create_ingest_pipeline()  # Uses all stages

# Quick QC pipeline (no Kitsu)
Pipeline([
    OIIOColorTransformStage(),
    ProxyGenerationStage(),
])

# Reprocessing pipeline (assumes conversion done)
Pipeline([
    OIIOColorTransformStage(),
    ShotTreeOrganizationStage(),
    KitsuIntegrationStage(),
])

# Custom pipeline with burn-in proxy
Pipeline([
    SonyRawConversionStage(),
    OIIOColorTransformStage(),
    BurnInProxyStage(),  # Different proxy stage
    CleanupStage(),
])
```
