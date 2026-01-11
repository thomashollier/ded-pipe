#!/usr/bin/env python3
"""Check what proxy file was created."""

import os
from pathlib import Path

# Check temp directories
temp_dirs = [
    "/tmp/",
    "/mnt/c/shottree_test/tst100/",
]

print("Searching for proxy files...\n")

for temp_dir in temp_dirs:
    if Path(temp_dir).exists():
        print(f"Checking: {temp_dir}")
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith('.mp4'):
                    filepath = Path(root) / file
                    size = filepath.stat().st_size
                    size_mb = size / (1024 * 1024)
                    print(f"  Found: {filepath}")
                    print(f"  Size: {size_mb:.2f} MB")
                    
                    # Check if it's a real video or placeholder
                    if size < 1024 * 1024 * 2:  # Less than 2MB
                        print(f"  ⚠️  WARNING: File is very small - might be placeholder!")
                    
                    # Try to check with ffprobe if available
                    try:
                        import subprocess
                        result = subprocess.run(
                            ['ffprobe', str(filepath)],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if 'Invalid data found' in result.stderr or 'moov atom not found' in result.stderr:
                            print(f"  ❌ NOT a valid video file!")
                        else:
                            print(f"  ✅ Valid video file")
                    except:
                        pass
                    
                    print()

print("\nDone!")