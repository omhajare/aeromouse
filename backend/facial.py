"""
Facial Control Module - Head Movement Based Control
Features: Presentation navigation (Left/Right) with slide lock/unlock, Scroll control (Up/Down)

SLIDE LOCK FEATURE:
- Hand with all 5 fingers open: LOCK slides
- Hand with all fingers closed (fist): UNLOCK slides
- Lock persists until explicit unlock
"""

import cv2
import numpy as np
import pyautogui
import time
import sys
import ctypes

def _scroll_foreground(amount):
    """Send WM_MOUSEWHEEL to the foreground window (works regardless of mouse position)."""
    if sys.platform == 'win32':
        WM_MOUSEWHEEL = 0x020A
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        # WPARAM high word = wheel delta, low word = virtual key flags (0)
        wheel_delta = int(amount) * 120  # 120 = one notch
        wparam = (wheel_delta & 0xFFFF) << 16  # Pack delta into high word
        ctypes.windll.user32.SendMessageW(hwnd, WM_MOUSEWHEEL, wparam, 0)
    else:
        pyautogui.scroll(amount)

class FacialController:
    """Facial gesture based control system with slide lock feature"""
    
    def __init__(self):
        # Head position tracking with history for smoothing
        self.nose_position_history = []
        self.history_size = 5  # Track last 5 positions for smoothing
        
        # IMPROVED THRESHOLDS - Reduced for easier triggering
        self.vertical_threshold = 10  # Reduced from 15 (easier vertical movement)
        self.horizontal_threshold = 12  # Reduced from 18 (easier horizontal movement)
        
        # Cooldown timers - Optimized for responsiveness
        self.action_cooldown = 0.6  # Reduced from 1.0 for faster response
        self.last_action_time = 0
        self.last_action_type = None
        
        # Calibration
        self.baseline_y = None
        self.baseline_x = None
        self.calibration_frames = 0
        self.calibrated = False
        
        # IMPROVED STABILITY - Reduced buffer for faster response
        self.movement_buffer = []
        self.buffer_size = 3  # Reduced from 4 (faster detection)
        
        # ========== SLIDE LOCK/UNLOCK FEATURE ==========
        self.slides_locked = False  # Initially unlocked
        self.last_lock_gesture_time = 0
        self.lock_gesture_cooldown = 1.0  # Prevent rapid lock/unlock toggling
        self.lock_gesture_buffer = []
        self.lock_buffer_size = 5  # Confirm lock gesture over 5 frames
        
        # Gesture detection (unused but kept for compatibility)
        self.mouth_open_threshold = 0.03
        self.eyebrow_raise_threshold = 0.015
    
    def calculate_distance(self, p1, p2):
        """Calculate Euclidean distance between two points"""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def smooth_position(self, nose_y, nose_x):
        """
        SMOOTHNESS IMPROVEMENT: Apply moving average to reduce jitter
        This prevents micro-movements from triggering actions
        """
        self.nose_position_history.append((nose_y, nose_x))
        
        # Keep only recent history
        if len(self.nose_position_history) > self.history_size:
            self.nose_position_history.pop(0)
        
        # Calculate average position
        avg_y = sum(pos[0] for pos in self.nose_position_history) / len(self.nose_position_history)
        avg_x = sum(pos[1] for pos in self.nose_position_history) / len(self.nose_position_history)
        
        return avg_y, avg_x
    
    def calibrate(self, nose_y, nose_x):
        """Calibrate baseline position"""
        if self.calibration_frames < 30:
            if self.baseline_y is None:
                self.baseline_y = nose_y
                self.baseline_x = nose_x
            else:
                self.baseline_y = (self.baseline_y + nose_y) / 2
                self.baseline_x = (self.baseline_x + nose_x) / 2
            self.calibration_frames += 1
        else:
            self.calibrated = True
    
    def detect_hand_lock_gesture(self, hand_results):
        """
        ========== SLIDE LOCK/UNLOCK DETECTION ==========
        
        Detect hand gestures for locking/unlocking slides:
        
        LOCK:   All 5 fingers open (🖐️) → Slides locked
        UNLOCK: All fingers closed - Fist (✊) → Slides unlocked
        
        Returns: "LOCK", "UNLOCK", or None
        """
        # No hand detected
        if not hand_results or not hand_results.multi_hand_landmarks:
            return None
        
        hand_landmarks = hand_results.multi_hand_landmarks[0]
        
        # Check finger states (compare tip vs pip joint positions)
        fingers_extended = 0
        fingers_closed = 0
        
        # Check each finger: index, middle, ring, pinky
        finger_pairs = [
            (8, 6),   # Index finger
            (12, 10), # Middle finger
            (16, 14), # Ring finger
            (20, 18)  # Pinky finger
        ]
        
        # Also check thumb separately
        thumb_tip = hand_landmarks.landmark[4]
        thumb_ip = hand_landmarks.landmark[3]
        
        # Count extended and closed fingers
        for tip_idx, pip_idx in finger_pairs:
            tip = hand_landmarks.landmark[tip_idx]
            pip = hand_landmarks.landmark[pip_idx]
            
            if tip.y < pip.y - 0.02:  # Finger extended (tip above pip)
                fingers_extended += 1
            elif tip.y > pip.y + 0.01:  # Finger closed (tip below pip)
                fingers_closed += 1
        
        # Check thumb (different logic due to thumb orientation)
        if abs(thumb_tip.x - thumb_ip.x) > 0.05:  # Thumb extended
            fingers_extended += 1
        else:  # Thumb closed
            fingers_closed += 1
        
        detected_gesture = None
        
        # ========== LOCK GESTURE: ALL 5 FINGERS OPEN ==========
        if fingers_extended >= 5:
            detected_gesture = "LOCK"
        
        # ========== UNLOCK GESTURE: ALL FINGERS CLOSED (FIST) ==========
        elif fingers_closed >= 5:
            detected_gesture = "UNLOCK"
        
        # Add to buffer for stability (prevent false triggers from noise)
        if detected_gesture:
            self.lock_gesture_buffer.append(detected_gesture)
            if len(self.lock_gesture_buffer) > self.lock_buffer_size:
                self.lock_gesture_buffer.pop(0)
            
            # Confirm gesture only if consistent across all buffered frames
            if len(self.lock_gesture_buffer) >= self.lock_buffer_size:
                if all(g == detected_gesture for g in self.lock_gesture_buffer):
                    return detected_gesture
        
        return None
    
    def update_slide_lock(self, lock_gesture):
        """
        ========== UPDATE SLIDE LOCK STATE ==========
        
        Lock persists until explicit unlock
        Cooldown prevents rapid toggling
        
        Returns: True if state changed, False otherwise
        """
        current_time = time.time()
        
        # Prevent rapid toggling
        if current_time - self.last_lock_gesture_time < self.lock_gesture_cooldown:
            return False
        
        state_changed = False
        
        # Lock slides if currently unlocked
        if lock_gesture == "LOCK" and not self.slides_locked:
            self.slides_locked = True
            self.last_lock_gesture_time = current_time
            self.lock_gesture_buffer = []
            state_changed = True
        
        # Unlock slides if currently locked
        elif lock_gesture == "UNLOCK" and self.slides_locked:
            self.slides_locked = False
            self.last_lock_gesture_time = current_time
            self.lock_gesture_buffer = []
            state_changed = True
        
        return state_changed
    
    def detect_head_gesture(self, nose_y, nose_x):
        """
        IMPROVED HEAD MOVEMENT DETECTION:
        - Reduced thresholds for easier triggering
        - Smoothed position tracking
        - Better stability
        
        Returns: (gesture_type, direction)
        """
        if not self.calibrated:
            self.calibrate(nose_y, nose_x)
            return "CALIBRATING", None
        
        # SMOOTHNESS IMPROVEMENT: Apply moving average filter
        smooth_y, smooth_x = self.smooth_position(nose_y, nose_x)
        
        # Calculate deviation from baseline (normalized coordinates)
        vertical_movement = (smooth_y - self.baseline_y) * 1000
        horizontal_movement = (smooth_x - self.baseline_x) * 1000
        
        current_time = time.time()
        detected_gesture = None
        
        # Check cooldown (prevents continuous triggering)
        if current_time - self.last_action_time < self.action_cooldown:
            return "COOLDOWN", None
        
        # ========== PRIMARY: HORIZONTAL MOVEMENT (PPT SLIDES) ==========
        if abs(horizontal_movement) > self.horizontal_threshold:
            # Ensure horizontal is dominant (not diagonal)
            if abs(horizontal_movement) > abs(vertical_movement) * 1.15:
                if horizontal_movement > 0:
                    detected_gesture = "HEAD_RIGHT"  # Next slide
                else:
                    detected_gesture = "HEAD_LEFT"   # Previous slide
        
        # ========== SECONDARY: VERTICAL MOVEMENT (SCROLLING) ==========
        elif abs(vertical_movement) > self.vertical_threshold:
            # Ensure vertical is dominant
            if abs(vertical_movement) > abs(horizontal_movement) * 1.15:
                if vertical_movement > 0:
                    detected_gesture = "HEAD_DOWN"   # Scroll down
                else:
                    detected_gesture = "HEAD_UP"     # Scroll up
        
        # ========== STABILITY BUFFER ==========
        if detected_gesture:
            self.movement_buffer.append(detected_gesture)
            if len(self.movement_buffer) > self.buffer_size:
                self.movement_buffer.pop(0)
            
            # Confirm gesture if consistent
            if len(self.movement_buffer) >= self.buffer_size:
                if all(g == detected_gesture for g in self.movement_buffer):
                    return detected_gesture, self.get_direction(detected_gesture)
        
        return "NEUTRAL", None
    
    def get_direction(self, gesture):
        """Get direction string for gesture"""
        directions = {
            "HEAD_UP": "UP",
            "HEAD_DOWN": "DOWN",
            "HEAD_LEFT": "LEFT",
            "HEAD_RIGHT": "RIGHT"
        }
        return directions.get(gesture, "UNKNOWN")
    
    def perform_head_action(self, gesture):
        """
        Perform action based on head gesture
        
        ========== SLIDE LOCK GATE ==========
        If slides_locked == True:
            - Ignore HEAD_LEFT and HEAD_RIGHT
            - Do NOT change slides under any condition
        
        If slides_locked == False:
            - Allow HEAD_LEFT and HEAD_RIGHT to work normally
        
        PPT NAVIGATION (gated by lock state):
        HEAD_LEFT  -> Previous Slide (Left Arrow)
        HEAD_RIGHT -> Next Slide (Right Arrow)
        
        SCROLLING (always available regardless of lock):
        HEAD_UP    -> Scroll Up
        HEAD_DOWN  -> Scroll Down
        """
        current_time = time.time()
        
        # Prevent repeated actions
        if current_time - self.last_action_time < self.action_cooldown:
            return False
        
        # Extra protection for same action
        if gesture == self.last_action_type:
            if current_time - self.last_action_time < self.action_cooldown * 1.3:
                return False
        
        action_performed = False
        
        # ========== SLIDE LOCK CHECK: GATE SLIDE MOVEMENTS ==========
        if gesture in ["HEAD_LEFT", "HEAD_RIGHT"]:
            if self.slides_locked:
                # Slides are LOCKED - ignore head movements for slides
                return False  # Return False = action not performed
        
        # ========== PPT SLIDE NAVIGATION (only if unlocked) ==========
        if gesture == "HEAD_RIGHT":
            pyautogui.press('right')
            action_performed = True
            
        elif gesture == "HEAD_LEFT":
            pyautogui.press('left')
            action_performed = True
        
        # ========== VERTICAL SCROLLING (always works) ==========    
        elif gesture == "HEAD_UP":
            # Send scroll to focused window (not just window under cursor)
            _scroll_foreground(5)
            action_performed = True
            
        elif gesture == "HEAD_DOWN":
            _scroll_foreground(-5)
            action_performed = True
        
        # Update state if action performed
        if action_performed:
            self.last_action_time = current_time
            self.last_action_type = gesture
            self.movement_buffer = []
        
        return action_performed
    
    def detect_mouth_open(self, face_landmarks, frame_h):
        """Detect if mouth is open (unused but kept for compatibility)"""
        upper_lip = face_landmarks.landmark[13]
        lower_lip = face_landmarks.landmark[14]
        distance = abs(upper_lip.y - lower_lip.y)
        return distance > self.mouth_open_threshold
    
    def detect_eyebrow_raise(self, face_landmarks):
        """Detect eyebrow raise (unused but kept for compatibility)"""
        left_eyebrow = face_landmarks.landmark[70]
        right_eyebrow = face_landmarks.landmark[300]
        nose_bridge = face_landmarks.landmark[6]
        left_distance = abs(left_eyebrow.y - nose_bridge.y)
        right_distance = abs(right_eyebrow.y - nose_bridge.y)
        avg_distance = (left_distance + right_distance) / 2
        return avg_distance > self.eyebrow_raise_threshold


