# Aero-Mouse Systems: Backend Architecture and Implementation Documentation

This document extensively outlines the backend architecture, implementation details, theoretical concepts, and potential review questions for the Aero-Mouse project.

---

## 1. What Exactly Have We Done?

We have developed a comprehensive, real-time backend system using Python to facilitate Touchless Human-Computer Interaction (HCI). This backend replaces traditional physical input devices (mouse, keyboard) with spatial gestures (hand and face tracking). 

Specifically, the backend is responsible for:
1. **Capturing Real-time Video Feeds** from a standard webcam.
2. **Extracting Spatial Landmarks** for hands and face meshes natively.
3. **Translating Spatial Movements into OS-Level Commands** (Cursor movement, left/right clicks, double clicks, scrolling, clicking and dragging, presentation navigation).
4. **Implementing an "Air Signature" Authentication** layer by converting hand trajectories into actionable authorization data.
5. **Streaming System Feedback** via a REST API backend and MJPEG rendering pipeline to interface with a modern dynamic React frontend dashboard.

---

## 2. How Have We Done It?

The backend is built around a two-tier architectural pattern:
- **Core Processing Engine (`main.py`)**: Runs an asynchronous loop relying on **OpenCV** to get webcam arrays and **Google MediaPipe** to compute landmark matrices in real-time.
- **RESTful API Bridge (`app.py`)**: Runs a **Flask-based server** providing interaction endpoints to control states, stream the processed frames asynchronously (via Multipart MJPEG format), and perform secure backend-to-database requests. 

The logic is modularized into feature-specific python scripts:
- `mouse.py`: Evaluates hand landmark nodes. Differentiates "Index up" (Move), "Pinch" (Drag), "All fingers" (Scroll), "Fist" (Clear). It maps these via **PyAutoGUI** to control native desktop bindings.
- `facial.py`: Handles high-precision facial mesh rendering focusing primarily on the nose landmark (Position 1). To avoid unintentional triggering, a **Slide Lock** feature checks for hand gestures (Fist = Unlock slides, 5 Fingers open = Lock slides) before triggering slide transitions.
- `air.py` & `signature_auth.py`: Creates a virtual spatial canvas. When in authentication mode, it grabs successive `X, Y` positional points. It uses `scipy` and `fastdtw` to establish similarity equations over time.
- `db.py` & `cloud_storage.py`: PostgreSQL maps serialized user features to database schemas, while Cloudinary allows remote object mapping of resulting images safely.

---

## 3. What Theory Concepts Have We Used?

To ensure accuracy, we tapped into several mathematical and computer-science algorithms:

### A. Computer Vision and Spatial Kinematics
- **Vector Projection:** Instead of blindly predicting gestures from Y-heights, vector dot products are used (e.g., in `is_thumb_extended`). Projecting the thumb's direction over the lateral palm direction allows thumb detection to be invariant of hand rotation or left/right hands.
- **Deep Learning Meshing:** Google MediaPipe natively predicts 3D coordinates (x, y, z) relying on BlazeFace/BlazePalm Machine Learning CNN models internally.

### B. Signal Processing & Smoothening
- **Moving Average Filter:** High-frequency jitter exists in webcam mapping. In `facial.py`, passing $N$ immediate frames to a rolling average dramatically dampens micro-movements so a user's head position stabilizes securely.
- **Velocity/Acceleration Derivation:** For Air-Signatures, 1st derivatives (velocity) and 2nd derivatives (acceleration) are formulated out of position over time to assess how a user signs, not just what it visually looks like.

### C. Dynamic Time Warping (DTW)
- **Time-Series Matching Calculation:** People draw their signature at different speeds. Euclidean distance algorithms fail strictly because the number of trajectory frames rarely lines up. DTW efficiently matches sequence $P$ with sequence $Q$ by stretching/compressing them on a temporal axis to find the minimal distance path (lowest discrepancy cost).

---

## 4. What Have We Implemented?

- **Real-Time Touchless Control**: Allows full desktop interaction without external hardware other than a camera, utilizing state-of-the-art gesture algorithms.
- **Context-Aware Safety Mechanisms**: Built-in logic like the "lock/unlock slides gesture" mapping stops accidental head twitches from breaking a presentation slide run.
- **Continuous Stream Web Integration**: Connected a thick-client logic (heavy Python processing) securely to a thin web-client UI (React) cleanly bypassing thread-locking via `flask_cors` and Yield loop streaming.
- **Multi-Factor Feature Comparisons**: A highly resilient authentication model taking DTW distance (weight: 70%) and Trajectory metrics (Velocity, Sharp curves, Aspect Ratios — weight: 30%) to accept or reject enrollments securely.

---

## 5. Potential Review Questions from Project Guide / Reviewer

**Q1: Why did you use Dynamic Time Warping (DTW) for air signatures instead of a Convolutional Neural Network (CNN) like standard image recognition?**
**Answer:** A CNN is meant for static grid data (pictures). If a signature image plot was simply passed to a CNN, it ignores *how* the user drew the signature. An attacker could simply forge the shape. DTW works on time-series trajectories; it measures speed, acceleration, and sequence strokes. This means the system authenticates the user's specific spatial rhythm and motor memory, making it far superior in security for spatial gestures compared to basic image learning networks.

**Q2: Since video processing is intensive, how do you manage system lag or frame drops when hooked to a web frontend?**
**Answer:** The system splits responsibility cleanly. The OpenCV rendering runs safely behind a separate daemon thread utilizing DirectShow. The backend serves the web a highly compressed MJPEG stream using a buffered asynchronous generator. This allows MediaPipe to maintain high native frame rates without bottlenecking the Flask web-server networking requests.

**Q3: How do you prevent accidental clicks or erratic cursor jumps?**
**Answer:** We implemented multiple safety nets:
1. **Mathematical Smoothening:** X/Y coordinates are passed through division smoothing ratios reducing jitter.
2. **Gesture Stability Buffers:** In critical functions, a gesture must be witnessed for $N$ consecutive frames (e.g., `lock_buffer_size = 5`) before the state locks.
3. **Cooldown Timers:** We ensure clicks/toggles have a ~0.6 to 1.0 second cooldown between requests to prevent massive looping executions.

**Q4: In Facial control, how are you preventing slides from changing when the user randomly looks away?**
**Answer:** We engineered a "Slide Lock Feature". The camera concurrently checks for hand actions during Face mode. The default state is locked. Holding a fist upwards unlocks the slide navigation temporarily. Moving an open palm resets the lock. Without this contextual safety, the product wouldn't perform functionally in an actual presentation environment.

**Q5: How does this authentication handle variables like webcam distance and image resolutions?**
**Answer:** Within `extract_features(...)` in the signature module, the entire trajectory sequence maps from absolute pixel offsets to normalized bounding ratios (0.0 to 1.0 logic). This guarantees size, scale, and varying webcam boundaries do not distort the signature validation mechanics. 

**Q6: What is the benefit of your Hybrid SQL (PostgreSQL) and Blob (Cloudinary) Storage model?**
**Answer:** Image buffers shouldn't be stringified inside relational tables as it massively inflates memory overhead causing slowdowns. We offload heavy media artifacts (images of the signatures) rapidly via the Cloudinary API fetching back a direct `secure_url`. We then store only the essential lightweight structural metadata—`user_id`, `features array (json)`, and `url`—into the PostgreSQL table cleanly for instantaneous traversal. 
