"""
AERO MOUSE - Multi-Modal Touchless HCI System
Main Controller - Central camera loop and mode switching
Author: Final Year Engineering Project
"""

import cv2
import mediapipe as mp
import threading
import time
from mouse import run_virtual_mouse
from facial import run_facial_control
from air import run_air_signature

class AeroMouseController:
    """Central controller for AERO MOUSE system"""
    
    def __init__(self):
        self.cap = None
        self.current_mode = 0  # 0: Standby, 1: Mouse, 2: Facial, 3: Air Signature
        self.running = False
        self.start_failed = False  # Set True if camera cannot open
        self.signature_points = []  # For air signature feature
        
        # Frame buffering for web stream
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.enable_native_ui = False  # Set True if running without Flask
        
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.mp_face_mesh = mp.solutions.face_mesh
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        
    def start(self):
        """Initialize camera and start the main loop"""
        # Using cv2.CAP_DSHOW (DirectShow) is much faster on Windows and avoids hangs
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        if not self.cap.isOpened():
            print("Error: Cannot access camera")
            self.start_failed = True  # Signal failure so watcher can exit
            return
        
        # ── Camera is open and ready — mark system as running ──
        self.running = True
        print("AERO MOUSE System Started")
        print("Controls:")
        print("  Press '1' - Virtual Mouse Mode")
        print("  Press '2' - Facial Control Mode")
        print("  Press '3' - Air Signature Mode")
        print("  Press 'Q' - Quit Application")
        
        self.main_loop()
    
    def main_loop(self):
        """Single camera loop handling all modes"""
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Failed to capture frame")
                break
            
            # Flip frame for mirror effect
            frame = cv2.flip(frame, 1)
            h, w, c = frame.shape
            
            # Convert BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Display current mode
            mode_text = self.get_mode_text()
            cv2.rectangle(frame, (10, 10), (300, 50), (0, 0, 0), -1)
            cv2.putText(frame, mode_text, (20, 35), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Route to appropriate feature based on current mode
            if self.current_mode == 1:
                # Virtual Mouse Mode
                hand_results = self.hands.process(rgb_frame)
                frame = run_virtual_mouse(frame, hand_results, w, h)
                
            elif self.current_mode == 2:
                # Facial Control Mode
                face_results = self.face_mesh.process(rgb_frame)
                frame = run_facial_control(frame, face_results, w, h)
                
            elif self.current_mode == 3:
                # Air Signature Mode
                hand_results = self.hands.process(rgb_frame)
                frame, self.signature_points = run_air_signature(
                    frame, hand_results, self.signature_points, w, h
                )
            
            # Store latest frame for Flask stream
            with self.frame_lock:
                self.latest_frame = frame.copy()
            
            # Display frame natively if enabled OR if we are NOT in Air Signature mode (3)
            show_native = self.enable_native_ui or (self.current_mode != 3)
            
            if show_native:
                cv2.imshow('AERO MOUSE - Touchless HCI System', frame)
            else:
                try:
                    if cv2.getWindowProperty('AERO MOUSE - Touchless HCI System', cv2.WND_PROP_VISIBLE) > 0:
                        cv2.destroyWindow('AERO MOUSE - Touchless HCI System')
                except cv2.error:
                    pass
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('1'):
                self.switch_mode(1)
            elif key == ord('2'):
                self.switch_mode(2)
            elif key == ord('3'):
                self.switch_mode(3)
            elif key == ord('q') or key == ord('Q'):
                self.running = False
        
        self.cleanup()
    
    def switch_mode(self, mode):
        """Switch between different modes"""
        if mode == self.current_mode:
            return
        
        self.current_mode = mode
        
        # Clear signature points when switching modes
        if mode != 3:
            self.signature_points = []
        
        print(f"Switched to {self.get_mode_text()}")
    
    def get_mode_text(self):
        """Get current mode display text"""
        modes = {
            0: "MODE: Standby",
            1: "MODE: Virtual Mouse",
            2: "MODE: Facial Control",
            3: "MODE: Air Signature"
        }
        return modes.get(self.current_mode, "MODE: Unknown")
    
    def cleanup(self):
        """Release resources"""
        print("Shutting down AERO MOUSE system...")
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        self.hands.close()
        self.face_mesh.close()
        print("System shutdown complete")
    
    def set_mode(self, mode):
        """API method to set mode (called from Flask)"""
        if 0 <= mode <= 3:
            self.switch_mode(mode)
            return True
        return False


# Global controller instance for Flask integration
controller = None

def run_controller():
    """Run the controller in a separate thread"""
    global controller
    controller = AeroMouseController()
    controller.start()

def start_system():
    """Start the system in a background thread"""
    global controller
    if controller is None or not controller.running:
        thread = threading.Thread(target=run_controller, daemon=True)
        thread.start()
        # Do NOT sleep here — the watcher thread in app.py polls asynchronously

def get_controller():
    """Get the global controller instance"""
    return controller


if __name__ == "__main__":
    # Run directly without Flask
    controller = AeroMouseController()
    controller.enable_native_ui = True
    controller.start()