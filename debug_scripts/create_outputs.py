#!/usr/bin/env python3
"""Create Output Types in Kitsu"""

import gazu

# EDIT THESE
KITSU_HOST = "KITSU URL"
KITSU_EMAIL = "KITSU USER"
KITSU_PASSWORD = "KITSU PASSWORD"

# Connect
print("Connecting to Kitsu...")
gazu.set_host(KITSU_HOST)
gazu.log_in(KITSU_EMAIL, KITSU_PASSWORD)
print("✅ Connected!\n")

# Create Output Types
output_types_to_create = [
    {"name": "Plate", "short_name": "plate"},
    {"name": "Proxy", "short_name": "proxy"}
]

for ot_data in output_types_to_create:
    try:
        # Check if it already exists
        existing = gazu.files.all_output_types()
        if any(ot['name'] == ot_data['name'] for ot in existing):
            print(f"⚠️  Output type '{ot_data['name']}' already exists, skipping")
            continue
        
        # Create it
        output_type = gazu.client.post('data/output-types', ot_data)
        print(f"✅ Created output type: {ot_data['name']} (ID: {output_type['id']})")
        
    except Exception as e:
        print(f"❌ Failed to create '{ot_data['name']}': {e}")

print("\n✅ Done! Output types created.")

# List all output types
print("\n📋 All output types in Kitsu:")
all_types = gazu.files.all_output_types()
for ot in all_types:
    print(f"  - {ot['name']} (short: {ot.get('short_name', 'N/A')})")