"""
State Manager - Track extraction, transformation, and upload states

This module provides state management for the migration process,
allowing independent execution of extraction, transformation, and upload phases.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum


class PhaseStatus(Enum):
    """Status of a migration phase."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExtractionState:
    """State of an extraction operation."""
    source_type: str  # confluence or jira
    source_id: str  # space key or project key
    status: str
    extracted_at: Optional[str] = None
    output_path: Optional[str] = None
    item_count: int = 0
    error_message: Optional[str] = None


@dataclass
class TransformationState:
    """State of a transformation operation."""
    source_type: str
    source_id: str
    target_format: str  # markdown, html, etc.
    status: str
    transformed_at: Optional[str] = None
    input_path: Optional[str] = None
    output_path: Optional[str] = None
    item_count: int = 0
    error_message: Optional[str] = None


@dataclass
class UploadState:
    """State of an upload operation."""
    target_system: str  # wikijs, openproject, gitlab
    source_type: str
    source_id: str
    status: str
    uploaded_at: Optional[str] = None
    input_path: Optional[str] = None
    item_count: int = 0
    error_message: Optional[str] = None


class StateManager:
    """
    Manage state of migration phases.
    
    Tracks extraction, transformation, and upload states to enable
    independent execution of each phase.
    """
    
    def __init__(self, state_file: str = "data/state/migration_state.json"):
        """Initialize state manager."""
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """Load state from file."""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            'extractions': {},
            'transformations': {},
            'uploads': {},
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
        }
    
    def _save_state(self) -> None:
        """Save state to file."""
        self.state['metadata']['last_updated'] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    # Extraction state management
    
    def record_extraction_start(self, source_type: str, source_id: str, output_path: str) -> None:
        """Record that an extraction has started."""
        key = f"{source_type}:{source_id}"
        self.state['extractions'][key] = asdict(ExtractionState(
            source_type=source_type,
            source_id=source_id,
            status=PhaseStatus.IN_PROGRESS.value,
            output_path=output_path
        ))
        self._save_state()
    
    def record_extraction_complete(
        self, 
        source_type: str, 
        source_id: str, 
        item_count: int,
        output_path: str
    ) -> None:
        """Record that an extraction has completed."""
        key = f"{source_type}:{source_id}"
        self.state['extractions'][key] = asdict(ExtractionState(
            source_type=source_type,
            source_id=source_id,
            status=PhaseStatus.COMPLETED.value,
            extracted_at=datetime.now().isoformat(),
            output_path=output_path,
            item_count=item_count
        ))
        self._save_state()
    
    def record_extraction_failed(
        self, 
        source_type: str, 
        source_id: str, 
        error_message: str
    ) -> None:
        """Record that an extraction has failed."""
        key = f"{source_type}:{source_id}"
        if key in self.state['extractions']:
            self.state['extractions'][key]['status'] = PhaseStatus.FAILED.value
            self.state['extractions'][key]['error_message'] = error_message
        else:
            self.state['extractions'][key] = asdict(ExtractionState(
                source_type=source_type,
                source_id=source_id,
                status=PhaseStatus.FAILED.value,
                error_message=error_message
            ))
        self._save_state()
    
    def get_extraction_state(self, source_type: str, source_id: str) -> Optional[Dict[str, Any]]:
        """Get extraction state for a specific source."""
        key = f"{source_type}:{source_id}"
        return self.state['extractions'].get(key)
    
    def get_all_extractions(self) -> Dict[str, Any]:
        """Get all extraction states."""
        return self.state['extractions']
    
    def get_completed_extractions(self) -> List[Dict[str, Any]]:
        """Get all completed extractions."""
        return [
            state for state in self.state['extractions'].values()
            if state['status'] == PhaseStatus.COMPLETED.value
        ]
    
    # Transformation state management
    
    def record_transformation_start(
        self, 
        source_type: str, 
        source_id: str,
        target_format: str,
        input_path: str,
        output_path: str
    ) -> None:
        """Record that a transformation has started."""
        key = f"{source_type}:{source_id}:{target_format}"
        self.state['transformations'][key] = asdict(TransformationState(
            source_type=source_type,
            source_id=source_id,
            target_format=target_format,
            status=PhaseStatus.IN_PROGRESS.value,
            input_path=input_path,
            output_path=output_path
        ))
        self._save_state()
    
    def record_transformation_complete(
        self,
        source_type: str,
        source_id: str,
        target_format: str,
        item_count: int,
        output_path: str
    ) -> None:
        """Record that a transformation has completed."""
        key = f"{source_type}:{source_id}:{target_format}"
        self.state['transformations'][key] = asdict(TransformationState(
            source_type=source_type,
            source_id=source_id,
            target_format=target_format,
            status=PhaseStatus.COMPLETED.value,
            transformed_at=datetime.now().isoformat(),
            output_path=output_path,
            item_count=item_count
        ))
        self._save_state()
    
    def record_transformation_failed(
        self,
        source_type: str,
        source_id: str,
        target_format: str,
        error_message: str
    ) -> None:
        """Record that a transformation has failed."""
        key = f"{source_type}:{source_id}:{target_format}"
        if key in self.state['transformations']:
            self.state['transformations'][key]['status'] = PhaseStatus.FAILED.value
            self.state['transformations'][key]['error_message'] = error_message
        else:
            self.state['transformations'][key] = asdict(TransformationState(
                source_type=source_type,
                source_id=source_id,
                target_format=target_format,
                status=PhaseStatus.FAILED.value,
                error_message=error_message
            ))
        self._save_state()
    
    def get_transformation_state(
        self, 
        source_type: str, 
        source_id: str,
        target_format: str
    ) -> Optional[Dict[str, Any]]:
        """Get transformation state for a specific source."""
        key = f"{source_type}:{source_id}:{target_format}"
        return self.state['transformations'].get(key)
    
    def get_all_transformations(self) -> Dict[str, Any]:
        """Get all transformation states."""
        return self.state['transformations']
    
    def get_completed_transformations(self) -> List[Dict[str, Any]]:
        """Get all completed transformations."""
        return [
            state for state in self.state['transformations'].values()
            if state['status'] == PhaseStatus.COMPLETED.value
        ]
    
    # Upload state management
    
    def record_upload_start(
        self,
        target_system: str,
        source_type: str,
        source_id: str,
        input_path: str
    ) -> None:
        """Record that an upload has started."""
        key = f"{target_system}:{source_type}:{source_id}"
        self.state['uploads'][key] = asdict(UploadState(
            target_system=target_system,
            source_type=source_type,
            source_id=source_id,
            status=PhaseStatus.IN_PROGRESS.value,
            input_path=input_path
        ))
        self._save_state()
    
    def record_upload_complete(
        self,
        target_system: str,
        source_type: str,
        source_id: str,
        item_count: int
    ) -> None:
        """Record that an upload has completed."""
        key = f"{target_system}:{source_type}:{source_id}"
        if key in self.state['uploads']:
            self.state['uploads'][key]['status'] = PhaseStatus.COMPLETED.value
            self.state['uploads'][key]['uploaded_at'] = datetime.now().isoformat()
            self.state['uploads'][key]['item_count'] = item_count
        self._save_state()
    
    def record_upload_failed(
        self,
        target_system: str,
        source_type: str,
        source_id: str,
        error_message: str
    ) -> None:
        """Record that an upload has failed."""
        key = f"{target_system}:{source_type}:{source_id}"
        if key in self.state['uploads']:
            self.state['uploads'][key]['status'] = PhaseStatus.FAILED.value
            self.state['uploads'][key]['error_message'] = error_message
        else:
            self.state['uploads'][key] = asdict(UploadState(
                target_system=target_system,
                source_type=source_type,
                source_id=source_id,
                status=PhaseStatus.FAILED.value,
                error_message=error_message
            ))
        self._save_state()
    
    def get_upload_state(
        self,
        target_system: str,
        source_type: str,
        source_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get upload state for a specific source."""
        key = f"{target_system}:{source_type}:{source_id}"
        return self.state['uploads'].get(key)
    
    def get_all_uploads(self) -> Dict[str, Any]:
        """Get all upload states."""
        return self.state['uploads']
    
    def get_completed_uploads(self) -> List[Dict[str, Any]]:
        """Get all completed uploads."""
        return [
            state for state in self.state['uploads'].values()
            if state['status'] == PhaseStatus.COMPLETED.value
        ]
    
    # Pipeline status
    
    def get_pipeline_status(self, source_type: str, source_id: str) -> Dict[str, str]:
        """
        Get complete pipeline status for a source.
        
        Returns status of extraction, transformation, and upload phases.
        """
        ext_key = f"{source_type}:{source_id}"
        extraction_status = "not_started"
        if ext_key in self.state['extractions']:
            extraction_status = self.state['extractions'][ext_key]['status']
        
        # Find any transformations for this source
        transformation_status = "not_started"
        for key, trans in self.state['transformations'].items():
            if trans['source_type'] == source_type and trans['source_id'] == source_id:
                transformation_status = trans['status']
                break
        
        # Find any uploads for this source
        upload_status = "not_started"
        for key, upl in self.state['uploads'].items():
            if upl['source_type'] == source_type and upl['source_id'] == source_id:
                upload_status = upl['status']
                break
        
        return {
            'source_type': source_type,
            'source_id': source_id,
            'extraction': extraction_status,
            'transformation': transformation_status,
            'upload': upload_status
        }
    
    def get_all_pipeline_statuses(self) -> List[Dict[str, str]]:
        """Get pipeline status for all sources."""
        sources = set()
        
        # Collect all unique sources
        for key in self.state['extractions'].keys():
            source_type, source_id = key.split(':', 1)
            sources.add((source_type, source_id))
        
        for key in self.state['transformations'].keys():
            parts = key.split(':')
            if len(parts) >= 2:
                source_type, source_id = parts[0], parts[1]
                sources.add((source_type, source_id))
        
        for key in self.state['uploads'].keys():
            parts = key.split(':')
            if len(parts) >= 3:
                source_type, source_id = parts[1], parts[2]
                sources.add((source_type, source_id))
        
        return [
            self.get_pipeline_status(source_type, source_id)
            for source_type, source_id in sorted(sources)
        ]
    
    def clear_state(self, source_type: Optional[str] = None, source_id: Optional[str] = None) -> None:
        """
        Clear state for specific source or all sources.
        
        Args:
            source_type: If provided, only clear this source type
            source_id: If provided (with source_type), only clear this specific source
        """
        if source_type and source_id:
            # Clear specific source
            key_prefix = f"{source_type}:{source_id}"
            self.state['extractions'] = {
                k: v for k, v in self.state['extractions'].items()
                if not k.startswith(key_prefix)
            }
            self.state['transformations'] = {
                k: v for k, v in self.state['transformations'].items()
                if not k.startswith(key_prefix)
            }
            self.state['uploads'] = {
                k: v for k, v in self.state['uploads'].items()
                if key_prefix not in k
            }
        elif source_type:
            # Clear all sources of this type
            key_prefix = f"{source_type}:"
            self.state['extractions'] = {
                k: v for k, v in self.state['extractions'].items()
                if not k.startswith(key_prefix)
            }
            self.state['transformations'] = {
                k: v for k, v in self.state['transformations'].items()
                if not k.startswith(key_prefix)
            }
            self.state['uploads'] = {
                k: v for k, v in self.state['uploads'].items()
                if not k.split(':')[1] == source_type
            }
        else:
            # Clear everything
            self.state['extractions'] = {}
            self.state['transformations'] = {}
            self.state['uploads'] = {}
        
        self._save_state()
