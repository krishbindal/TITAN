from abc import ABC, abstractmethod
import numpy as np
from typing import Optional

class BaseCapture(ABC):
    """
    Abstract interface for screen capture implementations.
    Decouples the capture mechanism from the vision pipeline.
    """

    @abstractmethod
    def connect(self) -> bool:
        """Initialize the connection to the capture source."""
        pass

    @abstractmethod
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Capture the screen.
        Returns:
            A BGR numpy array (OpenCV format) of the screen, or None if failed.
        """
        pass
