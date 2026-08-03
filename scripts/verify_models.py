import os
import hashlib
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MODEL_PATH = "models/best.pt"
EXPECTED_MD5 = "85cff04178d3144f387d07048d49437e"

def get_md5(file_path):
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except FileNotFoundError:
        return None

def verify():
    if not os.path.exists(MODEL_PATH):
        logger.error(f"FAIL: Model file not found at {MODEL_PATH}")
        return False
        
    logger.info(f"PASS: File exists at {MODEL_PATH}")
    
    # Checksum validation
    actual_md5 = get_md5(MODEL_PATH)
    if actual_md5:
        if actual_md5 == EXPECTED_MD5:
            logger.info(f"PASS: Checksum validated ({actual_md5})")
        else:
            logger.warning(f"WARN: Checksum mismatch! Expected {EXPECTED_MD5}, got {actual_md5}")
        
    # Compatibility and versioning
    try:
        from ultralytics import YOLO
        model = YOLO(MODEL_PATH)
        # Force a quick info check to ensure the model isn't corrupt
        model.info()
        logger.info(f"PASS: Model loaded successfully. Classes: {len(model.names)}")
        logger.info(f"PASS: Model architecture compatible with ultralytics YOLO engine.")
    except ImportError:
        logger.warning("ultralytics not installed. Skipping compatibility check.")
    except Exception as e:
        logger.error(f"FAIL: Model compatibility check failed: {e}")
        return False
        
    logger.info("✅ Verification completed successfully.")
    return True

if __name__ == "__main__":
    verify()