# Global instance
facial_controller = FacialController()


def run_facial_control(frame, face_results, frame_w, frame_h, hand_results=None):
    """
    Main function for facial control
    Called from main.py with each frame
    
    NEW PARAMETER: hand_results (optional)
    - If provided: slide lock/unlock feature is active
    - If None: lock feature disabled, works as before
    """
    global facial_controller
    
    # ========== SLIDE LOCK/UNLOCK DETECTION (if hand_results provided) ==========
    if hand_results:
        lock_gesture = facial_controller.detect_hand_lock_gesture(hand_results)
        if lock_gesture:
            state_changed = facial_controller.update_slide_lock(lock_gesture)
            if state_changed:
                # Visual feedback for lock state change
                if facial_controller.slides_locked:
                    lock_text = "SLIDES LOCKED"
                    lock_color = (0, 0, 255)  # Red
                else:
                    lock_text = "SLIDES UNLOCKED"
                    lock_color = (0, 255, 0)  # Green
                
                cv2.putText(frame, lock_text, (frame_w//2 - 150, frame_h//2),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.2, lock_color, 3)
    
    # ========== FACE DETECTION AND GESTURE CONTROL ==========
    if face_results and face_results.multi_face_landmarks:
        face_landmarks = face_results.multi_face_landmarks[0]
        
        # Get nose tip position (landmark 1)
        nose = face_landmarks.landmark[1]
        nose_x = int(nose.x * frame_w)
        nose_y = int(nose.y * frame_h)
        
        # Draw nose point
        cv2.circle(frame, (nose_x, nose_y), 8, (0, 255, 0), -1)
        
        # Draw key facial landmarks
        for idx in [70, 300, 13, 14, 6]:
            landmark = face_landmarks.landmark[idx]
            x = int(landmark.x * frame_w)
            y = int(landmark.y * frame_h)
            cv2.circle(frame, (x, y), 3, (255, 0, 255), -1)
        
        # Detect head gesture
        gesture, direction = facial_controller.detect_head_gesture(nose.y, nose.x)
        
        # Display calibration status
        if gesture == "CALIBRATING":
            progress = (facial_controller.calibration_frames / 30) * 100
            cv2.putText(frame, f"Calibrating: {progress:.0f}%", (10, 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame, "Keep your head still...", (10, 110),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
        else:
            # ========== DISPLAY LOCK STATUS (if hand detection active) ==========
            if hand_results and facial_controller.slides_locked:
                cv2.putText(frame, "LOCKED", (frame_w - 150, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Display detected gesture
            if gesture != "NEUTRAL" and gesture != "COOLDOWN":
                cv2.putText(frame, f"Gesture: {gesture}", (10, 80),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
                # Perform action and show feedback
                if facial_controller.perform_head_action(gesture):
                    # Visual feedback
                    if gesture in ["HEAD_LEFT", "HEAD_RIGHT"]:
                        color = (255, 0, 255) if gesture == "HEAD_LEFT" else (0, 255, 255)
                        action_text = "Previous" if gesture == "HEAD_LEFT" else "Next"
                    else:
                        color = (0, 255, 0) if gesture == "HEAD_UP" else (0, 0, 255)
                        action_text = "Scroll Up" if gesture == "HEAD_UP" else "Scroll Down"
                    
                    cv2.putText(frame, action_text, (10, 120),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                    cv2.circle(frame, (nose_x, nose_y), 30, color, 3)
                
                # ========== SHOW "LOCKED" MESSAGE WHEN TRYING TO CHANGE SLIDES ==========
                elif gesture in ["HEAD_LEFT", "HEAD_RIGHT"] and facial_controller.slides_locked:
                    cv2.putText(frame, "Slides Locked", (10, 120),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                cv2.putText(frame, "Gesture: NEUTRAL", (10, 80),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Draw baseline crosshair
        if facial_controller.calibrated and facial_controller.baseline_y:
            baseline_screen_y = int(facial_controller.baseline_y * frame_h)
            baseline_screen_x = int(facial_controller.baseline_x * frame_w)
            
            cv2.line(frame, (0, baseline_screen_y), (frame_w, baseline_screen_y),
                    (0, 255, 255), 1)
            cv2.line(frame, (baseline_screen_x, 0), (baseline_screen_x, frame_h),
                    (0, 255, 255), 1)
    
    else:
        cv2.putText(frame, "No face detected", (10, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        # Reset on face loss
        facial_controller.calibrated = False
        facial_controller.calibration_frames = 0
        facial_controller.movement_buffer = []
        facial_controller.nose_position_history = []
    
    # Instructions
    instructions = "Head L/R: Prev/Next | Head U/D: Scroll"
    if hand_results:
        instructions += " | Hand Open: Lock | Fist: Unlock"
    
    cv2.putText(frame, instructions, (10, frame_h - 15),
               cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    
    return frame
