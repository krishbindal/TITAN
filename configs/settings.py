# === Model ===
MODEL_PATH = "models/best.onnx"

# === Detection ===
CONFIDENCE_THRESHOLD = 0.55

# === Screen ===
SCREEN_WIDTH = 720
SCREEN_HEIGHT = 1280

# === Screen Regions ===
GAMEPLAY_ZONE_BOTTOM = 950
CARD_ZONE_TOP = 950

# === Tracking ===
TRACK_DISTANCE = 50
MAX_MISSED_FRAMES = 10
CONFIRM_FRAMES = 3

# === Data Pipeline ===
FRAME_EXTRACT_INTERVAL = 30
DUPLICATE_THRESHOLD = 8
AUTO_LABEL_CONFIDENCE = 0.75

# === Paths ===
DECK_CONFIG_PATH = "configs/deck.json"
VIDEO_SOURCE_DIR = "C:/Users/krish/Music/clash royale"
EXTRACTED_FRAMES_DIR = "data/extracted"
AUTO_LABELED_DIR = "data/auto_labeled"

# === Debug ===
SAVE_DEBUG_IMAGES = True
ENABLE_DEBUG_OVERLAY = True

# === Analytics ===
ENABLE_ANALYTICS = True
ANALYTICS_DIR = "logs/analytics"
REPLAYS_DIR = "replays"
