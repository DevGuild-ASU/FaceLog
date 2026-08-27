# FaceLog Contributor Guide

## Purpose

FaceLog is an offline desktop attendance application. It runs as one Python process on the local machine: Tkinter presents the interface, OpenCV detects and recognizes faces, and SQLite stores attendance. There are no remote services, APIs, background workers, or web clients.

## Architecture

This is a **modular monolith**. Keep the application deployable and runnable as a single local program while preserving these simple boundaries:

| Area | Location | Responsibility |
| --- | --- | --- |
| Entry point | `src/main.py` | Creates the Tk root window and starts the application. |
| Configuration | `src/config.py` | Central source for local paths and application/vision constants. |
| UI and workflow | `src/app/` | Tkinter screens, camera loop, registration, and attendance-session flow. |
| Face processing | `src/face/` | DNN detection, face crops, LBPH recognition, and model training. |
| Local storage | `src/data/` | SQLite schema and query functions only. |
| Assets | `src/models/` | Bundled DNN detector files and generated LBPH model. |

Dependencies flow inward: `app` may call `face` and `data`; `face` may call `data`; neither `face` nor `data` imports the Tkinter UI. Put shared constants and paths in `config.py`, not in individual feature modules.

## Development rules

- Favor the smallest direct change that supports a user workflow. Do not add services, repositories, dependency injection, ORMs, or plugin systems.
- Keep database access in `data/database.py`; use parameterized SQL and context-managed connections.
- Keep OpenCV and model behavior in `face/face_manager.py`; UI code should not know model file details.
- Tkinter widgets must only be updated on the main thread. The current camera loop uses `root.after` for that reason.
- Generated data belongs at the project root: `database.db`, `images/`, `exports/`, and `src/models/face_model.yml`.
- Never delete local data as part of the normal application flow. `src/wipe_db_script.py` is an explicit development-only reset tool.

## Run and verify

Use the repository virtual environment on Windows:

```powershell
.\.venv\Scripts\python.exe src\main.py
.\.venv\Scripts\python.exe -m py_compile src\main.py src\config.py src\app\attendance_app.py src\face\face_manager.py src\data\database.py
```

Manual verification requires a webcam: register one person, start a session, present the registered face, and confirm a single attendance row is written to `exports/session_<id>.csv`.
