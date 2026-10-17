<div align="center">

# 🛡️ SENTINEL AI // DRIVER VIGILANCE GUARDIAN
### *Next-Generation Autonomous Driver Monitoring System (DMS) & Neuro-Distraction Shield*

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.x%20ResNet--18-EE4C2C.svg?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-468--Point%20FaceMesh-00C7B7.svg?logo=google&logoColor=white)](https://developers.google.com/mediapipe)
[![PySide6](https://img.shields.io/badge/UI-PySide6%20Qt%20Cyber--HUD-41CD52.svg?logo=qt&logoColor=white)](https://wiki.qt.io/Qt_for_Python)
[![OpenCV](https://img.shields.io/badge/OpenCV-Real--Time%20CV-5C3EE8.svg?logo=opencv&logoColor=white)](https://opencv.org/)
[![Euro NCAP Aligned](https://img.shields.io/badge/Euro%20NCAP-DMS%20Standard-success.svg)](https://www.euroncap.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<p align="center">
  <b>A real-time, zero-latency desktop co-pilot engineered to eradicate driver fatigue, micro-sleep, and off-road distractions using an asynchronous dual-engine neural pipeline and a futuristic liquid-chrome avionics HUD.</b>
</p>

</div>

---

## ⚡ Executive Summary

**Sentinel AI** is an advanced automotive Driver Monitoring System (DMS) built to meet and exceed modern active safety standards (Euro NCAP / NHTSA). By fusing **high-frequency geometric landmark analysis (MediaPipe 468-point FaceMesh)** with an **asynchronously decoupled deep convolutional neural network (fine-tuned ResNet-18)**, Sentinel AI achieves micro-sleep detection accuracy while eliminating camera lag and false alarms.

The system features an avionic **Liquid-Chrome Cyber-HUD** built on PySide6 with custom vector painting and cognitive ergonomics to convey immediate, actionable alerts without startling or overloading the driver.

---

## 🧠 Dual-Stage Neural Architecture

Traditional fatigue detection systems suffer from a dilemma: landmark algorithms can jitter on squinting or rapid head movement, while deep CNNs are too computationally heavy to run synchronously on every webcam frame without dragging the UI down to single-digit FPS. 

Sentinel AI resolves this with a **decoupled dual-tier pipeline**:

```mermaid
graph TD
    A[Webcam 30 FPS Ingestion] --> B[SIMD Mirror Flip & Bilateral Scale]
    B --> C[MediaPipe 468-pt FaceMesh]
    
    subgraph Stage 1: Ultra-Fast Geometric Pipeline
        C --> D[Bilateral EAR Calculation]
        C --> E[3D Head Pose PnP Solver]
        D --> F[3-Frame Temporal Debounce]
        E --> G[Gaze Vector & Mirror Check Zone]
    end
    
    subgraph Stage 2: Asynchronous ResNet-18 Texture Verifier
        C -.->|Decoupled Worker Queue| H[OpenCV SIMD Crop & Normalization]
        H --> I[PyTorch ResNet-18 Inference]
        I -.->|Async Update| J[Confidence & Micro-Feature Score]
    end
    
    F --> K{Closure Duration >= 1.50s?}
    G --> L{Off-Road Duration >= 1.80s?}
    
    K -->|YES| M[🚨 CRITICAL ACOUSTIC WARBLE ALARM]
    L -->|YES| M
    K -->|NO: <1.5s| N[Calm Indicator / Blink Tracker]
    G -->|0.4s - 1.8s| O[🟢 SAFE MIRROR CHECK ZONE]
```

### 1. Stage 1: High-Rate Geometric Tracker (30+ FPS)
- **Eye Aspect Ratio (EAR)**: Computes the 3D Euclidean distance ratio across 6 canonical orbital landmarks per eye:
  $$\text{EAR} = \frac{\|p_2 - p_6\| + \|p_3 - p_5\|}{2 \|p_1 - p_4\|}$$
- **3-Frame Temporal Debounce**: Filters momentary landmark micro-jitters without resetting active micro-sleep accumulators.
- **Micro-Sleep Trigger**: A continuous eye closure lasting **exactly 1.50 seconds** triggers Level-3 emergency alerts.

### 2. Stage 2: Deep Texture Verifier (ResNet-18)
- Fine-tuned on the **MRL Infrared Eye Dataset** (84,898 images).
- Runs on a dedicated background worker (`AsyncResNetWorker`) using zero-copy tensor preprocessing.
- Evaluates micro-features invisible to point landmarks (corneal glint, sclera exposure, dynamic eyelid drooping).

---

## 🚘 Intelligent Mirror-Check vs. Distraction Engine

A common flaw in driver monitoring systems is sounding false alarms when the driver glances at the rearview or side mirrors. Sentinel AI solves this using **temporal gaze classification**:

| Driver Action | Head Yaw / Pitch Angle | Duration Window | System Response |
| :--- | :--- | :--- | :--- |
| **Normal Forward Driving** | $\pm 12^\circ$ centered | Continuous | `🟢 ROAD AHEAD` — Maximum Vigilance |
| **Mirror Inspection** | Left/Right $\pm 18^\circ$ to $38^\circ$ | **$0.40\text{s} - 1.80\text{s}$** | `🟡 MIRROR CHECK` — Safe glance feedback, **0 alarms** |
| **Off-Road Distraction** | Phone, passenger, lap, away | **$\ge 1.80\text{s}$** | `🔴 DISTRACTION ALARM` — Warning tone & visual pulse |
| **Micro-Sleep Episode** | Eyelids closed ($EAR < 0.24$) | **$\ge 1.50\text{s}$** | `🚨 DANGER: FATIGUE CRITICAL` — Continuous acoustic warble |

> [!NOTE]
> **Euro NCAP / NHTSA Guidelines**: Safe off-road glances for driving mirrors range between 0.5s to 1.5s. Sentinel AI sets the distraction threshold at **1.80 seconds**, ensuring safe driving glances never trigger nuisance warnings.

---

## 🎨 Liquid Chrome Futuristic Cyber-HUD

Designed following cognitive psychology principles to minimize stress and maximize situational awareness:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│  SENTINEL // DRIVER MONITOR   [ ◉ ROAD AHEAD ]    CAM: 640x480 @ 30 FPS    LATENCY: 12.4ms   │
├──────────────────────────────────────────────────────┬─────────────────────────────────────────┤
│                                                      │  VIGILANCE CORE                         │
│                  LIVE CAMERA FEED                    │      ╭──────────────╮                   │
│                                                      │     │    98.4 %     │  [ OPTIMAL ]      │
│     [  (·)  ]                 [  (·)  ]              │      ╰──────────────╯                   │
│     L-RETICLE                 R-RETICLE              ├─────────────────────────────────────────┤
│                                                      │  EMERGENCY COUNTDOWN                    │
│                                                      │      ╭──────────────╮                   │
│             + LASER SCANNER +                        │     │    1.50 s     │  [ STANDBY ]      │
│                                                      │      ╰──────────────╯                   │
│                                                      ├─────────────────────────────────────────┤
│          [ 3D ATTITUDE GYROSCOPE ]                   │  VITAL RHYTHM OSCILLOGRAPH              │
│                                                      │   /\    /\      /\    /\   [ 72 BPM ]   │
│  [◀ L-MIRROR] ────── [ ◉ ROAD AHEAD ] ────── [ R-MIRROR ▶]    │  /  \  /  \    /  \  /  \               │
├──────────────────────────────────────────────────────┴─────────────────────────────────────────┤
│  SESSION: 01:24:18  │  TOTAL BLINKS: 412  │  MICROSLEEPS: 0  │  STATUS: NOMINAL              │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

- **Specular Chrome Reticles**: Active orbital target reticles lock onto left and right eyes with real-time EAR meters.
- **Avionic Road Tape**: Top-mounted horizontal gaze compass shows real-time glance angles between `L-MIRROR`, `ROAD AHEAD`, and `R-MIRROR`.
- **Reactor Vigilance Gauge**: Polished chrome circular core with a multi-stop metallic gradient displaying real-time alertness (0–100%).
- **Acoustic Synthesizer Daemon**: Single-thread Windows `winsound` kernel synthesizer with instant warble modulation (2600 Hz ⇄ 3200 Hz) and PortAudio fallback, running completely asynchronously without blocking the UI thread.

---

## 📊 Dataset & Model Specifications

The eye verification classifier is trained on the **MRL Infrared Eye Images Dataset**:

- **Total Images**: 84,898 infrared images across 37 diverse human subjects.
- **Sensor Conditions**: Captured across multiple optical sensors under variable illumination and night-vision IR conditions.
- **Labels**: Binary classification — `Awake` (Open) vs. `Sleepy` (Closed).

### Dataset Partitioning:
| Partition | Awake Images | Sleepy Images | Total Images |
| :--- | :--- | :--- | :--- |
| **Train Set** | 25,770 | 25,167 | 50,937 |
| **Validation Set** | 8,591 | 8,389 | 16,980 |
| **Test Set** | 8,591 | 8,390 | 16,981 |
| **Total** | **42,952** | **41,946** | **84,898** |

### Original Dataset Resources:
- **Forked Dataset**: [Download Forked Dataset](http://mrl.cs.vsb.cz/data/eyedataset/mrlEyes_2018_01.zip)
- **Original Dataset**: [Download Original MRL Eye Dataset](http://mrl.cs.vsb.cz/data/eyedataset/mrlEyes_2018_01.zip)
- **Pupil Annotations**: [Download Pupil Annotations](http://mrl.cs.vsb.cz/data/eyedataset/pupil.txt)
- **Author Reference**: [Radovan Fusek, MRL Laboratory](http://mrl.cs.vsb.cz//people/fusek/)

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12
- Standard RGB or Infrared USB Webcam
- Windows 10/11, macOS, or Linux

### 2. Clone the Repository
```bash
git clone https://github.com/optimalcooler/drowsiness-detector-model.git
cd drowsiness-detector-model
```

### 3. Create a Virtual Environment & Install Dependencies
```bash
# Create virtual environment
python -m venv .venv

# Activate on Windows
.\.venv\Scripts\activate

# Activate on Linux/macOS
# source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 4. Launch Sentinel AI
```bash
# Launch the main Cyber-HUD application
python yolo.py
```
*(Alternatively: `python sentinel_ui.py`)*

---

## 📁 Repository Directory Structure

```text
drowsiness-detector-model/
├── drowsiness_model.pth     # Pre-trained deep ResNet-18 model weights (~42.7 MB)
├── sentinel_engine.py       # Computer vision pipeline, FaceMesh, async ResNet & audio daemon
├── sentinel_ui.py           # Futuristic Liquid-Chrome PySide6 desktop HUD interface
├── yolo.py                  # Primary application entrypoint
├── requirements.txt         # Pinned production dependencies
├── train.py                 # ResNet-18 model training & validation script
├── split_data.py            # Automated train/validation/test dataset split utility
├── get_info.py              # Dataset inspection & metadata analysis
├── labels.txt               # Class label definitions
├── README.md                # System documentation
└── .gitignore               # Ignored environments, cache, and raw image datasets
```

---

## ⚙️ Key Technical Features

- **Zero-Backpressure Frame Loop**: Uses a `gui_busy` atomic semaphore preventing frame queuing so video never lags behind real time.
- **SIMD Image Processing**: Replaced slow PIL/PyTorch conversions with native C++ OpenCV SIMD operations for crop and normalization.
- **Fail-Safe Audio Engine**: Dedicated thread running hardware `winsound.Beep` on Windows with zero thread-creation overhead and non-blocking operation.
- **Mirror Alignment Logic**: Explicit horizontal landmark inversion so winking your left eye moves the left eye reticle on screen naturally.

---

## 📜 License & Citation

This project is open-source under the **MIT License**.

If you use this model or system in your research or project, please cite:
```bibtex
@article{fusek2018mrl,
  title={MRL Eye Dataset for Drowsiness and Eye State Detection},
  author={Fusek, Radovan},
  journal={VSB - Technical University of Ostrava},
  year={2018}
}
```
