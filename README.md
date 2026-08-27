# FaceLog

FaceLog is a local, offline desktop application for face-based attendance. Register a person from a webcam feed, start an attendance session, and FaceLog marks each recognized person present once. Attendance records are saved in SQLite and written to a CSV file for each session.

The project is intentionally a small **modular monolith**: it runs as one Python desktop process and has internal modules only where they make the code easier to understand and maintain.

## Features

- Offline face registration using webcam samples.
- DNN-based face detection and LBPH face recognition.
- Named attendance sessions with one attendance record per person.
- Clear live feedback for unknown faces, captured samples, successful attendance, and duplicate detections.
- Local SQLite storage and per-session CSV exports.

## Architecture

```text
Tkinter UI and workflow (src/app)
        |
        +--> Face processing (src/face) --> OpenCV DNN + LBPH model
        |
        +--> Local storage (src/data) --> SQLite database
        |
        +--> Shared settings (src/config.py)
```

All modules run in the same local process. The UI controls the user workflow, the face module owns OpenCV operations, and the data module owns SQL. This keeps the application simple to run and change without introducing networked components or unneeded abstractions.

## Project layout

```text
src/
├── main.py                 # Launches the desktop app
├── config.py               # Paths and shared vision/application settings
├── app/
│   ├── attendance_app.py   # UI, camera loop, registration and attendance workflow
│   └── about_app.py        # About screen
├── face/
│   └── face_manager.py     # Detection, recognition, registration and model training
├── data/
│   └── database.py         # SQLite schema and attendance/person/session queries
├── models/dnn/             # Bundled DNN detector files
└── wipe_db_script.py       # Explicit local-data reset utility
```

Generated local data stays outside `src/`:

- `database.db` — people, sessions, and attendance records.
- `images/` — captured face samples used to train the recognizer.
- `exports/` — CSV files named `session_<id>.csv`.
- `src/models/face_model.yml` — trained LBPH recognition model.

## Setup

Prerequisites: Python 3.8+ and a webcam.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src\main.py
```

`opencv-contrib-python` is required because the application uses OpenCV's LBPH face recognizer.

## How to use it

1. Open **Register face**.
2. Enter a unique name and select **Capture and register**.
3. Keep the person’s face visible until the registration confirmation appears.
4. Open **Take attendance**, enter a session name, and select **Start session**.
5. Present a registered face. A green `marked present` label confirms a successful first check-in; later detections show `already marked`.
6. Select **Stop session** when complete. The session remains in SQLite, and any marked attendance is in `exports/session_<id>.csv`.

## Development

Run a quick syntax check before committing:

```powershell
.\.venv\Scripts\python.exe -m py_compile src\main.py src\config.py src\app\attendance_app.py src\face\face_manager.py src\data\database.py
```

For a full design and contribution guide, read [AGENTS.md](AGENTS.md).

## Reset local data

This command permanently removes the local database, captured images, CSV exports, and trained recognition model. Use it only when you intentionally want a clean start:

```powershell
.\.venv\Scripts\python.exe src\wipe_db_script.py
```
