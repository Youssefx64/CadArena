"""
Furniture specification model.

This module defines the FurnitureSpec class for representing furniture
items with dimensions and clearance requirements.
"""

class FurnitureSpec:
    """
    Specification for a furniture item.
    
    Attributes:
        name: Furniture item name/type.
        width: Furniture width in meters.
        depth: Furniture depth in meters.
        clearance: Required clearance space around furniture in meters.
    """

    def __init__(self, name: str, width: float, depth: float, clearance: float):
        """
        Initialize furniture specification.
        
        Args:
            name: Furniture item name/type.
            width: Furniture width in meters.
            depth: Furniture depth in meters.
            clearance: Required clearance space in meters.
        """
        self.name = name
        self.width = width
        self.depth = depth
        self.clearance = clearance
