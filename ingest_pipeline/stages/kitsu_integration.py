"""
Stage for integrating with Kitsu asset management system.
Creates and updates shot and asset entries in Kitsu.
"""
import requests
from typing import Optional, Dict, Any

from .base import PipelineStage
from ..models import ProcessingResult, ShotInfo
from ..config import KitsuConfig


class KitsuIntegrationStage(PipelineStage):
    """
    Create and update assets in Kitsu.
    
    Registers plate sequences and associated metadata in the
    Kitsu production tracking system.
    """
    
    def __init__(
        self,
        kitsu_host: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Kitsu integration.
        
        Args:
            kitsu_host: Kitsu API host URL
            email: Login email
            password: Login password
        """
        super().__init__(**kwargs)
        self.kitsu_host = kitsu_host or KitsuConfig.KITSU_HOST
        self.email = email or KitsuConfig.KITSU_EMAIL
        self.password = password or KitsuConfig.KITSU_PASSWORD
        self.access_token = None
        self.session = requests.Session()
    
    def process(self, shot_info: ShotInfo, result: ProcessingResult, **kwargs):
        """
        Create or update Kitsu entries.
        
        Args:
            shot_info: Shot information
            result: Result object to populate
            **kwargs: Additional arguments
                - project_id: Kitsu project ID (required if not in kwargs)
                - asset_type: Type of asset (default: 'plate')
                - update_if_exists: Update existing entry (default: True)
        """
        if not self.validate_inputs(shot_info, result):
            return
        
        # Authenticate
        if not self._authenticate(result):
            return
        
        project_id = kwargs.get('project_id')
        if not project_id:
            result.add_error("Kitsu project_id not provided")
            return
        
        asset_type = kwargs.get('asset_type', 'plate')
        update_if_exists = kwargs.get('update_if_exists', True)
        
        # First, ensure the shot exists
        shot_id = self._get_or_create_shot(
            project_id=project_id,
            sequence=shot_info.sequence,
            shot=shot_info.shot,
            result=result
        )
        
        if not shot_id:
            return
        
        # Create or update the plate asset
        asset_id = self._create_or_update_asset(
            project_id=project_id,
            shot_id=shot_id,
            shot_info=shot_info,
            asset_type=asset_type,
            update_if_exists=update_if_exists,
            result=result
        )
        
        if asset_id:
            result.data['kitsu_shot_id'] = shot_id
            result.data['kitsu_asset_id'] = asset_id
            self.logger.info(f"Successfully registered in Kitsu: {shot_info.shot_name}")
    
    def _authenticate(self, result: ProcessingResult) -> bool:
        """
        Authenticate with Kitsu API.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.email or not self.password:
            result.add_error("Kitsu credentials not provided")
            return False
        
        try:
            # Placeholder - in production would call actual Kitsu API
            # auth_url = f"{self.kitsu_host}/auth/login"
            # response = self.session.post(
            #     auth_url,
            #     json={'email': self.email, 'password': self.password},
            #     timeout=KitsuConfig.CONNECTION_TIMEOUT
            # )
            # response.raise_for_status()
            # self.access_token = response.json()['access_token']
            # self.session.headers.update({'Authorization': f'Bearer {self.access_token}'})
            
            self.logger.info("Authenticated with Kitsu (placeholder)")
            result.add_warning("Kitsu authentication placeholder - not connected to real API")
            return True
            
        except requests.RequestException as e:
            result.add_error(f"Kitsu authentication failed: {str(e)}")
            return False
    
    def _get_or_create_shot(
        self,
        project_id: str,
        sequence: str,
        shot: str,
        result: ProcessingResult
    ) -> Optional[str]:
        """
        Get or create a shot in Kitsu.
        
        Returns:
            Shot ID if successful, None otherwise
        """
        try:
            # Placeholder - would call actual Kitsu API
            # First try to find existing shot
            # shots_url = f"{self.kitsu_host}/data/shots"
            # response = self.session.get(
            #     shots_url,
            #     params={'project_id': project_id, 'name': f"{sequence}{shot}"}
            # )
            # 
            # if response.status_code == 200 and response.json():
            #     return response.json()[0]['id']
            # 
            # # Create new shot
            # response = self.session.post(
            #     shots_url,
            #     json={
            #         'project_id': project_id,
            #         'sequence_name': sequence,
            #         'name': shot
            #     }
            # )
            # response.raise_for_status()
            # return response.json()['id']
            
            # Return placeholder ID
            shot_id = f"shot_{sequence}_{shot}_placeholder"
            self.logger.info(f"Got/created shot in Kitsu: {shot_id}")
            return shot_id
            
        except Exception as e:
            result.add_error(f"Failed to get/create shot in Kitsu: {str(e)}")
            return None
    
    def _create_or_update_asset(
        self,
        project_id: str,
        shot_id: str,
        shot_info: ShotInfo,
        asset_type: str,
        update_if_exists: bool,
        result: ProcessingResult
    ) -> Optional[str]:
        """
        Create or update asset in Kitsu.
        
        Returns:
            Asset ID if successful, None otherwise
        """
        try:
            # Build asset data
            asset_data = {
                'project_id': project_id,
                'entity_id': shot_id,
                'entity_type': 'Shot',
                'asset_type': asset_type,
                'name': f"{shot_info.shot_name}_plate",
                'data': {
                    'frame_range': shot_info.frame_range,
                    'first_frame': shot_info.first_frame,
                    'last_frame': shot_info.last_frame,
                    'total_frames': shot_info.total_frames,
                    'plates_path': str(shot_info.output_plates_path) if shot_info.output_plates_path else None,
                    'proxy_path': str(shot_info.output_proxy_path) if shot_info.output_proxy_path else None,
                    'editorial_in': shot_info.editorial_info.in_point,
                    'editorial_out': shot_info.editorial_info.out_point,
                    'source_file': str(shot_info.source_raw_path) if shot_info.source_raw_path else None,
                }
            }
            
            # Placeholder - would call actual Kitsu API
            # assets_url = f"{self.kitsu_host}/data/assets"
            # 
            # if update_if_exists:
            #     # Try to find existing asset
            #     response = self.session.get(
            #         assets_url,
            #         params={'entity_id': shot_id, 'asset_type': asset_type}
            #     )
            #     
            #     if response.status_code == 200 and response.json():
            #         # Update existing
            #         asset_id = response.json()[0]['id']
            #         response = self.session.put(
            #             f"{assets_url}/{asset_id}",
            #             json=asset_data
            #         )
            #         response.raise_for_status()
            #         return asset_id
            # 
            # # Create new asset
            # response = self.session.post(assets_url, json=asset_data)
            # response.raise_for_status()
            # return response.json()['id']
            
            # Return placeholder ID
            asset_id = f"asset_{shot_info.shot_name}_plate_placeholder"
            self.logger.info(f"Created/updated asset in Kitsu: {asset_id}")
            result.data['asset_data'] = asset_data
            return asset_id
            
        except Exception as e:
            result.add_error(f"Failed to create/update asset in Kitsu: {str(e)}")
            return None
    
    def validate_inputs(self, shot_info: ShotInfo, result: ProcessingResult) -> bool:
        """Validate inputs."""
        if not super().validate_inputs(shot_info, result):
            return False
        
        if not self.kitsu_host:
            result.add_error("Kitsu host not configured")
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
        self.access_token = None
        self.session = requests.Session()
    
    def process(self, shot_info: ShotInfo, result: ProcessingResult, **kwargs):
        """
        Query Kitsu for information.
        
        Args:
            shot_info: Shot information (may be incomplete)
            result: Result object
            **kwargs: Query parameters
                - query_type: 'project', 'sequence', 'shot', 'asset'
                - project_name: Project name to query
        """
        query_type = kwargs.get('query_type', 'shot')
        
        # Authenticate first
        if not self._authenticate(result):
            return
        
        if query_type == 'project':
            self._query_project(kwargs.get('project_name'), result)
        elif query_type == 'shot':
            self._query_shot(shot_info, result)
        
        # Add more query types as needed
    
    def _authenticate(self, result: ProcessingResult) -> bool:
        """Authenticate with Kitsu."""
        # Same as KitsuIntegrationStage._authenticate
        self.logger.info("Authenticated with Kitsu (placeholder)")
        result.add_warning("Kitsu query placeholder - not connected to real API")
        return True
    
    def _query_project(self, project_name: str, result: ProcessingResult):
        """Query project information."""
        # Placeholder
        result.data['project_info'] = {
            'name': project_name,
            'id': f"project_{project_name}_placeholder"
        }
    
    def _query_shot(self, shot_info: ShotInfo, result: ProcessingResult):
        """Query shot information."""
        # Placeholder
        result.data['shot_info'] = {
            'shot_name': shot_info.shot_name,
            'exists': False
        }
