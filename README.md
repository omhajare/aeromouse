# Aero-Mouse Systems

Control your cursor with a gesture, navigate with your gaze, and authenticate with your unique air signature — all in real time. No hardware. No touch. Just you.

Aero-Mouse is a cutting-edge Human-Computer Interaction (HCI) project that leverages computer vision and machine learning to build a completely touchless interface capable of mouse control, facial navigation, and 3D space signature authentication.

---

## Features

- **Virtual Mouse Control**
  Navigate, click, scroll, and drag using fluid hand gestures captured by your webcam.
- **Gaze and Facial Navigation**
  Hands-free navigation powered by high-precision facial mesh tracking.
- **Air Signature Authentication**
  Draw your unique signature in the air to securely authenticate. powered by Dynamic Time Warping (DTW) algorithms for accuracy, comparing spatial trajectories rather than static images.
- **Real-Time Data Processing**
  Seamless synchronization between the gesture-capturing backend and an immersive 3D-accelerated frontend.

---

## Technical Architecture

The architecture is divided into two decoupled layers:

### Frontend
- **Framework:** React 19, Vite
- **Styling:** TailwindCSS
- **3D Rendering:** Three.js, React Three Fiber, React Three Drei
- **Animation:** Motion

### Backend
- **Server:** Python Flask REST API
- **Computer Vision:** OpenCV, Google MediaPipe (Hands and Face Mesh)
- **Authentication:** FastDTW (Dynamic Time Warping), SciPy
- **System Control:** PyAutoGUI, Pynput
- **Database & Storage:** PostgreSQL, Cloudinary

---

## Installation & Setup

### Prerequisites
- Python 3.9 - 3.11
- Node.js (v18+)
- PostgreSQL installed and running
- Cloudinary account for media storage
- Standard webcam 

### Backend Setup

1. **Navigate to the backend directory and set up a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the root backend directory:
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=aeromouse
   DB_USER=your_user
   DB_PASSWORD=your_password

   CLOUDINARY_CLOUD_NAME=your_cloud_name
   CLOUDINARY_API_KEY=your_api_key
   CLOUDINARY_API_SECRET=your_api_secret
   ```

4. **Run the Flask server:**
   ```bash
   cd backend
   python app.py
   ```

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install Node modules:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

The frontend will start at `http://localhost:3000`.

---

## Usage

1. Complete the installation and start both servers.
2. Ensure you have decent lighting facing your webcam.
3. Open the frontend dashboard `http://localhost:3000`.
4. Register a new user profile by executing your Air Signature.
5. Enable gesture control and interact with the physical OS without touching your physical mouse.

---

**Disclaimer**
This system was built primarily for academic and demonstration purposes. Performance may vary based on webcam resolution, frame rate constraints, and ambient environmental lighting.
