import subprocess
import cv2
import numpy as np
import time


class ADBController:
    """
    Interfaces with BlueStacks / Android Emulator via ADB.
    Allows TITAN to capture the screen and inject touch events.
    """

    def __init__(self, device_id="127.0.0.1:5555"):
        self.device_id = device_id
        # Ensure ADB is connected
        self._connect()

    def _connect(self):
        try:
            subprocess.run(
                ["adb", "connect", self.device_id], capture_output=True, check=True
            )
            print(f"[ADB] Connected to {self.device_id}")
        except Exception as e:
            print(
                f"[ADB] Warning: Could not connect to {self.device_id}. Is ADB in PATH?"
            )

    def ping(self):
        """Check if the ADB connection is alive."""
        try:
            result = subprocess.run(
                ["adb", "-s", self.device_id, "shell", "echo", "ok"],
                capture_output=True,
                timeout=3,
            )
            return result.returncode == 0
        except Exception:
            return False

    def reconnect(self, max_retries=3):
        """Attempt to reconnect to the emulator."""
        for attempt in range(max_retries):
            print(f"[ADB] Reconnect attempt {attempt + 1}/{max_retries}...")
            try:
                # Kill and restart ADB server
                subprocess.run(["adb", "kill-server"], capture_output=True, timeout=5)
                time.sleep(1)
                subprocess.run(["adb", "start-server"], capture_output=True, timeout=5)
                time.sleep(2)
                self._connect()

                if self.ping():
                    print("[ADB] Reconnected successfully!")
                    return True
            except Exception as e:
                print(f"[ADB] Reconnect failed: {e}")

            time.sleep(2)

        print("[ADB] All reconnect attempts failed.")
        return False

    def capture_screen(self):
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
                print(f"[ADB] capture_screen returned no data. stderr: {result.stderr}")
                return None

            # Decode bytes to OpenCV format
            image_array = np.frombuffer(image_bytes, dtype=np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if frame is not None:
                # Resize to standard TITAN resolution if necessary
                return cv2.resize(frame, (720, 1280))
            return None
        except Exception as e:
            print(f"[ADB] Capture Error: {e}")
            return None

    def tap(self, x, y):
        """Send a tap event to specific coordinates."""
        try:
            subprocess.run(
                [
                    "adb",
                    "-s",
                    self.device_id,
                    "shell",
                    "input",
                    "tap",
                    str(int(x)),
                    str(int(y)),
                ],
                capture_output=True,
                check=False,
            )
        except Exception as e:
            print(f"[ADB] Tap failed at ({x}, {y}): {e}")

    def swipe(self, x1, y1, x2, y2, duration_ms=200):
        """
        Send a swipe (drag) event. Used to drag cards from the hand onto the battlefield.
        """
        try:
            subprocess.run(
                [
                    "adb",
                    "-s",
                    self.device_id,
                    "shell",
                    "input",
                    "swipe",
                    str(int(x1)),
                    str(int(y1)),
                    str(int(x2)),
                    str(int(y2)),
                    str(int(duration_ms)),
                ],
                capture_output=True,
                check=False,
            )
        except Exception as e:
            print(f"[ADB] Swipe failed from ({x1}, {y1}) to ({x2}, {y2}): {e}")

    def play_card(self, card_index, target_x, target_y):
        """
        Executes a card play action.
        card_index: 0 to 3 (which card slot in the hand)
        target_x, target_y: Drop coordinates
        """
        # Hand coordinates based on 720x1280 screen
        hand_y = 1150
        # The hand in Clash Royale is offset to the right because of the 'Next' card
        card_x_positions = [240, 370, 500, 630]

        if 0 <= card_index < 4:
            start_x = card_x_positions[card_index]
            # Use tap to select, then tap to place (much more reliable than swipe)
            self.tap(start_x, hand_y)
            time.sleep(0.1)
            self.tap(target_x, target_y)
            print(f"[ADB] Played card {card_index} at ({target_x}, {target_y})")
