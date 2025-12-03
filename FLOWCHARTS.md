# DED-IO Pipeline Flowcharts

This document contains flowcharts showing the pipeline workflow and codebase structure.

## Table of Contents
1. [High-Level Pipeline Workflow](#high-level-pipeline-workflow)
2. [Detailed Processing Flow](#detailed-processing-flow)
3. [Codebase Architecture](#codebase-architecture)
4. [CLI Execution Flow](#cli-execution-flow)
5. [Stage Execution Flow](#stage-execution-flow)
6. [Data Model Relationships](#data-model-relationships)
7. [Frame Number Mapping](#frame-number-mapping)
8. [Configuration Loading](#configuration-loading)
9. [Error Handling Flow](#error-handling-flow)

---

## High-Level Pipeline Workflow

```mermaid
graph TB
    Start([User Input]) --> Input{Input Method}
    
    Input -->|CLI| CLI["Command Line Interface<br/>ingest-cli.py"]
    Input -->|Python API| API["Python Function<br/>ingest_shot function"]
    Input -->|OOP| OOP["FootageIngestPipeline<br/>Object"]
    
    CLI --> Config["Load Configuration<br/>config.json"]
    API --> Build["Build ShotInfo"]
    OOP --> Build
    
    Config --> Build
    Build --> Pipeline["Create Pipeline<br/>6 Stages"]
    
    Pipeline --> Stage1["Stage 1:<br/>Sony Raw Conversion<br/>MXF to DPX"]
    Stage1 --> Stage2["Stage 2:<br/>OIIO Color Transform<br/>DPX to EXR with ACES"]
    Stage2 --> Stage3["Stage 3:<br/>Proxy Generation<br/>EXR to MP4"]
    Stage3 --> Stage4["Stage 4:<br/>Shot Tree Organization<br/>Copy to Structure"]
    Stage4 --> Stage5["Stage 5:<br/>Kitsu Integration<br/>Register in DB"]
    Stage5 --> Stage6["Stage 6:<br/>Cleanup<br/>Remove Temp Files"]
    
    Stage6 --> Success{Success?}
    Success -->|Yes| Report["Generate Report<br/>Summary"]
    Success -->|No| Error["Error Handling<br/>Log and Report"]
    
    Report --> Output(["Output:<br/>EXR Plates<br/>MP4 Proxy<br/>Metadata"])
    Error --> Output
    
    style Start fill:#e1f5ff
    style Output fill:#c8e6c9
    style Error fill:#ffcdd2
    style Pipeline fill:#fff9c4
    style Stage1 fill:#f0f4c3
    style Stage2 fill:#f0f4c3
    style Stage3 fill:#f0f4c3
    style Stage4 fill:#f0f4c3
    style Stage5 fill:#f0f4c3
    style Stage6 fill:#f0f4c3
```

---

## Detailed Processing Flow

```mermaid
graph TB
    subgraph Input ["Input Data"]
        Raw["Raw MXF File<br/>Sony Venice 2"]
        Editorial["Editorial Info<br/>In: 100, Out: 150"]
        Project["Project Info<br/>Name, Sequence, Shot"]
    end
    
    subgraph Processing ["Processing Pipeline"]
        direction TB
        
        subgraph Stage1 ["Stage 1: Sony Conversion"]
            S1A["Extract Frames<br/>with Handles"]
            S1B["Convert to DPX<br/>Temp Directory"]
            S1A --> S1B
        end
        
        subgraph Stage2 ["Stage 2: Color Transform"]
            S2A["Load DPX Frames"]
            S2B["Apply ACES Color<br/>SLog3 to ACEScg"]
            S2C["Desqueeze 2.0x<br/>Anamorphic"]
            S2D["Letterbox to UHD<br/>3840x2160"]
            S2E["Save as EXR<br/>DWAA Compression"]
            S2A --> S2B --> S2C --> S2D --> S2E
        end
        
        subgraph Stage3 ["Stage 3: Proxy Generation"]
            S3A["Load EXR Sequence"]
            S3B["Convert to sRGB"]
            S3C["Encode H.264<br/>MP4 Proxy"]
            S3A --> S3B --> S3C
        end
        
        subgraph Stage4 ["Stage 4: Organization"]
            S4A["Create Shot Tree<br/>Directory Structure"]
            S4B["Copy EXR to<br/>plates directory"]
            S4C["Copy MP4 to<br/>proxy directory"]
            S4A --> S4B --> S4C
        end
        
        subgraph Stage5 ["Stage 5: Kitsu"]
            S5A["Authenticate API"]
            S5B["Create or Update Shot"]
            S5C["Register Plate<br/>Metadata"]
            S5A --> S5B --> S5C
        end
        
        subgraph Stage6 ["Stage 6: Cleanup"]
            S6A["Remove Temp DPX"]
            S6B["Remove Temp Dirs"]
            S6A --> S6B
        end
        
        Stage1 --> Stage2
        Stage2 --> Stage3
        Stage3 --> Stage4
        Stage4 --> Stage5
        Stage5 --> Stage6
    end
    
    subgraph Output ["Output Structure"]
        Tree["Shot Tree:<br/>/project/sequences/seq/shot/"]
        Plates["plates/<br/>shot.0993.exr<br/>shot.0994.exr<br/>etc"]
        Proxy["proxy/<br/>shot.mp4"]
        Kitsu["Kitsu Database<br/>Metadata Entry"]
    end
    
    Raw --> Stage1
    Editorial --> Stage1
    Project --> Stage1
    
    Stage6 --> Tree
    Tree --> Plates
    Tree --> Proxy
    Stage5 --> Kitsu
    
    style Input fill:#e3f2fd
    style Processing fill:#fff9c4
    style Output fill:#c8e6c9
    style Stage1 fill:#f0f4c3
    style Stage2 fill:#f0f4c3
    style Stage3 fill:#f0f4c3
    style Stage4 fill:#f0f4c3
    style Stage5 fill:#f0f4c3
    style Stage6 fill:#f0f4c3
```

---

## Codebase Architecture

```mermaid
graph TB
    subgraph User ["User Interface Layer"]
        CLI["ingest-cli.py<br/>Command Line Interface"]
        Example["examples.py<br/>Python API Examples"]
        Test["process_tst100.py<br/>Test Script"]
    end
    
    subgraph API ["High-Level API Layer"]
        Ingest["footage_ingest.py<br/>FootageIngestPipeline<br/>ingest_shot function"]
    end
    
    subgraph Core ["Core Pipeline Layer"]
        Pipeline["pipeline.py<br/>Pipeline Orchestrator<br/>PipelineBuilder"]
        Config["config.py<br/>PipelineConfig<br/>KitsuConfig"]
        Models["models.py<br/>ShotInfo<br/>EditorialCutInfo<br/>ProcessingResult"]
    end
    
    subgraph Stages ["Processing Stages Layer"]
        Base["stages/base.py<br/>PipelineStage<br/>Abstract Base"]
        Sony["stages/sony_conversion.py<br/>SonyRawConversionStage"]
        OIIO["stages/oiio_transform.py<br/>OIIOColorTransformStage"]
        Proxy["stages/proxy_generation.py<br/>ProxyGenerationStage"]
        Kitsu["stages/kitsu_integration.py<br/>KitsuIntegrationStage"]
        Files["stages/file_operations.py<br/>ShotTreeOrganizationStage"]
    end
    
    subgraph External ["External Tools"]
        SonyTool["Sony Converter<br/>Command Line"]
        OIIOTool["OpenImageIO<br/>oiiotool"]
        FFmpeg["FFmpeg<br/>Video Encoder"]
        KitsuAPI["Kitsu API<br/>REST"]
    end
    
    CLI --> Ingest
    Example --> Ingest
    Test --> Ingest
    
    Ingest --> Pipeline
    Ingest --> Models
    
    Pipeline --> Config
    Pipeline --> Models
    Pipeline --> Base
    
    Base --> Sony
    Base --> OIIO
    Base --> Proxy
    Base --> Kitsu
    Base --> Files
    
    Sony --> SonyTool
    OIIO --> OIIOTool
    Proxy --> FFmpeg
    Kitsu --> KitsuAPI
    
    Config -.-> Sony
    Config -.-> OIIO
    Config -.-> Proxy
    Config -.-> Files
    
    Models -.-> Sony
    Models -.-> OIIO
    Models -.-> Proxy
    Models -.-> Kitsu
    Models -.-> Files
    
    style User fill:#e3f2fd
    style API fill:#f3e5f5
    style Core fill:#fff9c4
    style Stages fill:#c8e6c9
    style External fill:#ffccbc
```

---

## CLI Execution Flow

```mermaid
graph TB
    Start([CLI Command]) --> Parse["Parse Arguments<br/>source, sequence, etc."]
    
    Parse --> ConfigLoad{Config File?}
    ConfigLoad -->|Yes| LoadConfig["Load config.json<br/>Project Settings"]
    ConfigLoad -->|No| Defaults["Use Defaults"]
    
    LoadConfig --> Validate
    Defaults --> Validate
    
    Validate["Validate Arguments<br/>Check File Exists<br/>Check Frame Range"]
    
    Validate --> Mode{Mode?}
    
    Mode -->|Single Shot| BuildShot["Build ShotInfo<br/>from Arguments"]
    Mode -->|Batch| LoadBatch["Load batch.json<br/>Shot List"]
    
    BuildShot --> DryRun{Dry Run?}
    LoadBatch --> DryRun
    
    DryRun -->|Yes| Preview["Print Preview<br/>No Processing"]
    DryRun -->|No| Execute["Execute Pipeline"]
    
    Execute --> Process["Process Stages<br/>1 through 6"]
    
    Process --> Collect["Collect Results<br/>Success and Errors"]
    
    Collect --> Report{Generate Report?}
    
    Report -->|Yes| SaveReport["Save JSON Report"]
    Report -->|No| Display
    
    SaveReport --> Display["Display Summary<br/>Console Output"]
    Preview --> Display
    
    Display --> End([Exit])
    
    style Start fill:#e1f5ff
    style End fill:#c8e6c9
    style Execute fill:#fff9c4
    style Process fill:#f0f4c3
```

---

## Stage Execution Flow

```mermaid
graph TB
    Start([Stage Start]) --> Init["Initialize Stage<br/>Load Config"]
    
    Init --> PreCheck["Pre-Execution Checks<br/>Validate Inputs<br/>Check Tools Available"]
    
    PreCheck --> Valid{Valid?}
    
    Valid -->|No| Error["Add Error to Result<br/>Mark as Failed"]
    Valid -->|Yes| Setup["Setup Stage<br/>Create Directories<br/>Prepare Paths"]
    
    Setup --> Process["Execute Stage Logic<br/>Process Files"]
    
    Process --> Monitor["Monitor Progress<br/>Log Messages<br/>Track Timing"]
    
    Monitor --> PostCheck["Post-Execution Checks<br/>Verify Output<br/>Validate Results"]
    
    PostCheck --> Success{Success?}
    
    Success -->|No| Error
    Success -->|Yes| Result["Create ProcessingResult<br/>Success equals True<br/>Output Paths"]
    
    Error --> Return
    Result --> Return["Return to Pipeline"]
    
    Return --> Next{More Stages?}
    
    Next -->|Yes| NextStage([Next Stage])
    Next -->|No| Complete([Pipeline Complete])
    
    style Start fill:#e1f5ff
    style Complete fill:#c8e6c9
    style Error fill:#ffcdd2
    style Process fill:#fff9c4
```

---

## Data Model Relationships

```mermaid
classDiagram
    class EditorialCutInfo {
        +String sequence
        +String shot
        +Path source_file
        +int in_point
        +int out_point
        +float source_fps
        +String source_timecode_start
        +calculate_duration()
        +to_dict()
    }
    
    class ShotInfo {
        +String project
        +String sequence
        +String shot
        +EditorialCutInfo editorial_info
        +int first_frame
        +int last_frame
        +Path source_plates_path
        +Path proxy_path
        +String status
        +get_shot_name()
        +get_frame_range()
        +to_dict()
    }
    
    class ProcessingResult {
        +String stage_name
        +bool success
        +String message
        +List errors
        +List warnings
        +float duration_seconds
        +Dict data
        +add_error()
        +add_warning()
        +to_dict()
    }
    
    class ImageSequence {
        +Path directory
        +String base_name
        +String extension
        +int first_frame
        +int last_frame
        +int padding
        +get_frame_path()
        +get_all_frames()
        +verify_sequence()
    }
    
    class PipelineConfig {
        +int DIGITAL_START_FRAME
        +int HEAD_HANDLE_FRAMES
        +int TAIL_HANDLE_FRAMES
        +String SOURCE_COLORSPACE
        +String TARGET_COLORSPACE
        +float ANAMORPHIC_SQUEEZE
        +Path SHOT_TREE_ROOT
    }
    
    class Pipeline {
        +String name
        +List stages
        +Logger logger
        +add_stage()
        +execute()
        +get_summary()
    }
    
    class PipelineStage {
        +String name
        +Logger logger
        +execute()
        +process()
        +validate()
    }
    
    ShotInfo --> EditorialCutInfo : contains
    ShotInfo --> PipelineConfig : uses
    Pipeline --> PipelineStage : manages multiple
    PipelineStage --> ProcessingResult : creates
    PipelineStage --> ShotInfo : processes
    PipelineStage --> ImageSequence : works with
    PipelineStage --> PipelineConfig : reads from
```

---

## Frame Number Mapping

```mermaid
graph LR
    subgraph Editorial ["Editorial"]
        E1["Editorial Frame 100<br/>Cut In Point"]
        E2["Editorial Frame 150<br/>Cut Out Point"]
        E3["Duration: 51 frames"]
    end
    
    subgraph Digital ["Digital with Handles"]
        D1["Digital Frame 993<br/>Start with Handle"]
        D2["Digital Frame 1001<br/>Shot Start"]
        D3["Digital Frame 1051<br/>Shot End"]
        D4["Digital Frame 1059<br/>End with Handle"]
        D5["Total: 67 frames<br/>51 plus 8 plus 8"]
    end
    
    subgraph Output ["Output Files"]
        O1["shot.0993.exr"]
        O2["shot.1001.exr"]
        O3["shot.1051.exr"]
        O4["shot.1059.exr"]
    end
    
    E1 -.->|Maps to| D2
    E2 -.->|Maps to| D3
    
    D1 -.->|Creates| O1
    D2 -.->|Creates| O2
    D3 -.->|Creates| O3
    D4 -.->|Creates| O4
    
    style Editorial fill:#e3f2fd
    style Digital fill:#fff9c4
    style Output fill:#c8e6c9
```

---

## Configuration Loading

```mermaid
graph TB
    Start([Application Start]) --> CheckCLI{CLI Config<br/>Provided?}
    
    CheckCLI -->|Yes| LoadJSON["Load JSON Config<br/>config.json"]
    CheckCLI -->|No| LoadDefault["Load Default Config<br/>PipelineConfig"]
    
    LoadJSON --> Merge["Merge with Defaults<br/>CLI overrides JSON<br/>JSON overrides Defaults"]
    LoadDefault --> Merge
    
    Merge --> Validate["Validate Config<br/>Check Paths<br/>Check Tools"]
    
    Validate --> Valid{Valid?}
    
    Valid -->|No| Error["Show Errors<br/>Exit"]
    Valid -->|Yes| Store["Store Config<br/>Make Available to Stages"]
    
    Store --> Ready([Ready to Execute])
    
    style Start fill:#e1f5ff
    style Ready fill:#c8e6c9
    style Error fill:#ffcdd2
    style Merge fill:#fff9c4
```

---

## Error Handling Flow

```mermaid
graph TB
    Stage([Stage Executing]) --> Try{Try<br/>Execute}
    
    Try -->|Success| Result["Create Success Result<br/>success equals true"]
    Try -->|Exception| Catch["Catch Exception<br/>Log Error"]
    
    Catch --> StopError{Stop on<br/>Error?}
    
    StopError -->|Yes| Abort["Abort Pipeline<br/>Return Error"]
    StopError -->|No| Continue["Continue to<br/>Next Stage"]
    
    Result --> Next
    Continue --> Next
    
    Next{More<br/>Stages?}
    
    Next -->|Yes| NextStage([Next Stage])
    Next -->|No| Summary["Generate Summary<br/>All Results"]
    
    Abort --> Summary
    
    Summary --> Report["Create Report<br/>JSON Format"]
    
    Report --> Output{Output<br/>Method?}
    
    Output -->|Console| Console["Print Summary<br/>Colored Output"]
    Output -->|File| File["Save Report<br/>JSON File"]
    Output -->|Both| Both["Console and File"]
    
    Console --> End([Complete])
    File --> End
    Both --> End
    
    style Stage fill:#e1f5ff
    style End fill:#c8e6c9
    style Abort fill:#ffcdd2
    style Result fill:#c8e6c9
```

---

## Usage: Viewing These Flowcharts

These flowcharts use **Mermaid** syntax, which is supported by:

1. **GitHub** - Displays automatically in README files
2. **VS Code** - Install "Markdown Preview Mermaid Support" extension
3. **Online** - Use https://mermaid.live to view/edit
4. **Obsidian** - Native support
5. **GitLab** - Native support

### To View on GitHub:
Just push this file to your repository and view it on GitHub - the charts will render automatically!

### To View Locally:
1. Install VS Code extension: "Markdown Preview Mermaid Support"
2. Open this file in VS Code
3. Press `Cmd+Shift+V` (Mac) or `Ctrl+Shift+V` (Windows) for preview

### To Export as Images:
1. Visit https://mermaid.live
2. Copy/paste any diagram
3. Click "Download PNG" or "Download SVG"

---

## Legend

**Symbols:**
- Circle with text `([Text])` - Start/End points
- Rectangle `["Text"]` - Process steps
- Diamond `{Text}` - Decision points
- Subgraph - Grouped related items

**Colors:**
- Blue `#e1f5ff` - Input/Start
- Green `#c8e6c9` - Output/Success
- Yellow `#fff9c4` - Processing
- Red `#ffcdd2` - Error/Failure
- Purple `#f3e5f5` - API Layer
- Orange `#ffccbc` - External Tools

**Arrows:**
- Solid line `-->` - Process flow
- Dashed line `-.->` - Data reference
- Labeled arrow `-->|Label|` - Conditional flow
