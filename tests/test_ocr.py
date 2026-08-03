import cv2
import time
from core.adb_controller import ADBController
from capture.adb_capture import AdbCapture
from vision.collection_reader import CollectionReader

if __name__ == '__main__':
    capture = AdbCapture()
    adb = ADBController(capture_backend=capture)
    
    print("Tapping (430, 650) to open popup...")
    adb.tap(430, 650)
    time.sleep(1.0)
    
    print("Capturing screen...")
    frame = adb.capture_screen()
    cv2.imwrite("popup_test.png", frame)
    
    reader = CollectionReader()
    text = reader.read_card_popup_name(frame, 430, 650)
    print(f"OCR Result: {text}")
    
    # Tap outside to close
    adb.tap(10, 600)
