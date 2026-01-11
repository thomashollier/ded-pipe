#!/usr/bin/env python3
"""Delete ALL output files for a project (cleanup script)"""

import sys
sys.path.insert(0, '/home/pigeon/ded-pipe-main')

from ded_io.config import KitsuConfig
import gazu

# Use existing config
KITSU_HOST = KitsuConfig.KITSU_HOST
KITSU_EMAIL = KitsuConfig.KITSU_EMAIL
KITSU_PASSWORD = KitsuConfig.KITSU_PASSWORD
PROJECT_NAME = KitsuConfig.KITSU_PROJECT

print(f"Using config from ded_io:")
print(f"  Host: {KITSU_HOST}")
print(f"  Email: {KITSU_EMAIL}")
print(f"  Project: {PROJECT_NAME}")
print()

# Connect
print("Connecting to Kitsu...")
gazu.set_host(KITSU_HOST)
gazu.log_in(KITSU_EMAIL, KITSU_PASSWORD)
print("✅ Connected!\n")

# Get project
project = gazu.project.get_project_by_name(PROJECT_NAME)
print(f"Found project: {project['name']}\n")

# Get all shots in project
print("Finding all shots...")
shots = gazu.shot.all_shots_for_project(project)
print(f"Found {len(shots)} shots\n")

total_deleted = 0

for shot in shots:
    shot_name = shot['name']
    print(f"Processing shot: {shot_name}")
    
    try:
        # Get output files for this shot
        output_files = gazu.files.all_output_files_for_entity(shot)
        
        if output_files:
            print(f"  Found {len(output_files)} output files")
            
            for of in output_files:
                try:
                    output_type = of.get('output_type_name', 'Unknown')
                    output_id = of['id']
                    print(f"    Deleting: {output_type} - {output_id}")
                    
                    # Use the raw API client to delete
                    gazu.client.delete(f"data/output-files/{output_id}")
                    total_deleted += 1
                    print(f"    ✅ Deleted")
                    
                except Exception as e:
                    print(f"    ❌ Failed to delete {output_id}: {e}")
        else:
            print(f"  No output files")
    
    except Exception as e:
        print(f"  ⚠️  Error checking shot: {e}")
    
    print()

print(f"\n{'='*60}")
print(f"✅ Deleted {total_deleted} output files total")
print(f"{'='*60}")
print("\nYou can now delete shots normally in Kitsu UI!")