import os
import urllib.request
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODELS_DIR = "models"
MODEL_URL = "https://github.com/krishbindal/TITAN/releases/download/v1.0/best.pt"
MODEL_PATH = os.path.join(MODELS_DIR, "best.pt")

def download_model():
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
        
    if os.path.exists(MODEL_PATH):
        logger.info(f"Model already exists at {MODEL_PATH}")
        return
        
    logger.info(f"Downloading model from {MODEL_URL}...")
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        logger.info("Download complete.")
    except Exception as e:
        logger.error(f"Failed to download model: {e}")

if __name__ == "__main__":
    download_model()
