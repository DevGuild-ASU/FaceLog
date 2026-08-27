"""Application-wide configuration for the FaceLog desktop monolith."""

from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SRC_DIR.parent

APP_TITLE = "FaceLog"
DATABASE_PATH = PROJECT_DIR / "database.db"
IMAGE_DIR = PROJECT_DIR / "images"
EXPORT_DIR = PROJECT_DIR / "exports"
MODEL_DIR = SRC_DIR / "models"
FACE_MODEL_PATH = MODEL_DIR / "face_model.yml"
DNN_PROTOTXT_PATH = MODEL_DIR / "dnn" / "deploy.prototxt"
DNN_CAFFEMODEL_PATH = MODEL_DIR / "dnn" / "res10_300x300_ssd_iter_140000_fp16.caffemodel"

VIDEO_SIZE = (640, 480)
FACE_SIZE = (100, 100)
DNN_CONFIDENCE = 0.7
RECOGNITION_CONFIDENCE = 70
