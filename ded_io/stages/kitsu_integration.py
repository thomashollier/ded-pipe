"""
Stage for integrating with Kitsu asset management system.
Creates shots, uploads proxies, and updates metadata.
"""
import gazu
from typing import Optional, Dict, Any, List
from pathlib import Path
import time

from .base import PipelineStage
from ..models import ProcessingResult, ShotInfo
from ..config import KitsuConfig, PipelineConfig


class KitsuIntegrationStage(PipelineStage):
    """
    Create and update shots in Kitsu.
    
    Registers plate sequences and associated metadata in the
    Kitsu production tracking system.
    """
    
    # Define task order for pipeline
    PIPELINE_TASKS = [
        "Prep & Unwarp",
        "Layout",
        "Animation",
        "FX",
        "Lighting",
        "Compositing",
        "Motion GFX",
        "Background Painting",
        "Final Compositing"
    ]
    
    def __init__(
        self,
        kitsu_host: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        project_name: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Kitsu integration.
        
        Args:
            kitsu_host: Kitsu API host URL (e.g., "https://yourstudio.kitsu.cg-wire.com/api")
            email: Login email
            password: Login password
            project_name: Kitsu project name (e.g., "DRIVER ED")
        """
        super().__init__(**kwargs)
        self.kitsu_host = kitsu_host or KitsuConfig.KITSU_HOST
        self.email = email or KitsuConfig.KITSU_EMAIL
        self.password = password or KitsuConfig.KITSU_PASSWORD
        self.project_name = project_name or KitsuConfig.KITSU_PROJECT
        self.authenticated = False
        self.project = None
    
    def process(self, shot_info: ShotInfo, result: ProcessingResult, **kwargs):
        """
        Create or update Kitsu entries.
        
        This stage should run AFTER:
        - ProxyGenerationStage (so shot_info.output_proxy_path exists)
        - ShotTreeOrganizationStage (so final paths are set)
        
        Args:
            shot_info: Shot information with paths populated
            result: Result object to populate
            **kwargs: Additional arguments
                - project_name: Override default project name
                - upload_task_name: Task to upload proxy to (default: 'Prep & Unwarp')
                - upload_proxy: Whether to upload proxy (default: True)
                - create_tasks: Whether to create pipeline tasks (default: True)
                - create_output_files: Whether to create output file records (default: True)
        """
        if not self.validate_inputs(shot_info, result):
            return
        
        # Authenticate
        if not self._authenticate(result):
            return
        
        # Get parameters
        project_name = kwargs.get('project_name', self.project_name)
        upload_task_name = kwargs.get('upload_task_name', 'Prep & Unwarp')
        upload_proxy = kwargs.get('upload_proxy', True)
        create_tasks = kwargs.get('create_tasks', True)
        create_output_files = kwargs.get('create_output_files', True)
        
        self.logger.info(f"Processing Kitsu integration for shot: {shot_info.shot_name}")
        
        # Get or create shot
        shot = self._get_or_create_shot(
            project_name=project_name,
            shot_info=shot_info,
            result=result
        )
        
        if not shot:
            return
        
        # Create all pipeline tasks for this shot
        if create_tasks:
            self._create_pipeline_tasks(shot, result)
        
        # Update metadata (EXR path, original clip location, etc.)
        self._update_metadata(shot, shot_info, result)
        
        # Create output files FIRST (before uploading proxy)
        output_files = {}
        if create_output_files:
            output_files = self._create_output_files(shot, shot_info, upload_task_name, result)
            self.logger.info(f"🔍 DEBUG: output_files after creation: {list(output_files.keys())}")
            for key, of in output_files.items():
                self.logger.info(f"🔍 DEBUG: {key} output file ID: {of.get('id')}")
        
        # Upload proxy with links to output files in comment
        if upload_proxy and shot_info.output_proxy_path:
            self._upload_proxy(shot, shot_info, upload_task_name, output_files, result)
        
        # Store results
        result.data['kitsu_shot_id'] = shot['id']
        result.data['kitsu_shot_name'] = shot['name']
        self.logger.info(f"Successfully registered in Kitsu: {shot_info.shot_name}")
    
    def _authenticate(self, result: ProcessingResult) -> bool:
        """
        Authenticate with Kitsu API using Gazu.
        
        Returns:
            True if successful, False otherwise
        """
        if self.authenticated:
            return True
        
        if not self.email or not self.password:
            result.add_error("Kitsu credentials not provided")
            return False
        
        try:
            gazu.set_host(self.kitsu_host)
            gazu.log_in(self.email, self.password)
            self.authenticated = True
            self.logger.info("Authenticated with Kitsu")
            return True
            
        except Exception as e:
            result.add_error(f"Kitsu authentication failed: {str(e)}")
            self.logger.error(f"Authentication failed: {e}")
            return False
    
    def _get_or_create_shot(
        self,
        project_name: str,
        shot_info: ShotInfo,
        result: ProcessingResult
    ) -> Optional[Dict[str, Any]]:
        """
        Get or create a shot in Kitsu.
        
        Args:
            project_name: Kitsu project name
            shot_info: Shot information
            result: Result object
            
        Returns:
            Shot dict if successful, None otherwise
        """
        try:
            # Get project (cache it)
            if not self.project or self.project['name'] != project_name:
                self.project = gazu.project.get_project_by_name(project_name)
                self.logger.info(f"Found project: {project_name}")
            
            # Try to get existing shot
            try:
                shot = gazu.shot.get_shot_by_name(self.project, shot_info.shot_name)
                self.logger.info(f"Found existing shot: {shot_info.shot_name}")
                return shot
            except:
                # Shot doesn't exist, we'll create it
                pass
            
            # Get or create sequence
            sequence_name = shot_info.sequence
            try:
                sequence = gazu.shot.get_sequence_by_name(self.project, sequence_name)
                self.logger.info(f"Found existing sequence: {sequence_name}")
            except:
                sequence = gazu.shot.new_sequence(self.project, sequence_name)
                self.logger.info(f"Created new sequence: {sequence_name}")
            
            # Create shot
            shot = gazu.shot.new_shot(
                self.project,
                sequence,
                shot_info.shot_name
            )
            self.logger.info(f"Created new shot: {shot_info.shot_name}")
            return shot
            
        except Exception as e:
            result.add_error(f"Failed to get/create shot in Kitsu: {str(e)}")
            self.logger.error(f"Shot creation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _create_pipeline_tasks(
        self,
        shot: Dict[str, Any],
        result: ProcessingResult
    ):
        """
        Create all pipeline tasks for this specific shot.
        
        Creates task instances (not task types) for this shot.
        Sets all tasks to "To Do" status.
        
        Args:
            shot: Shot dict from Kitsu
            result: Result object
        """
        try:
            # Get all task types (these are global templates)
            all_task_types = gazu.task.all_task_types()
            task_type_map = {tt['name']: tt for tt in all_task_types}
            
            # Get "To Do" status
            todo_status = None
            try:
                todo_status = gazu.task.get_task_status_by_short_name("todo")
            except:
                try:
                    statuses = gazu.task.all_task_statuses()
                    todo_status = next((s for s in statuses if s['name'].lower() == 'to do'), None)
                except:
                    pass
            
            if not todo_status:
                self.logger.warning("'To Do' status not found, tasks will use default status")
            
            # Get existing tasks for this shot
            existing_tasks = gazu.task.all_tasks_for_shot(shot)
            existing_task_names = {t['task_type_name'] for t in existing_tasks}
            
            tasks_created = 0
            tasks_skipped = 0
            
            for task_name in self.PIPELINE_TASKS:
                # Check if task type exists globally
                if task_name not in task_type_map:
                    self.logger.warning(f"Task type '{task_name}' not found in Kitsu, skipping")
                    continue
                
                # Check if this shot already has this task
                if task_name in existing_task_names:
                    tasks_skipped += 1
                    self.logger.debug(f"Task '{task_name}' already assigned to shot, skipping")
                    continue
                
                task_type = task_type_map[task_name]
                
                # Create the task instance for this shot
                try:
                    task = gazu.task.new_task(shot, task_type)
                    
                    # Set to "To Do" status if available
                    if todo_status:
                        try:
                            # Update the task status
                            gazu.client.put(
                                f"data/tasks/{task['id']}",
                                {"task_status_id": todo_status['id']}
                            )
                        except Exception as status_error:
                            self.logger.debug(f"Could not set 'To Do' status for {task_name}: {status_error}")
                    
                    tasks_created += 1
                    self.logger.debug(f"Created task instance: {task_name}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to create task '{task_name}': {e}")
            
            if tasks_created > 0:
                self.logger.info(f"Created {tasks_created} task instances for shot (skipped {tasks_skipped} existing)")
                result.data['tasks_created'] = tasks_created
            elif tasks_skipped > 0:
                self.logger.info(f"All {tasks_skipped} tasks already assigned to shot")
            
        except Exception as e:
            result.add_warning(f"Failed to create pipeline tasks: {str(e)}")
            self.logger.warning(f"Task creation failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _update_metadata(
        self,
        shot: Dict[str, Any],
        shot_info: ShotInfo,
        result: ProcessingResult
    ):
        """
        Update shot metadata in Kitsu.
        
        Updates the following metadata columns:
        - EXR File Path (field: exr_file_path)
        - Original Clip Location (field: original_clip_location)
        - Original Clip Name (field: original_clip_name)
        - Proxy Movie File Path (field: proxy_movie_file_path)
        - Bit Depth (field: bit_depth)
        - Working Colorspace (field: working_colorspace)
        - Source Colorspace (field: source_colorspace)
        - Turnover Date (field: turnover_date)
        - Element Name (field: element_name)
        - EXR Folder Size (field: exr_folder_size)
        - Resolution (field: resolution)
        - FPS (field: fps)
        - Plus frame ranges, timecodes, etc.
        
        Args:
            shot: Shot dict from Kitsu
            shot_info: Shot information
            result: Result object
        """
        try:
            metadata = {}
            
            # EXR File Path - build the final organized path
            if shot_info.output_plates_path:
                # Build the expected final organized path
                shot_root = PipelineConfig.SHOT_TREE_ROOT
                shot_name = shot_info.shot_name
                
                final_path = (
                    f"{shot_root}/{shot_name}/pla/"
                    f"{shot_name}_pla_rawPlate_v001/main_ACEScg/"
                    f"{shot_name}_pla_rawPlate_v001_main_ACEScg.####.exr"
                )
                
                metadata['exr_file_path'] = final_path
                self.logger.debug(f"Setting EXR path: {final_path}")
            
            # Original Clip Location - source camera file (full path)
            if shot_info.source_raw_path:
                metadata['original_clip_location'] = str(shot_info.source_raw_path)
                self.logger.debug(f"Setting original clip: {shot_info.source_raw_path}")
            
            # Original Clip Name - just the filename (not full path)
            if shot_info.source_raw_path:
                original_filename = Path(shot_info.source_raw_path).name
                metadata['original_clip_name'] = original_filename
                self.logger.debug(f"Setting original clip name: {original_filename}")
            
            # Proxy Movie File Path
            if shot_info.output_proxy_path:
                # Build the final proxy path
                shot_root = PipelineConfig.SHOT_TREE_ROOT
                shot_name = shot_info.shot_name
                
                proxy_path = (
                    f"{shot_root}/{shot_name}/pla/"
                    f"{shot_name}_pla_rawPlate_v001/"
                    f"{shot_name}_pla_rawPlate_v001_proxy_sRGB.mp4"
                )
                
                metadata['proxy_movie_file_path'] = proxy_path
                self.logger.debug(f"Setting proxy path: {proxy_path}")
            
            # Bit Depth - dropdown (static value)
            metadata['bit_depth'] = "16 Bit (Half Float)"
            
            # Working Colorspace - dropdown (static value)
            metadata['working_colorspace'] = "ACEScg"
            
            # Source Colorspace - dropdown (static value)
            metadata['source_colorspace'] = "SLog3"
            
            # Resolution - hardcoded value
            metadata['resolution'] = "3840x2160"
            self.logger.debug("Setting resolution: 3840x2160")
            
            # FPS - hardcoded value
            metadata['fps'] = 23.976
            self.logger.debug("Setting FPS: 23.976")
            
            # Turnover Date - set to today's date
            from datetime import datetime
            today = datetime.now().strftime("%m/%d/%y")  # Format: MM/DD/YY (e.g., 12/17/24)
            metadata['turnover_date'] = today
            self.logger.debug(f"Setting turnover date: {today}")
            
            # Element Name - the processed EXR filename pattern
            shot_name = shot_info.shot_name
            element_name = f"{shot_name}_pla_rawPlate_v001_main_ACEScg"
            metadata['element_name'] = element_name
            self.logger.debug(f"Setting element name: {element_name}")
            
            # EXR Folder Size - calculate total size of all EXR files
            if shot_info.output_plates_path:
                try:
                    # Build path to the EXR folder
                    shot_root = PipelineConfig.SHOT_TREE_ROOT
                    shot_name = shot_info.shot_name
                    
                    exr_folder = Path(
                        f"{shot_root}/{shot_name}/pla/"
                        f"{shot_name}_pla_rawPlate_v001/main_ACEScg/"
                    )
                    
                    # Calculate total size of all EXR files
                    if exr_folder.exists():
                        total_bytes = 0
                        for exr_file in exr_folder.glob("*.exr"):
                            if exr_file.is_file():
                                total_bytes += exr_file.stat().st_size
                        
                        # Convert to GB and MB
                        total_gb = total_bytes / (1024 ** 3)  # Convert to GB
                        remaining_bytes = total_bytes % (1024 ** 3)
                        remaining_mb = remaining_bytes / (1024 ** 2)  # Remaining as MB
                        
                        # Format as "##GB ##MB"
                        size_string = f"{int(total_gb)}GB {int(remaining_mb)}MB"
                        metadata['exr_folder_size'] = size_string
                        self.logger.debug(f"Setting EXR folder size: {size_string} ({total_bytes:,} bytes)")
                    else:
                        self.logger.warning(f"EXR folder not found: {exr_folder}")
                        metadata['exr_folder_size'] = "0GB 0MB"
                        
                except Exception as e:
                    self.logger.warning(f"Could not calculate EXR folder size: {e}")
                    metadata['exr_folder_size'] = "Unknown"
            
            # Frame range information
            if shot_info.first_frame is not None:
                metadata['frame_in'] = shot_info.first_frame
            
            if shot_info.last_frame is not None:
                metadata['frame_out'] = shot_info.last_frame
            
            if shot_info.total_frames is not None:
                metadata['frame_count'] = shot_info.total_frames
            
            # Frame range string (e.g., "993-1059")
            if shot_info.frame_range:
                metadata['frame_range'] = shot_info.frame_range
            
            # Editorial/Timecode information
            if hasattr(shot_info, 'editorial_info') and shot_info.editorial_info:
                if hasattr(shot_info.editorial_info, 'in_point') and shot_info.editorial_info.in_point:
                    metadata['source_tc_in'] = shot_info.editorial_info.in_point
                
                if hasattr(shot_info.editorial_info, 'out_point') and shot_info.editorial_info.out_point:
                    metadata['source_tc_out'] = shot_info.editorial_info.out_point
            
            # Update in Kitsu
            if metadata:
                gazu.shot.update_shot_data(shot, metadata)
                self.logger.info(f"Updated {len(metadata)} metadata fields")
                result.data['metadata_updated'] = list(metadata.keys())
            else:
                self.logger.warning("No metadata to update")
            
        except Exception as e:
            result.add_warning(f"Failed to update metadata: {str(e)}")
            self.logger.warning(f"Metadata update failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _create_output_files(
        self,
        shot: Dict[str, Any],
        shot_info: ShotInfo,
        task_name: str,
        result: ProcessingResult
    ) -> Dict[str, Any]:
        """
        Create output file records in Kitsu.
        
        Creates two output files:
        1. Proxy output file
        2. Plate output file (EXR sequence metadata)
        
        Args:
            shot: Shot dict from Kitsu
            shot_info: Shot information
            task_name: Task name for output files
            result: Result object
            
        Returns:
            Dict with 'proxy' and 'plate' output file records
        """
        output_files = {}
        proxy_metadata = {}
        plate_metadata = {}
        
        try:
            self.logger.info("🔍 Starting output file creation...")
            
            # Get task
            all_tasks = gazu.task.all_tasks_for_shot(shot)
            task = None
            for t in all_tasks:
                if t.get('task_type_name') == task_name:
                    task = t
                    break
            
            if not task:
                self.logger.warning(f"Task '{task_name}' not found, skipping output file creation")
                return output_files
            
            # Get task type
            task_type = gazu.task.get_task_type(task['task_type_id'])
            
            # Get output types
            output_types = gazu.files.all_output_types()
            plate_output_type = next((ot for ot in output_types if ot['name'] == 'Plate'), None)
            proxy_output_type = next((ot for ot in output_types if ot['name'] == 'Proxy'), None)
            
            if not plate_output_type or not proxy_output_type:
                self.logger.warning("Output types not found")
                return output_files
            
            self.logger.info(f"🔍 Proxy output type ID: {proxy_output_type['id']}")
            self.logger.info(f"🔍 Plate output type ID: {plate_output_type['id']}")
            
            # Build metadata BEFORE creating files
            if shot_info.output_proxy_path:
                proxy_metadata = {
                    "original_file": str(shot_info.source_raw_path) if shot_info.source_raw_path else "",
                    "color_space": "sRGB",
                    "source_color_space": "SLog3",
                    "resolution": "3840x2160",
                    "frame_range": shot_info.frame_range if shot_info.frame_range else "",
                    "fps": 23.976,
                    "processed_path": str(shot_info.output_proxy_path)
                }
            
            if shot_info.output_plates_path:
                shot_root = PipelineConfig.SHOT_TREE_ROOT
                shot_name = shot_info.shot_name
                
                exr_path = (
                    f"{shot_root}/{shot_name}/pla/"
                    f"{shot_name}_pla_rawPlate_v001/main_ACEScg/"
                    f"{shot_name}_pla_rawPlate_v001_main_ACEScg.####.exr"
                )
                
                exr_folder = Path(f"{shot_root}/{shot_name}/pla/{shot_name}_pla_rawPlate_v001/main_ACEScg/")
                folder_size = "Unknown"
                if exr_folder.exists():
                    total_bytes = sum(f.stat().st_size for f in exr_folder.glob("*.exr") if f.is_file())
                    total_gb = total_bytes / (1024 ** 3)
                    remaining_mb = (total_bytes % (1024 ** 3)) / (1024 ** 2)
                    folder_size = f"{int(total_gb)}GB {int(remaining_mb)}MB"
                
                plate_metadata = {
                    "original_file": str(shot_info.source_raw_path) if shot_info.source_raw_path else "",
                    "color_space": "ACEScg",
                    "source_color_space": "SLog3",
                    "resolution": "3840x2160",
                    "frame_range": shot_info.frame_range if shot_info.frame_range else "",
                    "fps": 23.976,
                    "bit_depth": "16 Bit (Half Float)",
                    "processed_path": exr_path,
                    "total_size": folder_size,
                    "frame_count": shot_info.total_frames if shot_info.total_frames else 0
                }
            
            # Try to create proxy output file (ignore errors)
            if shot_info.output_proxy_path:
                self.logger.info("🔍 Creating proxy output file...")
                try:
                    gazu.files.new_entity_output_file(
                        shot, proxy_output_type, task_type, "",
                        representation="mov", nb_elements=1
                    )
                    self.logger.info("✅ Proxy output file create call completed")
                except Exception as e:
                    self.logger.info(f"⚠️ Proxy creation returned error (file may still be created): {e}")
            
            # Try to create plate output file (ignore errors)
            if shot_info.output_plates_path:
                self.logger.info("🔍 Creating plate output file...")
                try:
                    gazu.files.new_entity_output_file(
                        shot, plate_output_type, task_type, "",
                        representation="exr",
                        nb_elements=shot_info.total_frames if shot_info.total_frames else 1
                    )
                    self.logger.info("✅ Plate output file create call completed")
                except Exception as e:
                    self.logger.info(f"⚠️ Plate creation returned error (file may still be created): {e}")
            
            # NOW fetch all output files that exist (wait 3 seconds for DB sync)
            self.logger.info("🔍 Waiting 3 seconds for database sync...")
            time.sleep(3)
            
            self.logger.info("🔍 Fetching all output files for shot...")
            all_output_files = gazu.files.all_output_files_for_entity(shot)
            
            self.logger.info(f"🔍 Found {len(all_output_files)} total output files")
            
            # Find proxy and plate files by output_type_id and update metadata
            for of in all_output_files:
                output_type_id = of.get('output_type_id', '')
                output_type_name = of.get('output_type_name', 'Unknown')
                file_id = of.get('id', 'no-id')
                
                self.logger.info(f"🔍 Found output file: {output_type_name} (type_id: {output_type_id}) - {file_id}")
                
                # Match by output_type_id instead of output_type_name
                if output_type_id == proxy_output_type['id'] and 'proxy' not in output_files:
                    # Update metadata
                    try:
                        updated_file = gazu.files.update_output_file(of, {"data": proxy_metadata})
                        # Refetch to get the updated data
                        output_files['proxy'] = gazu.files.get_output_file(of['id'])
                        self.logger.info("✅ Updated and refetched proxy metadata")
                    except Exception as e:
                        output_files['proxy'] = of
                        self.logger.warning(f"Could not update proxy metadata: {e}")
                    self.logger.info(f"✅ Using proxy output file: {of['id']}")
                
                elif output_type_id == plate_output_type['id'] and 'plate' not in output_files:
                    # Update metadata
                    try:
                        updated_file = gazu.files.update_output_file(of, {"data": plate_metadata})
                        # Refetch to get the updated data
                        output_files['plate'] = gazu.files.get_output_file(of['id'])
                        self.logger.info("✅ Updated and refetched plate metadata")
                    except Exception as e:
                        output_files['plate'] = of
                        self.logger.warning(f"Could not update plate metadata: {e}")
                    self.logger.info(f"✅ Using plate output file: {of['id']}")
            
            self.logger.info(f"🔍 Final output_files: {list(output_files.keys())}")
            
        except Exception as e:
            self.logger.warning(f"Output file creation failed: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return output_files
    
    def _upload_proxy(
        self,
        shot: Dict[str, Any],
        shot_info: ShotInfo,
        task_name: str,
        output_files: Dict[str, Any],
        result: ProcessingResult
    ):
        """
        Upload proxy MP4 file to specified task in Kitsu using publish_preview.
        
        Args:
            shot: Shot dict from Kitsu
            shot_info: Shot information with output_proxy_path set
            task_name: Name of task to upload to (default: "Prep & Unwarp")
            output_files: Dict with output file records (proxy and plate)
            result: Result object
        """
        try:
            self.logger.info("🔍 Starting proxy upload...")
            self.logger.info(f"🔍 output_files received: {list(output_files.keys())}")
            
            # Validate proxy path exists
            if not shot_info.output_proxy_path:
                self.logger.warning("No proxy path specified, skipping upload")
                return
            
            proxy_path = Path(shot_info.output_proxy_path)
            
            if not proxy_path.exists():
                result.add_warning(f"Proxy file not found: {proxy_path}")
                self.logger.warning(f"Proxy file not found: {proxy_path}")
                return
            
            self.logger.info(f"Uploading proxy: {proxy_path.name}")
            
            # Get all tasks for this shot
            all_tasks = gazu.task.all_tasks_for_shot(shot)
            
            # Find the task by name
            task = None
            for t in all_tasks:
                if t.get('task_type_name') == task_name:
                    task = t
                    break
            
            if not task:
                result.add_warning(f"Task '{task_name}' not found for this shot")
                self.logger.warning(f"Task '{task_name}' not found, skipping proxy upload")
                return
            
            self.logger.debug(f"Found task: {task_name}")
            
            # Build comment with links to output file viewer
            comment_text = f"**{shot_info.shot_name}** - Plate v001 processed from camera raw"
            
            self.logger.info(f"🔍 Building comment... output_files has {len(output_files)} items")
            
            # Get viewer URL (localhost for now - change this when deployed)
            viewer_base_url = "http://localhost:5000"
            
            # Add output file links
            if output_files:
                self.logger.info("🔍 output_files is NOT empty, adding viewer links...")
                
                comment_text += f"\n\n**Output Files:**"
                
                # Add proxy link
                if 'proxy' in output_files:
                    proxy_file = output_files['proxy']
                    proxy_id = proxy_file['id']
                    proxy_viewer_url = f"{viewer_base_url}/output-file/{proxy_id}"
                    comment_text += f"\n• [View Proxy Metadata]({proxy_viewer_url})"
                    self.logger.info(f"✅ Added proxy viewer link: {proxy_viewer_url}")
                
                # Add plate link
                if 'plate' in output_files:
                    plate_file = output_files['plate']
                    plate_id = plate_file['id']
                    plate_viewer_url = f"{viewer_base_url}/output-file/{plate_id}"
                    
                    # Get quick summary from metadata
                    plate_data = plate_file.get('data') or {}
                    size = plate_data.get('total_size', 'Unknown')
                    frames = plate_data.get('frame_range', 'Unknown')
                    
                    comment_text += f"\n• [View Plate Metadata]({plate_viewer_url}) - {size} | {frames}"
                    self.logger.info(f"✅ Added plate viewer link: {plate_viewer_url}")
                
                # Build correct Kitsu shot URL
                kitsu_base_url = self.kitsu_host.replace('/api', '')
                project_id = shot.get('project_id')
                shot_id = shot.get('id')
                episode_id = shot.get('episode_id')
                
                if episode_id:
                    shot_url = f"{kitsu_base_url}/productions/{project_id}/episodes/{episode_id}/shots/{shot_id}/"
                else:
                    shot_url = f"{kitsu_base_url}/productions/{project_id}/shots/{shot_id}/"
                
                comment_text += f"\n\n[→ View Shot in Kitsu]({shot_url})"
                
                self.logger.info(f"✅ Added output file viewer links")
            else:
                self.logger.warning("⚠️ output_files is EMPTY!")
            
            self.logger.info(f"🔍 FINAL COMMENT TEXT:\n{comment_text}")
            
            # Get "Waiting for Approval" status
            try:
                wfa_status = gazu.task.get_task_status_by_short_name("wfa")
            except:
                # If "wfa" doesn't exist, use current task status
                wfa_status = task.get('task_status_id')
                self.logger.debug("Using default task status (wfa not found)")
            
            # Publish preview with comment
            self.logger.info(f"Publishing preview with {proxy_path.stat().st_size / (1024*1024):.2f}MB...")
            
            comment, preview = gazu.task.publish_preview(
                task,
                wfa_status,
                comment=comment_text,
                preview_file_path=str(proxy_path)
            )
            
            self.logger.info(f"✅ Preview published! Comment ID: {comment.get('id')}")
            self.logger.info(f"✅ Uploaded proxy to Kitsu: {proxy_path.name}")
            result.data['proxy_uploaded'] = True
            result.data['proxy_file'] = str(proxy_path)
            result.data['comment_id'] = comment.get('id')
            result.data['preview_id'] = preview.get('id')
            
        except Exception as e:
            result.add_warning(f"Failed to upload proxy: {str(e)}")
            self.logger.warning(f"Proxy upload failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def validate_inputs(self, shot_info: ShotInfo, result: ProcessingResult) -> bool:
        """Validate inputs before processing."""
        if not super().validate_inputs(shot_info, result):
            return False
        
        if not self.kitsu_host:
            result.add_error("Kitsu host not configured")
            return False
        
        if not shot_info.shot_name:
            result.add_error("Shot name not provided in ShotInfo")
            return False
        
        if not shot_info.sequence:
            result.add_error("Sequence not provided in ShotInfo")
            return False
        
        return True


class KitsuQueryStage(PipelineStage):
    """
    Query information from Kitsu.
    
    Can be used to fetch project, sequence, or shot information
    before processing.
    """
    
    def __init__(
        self,
        kitsu_host: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.kitsu_host = kitsu_host or KitsuConfig.KITSU_HOST
        self.email = email or KitsuConfig.KITSU_EMAIL
        self.password = password or KitsuConfig.KITSU_PASSWORD
        self.authenticated = False
    
    def process(self, shot_info: ShotInfo, result: ProcessingResult, **kwargs):
        """
        Query Kitsu for information.
        
        Args:
            shot_info: Shot information (may be incomplete)
            result: Result object
            **kwargs: Query parameters
                - query_type: 'project', 'shot', 'output_types'
                - project_name: Project name to query
        """
        query_type = kwargs.get('query_type', 'shot')
        
        # Authenticate first
        if not self._authenticate(result):
            return
        
        if query_type == 'project':
            self._query_project(kwargs.get('project_name'), result)
        elif query_type == 'shot':
            self._query_shot(shot_info, kwargs.get('project_name'), result)
        elif query_type == 'output_types':
            self._query_output_types(result)
    
    def _authenticate(self, result: ProcessingResult) -> bool:
        """Authenticate with Kitsu."""
        if self.authenticated:
            return True
        
        try:
            gazu.set_host(self.kitsu_host)
            gazu.log_in(self.email, self.password)
            self.authenticated = True
            self.logger.info("Successfully authenticated with Kitsu")
            return True
        except Exception as e:
            result.add_error(f"Kitsu authentication failed: {str(e)}")
            return False
    
    def _query_project(self, project_name: str, result: ProcessingResult):
        """Query project information."""
        try:
            project = gazu.project.get_project_by_name(project_name)
            result.data['project_info'] = {
                'id': project['id'],
                'name': project['name'],
                'code': project.get('code'),
                'exists': True
            }
            self.logger.info(f"Found project: {project_name}")
        except Exception as e:
            result.data['project_info'] = {'exists': False}
            result.add_warning(f"Project not found: {project_name}")
    
    def _query_shot(self, shot_info: ShotInfo, project_name: str, result: ProcessingResult):
        """Query shot information."""
        try:
            project = gazu.project.get_project_by_name(project_name)
            shot = gazu.shot.get_shot_by_name(project, shot_info.shot_name)
            
            result.data['shot_info'] = {
                'id': shot['id'],
                'name': shot['name'],
                'sequence': shot.get('sequence_name'),
                'exists': True,
                'data': shot.get('data', {})
            }
            self.logger.info(f"Found shot: {shot_info.shot_name}")
        except Exception as e:
            result.data['shot_info'] = {'exists': False}
            result.add_warning(f"Shot not found: {shot_info.shot_name}")
    
    def _query_output_types(self, result: ProcessingResult):
        """Query available output types."""
        try:
            output_types = gazu.files.all_output_types()
            result.data['output_types'] = [
                {'id': ot['id'], 'name': ot['name'], 'short_name': ot['short_name']}
                for ot in output_types
            ]
            self.logger.info(f"Found {len(output_types)} output types")
        except Exception as e:
            result.add_error(f"Failed to query output types: {str(e)}")
