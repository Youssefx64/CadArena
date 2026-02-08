"""
Configuration constants for the planner agent.

This module contains configuration values used by the room placement planner,
including maximum placement attempts and minimum spacing requirements.
"""


class PlannerConfig:
    """
    Configuration class for planner agent behavior.
    
    Attributes:
        MAX_PLACEMENT_TRIES: Maximum number of placement attempts before giving up.
        MIN_SPACING: Minimum spacing (in meters) required between rooms.
    """
    MAX_PLACEMENT_TRIES = 100
    MIN_SPACING = 0.5
    