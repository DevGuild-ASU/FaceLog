"""Small Tkinter interface for offline face-based attendance."""

import csv
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

import cv2
from PIL import Image, ImageTk

from app.about_app import create_about_frame
from config import APP_TITLE, EXPORT_DIR, VIDEO_SIZE
from data.database import create_session, end_session, get_person_id_by_name, init_db, log_attendance
from face.face_manager import FaceManager

CAPTURE_SECONDS = 4
CAPTURE_INTERVAL_MS = 250
MIN_FACE_SAMPLES = 10


class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.resizable(False, False)
        init_db()
        self.face_manager = FaceManager()
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, VIDEO_SIZE[0])
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, VIDEO_SIZE[1])
        self.running = True
        self.session_id = None
        self.session_name = ""
        self.captured_faces = []
        self.capture_started_at = None
        self.last_capture_at = None
        self._build_ui()
        self._update_camera()

    def _build_ui(self):
        container = ttk.Frame(self.root, padding=14)
        container.pack(fill="both", expand=True)
        notebook = ttk.Notebook(container)
        notebook.pack(fill="both", expand=True)
        self.register_tab = ttk.Frame(notebook, padding=12)
        self.attendance_tab = ttk.Frame(notebook, padding=12)
        notebook.add(self.register_tab, text="Register face")
        notebook.add(self.attendance_tab, text="Take attendance")
        notebook.add(create_about_frame(notebook), text="About")
        self._build_registration_tab()
        self._build_attendance_tab()

    def _build_registration_tab(self):
        ttk.Label(self.register_tab, text="Register a person", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(self.register_tab, text="Enter a name, then keep one face in view for a few seconds.").pack(anchor="w", pady=(2, 10))
        fields = ttk.Frame(self.register_tab)
        fields.pack(fill="x")
        ttk.Label(fields, text="Name:").pack(side="left")
        self.name_entry = ttk.Entry(fields, width=32)
        self.name_entry.pack(side="left", padx=8)
        self.register_button = ttk.Button(fields, text="Capture and register", command=self.start_registration)
        self.register_button.pack(side="left")
        self.register_status = ttk.Label(self.register_tab, text="Ready to register.")
        self.register_status.pack(anchor="w", pady=10)
        self.register_video = ttk.Label(self.register_tab)
        self.register_video.pack()

    def _build_attendance_tab(self):
        ttk.Label(self.attendance_tab, text="Take attendance", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(self.attendance_tab, text="Start a session. Each recognized person is marked once.").pack(anchor="w", pady=(2, 10))
        fields = ttk.Frame(self.attendance_tab)
        fields.pack(fill="x")
        ttk.Label(fields, text="Session name:").pack(side="left")
        self.session_entry = ttk.Entry(fields, width=28)
        self.session_entry.pack(side="left", padx=8)
        self.start_button = ttk.Button(fields, text="Start session", command=self.start_session)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(fields, text="Stop session", command=self.stop_session, state="disabled")
        self.stop_button.pack(side="left", padx=(6, 0))
        self.attendance_status = ttk.Label(self.attendance_tab, text="No active session.", font=("Segoe UI", 11, "bold"))
        self.attendance_status.pack(anchor="w", pady=10)
        self.attendance_video = ttk.Label(self.attendance_tab)
        self.attendance_video.pack()

    def start_registration(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Name required", "Enter the person's name first.")
            return
        if get_person_id_by_name(name):
            messagebox.showwarning("Already registered", f"{name} is already registered.")
            return
        self.captured_faces = []
        self.capture_started_at = datetime.now()
        self.last_capture_at = None
        self.register_button.config(state="disabled")
        self.register_status.config(text="Capturing face samples… keep looking at the camera.")

    def start_session(self):
        name = self.session_entry.get().strip()
        if not name:
            messagebox.showwarning("Session name required", "Enter a session name first.")
            return
        self.session_id = create_session(name)
        self.session_name = name
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.attendance_status.config(text=f"Session active: {name}. Looking for registered faces.")

    def stop_session(self):
        if self.session_id:
            end_session(self.session_id)
            self.attendance_status.config(text=f"Session stopped: {self.session_name}.")
        self.session_id = None
        self.session_name = ""
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

    def _update_camera(self):
        if not self.running:
            return
        ok, frame = self.camera.read()
        if ok:
            frame = cv2.flip(frame, 1)
            self._process_frame(frame)
            self._show_frame(self.register_video, frame)
            self._show_frame(self.attendance_video, frame)
        else:
            self.attendance_status.config(text="Camera unavailable. Check that it is connected and not in use.")
        self.root.after(30, self._update_camera)

    def _process_frame(self, frame):
        boxes = self.face_manager.detect_faces(frame)
        now = datetime.now()
        for box in boxes:
            x1, y1, x2, y2 = box
            face = self.face_manager.get_face_roi(frame, box)
            color, label = (0, 0, 255), "Unknown face"
            if self.capture_started_at and face is not None:
                if self.last_capture_at is None or (now - self.last_capture_at).total_seconds() * 1000 >= CAPTURE_INTERVAL_MS:
                    self.captured_faces.append(face)
                    self.last_capture_at = now
                label, color = f"Capturing: {len(self.captured_faces)} samples", (0, 165, 255)
            if self.session_id and face is not None:
                name, _ = self.face_manager.recognize_face(face)
                if name:
                    person_id = get_person_id_by_name(name)
                    if log_attendance(person_id, self.session_id):
                        self._append_csv(name)
                        self.attendance_status.config(text=f"✓ {name} marked present at {now:%H:%M:%S}")
                        label, color = f"{name}: marked present", (0, 180, 0)
                    else:
                        label, color = f"{name}: already marked", (0, 180, 180)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, max(y1 - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
        self._finish_registration_if_due(now)

    def _finish_registration_if_due(self, now):
        if not self.capture_started_at or (now - self.capture_started_at).total_seconds() < CAPTURE_SECONDS:
            return
        name, samples = self.name_entry.get().strip(), self.captured_faces
        self.capture_started_at = None
        self.register_button.config(state="normal")
        if len(samples) < MIN_FACE_SAMPLES:
            self.register_status.config(text="Not enough face samples. Try again in better lighting.")
            return
        person_id = self.face_manager.register_person(name, samples)
        if person_id:
            self.name_entry.delete(0, tk.END)
            self.register_status.config(text=f"✓ {name} registered successfully.")
        else:
            self.register_status.config(text="Registration failed. That name may already exist.")

    def _append_csv(self, name):
        EXPORT_DIR.mkdir(exist_ok=True)
        path = EXPORT_DIR / f"session_{self.session_id}.csv"
        with path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if path.stat().st_size == 0:
                writer.writerow(["Session", self.session_name])
                writer.writerow(["Name", "Timestamp"])
            writer.writerow([name, datetime.now().isoformat(sep=" ", timespec="seconds")])

    @staticmethod
    def _show_frame(label, frame):
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).resize(VIDEO_SIZE)
        photo = ImageTk.PhotoImage(image=image)
        label.configure(image=photo)
        label.image = photo

    def on_closing(self):
        self.running = False
        if self.session_id:
            end_session(self.session_id)
        if self.camera.isOpened():
            self.camera.release()
        self.root.destroy()
