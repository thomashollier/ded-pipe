# Project Structure

Complete architecture overview including CLI, configuration files, and all components.

## Directory Tree

```
footage-ingest-pipeline/
│
├── Documentation (9 files)
│   ├── README.md                     # Main documentation
│   ├── QUICKSTART.md                 # Quick reference
│   ├── PROJECT_STRUCTURE.md          # This file
│   ├── CONTRIBUTING.md               # Contribution guidelines  
│   ├── CHANGELOG.md                  # Version history
│   ├── DOWNLOAD_GUIDE.md             # Download instructions
│   ├── SETUP_SCRIPT_GUIDE.md         # Setup automation guide
│   ├── CLI_DOCUMENTATION.md          # CLI complete guide ⭐
│   └── CLI_QUICK_REFERENCE.md        # CLI quick reference ⭐
│
├── Configuration (4 files)
│   ├── .gitignore                    # Git ignore rules
│   ├── LICENSE                       # MIT License
│   ├── requirements.txt              # Python dependencies
│   └── setup.py                      # Package installer
│
├── Example Files (2 files) ⭐
│   ├── config.example.json           # Example config file
│   └── batch.example.json            # Example batch file
│
├── Scripts (5 files)
│   ├── setup_repo.py                 # Repository setup automation
│   ├── setup_check.py                # Environment verification
│   ├── ingest-cli.py                 # Command-line interface ⭐
│   ├── examples.py                   # Python API examples
│   └── process_tst100.py             # Test shot script
│
├── .github/                          # GitHub configuration
│   ├── workflows/
│   │   └── python-ci.yml             # CI/CD workflow
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md             # Bug template
│   │   └── feature_request.md        # Feature template
│   └── pull_request_template.md      # PR template
│
└── ingest_pipeline/                  # Main package (12 files)
    ├── __init__.py                   # Package exports
    ├── config.py                     # Configuration classes
    ├── models.py                     # Data models
    ├── pipeline.py                   # Pipeline orchestration
    ├── footage_ingest.py             # High-level API
    └── stages/                       # Processing stages (7 files)
        ├── __init__.py               # Stage exports
        ├── base.py                   # Base classes
        ├── sony_conversion.py        # Sony MXF → DPX
        ├── oiio_transform.py         # Color & transform
        ├── proxy_generation.py       # Proxy creation
        ├── kitsu_integration.py      # Asset management
        └── file_operations.py        # File ops & cleanup
```

## File Descriptions

### Documentation Files (9 total)

#### README.md
Complete documentation with installation, usage, examples for both CLI and Python API.

#### QUICKSTART.md  
Quick 3-step setup guide with CLI and Python examples.

#### PROJECT_STRUCTURE.md (this file)
Architecture overview, file descriptions, data flow diagrams.

#### CONTRIBUTING.md
Development setup, code style, contribution workflow.

#### CHANGELOG.md
Version history, release notes, breaking changes.

#### DOWNLOAD_GUIDE.md
Complete file listing with download links, setup instructions.

#### SETUP_SCRIPT_GUIDE.md
How to use setup_repo.py for automated repository setup.

#### CLI_DOCUMENTATION.md ⭐ NEW
Complete command-line interface guide:
- All CLI arguments and options
- Configuration file format  
- Batch file format
- Usage examples
- Shell script integration
- Makefile examples

#### CLI_QUICK_REFERENCE.md ⭐ NEW
One-page quick reference for CLI with common commands and options table.

### Configuration Files (4 total)

#### .gitignore
Git ignore rules for Python, IDE files, temp files, logs.

#### LICENSE
MIT License - open source license terms.

#### requirements.txt
Python dependencies (currently just `requests`).

#### setup.py
Package installer with metadata, dependencies, CLI entry point.

### Example Files (2 total) ⭐ NEW

#### config.example.json
Example configuration file showing:
- Project settings
- Tool paths
- Pipeline defaults
- Output settings
- Paths configuration

#### batch.example.json
Example batch processing file with array of shot data.

### Scripts (5 total)

#### setup_repo.py
Automated repository setup:
- Extracts files from zip
- Creates directory structure
- Organizes files
- Initializes git
- Interactive prompts

#### setup_check.py
Environment verification:
- Python version check
- Tool availability (ffmpeg, oiiotool, etc.)
- Package import tests
- Directory structure validation

#### ingest-cli.py ⭐ NEW
Command-line interface:
- Single shot processing
- Batch processing
- Config file support
- Dry run mode
- Verbose logging
- Report generation
- Pipeline control options

#### examples.py
Python API usage examples:
- Single shot
- Batch processing
- Custom pipelines
- Individual stages
- All interface types

#### process_tst100.py
Quick start test shot script with helpful output formatting.

### Python Package (12 files)

#### ingest_pipeline/__init__.py
Package exports and version info.

#### ingest_pipeline/config.py
- `PipelineConfig`: Frame numbering, color spaces, formats, paths
- `KitsuConfig`: Kitsu API settings

#### ingest_pipeline/models.py
- `EditorialCutInfo`: Editorial cut data
- `ShotInfo`: Complete shot information
- `ProcessingResult`: Stage results
- `ImageSequence`: Image sequence representation

#### ingest_pipeline/pipeline.py
- `Pipeline`: Main orchestrator
- `PipelineBuilder`: Fluent interface
- `ConditionalPipeline`: Conditional execution

