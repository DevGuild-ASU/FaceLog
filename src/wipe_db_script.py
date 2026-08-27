"""Explicit development utility for removing locally generated FaceLog data."""

import shutil

from config import DATABASE_PATH, EXPORT_DIR, FACE_MODEL_PATH, IMAGE_DIR


def remove_path(path):
    """Remove one known generated file or directory if it exists."""
    if path.is_dir():
        shutil.rmtree(path)
        print(f"Removed directory: {path}")
    elif path.exists():
        path.unlink()
        print(f"Removed file: {path}")
    else:
        print(f"Nothing to remove: {path}")


def reset_local_data():
    """Delete attendance data, captured faces, exports, and the trained model."""
    for path in (DATABASE_PATH, IMAGE_DIR, EXPORT_DIR, FACE_MODEL_PATH):
        remove_path(path)


if __name__ == "__main__":
    reset_local_data()
