from abc import ABC, abstractmethod


class Constraint(ABC):
    """
    Base class for all constraints.
    """

    @abstractmethod
    def is_valid(self, *args, **kwargs) -> bool:
        pass
