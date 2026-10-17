"""
SENTINEL // Autonomous Bio-Telemetry Engine
Ultra-low-latency pipeline integrating MediaPipe FaceMesh + Asynchronous ResNet-18
with debounced temporal closure modeling, head pose distraction detection
with mirror-check tolerance, and persistent audio alarm.
"""

import time
import math
import collections
from dataclasses import dataclass, field
from typing import Optional, Tuple, List
import threading
import queue

import cv2
import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models
import mediapipe as mp

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

try:
    import winsound
    HAS_WINSOUND = True
except Exception:
    HAS_WINSOUND = False

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except Exception:
    HAS_SOUNDDEVICE = False


# =====================================================================
# DATA CONTRACTS
# =====================================================================

@dataclass
class EyeMetric:
    state: str = "AWAKE"           # "AWAKE" | "DROWSY"
    ear: float = 0.35              # Geometric Eye Aspect Ratio
    aperture_pct: int = 100        # Openness 0-100%
    resnet_prob: float = 0.0       # Model P(sleepy) 0.0 - 1.0
    box: Tuple[int, int, int, int] = (0, 0, 0, 0)
    pupil: Tuple[int, int] = (0, 0)


@dataclass
class TelemetrySnapshot:
    timestamp: float = 0.0
    fps: float = 0.0
    left_eye: EyeMetric = field(default_factory=EyeMetric)
    right_eye: EyeMetric = field(default_factory=EyeMetric)
    confidence_pct: int = 0
    fatigue_score: float = 0.0     # 0.0 - 1.0
    perclos_pct: float = 0.0       # Percentage of closure over window
    closure_duration: float = 0.0  # Seconds continuously closed
    is_closed: bool = False
    
    # Head Pose & Distraction Tracking (Euro NCAP / NHTSA aligned)
    head_pitch: float = 0.0        # Degrees (+ down, - up)
    head_yaw: float = 0.0          # Degrees (+ right, - left)
    head_roll: float = 0.0         # Degrees
    is_distracted: bool = False
    distraction_duration: float = 0.0
    distraction_state: str = "FORWARD ROAD" # "FORWARD ROAD" | "MIRROR CHECK" | "DISTRACTED"

    # Oral Fatigue (Yawn), Head Droop & Composite Index
    mar: float = 0.0               # Mouth Aspect Ratio
    is_yawning: bool = False
    yawn_duration: float = 0.0
    yawn_count: int = 0
    head_droop_count: int = 0
    composite_fatigue_score: int = 0  # 0 - 100 Index
    fatigue_tier: str = "ALERT"    # "ALERT" (0-39) | "MODERATE" (40-69) | "CRITICAL" (70-100)

    alert_level: int = 0           # 0: Nominal, 1: Advisory, 2: Warning, 3: Critical
    alert_reason: str = "NOMINAL"  # "NOMINAL" | "MICROSLEEP" | "DISTRACTION" | "FATIGUE" | "COFFEE_ADVISORY"

    total_blinks: int = 0
    blinks_per_min: float = 0.0
    microsleep_events: int = 0
    distraction_events: int = 0
    latency_capture_ms: float = 0.0
    latency_inference_ms: float = 0.0
    session_elapsed_sec: float = 0.0


# =====================================================================
# PERSISTENT AUDIO ALARM DAEMON
# =====================================================================

class AudioAlarmDaemon:
    """
    Dedicated single-thread avionics audio alarm daemon.
    Eliminates thread collisions, device locking, and latency.
    """
    def __init__(self):
        self._running = True
        self.muted = False
        self.desired_level = 0
        self._test_active = False
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def set_level(self, level: int):
        self.desired_level = level

    def set_muted(self, muted: bool):
        self.muted = muted

    def test_alarm(self):
        """Manual test trigger with re-entrancy protection."""
        if self._test_active:
            return
        self._test_active = True
        def _test():
            try:
                self._beep(2600, 100)
                self._beep(3200, 130)
            finally:
                self._test_active = False
        threading.Thread(target=_test, daemon=True).start()

    def stop(self):
        self._running = False
        self.desired_level = 0

    def _run_loop(self):
        while self._running:
            if self.muted or self.desired_level < 3:
                time.sleep(0.04)
                continue

            # Urgent tactical cockpit emergency alarm
            self._beep(2600, 100)
            if not self._running or self.desired_level < 3 or self.muted:
                continue
            self._beep(3200, 130)
            time.sleep(0.05)

    def _beep(self, freq: int, duration_ms: int):
        if self.muted:
            return
        if HAS_WINSOUND:
            try:
                winsound.Beep(freq, duration_ms)
                return
            except Exception:
                pass
        if HAS_SOUNDDEVICE:
            try:
                dur_s = duration_ms / 1000.0
                t = np.linspace(0, dur_s, int(44100 * dur_s), endpoint=False)
                wave = 0.45 * np.sin(2 * np.pi * freq * t)
                sd.play(wave.astype(np.float32), samplerate=44100, blocking=True)
            except Exception:
                pass


