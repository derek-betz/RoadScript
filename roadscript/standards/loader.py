"""
Standards Loader Module

Loads and provides access to the IDM standards JSON "Source of Truth".
Ensures standards are loaded once and cached for performance.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class StandardsLoader:
    """
    Loads and caches IDM standards from JSON.
    
    Provides thread-safe access to the standards "Source of Truth"
    for all calculation modules.
    """
    
    _instance: Optional['StandardsLoader'] = None
    _standards: Optional[Dict[str, Any]] = None
    
    def __new__(cls):
        """Singleton pattern to ensure standards are loaded only once."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the standards loader."""
        if self._standards is None:
            self._load_standards()
    
    def _load_standards(self) -> None:
        """Load standards from the JSON file in the data layer."""
        data_path = Path(__file__).resolve().parents[1] / "data" / "idm_standards.json"
        legacy_path = Path(__file__).parent / "idm_standards.json"
        standards_path = data_path if data_path.exists() else legacy_path

        if not standards_path.exists():
            raise FileNotFoundError(
                f"IDM standards file not found at {data_path}. "
                "This file is required for the system to operate."
            )
        
        try:
            with open(standards_path, 'r', encoding='utf-8') as f:
                self._standards = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON in IDM standards file: {e}. "
                "The standards file must be valid JSON."
            ) from e
    
    def get_standards(self) -> Dict[str, Any]:
        """
        Get the complete standards dictionary.
        
        Returns:
            Dict containing all IDM standards
        """
        if self._standards is None:
            self._load_standards()
        return self._standards
    
    def get_clear_zone_standards(self) -> Dict[str, Any]:
        """
        Get clear zone standards.
        
        Returns:
            Dict containing clear zone standards
        """
        return self.get_standards().get("clear_zones", {})
    
    def get_geometry_standards(self) -> Dict[str, Any]:
        """
        Get geometry standards.
        
        Returns:
            Dict containing geometry standards
        """
        return self.get_standards().get("geometry", {})
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """
        Get validation rules for all calculation types.
        
        Returns:
            Dict containing validation rules
        """
        return self.get_standards().get("validation_rules", {})
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get standards metadata (version, authority, etc.).
        
        Returns:
            Dict containing metadata
        """
        return self.get_standards().get("metadata", {})
