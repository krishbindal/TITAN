import os
import sys
import time

def verify():
    print("1. Verify project builds (py_compile)... ", end="")
    if os.system("python -m py_compile play_live.py") == 0:
        print("OK")
    else:
        print("FAIL")
        sys.exit(1)
        
    print("2. Verify imports... ", end="")
    try:
        import play_live
        from core.analytics import MatchLogger, ReplayLogger, get_engine
        from configs.settings import ENABLE_ANALYTICS, ENABLE_DEBUG_OVERLAY
        print("OK")
    except Exception as e:
        print(f"FAIL ({e})")
        sys.exit(1)
        
    print("3. Verify feature flags... ", end="")
    if ENABLE_ANALYTICS and ENABLE_DEBUG_OVERLAY:
        print("OK")
    else:
        print("FAIL (Flags not enabled)")
        sys.exit(1)
        
    print("4. Verify analytics folders exist... ", end="")
    engine = get_engine()
    if os.path.exists("logs/analytics"):
        print("OK")
    else:
        print("FAIL")
        sys.exit(1)
        
    print("5. Verify replay folder exists... ", end="")
    if os.path.exists("replays"):
        print("OK")
    else:
        print("FAIL")
        sys.exit(1)
        
    print("6. Verify logger starts correctly... ", end="")
    try:
        session_id = int(time.time())
        match_logger = MatchLogger(engine, session_id)
        match_logger.start_match()
        print("OK")
    except Exception as e:
        print(f"FAIL ({e})")
        sys.exit(1)
        
    print("7. Verify background analytics thread starts... ", end="")
    if engine.worker.is_alive():
        print("OK")
    else:
        print("FAIL")
        sys.exit(1)
        
    print("8. Verify replay writer initializes correctly... ", end="")
    try:
        replay = ReplayLogger(session_id)
        if replay.worker.is_alive():
            print("OK")
        else:
            print("FAIL")
            sys.exit(1)
    except Exception as e:
        print(f"FAIL ({e})")
        sys.exit(1)
        
    print("9. Verify debug overlay configuration... ", end="")
    try:
        from vision.visualizer import Visualizer
        import numpy as np
        vis = Visualizer()
        frame = np.zeros((1280, 720, 3), dtype=np.uint8)
        # Mock telemetry
        tel = {"action": "WAIT", "elixir_advantage": 1.0, "enemy_elixir": 2.0, "predicted_deck": []}
        vis.draw(frame, [], telemetry=tel)
        print("OK")
    except Exception as e:
        print(f"FAIL ({e})")
        sys.exit(1)
        
    print("10. Verify ADB device is online... ", end="")
    import subprocess
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    if "device\n" in result.stdout or "\tdevice" in result.stdout:
        print("OK")
    else:
        print("FAIL (Device offline or not attached)")
        sys.exit(1)

    print("\nALL PRE-CHECKS PASSED.")

if __name__ == "__main__":
    verify()
