import cv2
import pytesseract
from core.adb_controller import ADBController

adb = ADBController()
frame = adb.capture_screen()
cv2.imwrite("test_screen.png", frame)

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
print("OCR FULL SCREEN:")
print(pytesseract.image_to_string(frame))
