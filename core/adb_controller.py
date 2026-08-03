import subprocess
import cv2
import numpy as np
import time


class ADBController:
    """
    Interfaces with BlueStacks / Android Emulator via ADB.
    Allows TITAN to capture the screen and inject touch events.
    """

    def __init__(self, device_id="127.0.0.1:5555", capture_backend=None):
        self.device_id = device_id
        self.capture_backend = capture_backend
        # Ensure ADB is connected
        self._connect()

    def _connect(self):
        try:
            subprocess.run(
                ["adb", "connect", self.device_id], capture_output=True, check=True
            )
            print(f"[ADB] Connected to {self.device_id}")
            self._init_scaling()
        except Exception:
            print(
                f"[ADB] Warning: Could not connect to {self.device_id}. Is ADB in PATH?"
            )
            self.scale_x = 1.0
            self.scale_y = 1.0

    def _init_scaling(self):
        self.scale_x = 1.0
        self.scale_y = 1.0
        try:
            result = subprocess.run(
                ["adb", "-s", self.device_id, "shell", "wm", "size"],
                capture_output=True, text=True, timeout=3
            )
            # Output format: "Physical size: 1080x1920"
            if "Physical size:" in result.stdout:
                dims = result.stdout.strip().split()[-1]
                native_w, native_h = map(int, dims.split('x'))
                self.scale_x = native_w / 720.0
                self.scale_y = native_h / 1280.0
                print(f"[ADB] Device native resolution: {native_w}x{native_h}. Scaling: X={self.scale_x:.2f}, Y={self.scale_y:.2f}")
        except Exception as e:
            print(f"[ADB] Could not determine native resolution, defaulting to 1:1. Error: {e}")

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
        Legacy wrapper for backward compatibility.
        Delegates to capture_backend.
        """
        if self.capture_backend:
            return self.capture_backend.get_frame()
        else:
            print("[ADB] Error: No capture backend provided.")
            return None


    def tap(self, x, y):
        """Send a tap event to specific coordinates, scaled to native resolution."""
        scaled_x = int(x * getattr(self, 'scale_x', 1.0))
        scaled_y = int(y * getattr(self, 'scale_y', 1.0))
        
        try:
            # Use a 50ms swipe in place to simulate a reliable tap. 
            # Instantaneous taps are often ignored by game engines like Unity/Clash Royale.
            subprocess.run(
                [
                    "adb",
                    "-s",
                    self.device_id,
                    "shell",
                    "input",
                    "swipe",
                    str(scaled_x),
                    str(scaled_y),
                    str(scaled_x),
                    str(scaled_y),
                    "50",
                ],
                capture_output=True,
                check=False,
            )
        except Exception as e:
            print(f"[ADB] Tap failed at ({scaled_x}, {scaled_y}): {e}")

    def swipe(self, x1, y1, x2, y2, duration_ms=200):
        """
        Send a swipe (drag) event. Used to drag cards from the hand onto the battlefield.
        Scaled to native resolution.
        """
        scaled_x1 = int(x1 * getattr(self, 'scale_x', 1.0))
        scaled_y1 = int(y1 * getattr(self, 'scale_y', 1.0))
        scaled_x2 = int(x2 * getattr(self, 'scale_x', 1.0))
        scaled_y2 = int(y2 * getattr(self, 'scale_y', 1.0))
        
        try:
            subprocess.run(
                [
                    "adb",
                    "-s",
                    self.device_id,
                    "shell",
                    "input",
                    "swipe",
                    str(scaled_x1),
                    str(scaled_y1),
                    str(scaled_x2),
                    str(scaled_y2),
                    str(int(duration_ms)),
                ],
                capture_output=True,
                check=False,
            )
        except Exception as e:
            print(f"[ADB] Swipe failed from ({scaled_x1}, {scaled_y1}) to ({scaled_x2}, {scaled_y2}): {e}")

    def play_card(self, card_index, target_x, target_y):
        """
        Executes a card play action with visual verification.
        card_index: 0 to 3 (which card slot in the hand)
        target_x, target_y: Drop coordinates
        """
        # Card coordinates perfectly centered for 720x1280
        hand_y = 1100
        card_x_positions = [215, 345, 475, 605]

        if 0 <= card_index < 4:
            start_x = card_x_positions[card_index]
            
            # Selection Verification Loop
            for attempt in range(2):
                self.tap(start_x, hand_y)
                
                # Check if card was actually selected
                if self.capture_backend:
                    frame = self.capture_backend.get_frame()
                    if frame is not None:
                        # Look at the space just ABOVE the unselected card.
                        # Unselected card top is Y=1020. Selected card top is Y=980.
                        # This ROI (Y=960:1000) is background when unselected, but filled with card art when selected.
                        roi = frame[960:1000, start_x-20:start_x+20]
                        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                        variance = np.var(gray)
                        
                        if variance > 200:
                            print(f"[ADB] Card {card_index} selection verified (variance: {variance:.1f}).")
                            break
                        else:
                            print(f"[ADB] Card {card_index} selection missed (variance: {variance:.1f}). Retrying tap {attempt+1}...")
                    else:
                        # Frame capture failed, proceed blindly
                        break
                else:
                    break

            # Deploy
            self.tap(target_x, target_y)
            print(f"[ADB] Played card {card_index} at ({target_x}, {target_y})")