#### ingest_pipeline/footage_ingest.py
- `FootageIngestPipeline`: OOP interface
- `ingest_shot()`: Simple function
- `create_ingest_pipeline()`: Factory

#### ingest_pipeline/stages/base.py
- `PipelineStage`: Abstract base class
- `ValidationStage`: Validation base

#### ingest_pipeline/stages/sony_conversion.py
- `SonyRawConversionStage`: MXF → DPX

#### ingest_pipeline/stages/oiio_transform.py
- `OIIOColorTransformStage`: Color + geometric transforms

#### ingest_pipeline/stages/proxy_generation.py
- `ProxyGenerationStage`: MP4 proxy
- `BurnInProxyStage`: Proxy with burn-ins

#### ingest_pipeline/stages/kitsu_integration.py
- `KitsuIntegrationStage`: Asset registration
- `KitsuQueryStage`: Data queries

#### ingest_pipeline/stages/file_operations.py
- `FileCopyStage`: File copying
- `ShotTreeOrganizationStage`: Directory organization
- `CleanupStage`: Temp file cleanup

## Data Flow

### Standard Pipeline Flow
```
Editorial Data (manual or JSON)
    ↓
ShotInfo Model
    ↓
┌─────────────────────┐
│ Pipeline            │
│ Orchestrator        │
└─────────────────────┘
    ↓
Sony Conversion  → DPX (temp)
    ↓
OIIO Transform   → EXR (plates)
    ↓
Proxy Generation → MP4 (proxy)
    ↓
Organization     → Shot tree
    ↓
Kitsu Integration→ Database
    ↓
Cleanup          → Remove temps
    ↓
Complete!
```

### CLI Flow ⭐ NEW
```
CLI Arguments + Config File
    ↓
ingest-cli.py
    ↓
Parse & Validate
    ↓
Load Config (JSON)
    ↓
Single Shot OR Batch Mode
    ↓
Call ingest_shot() or FootageIngestPipeline
    ↓
Standard Pipeline Flow
    ↓
Print Summary + Save Report
```

## Usage Patterns

### Pattern 1: CLI (Production) ⭐ NEW
```bash
python ingest-cli.py --config show.json --batch dailies.json
```
**For:** Production use, shell scripts, TDs

### Pattern 2: Python Function (Simple)
```python
ingest_shot(project, sequence, shot, source, in, out)
```
**For:** Quick automation, simple scripts

### Pattern 3: OOP (Complex)
```python
pipeline = FootageIngestPipeline(project)
pipeline.ingest_batch(shots)
```
**For:** Stateful processing, multiple shots

### Pattern 4: Custom (Special)
```python
PipelineBuilder().add_stage(...).build()
```
**For:** R&D, experimental workflows

## Configuration System ⭐

### Three-Level Hierarchy
1. **Package defaults** (PipelineConfig class)
2. **Config file** (JSON via --config)
3. **CLI arguments** (command-line)

Later overrides earlier.

### Config File Example
```json
{
  "project": "my_film",
  "project_id": "kitsu_123",
  "tools": {
    "sony_converter": "/usr/local/bin/converter",
    "oiiotool": "oiiotool",
    "ffmpeg": "ffmpeg"
  },
  "paths": {
    "shot_tree_root": "/mnt/projects"
  }
}
```

## Output Structure

```
/mnt/projects/{project}/sequences/{sequence}/{shot}/
├── plates/
│   ├── {shot}.0993.exr    # Frame 993 (handle)
│   ├── {shot}.1001.exr    # Frame 1001 (start)
│   └── {shot}.####.exr    # Sequence
└── proxy/
    └── {shot}.mp4         # Proxy movie
```

## Key Design Principles

1. **Modularity** - Reusable, independent stages
2. **Flexibility** - Multiple interfaces (CLI, Python)
3. **Configuration** - File-based + command-line
4. **Error Handling** - Comprehensive with reports
5. **Logging** - Detailed, configurable levels
6. **Extensibility** - Easy to add stages/pipelines

## Stage Reusability

```python
# Full pipeline
create_ingest_pipeline()

# QC only (no Kitsu)
Pipeline([OIIOColorTransformStage(), ProxyGenerationStage()])

# Reprocess colors
Pipeline([OIIOColorTransformStage(), ShotTreeOrganizationStage()])

# Custom with burn-ins
Pipeline([..., BurnInProxyStage(), ...])
```

## Repository Stats

- **Total Files:** 33
- **Documentation:** 9 files
- **Configuration:** 4 files
- **Examples:** 2 files  
- **Scripts:** 5 files
- **Python Modules:** 12 files
- **GitHub Templates:** 4 files
- **Lines of Code:** ~4,500+

## What's New in This Version

⭐ **Command-Line Interface** (ingest-cli.py)
- Single shot and batch processing
- Config file support
- Dry run mode
- Report generation

⭐ **Example Files**
- config.example.json - Configuration template
- batch.example.json - Batch processing template

⭐ **Enhanced Documentation**
- CLI_DOCUMENTATION.md - Complete CLI guide
- CLI_QUICK_REFERENCE.md - Quick reference card
- Updated README and QUICKSTART with CLI examples

This creates a complete, production-ready system for footage ingest!
