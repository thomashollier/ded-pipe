"""
Properly setup Kitsu project with file tree template.
This fixes the 500 error when creating output files.
"""
import gazu
from ded_io.config import KitsuConfig

# Authenticate
gazu.set_host(KitsuConfig.KITSU_HOST)
gazu.log_in(KitsuConfig.KITSU_EMAIL, KitsuConfig.KITSU_PASSWORD)

# Get project
project = gazu.project.get_project_by_name(KitsuConfig.KITSU_PROJECT)
print(f"Found project: {project['name']} (ID: {project['id']})")

# Define file tree template based on your shot structure
# Mountpoint: /mnt/c/shottree_test
# Structure: /mnt/c/shottree_test/<shot_name>/pla/<shot_name>_pla_rawPlate_v001/
file_tree = {
    "working": {
        "mountpoint": "/mnt/c/shottree_test",
        "root": "",
        "folder_path": {
            "shot": "<Shot>/pla",
            "asset": "<Asset>/pla",
            "sequence": "<Sequence>/pla",
            "style": "lowercase"
        },
        "file_name": {
            "shot": "<Shot>_pla_rawPlate_v<Revision>",
            "asset": "<Asset>_pla_rawPlate_v<Revision>",
            "sequence": "<Sequence>_pla_rawPlate_v<Revision>",
            "style": "lowercase"
        }
    },
    "output": {
        "mountpoint": "/mnt/c/shottree_test",
        "root": "",
        "folder_path": {
            "shot": "<Shot>/pla/<Shot>_pla_rawPlate_v<Revision>",
            "asset": "<Asset>/pla/<Asset>_pla_rawPlate_v<Revision>",
            "sequence": "<Sequence>/pla/<Sequence>_pla_rawPlate_v<Revision>",
            "style": "lowercase"
        },
        "file_name": {
            "shot": "<Shot>_pla_rawPlate_v<Revision>_<OutputType>_<Name>",
            "asset": "<Asset>_pla_rawPlate_v<Revision>_<OutputType>_<Name>",
            "sequence": "<Sequence>_pla_rawPlate_v<Revision>_<OutputType>_<Name>",
            "style": "lowercase"
        }
    }
}

# Update project with file tree using gazu method
try:
    print("\nUpdating project file tree...")
    gazu.files.update_project_file_tree(project['id'], file_tree)
    print("✅ File tree template configured successfully!")
    
    # Verify it was set
    updated_project = gazu.project.get_project(project['id'])
    if updated_project.get('file_tree'):
        print("\n✅ File tree is now set on the project!")
        print(f"Working mountpoint: {updated_project['file_tree']['working']['mountpoint']}")
        print(f"Output mountpoint: {updated_project['file_tree']['output']['mountpoint']}")
    else:
        print("\n⚠️  File tree might not be set. Check Kitsu project settings.")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
