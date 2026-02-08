"""
Export request schema definitions.

This module defines request models for file export operations.
"""

from pydantic import BaseModel


class DxfDownloadRequest(BaseModel):
    """
    Request model for downloading a DXF file.
    
    Attributes:
        dxf_path: Path to the DXF file to download.
    """
    dxf_path: str
