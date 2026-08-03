import subprocess
import cv2
import numpy as np
from typing import Optional
import logging

from capture.base_capture import BaseCapture

logger = logging.getLogger(__name__)

class AdbCapture(BaseCapture):
    """
    Captures the screen using adb exec-out screencap.
    This is the fallback capturing method, which is reliable but slow (100-200ms per frame).
    """

    def __init__(self, device_id: str = "127.0.0.1:5555"):
        self.device_id = device_id
        
    def connect(self) -> bool:
        """
        In ADB's case, connection is usually handled by ADBController,
        but we verify we can reach the device here.
        """
        try:
            result = subprocess.run(
                ["adb", "-s", self.device_id, "shell", "echo", "ok"],
                capture_output=True,
                timeout=3,
            )
            if result.returncode == 0:
                logger.info(f"[AdbCapture] Verified connection to {self.device_id}")
                return True
            else:
                logger.warning(f"[AdbCapture] Ping failed to {self.device_id}")
                return False
        except Exception as e:
            logger.error(f"[AdbCapture] Connection error: {e}")
            return False

    def get_frame(self) -> Optional[np.ndarray]:
        """
        Captures the screen using ADB.
        Returns a BGR numpy array (OpenCV format) or None if failed.
        """
        try:
            # Fast raw screen capture with timeout to prevent hanging
            result = subprocess.run(
                ["adb", "-s", self.device_id, "exec-out", "screencap", "-p"],
                capture_output=True,
                timeout=2.0
            )
            image_bytes = result.stdout

            if not image_bytes:
                logger.warning(f"[AdbCapture] capture_screen returned no data. stderr: {result.stderr.decode('utf-8', errors='ignore')}")
                return None

            # Decode bytes to OpenCV format
            image_array = np.frombuffer(image_bytes, dtype=np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if frame is not None:
                # Resize to standard TITAN resolution if necessary
                return cv2.resize(frame, (720, 1280))
            return None
        except Exception as e:
            logger.error(f"[AdbCapture] Capture Error: {e}")
            return None
