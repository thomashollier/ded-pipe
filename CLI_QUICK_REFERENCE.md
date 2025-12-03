# Command-Line Interface - Quick Reference

## Installation

```bash
chmod +x ingest-cli.py
# Optional: Add to PATH
sudo ln -s $(pwd)/ingest-cli.py /usr/local/bin/ingest-cli
```

## Common Commands

### Single Shot (Basic)
```bash
python ingest-cli.py \
  --source /path/to/clip.mxf \
  --sequence seq010 \
  --shot 010 \
  --in 100 \
  --out 200
```

### Single Shot (With Config)
```bash
python ingest-cli.py \
  --config config.json \
  --source /path/to/clip.mxf \
  --sequence seq010 \
  --shot 010 \
  --in 100 \
  --out 200
```

### Batch Processing
```bash
python ingest-cli.py --config config.json --batch shots.json
```

### Dry Run (Preview)
```bash
python ingest-cli.py \
  --config config.json \
  --source clip.mxf \
  --sequence seq010 \
  --shot 010 \
  --in 100 \
  --out 200 \
  --dry-run
```

### Verbose with Log
```bash
python ingest-cli.py \
  --config config.json \
  --source clip.mxf \
  --sequence seq010 \
  --shot 010 \
  --in 100 \
  --out 200 \
  --verbose \
  --log-file process.log
```

### Save Report
```bash
python ingest-cli.py \
  --config config.json \
  --source clip.mxf \
  --sequence seq010 \
  --shot 010 \
  --in 100 \
  --out 200 \
  --report shot_010_report.json
```

## Options Quick Reference

| Option | Short | Description |
|--------|-------|-------------|
| `--config PATH` | `-c` | Configuration file |
| `--source PATH` | `-s` | Source footage file |
| `--sequence NAME` | | Sequence name |
| `--shot NAME` | | Shot number |
| `--in FRAME` | `-i` | In point |
| `--out FRAME` | `-o` | Out point |
| `--batch PATH` | `-b` | Batch file |
| `--project NAME` | `-p` | Project name |
| `--fps FLOAT` | | Frame rate (default: 24) |
| `--dry-run` | | Preview only |
| `--verbose` | `-v` | Debug output |
| `--quiet` | `-q` | Errors only |
| `--skip-kitsu` | | Skip Kitsu stage |
| `--skip-cleanup` | | Keep temp files |
| `--burn-in` | | Burn-in proxy |
| `--report PATH` | | Save report |
| `--log-file PATH` | | Log to file |

## Config File Format

```json
{
  "project": "my_project",
  "project_id": "kitsu_project_123",
  "paths": {
    "shot_tree_root": "/mnt/projects"
  },
  "tools": {
    "sony_converter": "/path/to/converter",
    "oiiotool": "oiiotool",
    "ffmpeg": "ffmpeg"
  }
}
```

## Batch File Format

```json
[
  {
    "sequence": "seq010",
    "shot": "010",
    "source_file": "/path/to/clip_001.mxf",
    "in_point": 100,
    "out_point": 250,
    "source_fps": 24.0
  },
  {
    "sequence": "seq010",
    "shot": "020",
    "source_file": "/path/to/clip_002.mxf",
    "in_point": 300,
    "out_point": 450,
    "source_fps": 24.0
  }
]
```

## Common Workflows

### Process Dailies
```bash
#!/bin/bash
for clip in /mnt/raw_footage/$(date +%Y-%m-%d)/*.mxf; do
    python ingest-cli.py \
        --config config.json \
        --source "$clip" \
        --sequence dailies \
        --shot "$(basename $clip .mxf)" \
        --in 0 \
        --out 100
done
```

### Preview Before Processing
```bash
# 1. Preview
python ingest-cli.py ... --dry-run

# 2. If looks good, process
python ingest-cli.py ...
```

### Debug Failed Shot
```bash
python ingest-cli.py \
    --config config.json \
    --source clip.mxf \
    --sequence seq010 \
    --shot 010 \
    --in 100 \
    --out 200 \
    --skip-cleanup \
    --verbose \
    --log-file debug.log
```

## Exit Codes

- `0` - Success
- `1` - Error
- `130` - Interrupted (Ctrl+C)

## See Also

- **Full Documentation:** [CLI_DOCUMENTATION.md](CLI_DOCUMENTATION.md)
- **Examples:** [examples.py](examples.py)
- **Package API:** [README.md](README.md)