# =====================================================================
# ASYNCHRONOUS DEEP-LEARNING INFERENCE WORKER (Non-Blocking)
# =====================================================================

class AsyncResNetWorker:
    """
    Executes ResNet-18 asynchronously in a dedicated background worker.
    Allows the camera capture & MediaPipe tracking loop to run at full 30-60 FPS
    without waiting for CPU convolutional forward passes (~80-100ms).
    """
    def __init__(self, weights_path: str = "drowsiness_model.pth"):
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model = models.resnet18(weights=None)
        self.model.fc = nn.Linear(self.model.fc.in_features, 2)
        
        self.weights_loaded = False
        try:
            state_dict = torch.load(weights_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            self.weights_loaded = True
        except Exception as e:
            print(f"[Sentinel] Warning: Could not load weights from {weights_path} ({e}).")

        self.model.to(self.device)
        self.model.eval()

        if self.device.type == "cpu":
            torch.set_num_threads(6)

        self._queue = queue.Queue(maxsize=1)
        self._latest_probs = (0.0, 0.0)
        self._running = True
        self._thread = threading.Thread(target=self._inference_loop, daemon=True)
        self._thread.start()

    def submit_crops(self, crop_l: np.ndarray, crop_r: np.ndarray):
        if crop_l.size == 0 or crop_r.size == 0:
            return
        if self._queue.empty():
            try:
                cl_res = cv2.resize(crop_l, (224, 224), interpolation=cv2.INTER_LINEAR)
                cr_res = cv2.resize(crop_r, (224, 224), interpolation=cv2.INTER_LINEAR)
                self._queue.put_nowait((cl_res, cr_res))
            except queue.Full:
                pass

    def get_latest_probs(self) -> Tuple[float, float]:
        return self._latest_probs

    def stop(self):
        self._running = False

    def _inference_loop(self):
        while self._running:
            try:
                cl_res, cr_res = self._queue.get(timeout=0.04)
            except queue.Empty:
                continue

            try:
                cl_rgb = cv2.cvtColor(cl_res, cv2.COLOR_BGR2RGB)
                cr_rgb = cv2.cvtColor(cr_res, cv2.COLOR_BGR2RGB)
                b_np = np.stack([cl_rgb, cr_rgb])

                b_tensor = torch.from_numpy(b_np).permute(0, 3, 1, 2).float().div_(255.0)
                b_tensor[:, 0].sub_(0.485).div_(0.229)
                b_tensor[:, 1].sub_(0.456).div_(0.224)
                b_tensor[:, 2].sub_(0.406).div_(0.225)
                b_tensor = b_tensor.to(self.device)

                with torch.inference_mode():
                    logits = self.model(b_tensor)
                    probs = torch.softmax(logits, dim=1)

                p_l = float(probs[0, 1].item())
                p_r = float(probs[1, 1].item())
                self._latest_probs = (p_l, p_r)
            except Exception:
                pass


# =====================================================================
# INFERENCE WORKER THREAD (Ultra-Low-Latency Producer)
# =====================================================================

class SentinelPipelineWorker(QThread):
    """
    Independent QThread capturing video frames and executing hybrid
    MediaPipe 3D Mesh + Asynchronous ResNet-18 inference, transmitting
    QImage and telemetry packets via zero-backpressure Qt Signals.
    """
    frame_ready = Signal(QImage, TelemetrySnapshot)
    error_signal = Signal(str)

    SCREEN_LEFT_EYE_INDICES  = [362, 385, 387, 263, 373, 380] # p1, p2, p3, p4, p5, p6
    SCREEN_RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]   # p1, p2, p3, p4, p5, p6
    SCREEN_LEFT_IRIS_INDEX  = 473
    SCREEN_RIGHT_IRIS_INDEX = 468

    def __init__(self, camera_index: int = 0, weights_path: str = "drowsiness_model.pth"):
        super().__init__()
        self.camera_index = camera_index
        self.weights_path = weights_path
        self._running = False
        self.gui_busy = False
        self.mutex = threading.Lock()

        # Calibration & Thresholds
        self.ear_threshold = 0.24         # Robust closure threshold for webcams
        self.resnet_threshold = 0.60      # ResNet sleepy confidence threshold
        self.warning_closure_sec = 0.70   # Visual advisory threshold
        self.critical_closure_sec = 1.50   # Exact 1.5s alarm requirement
        self.perclos_window_sec = 30.0

        # Head Pose Distraction vs Mirror Glance Thresholds
        # Healthy mirror checks take 0.5s - 1.5s; distraction alarms at 1.80s
        self.distraction_threshold_sec = 1.80
        self.head_away_start_time: Optional[float] = None
        self.distraction_event_count: int = 0

        # Temporal Tracking with Debounce Grace Frames
        self.closure_start_time: Optional[float] = None
        self.consecutive_open_frames = 0
        self.total_blinks: int = 0
        self.blink_timestamps = collections.deque(maxlen=100)
        self.microsleep_count: int = 0
        self.perclos_history = collections.deque(maxlen=900)
        self.session_start_time = time.time()

        # Oral Fatigue (Yawn) & Head Droop Modeling
        self.mar_threshold = 0.58
        self.yawn_duration_sec = 1.80
        self.yawn_start_time: Optional[float] = None
        self.yawn_count = 0
        self.head_nod_start_time: Optional[float] = None
        self.head_droop_count = 0

        # Initialize Asynchronous Neural Engine & Audio Daemon
        self.neural_engine = AsyncResNetWorker(self.weights_path)
        self.device = self.neural_engine.device
        self.weights_loaded = self.neural_engine.weights_loaded
        self.audio = AudioAlarmDaemon()

    def update_sensitivity(self, ear_thresh: float, resnet_thresh: float, warning_sec: float, critical_sec: float):
        with self.mutex:
            self.ear_threshold = ear_thresh
            self.resnet_threshold = resnet_thresh
            self.warning_closure_sec = warning_sec
            self.critical_closure_sec = critical_sec

    def set_muted(self, muted: bool):
        self.audio.set_muted(muted)

    def test_audio(self):
        self.audio.test_alarm()

    def run(self):
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        
        if not cap.isOpened():
            self.error_signal.emit(f"Failed to initialize Camera index {self.camera_index}")
            return

        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
        cap.set(cv2.CAP_PROP_FPS, 30)

        # Initialize MediaPipe FaceMesh
        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.55,
            min_tracking_confidence=0.55
        )

        self._running = True
        self.session_start_time = time.time()
        prev_frame_time = time.time()
        fps_smoother = 30.0

        while self._running:
            t_cap_start = time.perf_counter()
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            frame = cv2.flip(frame, 1)
            h, w, c = frame.shape
            t_cap_end = time.perf_counter()

            # Fast MediaPipe tracking on proxy downscaled tensor
            t_inf_start = time.perf_counter()
            small_frame = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_LINEAR)
            rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_small)

            telemetry = TelemetrySnapshot(
                timestamp=time.time(),
                session_elapsed_sec=time.time() - self.session_start_time,
                latency_capture_ms=(t_cap_end - t_cap_start) * 1000.0
            )

            now = time.time()
            instant_fps = 1.0 / max(now - prev_frame_time, 1e-5)
            prev_frame_time = now
            fps_smoother = 0.85 * fps_smoother + 0.15 * instant_fps
            telemetry.fps = round(fps_smoother, 1)

            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0].landmark
                self._analyze_facial_telemetry(frame, landmarks, w, h, telemetry)
            else:
                self._handle_no_face_detected(telemetry)

            t_inf_end = time.perf_counter()
            telemetry.latency_inference_ms = (t_inf_end - t_inf_start) * 1000.0

            if not self.gui_busy:
                self.gui_busy = True
                bytes_per_line = c * w
                q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_BGR888).copy()
                self.frame_ready.emit(q_img, telemetry)

        face_mesh.close()
        cap.release()
        self.neural_engine.stop()
        self.audio.stop()

    def stop(self):
        self._running = False
        self.neural_engine.stop()
        self.audio.stop()
        self.wait(1500)

    # -----------------------------------------------------------------
    # PIPELINE MATHEMATICS & GEOMETRY
    # -----------------------------------------------------------------

    @staticmethod
    def _calculate_ear(landmarks, indices, w: int, h: int) -> float:
        pts = np.array([[landmarks[idx].x * w, landmarks[idx].y * h] for idx in indices])
        d_v1 = np.linalg.norm(pts[1] - pts[5])
        d_v2 = np.linalg.norm(pts[2] - pts[4])
        d_h = np.linalg.norm(pts[0] - pts[3]) + 1e-6
        return float((d_v1 + d_v2) / (2.0 * d_h))

    @staticmethod
    def _calculate_mar(landmarks, w: int, h: int) -> float:
        """
        Calculates Mouth Aspect Ratio (MAR) for real-time oral yawn detection.
        Uses 3 vertical inner-lip pairs and horizontal mouth corner distance.
        """
        p13 = np.array([landmarks[13].x * w, landmarks[13].y * h])
        p14 = np.array([landmarks[14].x * w, landmarks[14].y * h])
        p82 = np.array([landmarks[82].x * w, landmarks[82].y * h])
        p87 = np.array([landmarks[87].x * w, landmarks[87].y * h])
        p312 = np.array([landmarks[312].x * w, landmarks[312].y * h])
        p317 = np.array([landmarks[317].x * w, landmarks[317].y * h])
        p61 = np.array([landmarks[61].x * w, landmarks[61].y * h])
        p291 = np.array([landmarks[291].x * w, landmarks[291].y * h])

        d_v1 = np.linalg.norm(p13 - p14)
        d_v2 = np.linalg.norm(p82 - p87)
        d_v3 = np.linalg.norm(p312 - p317)
        d_h = np.linalg.norm(p61 - p291) + 1e-6
        return float((d_v1 + d_v2 + d_v3) / (2.0 * d_h))

    def _extract_eye_crop(self, frame, landmarks, indices, w: int, h: int, pad_scale: float = 0.55):
        xs = [int(landmarks[idx].x * w) for idx in indices]
        ys = [int(landmarks[idx].y * h) for idx in indices]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        box_w = max_x - min_x
        box_h = max_y - min_y
        side = max(box_w, box_h)
        cx = (min_x + max_x) // 2
        cy = (min_y + max_y) // 2
        half = int(side * (0.5 + pad_scale))

        x1 = max(0, cx - half)
        y1 = max(0, cy - half)
        x2 = min(w, cx + half)
        y2 = min(h, cy + half)

        crop = frame[y1:y2, x1:x2]
        return crop, (x1, y1, x2, y2)

    def _estimate_head_pose(self, landmarks, w: int, h: int) -> Tuple[float, float, float]:
        nose = np.array([landmarks[1].x * w, landmarks[1].y * h])
        chin = np.array([landmarks[152].x * w, landmarks[152].y * h])
        l_eye = np.array([landmarks[33].x * w, landmarks[33].y * h])
        r_eye = np.array([landmarks[263].x * w, landmarks[263].y * h])

        d_left = np.linalg.norm(nose - l_eye)
        d_right = np.linalg.norm(nose - r_eye)
        yaw = float(np.clip((d_left - d_right) / (d_left + d_right + 1e-5) * 90.0, -90, 90))

        eye_center = (l_eye + r_eye) / 2.0
        face_height = np.linalg.norm(chin - eye_center) + 1e-5
        nose_relative = (nose[1] - eye_center[1]) / face_height
        pitch = float(np.clip((nose_relative - 0.35) * 120.0, -90, 90))

        delta = r_eye - l_eye
        roll = float(math.degrees(math.atan2(delta[1], delta[0])))

        return (
            0.0 if math.isnan(pitch) else pitch,
            0.0 if math.isnan(yaw) else yaw,
            0.0 if math.isnan(roll) else roll
        )

    def _analyze_facial_telemetry(self, frame, landmarks, w: int, h: int, telemetry: TelemetrySnapshot):
        # 1. Geometric EAR
        ear_l = self._calculate_ear(landmarks, self.SCREEN_LEFT_EYE_INDICES, w, h)
        ear_r = self._calculate_ear(landmarks, self.SCREEN_RIGHT_EYE_INDICES, w, h)
        avg_ear = (ear_l + ear_r) / 2.0

        # 2. Pupil/Iris locations
        num_landmarks = len(landmarks)
        if num_landmarks > self.SCREEN_LEFT_IRIS_INDEX:
            l_iris = (int(landmarks[self.SCREEN_LEFT_IRIS_INDEX].x * w), int(landmarks[self.SCREEN_LEFT_IRIS_INDEX].y * h))
        else:
            p1, p4 = self.SCREEN_LEFT_EYE_INDICES[0], self.SCREEN_LEFT_EYE_INDICES[3]
            l_iris = (int((landmarks[p1].x + landmarks[p4].x) * 0.5 * w), int((landmarks[p1].y + landmarks[p4].y) * 0.5 * h))

        if num_landmarks > self.SCREEN_RIGHT_IRIS_INDEX:
            r_iris = (int(landmarks[self.SCREEN_RIGHT_IRIS_INDEX].x * w), int(landmarks[self.SCREEN_RIGHT_IRIS_INDEX].y * h))
        else:
            p1, p4 = self.SCREEN_RIGHT_EYE_INDICES[0], self.SCREEN_RIGHT_EYE_INDICES[3]
            r_iris = (int((landmarks[p1].x + landmarks[p4].x) * 0.5 * w), int((landmarks[p1].y + landmarks[p4].y) * 0.5 * h))

        # 3. Eye crops for Asynchronous Deep Learning
        crop_l, box_l = self._extract_eye_crop(frame, landmarks, self.SCREEN_LEFT_EYE_INDICES, w, h)
        crop_r, box_r = self._extract_eye_crop(frame, landmarks, self.SCREEN_RIGHT_EYE_INDICES, w, h)

        self.neural_engine.submit_crops(crop_l, crop_r)
        prob_l_sleep, prob_r_sleep = self.neural_engine.get_latest_probs()

        aperture_l = int(np.clip((ear_l / 0.35) * 100, 0, 100))
        aperture_r = int(np.clip((ear_r / 0.35) * 100, 0, 100))

        is_left_drowsy = (ear_l < self.ear_threshold) or (prob_l_sleep > self.resnet_threshold)
        is_right_drowsy = (ear_r < self.ear_threshold) or (prob_r_sleep > self.resnet_threshold)

        telemetry.left_eye = EyeMetric(
            state="DROWSY" if is_left_drowsy else "AWAKE",
            ear=round(ear_l, 3),
            aperture_pct=aperture_l,
            resnet_prob=round(prob_l_sleep, 2),
            box=box_l,
            pupil=l_iris
        )
        telemetry.right_eye = EyeMetric(
            state="DROWSY" if is_right_drowsy else "AWAKE",
            ear=round(ear_r, 3),
            aperture_pct=aperture_r,
            resnet_prob=round(prob_r_sleep, 2),
            box=box_r,
            pupil=r_iris
        )
        telemetry.confidence_pct = int(np.clip((prob_l_sleep + prob_r_sleep) / 2.0 * 100, 0, 100))

        # 4. HEAD POSE & DISTRACTION VS. MIRROR CHECK
        pitch, yaw, roll = self._estimate_head_pose(landmarks, w, h)
        telemetry.head_pitch = round(pitch, 1)
        telemetry.head_yaw = round(yaw, 1)
        telemetry.head_roll = round(roll, 1)

        now = time.time()

        # Head looking away if turned significantly or tilted far down/up
        is_looking_away = (abs(yaw) > 28.0) or (pitch > 22.0) or (pitch < -26.0)

        if is_looking_away:
            if self.head_away_start_time is None:
                self.head_away_start_time = now
            dist_dur = now - self.head_away_start_time
            telemetry.distraction_duration = round(dist_dur, 2)

            if dist_dur >= self.distraction_threshold_sec:
                telemetry.distraction_state = "DISTRACTED"
                telemetry.is_distracted = True
            elif dist_dur >= 0.40:
                # Driver is checking side/rear mirrors or dashboard (healthy behavior)
                telemetry.distraction_state = "MIRROR CHECK"
                telemetry.is_distracted = False
            else:
                telemetry.distraction_state = "FORWARD ROAD"
                telemetry.is_distracted = False
        else:
            if self.head_away_start_time is not None:
                past_dur = now - self.head_away_start_time
                if past_dur >= self.distraction_threshold_sec:
                    self.distraction_event_count += 1
                self.head_away_start_time = None
            telemetry.distraction_duration = 0.0
            telemetry.distraction_state = "FORWARD ROAD"
            telemetry.is_distracted = False

        telemetry.distraction_events = self.distraction_event_count

        # 5. ROBUST DEBOUNCED CLOSURE EVALUATION
        frame_eyes_closed = (avg_ear < self.ear_threshold) or (is_left_drowsy and is_right_drowsy) or ((prob_l_sleep + prob_r_sleep) / 2.0 > 0.70)

        if frame_eyes_closed:
            self.consecutive_open_frames = 0
            if self.closure_start_time is None:
                self.closure_start_time = now
            closure_dur = now - self.closure_start_time
            telemetry.closure_duration = round(closure_dur, 2)
            telemetry.is_closed = True
            self.perclos_history.append((now, 1.0))
        else:
            self.consecutive_open_frames += 1
            if self.closure_start_time is not None:
                if self.consecutive_open_frames <= 3:
                    closure_dur = now - self.closure_start_time
                    telemetry.closure_duration = round(closure_dur, 2)
                    telemetry.is_closed = True
                    self.perclos_history.append((now, 1.0))
                else:
                    past_dur = now - self.closure_start_time
                    if 0.08 <= past_dur < self.warning_closure_sec:
                        self.total_blinks += 1
                        self.blink_timestamps.append(now)
                    elif past_dur >= self.critical_closure_sec:
                        self.microsleep_count += 1
                    self.closure_start_time = None
                    telemetry.closure_duration = 0.0
                    telemetry.is_closed = False
                    self.perclos_history.append((now, 0.0))
            else:
                telemetry.closure_duration = 0.0
                telemetry.is_closed = False
                self.perclos_history.append((now, 0.0))

        # 6. PERCLOS & BPM
        window_cutoff = now - self.perclos_window_sec
        recent_samples = [val for (t, val) in self.perclos_history if t >= window_cutoff]
        telemetry.perclos_pct = round((sum(recent_samples) / len(recent_samples)) * 100.0, 1) if recent_samples else 0.0

        bpm_cutoff = now - 60.0
        recent_blinks = [t for t in self.blink_timestamps if t >= bpm_cutoff]
        telemetry.blinks_per_min = float(len(recent_blinks))
        telemetry.total_blinks = self.total_blinks
        telemetry.microsleep_events = self.microsleep_count

        # 7. ORAL FATIGUE (MAR / YAWN DETECTION)
        mar = self._calculate_mar(landmarks, w, h)
        telemetry.mar = round(mar, 3)

        if mar >= self.mar_threshold:
            if self.yawn_start_time is None:
                self.yawn_start_time = now
            yawn_dur = now - self.yawn_start_time
            telemetry.yawn_duration = round(yawn_dur, 2)
            if yawn_dur >= self.yawn_duration_sec:
                telemetry.is_yawning = True
        else:
            if self.yawn_start_time is not None:
                past_dur = now - self.yawn_start_time
                if past_dur >= self.yawn_duration_sec:
                    self.yawn_count += 1
                self.yawn_start_time = None
            telemetry.is_yawning = False
            telemetry.yawn_duration = 0.0

        telemetry.yawn_count = self.yawn_count

        # 8. HEAD NODDING / DROOP DETECTION
        if pitch > 22.0:
            if self.head_nod_start_time is None:
                self.head_nod_start_time = now
            nod_dur = now - self.head_nod_start_time
            if nod_dur >= 1.20:
                self.head_droop_count += 1
                self.head_nod_start_time = None
        else:
            self.head_nod_start_time = None
        telemetry.head_droop_count = self.head_droop_count

        # 9. COMPOSITE DRIVER FATIGUE SCORE (Euro NCAP / Industrial DMS Formula)
        # Fatigue Index = w1*PERCLOS + w2*ClosureDuration + w3*YawnFrequency + w4*HeadDroop + w5*Distraction
        perclos_w = min(telemetry.perclos_pct, 100.0) * 0.35
        closure_w = min(telemetry.closure_duration / 1.5, 1.0) * 35.0
        yawn_w = min(self.yawn_count * 10.0 + (18.0 if telemetry.is_yawning else 0.0), 30.0)
        nod_w = min(self.head_droop_count * 15.0 + (15.0 if pitch > 20.0 else 0.0), 25.0)
        dist_w = min(telemetry.distraction_duration / 1.8, 1.0) * 20.0 if telemetry.distraction_state == "DISTRACTED" else 0.0

        raw_index = int(np.clip(perclos_w + closure_w + yawn_w + nod_w + dist_w, 0, 100))
        telemetry.composite_fatigue_score = raw_index
        telemetry.fatigue_score = round(raw_index / 100.0, 2)

        # Fatigue Tiers: ALERT (0-39) | MODERATE (40-69) | CRITICAL (70-100)
        if raw_index >= 70 or telemetry.closure_duration >= self.critical_closure_sec or telemetry.distraction_duration >= self.distraction_threshold_sec:
            telemetry.fatigue_tier = "CRITICAL"
        elif raw_index >= 40 or self.yawn_count >= 2 or telemetry.is_yawning:
            telemetry.fatigue_tier = "MODERATE"
        else:
            telemetry.fatigue_tier = "ALERT"

        # 10. MULTI-HAZARD ALARM TRIGGERING
        # 1) Micro-sleep Hazard: Eyes closed >= 1.50s OR PERCLOS > 65%
        # 2) Prolonged Distraction Hazard: Head turned away >= 1.80s
        # 3) Composite Fatigue Hazard: Tier == CRITICAL
        if telemetry.closure_duration >= self.critical_closure_sec or telemetry.perclos_pct > 65.0:
            telemetry.alert_level = 3
            telemetry.alert_reason = "MICROSLEEP"
            self.audio.set_level(3)
        elif telemetry.distraction_duration >= self.distraction_threshold_sec:
            telemetry.alert_level = 3
            telemetry.alert_reason = "DISTRACTION"
            self.audio.set_level(3)
        elif telemetry.fatigue_tier == "CRITICAL":
            telemetry.alert_level = 3
            telemetry.alert_reason = "FATIGUE"
            self.audio.set_level(3)
        elif telemetry.fatigue_tier == "MODERATE" or telemetry.closure_duration >= self.warning_closure_sec or telemetry.distraction_duration >= 1.20:
            telemetry.alert_level = 2
            telemetry.alert_reason = "COFFEE_ADVISORY" if (telemetry.is_yawning or self.yawn_count >= 2) else "WARNING"
            self.audio.set_level(0) # Visual caution only
        elif telemetry.perclos_pct > 15.0 or pitch > 18.0 or telemetry.distraction_state == "MIRROR CHECK":
            telemetry.alert_level = 1
            telemetry.alert_reason = "ADVISORY"
            self.audio.set_level(0)
        else:
            telemetry.alert_level = 0
            telemetry.alert_reason = "NOMINAL"
            self.audio.set_level(0)

    def _handle_no_face_detected(self, telemetry: TelemetrySnapshot):
        telemetry.alert_level = 1
        telemetry.alert_reason = "NO_FACE"
        telemetry.is_closed = False
        telemetry.closure_duration = 0.0
        telemetry.distraction_duration = 0.0
        telemetry.distraction_state = "UNKNOWN"
        self.closure_start_time = None
        self.head_away_start_time = None
        self.consecutive_open_frames = 0
        self.audio.set_level(0)
