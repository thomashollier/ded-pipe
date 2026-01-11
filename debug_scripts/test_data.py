#!/usr/bin/env python3
"""Check metadata column field names."""

import gazu

# EDIT THESE VALUES
# ==================
KITSU_HOST = "KITSU URL"
KITSU_EMAIL = "KITSU USER"
KITSU_PASSWORD = "KITSU PASSWORD"
PROJECT_NAME = "ED"
# ==================

# Connect
print(f"Connecting to {KITSU_HOST}...")
gazu.set_host(KITSU_HOST)
gazu.log_in(KITSU_EMAIL, KITSU_PASSWORD)
print("Connected!")

# Get project
project = gazu.project.get_project_by_name(PROJECT_NAME)
print(f"Found project: {PROJECT_NAME}")

# List all shots in project
print("\n" + "="*60)
print("AVAILABLE SHOTS")
print("="*60)
all_shots = gazu.shot.all_shots_for_project(project)
if all_shots:
    print(f"Found {len(all_shots)} shots:")
    for s in all_shots:
        print(f"  - {s['name']}")
    
    # Use the first shot
    shot = all_shots[0]
    print(f"\nUsing shot: {shot['name']}")
else:
    print("No shots found!")
    exit(1)

# Get the shot's data structure
print("\n" + "="*60)
print("EXISTING METADATA IN SHOT")
print("="*60)
if 'data' in shot and shot['data']:
    print("Current metadata fields:")
    for key, value in shot['data'].items():
        print(f"  '{key}' = {value}")
else:
    print("(No metadata set yet)")

# Try to get metadata descriptors
print("\n" + "="*60)
print("AVAILABLE METADATA COLUMNS")
print("="*60)
try:
    descriptors = gazu.client.get(f"data/projects/{project['id']}/metadata-descriptors/Shot")
    if descriptors:
        print("Shot metadata columns defined in Kitsu:")
        for desc in descriptors:
            display_name = desc.get('name', 'N/A')
            field_name = desc.get('field_name', 'N/A')
            print(f"  Display: '{display_name}' -> Field: '{field_name}'")
    else:
        print("(No metadata descriptors found)")
except Exception as e:
    print(f"Could not get descriptors: {e}")

print("\n" + "="*60)
print("TESTING FIELD NAMES")
print("="*60)
# Try different variations
test_names = [
    'exr_file_path',
    'exrs_file_path', 
    'exr_path',
    'exr_file_location',
    'exr_location',
    'EXRs_File_Path',
    'EXR_File_Path',
    'exr_s_file_path'
]

print("Trying different field name variations...")
working_name = None
for name in test_names:
    try:
        gazu.shot.update_shot_data(shot, {name: "TEST_PATH_123"})
        print(f"  SUCCESS: '{name}'")
        working_name = name
        # Clean up
        gazu.shot.update_shot_data(shot, {name: ""})
        break
    except Exception as e:
        print(f"  FAILED: '{name}'")

print("\n" + "="*60)
print("RESULT")
print("="*60)
if working_name:
    print(f"Use this field name in your script: '{working_name}'")
else:
    print("None of the tested names worked.")
    print("Check the 'AVAILABLE METADATA COLUMNS' section above for the correct field name.")

print("\nDone!")