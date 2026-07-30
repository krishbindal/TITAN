import time
from core.adb_controller import ADBController

adb = ADBController()

print("Tapping all over the bottom...")
for y in range(1000, 1250, 50):
    adb.tap(360, y)
    time.sleep(0.5)

print("Tapping Cards tab...")
adb.tap(250, 1200)
time.sleep(2)
print("Done.")
