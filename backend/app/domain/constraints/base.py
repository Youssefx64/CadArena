"""
Base constraint interface.

This module defines the abstract base class for all constraint validators
used in room placement planning.
"""

from abc import ABC, abstractmethod


class Constraint(ABC):
    """
    Abstract base class for all placement constraints.
    
    All constraint classes must implement the is_valid method to check
    whether a room placement satisfies the constraint.
    """

    @abstractmethod
    def is_valid(self, *args, **kwargs) -> bool:
        """
        Check if a room placement satisfies this constraint.
        
        Args:
            *args: Variable positional arguments (implementation-specific).
            **kwargs: Variable keyword arguments (implementation-specific).
        
        Returns:
            True if constraint is satisfied, False otherwise.
        """
        pass
