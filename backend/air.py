"""
Air Signature Module - Draw signature in air using hand gestures
Features: Draw (Index up), Save (Index + Middle up), Clear (Fist closed)
Authentication: User enrollment and verification using DTW
Improved gesture detection to prevent accidental clearing
"""

import cv2
import numpy as np
import time
import os
import json
from datetime import datetime
from signature_auth import authenticator
from cloud_storage import upload_signature as cloudinary_upload
from db import get_connection

class AirSignature:
    """Air signature drawing system with robust gesture detection"""
    
    def __init__(self):
        # Drawing state
        self.is_drawing = False
        self.drawing_color = (0, 0, 255)  # Red
        self.drawing_thickness = 3
        
        # Canvas
        self.canvas = None
        self.canvas_initialized = False
        
        # Previous point for continuous drawing
        self.prev_point = None
        
        # Gesture detection with stability
        self.gesture_buffer = []
        self.gesture_buffer_size = 5  # Frames to confirm gesture
        self.current_gesture = "NONE"
        
        # Cooldown for save and clear actions
        self.last_save_time = 0
        self.last_clear_time = 0
        self.action_cooldown = 1.0  # 1 second cooldown
        
        # Hand tracking loss tolerance
        self.frames_without_hand = 0
        self.max_frames_without_hand = 10  # Don't clear if hand lost briefly
        
        # Note: Signatures are now saved to Cloudinary (cloud_storage.py)
        # Local save_directory is no longer used
        
        # ===== AUTHENTICATION FEATURE =====
        # Trajectory tracking for authentication
        self.current_trajectory = []  # Store (x, y) points for current signature
        self.trajectory_recording = False  # Whether to record trajectory
        
        # Authentication mode state
        self.auth_mode = "NONE"  # NONE, ENROLL, VERIFY
        self.auth_username = None  # Username for enrollment/verification
        self.auth_result = None  # Store authentication result
        self.auth_result_time = 0  # Time when auth result was set
        self.auth_result_duration = 3.0  # How long to show auth result (seconds)
    
    def initialize_canvas(self, h, w):
        """Initialize drawing canvas"""
        self.canvas = np.zeros((h, w, 3), dtype=np.uint8)
        self.canvas_initialized = True
    
    def calculate_distance(self, p1, p2):
        """Calculate distance between two points"""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def is_index_finger_up(self, hand_landmarks):
        """
        Check if only index finger is up (drawing gesture)
        Index finger extended, all others closed
        """
        # Finger tip and pip joint indices
        # Index: tip=8, pip=6
        # Middle: tip=12, pip=10
        # Ring: tip=16, pip=14
        # Pinky: tip=20, pip=18
        
        index_tip = hand_landmarks.landmark[8]
        index_pip = hand_landmarks.landmark[6]
        
        middle_tip = hand_landmarks.landmark[12]
        middle_pip = hand_landmarks.landmark[10]
        
        ring_tip = hand_landmarks.landmark[16]
        ring_pip = hand_landmarks.landmark[14]
        
        pinky_tip = hand_landmarks.landmark[20]
        pinky_pip = hand_landmarks.landmark[18]
        
        # Check if index is up (tip above pip)
        index_up = index_tip.y < index_pip.y - 0.02
        
        # Check if other fingers are down (tip below or at pip level)
        middle_down = middle_tip.y >= middle_pip.y - 0.01
        ring_down = ring_tip.y >= ring_pip.y - 0.01
        pinky_down = pinky_tip.y >= pinky_pip.y - 0.01
        
        return index_up and middle_down and ring_down and pinky_down
    
    def is_two_fingers_up(self, hand_landmarks):
        """
        Check if index and middle fingers are up (save gesture)
        Both fingers extended, ring and pinky closed
        """
        index_tip = hand_landmarks.landmark[8]
        index_pip = hand_landmarks.landmark[6]
        
        middle_tip = hand_landmarks.landmark[12]
        middle_pip = hand_landmarks.landmark[10]
        
        ring_tip = hand_landmarks.landmark[16]
        ring_pip = hand_landmarks.landmark[14]
        
        pinky_tip = hand_landmarks.landmark[20]
        pinky_pip = hand_landmarks.landmark[18]
        
        # Check if index and middle are up
        index_up = index_tip.y < index_pip.y - 0.02
        middle_up = middle_tip.y < middle_pip.y - 0.02
        
        # Check if ring and pinky are down
        ring_down = ring_tip.y >= ring_pip.y - 0.01
        pinky_down = pinky_tip.y >= pinky_pip.y - 0.01
        
        return index_up and middle_up and ring_down and pinky_down
    
    def is_fist(self, hand_landmarks):
        """
        Detect fist gesture (all fingers closed) - clear canvas
        All fingertips below their respective PIP joints
        """
        # Check all fingers are closed
        fingers_closed = 0
        
        # Index finger
        if hand_landmarks.landmark[8].y >= hand_landmarks.landmark[6].y - 0.01:
            fingers_closed += 1
        
        # Middle finger
        if hand_landmarks.landmark[12].y >= hand_landmarks.landmark[10].y - 0.01:
            fingers_closed += 1
        
        # Ring finger
        if hand_landmarks.landmark[16].y >= hand_landmarks.landmark[14].y - 0.01:
            fingers_closed += 1
        
        # Pinky finger
        if hand_landmarks.landmark[20].y >= hand_landmarks.landmark[18].y - 0.01:
            fingers_closed += 1
        
        # All 4 fingers must be closed for fist
        return fingers_closed == 4
    
    def detect_gesture(self, hand_landmarks):
        """
        Detect hand gesture with stability checking
        Returns: gesture type (DRAW, SAVE, CLEAR, NONE)
        """
        # Check gestures in priority order
        if self.is_two_fingers_up(hand_landmarks):
            detected = "SAVE"
        elif self.is_index_finger_up(hand_landmarks):
            detected = "DRAW"
        elif self.is_fist(hand_landmarks):
            detected = "CLEAR"
        else:
            detected = "NONE"
        
        # Add to gesture buffer for stability
        self.gesture_buffer.append(detected)
        if len(self.gesture_buffer) > self.gesture_buffer_size:
            self.gesture_buffer.pop(0)
        
        # Confirm gesture if consistent across buffer
        if len(self.gesture_buffer) >= self.gesture_buffer_size:
            # Check if all gestures in buffer are the same
            if all(g == detected for g in self.gesture_buffer):
                return detected
        
        # Return current gesture or NONE if not stable
        return self.current_gesture if len(self.gesture_buffer) < self.gesture_buffer_size else "NONE"
    
    def clear_canvas(self):
        """Clear the drawing canvas and trajectory"""
        if self.canvas is not None:
            self.canvas = np.zeros_like(self.canvas)
            self.prev_point = None
        
        # Clear trajectory for authentication
        self.current_trajectory = []
        self.trajectory_recording = False
    
    def save_signature(self):
        """Save signature to Cloudinary and store metadata in PostgreSQL"""
        if self.canvas is None:
            return None

        # Check if canvas has any drawing
        if np.sum(self.canvas) == 0:
            return None

        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"signature_{timestamp}.png"

        # Encode canvas to PNG bytes
        success, png_buffer = cv2.imencode('.png', self.canvas)
        if not success:
            print("[AirSig] Failed to encode canvas to PNG")
            return None

        png_bytes = png_buffer.tobytes()

        # Upload to Cloudinary
        result = cloudinary_upload(png_bytes, filename)
        if result is None:
            print("[AirSig] Cloudinary upload failed. Please check your .env credentials.")
            return "ERROR_CLOUDINARY"

        # Store metadata in PostgreSQL
        try:
            point_count = len(self.current_trajectory) if self.current_trajectory else 0
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO signatures (filename, cloudinary_public_id, cloudinary_url, point_count)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (filename, result['public_id'], result['secure_url'], point_count)
                    )
        except Exception as e:
            print(f"[AirSig] Failed to save signature metadata to DB: {e}")

        return result['secure_url']
    
    # ===== AUTHENTICATION METHODS =====
    
    def start_enrollment(self, username):
        """
        Start signature enrollment for a user
        
        Args:
            username: Username to enroll
        """
        self.auth_mode = "ENROLL"
        self.auth_username = username
        self.auth_result = None
        self.clear_canvas()
        print(f"[AUTH] Started enrollment for user: {username}")
    
    def start_verification(self, username):
        """
        Start signature verification for a user
        
        Args:
            username: Username to verify
        """
        self.auth_mode = "VERIFY"
        self.auth_username = username
        self.auth_result = None
        self.clear_canvas()
        print(f"[AUTH] Started verification for user: {username}")
    
    def cancel_authentication(self):
        """Cancel current authentication operation"""
        self.auth_mode = "NONE"
        self.auth_username = None
        self.auth_result = None
        self.clear_canvas()
        print("[AUTH] Authentication cancelled")
    
    def process_enrollment(self):
        """
        Process enrollment with current trajectory
        
        Returns:
            dict: Enrollment result from authenticator
        """
        if not self.current_trajectory:
            return {
                'success': False,
                'message': 'No signature drawn. Please draw a signature first.'
            }
        
        result = authenticator.enroll_user(self.auth_username, self.current_trajectory)
        
        # Store result for display
        self.auth_result = result
        self.auth_result_time = time.time()
        
        # Reset auth mode after enrollment
        if result['success']:
            self.auth_mode = "NONE"
            self.auth_username = None
        
        return result
    
    def process_verification(self):
        """
        Process verification with current trajectory
        
        Returns:
            dict: Verification result from authenticator
        """
        if not self.current_trajectory:
            return {
                'authenticated': False,
                'confidence': 0.0,
                'message': 'No signature drawn. Please draw a signature first.'
            }
        
        result = authenticator.verify_signature(self.auth_username, self.current_trajectory)
        
        # Store result for display
        self.auth_result = result
        self.auth_result_time = time.time()
        
        # Reset auth mode after verification
        self.auth_mode = "NONE"
        self.auth_username = None
        
        return result
    
    def draw_ui_indicators(self, frame, h, w, current_gesture):
        """Draw UI indicators showing current gesture and authentication status"""
        
        # ===== AUTHENTICATION STATUS DISPLAY (TOP SECTION) =====
        if self.auth_mode != "NONE":
            # Draw authentication mode banner
            banner_height = 80
            cv2.rectangle(frame, (0, 0), (w, banner_height), (40, 40, 40), -1)
            cv2.rectangle(frame, (0, 0), (w, banner_height), (0, 255, 255), 3)
            
            if self.auth_mode == "ENROLL":
                mode_text = f"ENROLLMENT MODE: {self.auth_username}"
                mode_color = (0, 255, 255)
                instruction = "Draw your signature, then show TWO FINGERS to enroll"
            else:  # VERIFY
                mode_text = f"VERIFICATION MODE: {self.auth_username}"
                mode_color = (255, 165, 0)
                instruction = "Draw your signature, then show TWO FINGERS to verify"
            
            cv2.putText(frame, mode_text, (20, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, mode_color, 2)
            cv2.putText(frame, instruction, (20, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # ===== AUTHENTICATION RESULT DISPLAY =====
        if self.auth_result is not None:
            # Show result for a few seconds
            if time.time() - self.auth_result_time < self.auth_result_duration:
                result_y = 150
                
                if 'success' in self.auth_result:
                    # Enrollment result
                    if self.auth_result['success']:
                        result_color = (0, 255, 0)
                        result_text = "✓ ENROLLMENT SUCCESS"
                    else:
                        result_color = (0, 0, 255)
                        result_text = "✗ ENROLLMENT FAILED"
                else:
                    # Verification result
                    if self.auth_result.get('authenticated', False):
                        result_color = (0, 255, 0)
                        result_text = "✓ AUTHENTICATION SUCCESS"
                        confidence = self.auth_result.get('confidence', 0)
                        result_text += f" ({confidence:.1f}%)"
                    else:
                        result_color = (0, 0, 255)
                        result_text = "✗ AUTHENTICATION FAILED"
                
                # Draw result box
                cv2.rectangle(frame, (w//2 - 250, result_y - 40), 
                             (w//2 + 250, result_y + 60), (0, 0, 0), -1)
                cv2.rectangle(frame, (w//2 - 250, result_y - 40), 
                             (w//2 + 250, result_y + 60), result_color, 3)
                
                cv2.putText(frame, result_text, (w//2 - 230, result_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, result_color, 2)
                
                # Show message
                message = self.auth_result.get('message', '')
                if message:
                    # Split long messages
                    if len(message) > 50:
                        message = message[:50] + "..."
                    cv2.putText(frame, message, (w//2 - 230, result_y + 35),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            else:
                # Clear result after duration expires
                self.auth_result = None
        
        # ===== GESTURE STATUS DISPLAY (BOTTOM SECTION) =====
        # Background for gesture status
        cv2.rectangle(frame, (10, h - 100), (w - 10, h - 10), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, h - 100), (w - 10, h - 10), (255, 255, 255), 2)
        
        # Gesture status
        if current_gesture == "DRAW":
            status_text = "DRAWING MODE"
            status_color = (0, 255, 0)
        elif current_gesture == "SAVE":
            if self.auth_mode != "NONE":
                status_text = "PROCESSING AUTHENTICATION..."
                status_color = (255, 255, 0)
            else:
                status_text = "SAVE GESTURE DETECTED"
                status_color = (255, 255, 0)
        elif current_gesture == "CLEAR":
            status_text = "CLEAR GESTURE DETECTED"
            status_color = (0, 0, 255)
        else:
            status_text = "READY"
            status_color = (255, 255, 255)
        
        cv2.putText(frame, status_text, (20, h - 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Instructions
        cv2.putText(frame, "Index Up: Draw", (20, h - 45),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, "Index + Middle: Save/Auth", (20, h - 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Right side instructions
        cv2.putText(frame, "Fist: Clear", (w - 180, h - 45),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Show trajectory point count if recording
        if self.trajectory_recording and self.current_trajectory:
            points_text = f"Points: {len(self.current_trajectory)}"
            cv2.putText(frame, points_text, (w - 180, h - 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        return frame


# Global instance
air_signature = AirSignature()


def run_air_signature(frame, hand_results, signature_points, frame_w, frame_h):
    """
    Main function for air signature drawing
    Called from main.py with each frame
    Returns: (modified_frame, updated_signature_points)
    """
    global air_signature
    
    # Initialize canvas if needed
    if not air_signature.canvas_initialized:
        air_signature.initialize_canvas(frame_h, frame_w)
    
    current_time = time.time()
    current_gesture = "NONE"
    
    if hand_results and hand_results.multi_hand_landmarks:
        # Hand detected - reset lost frames counter
        air_signature.frames_without_hand = 0
        
        hand_landmarks = hand_results.multi_hand_landmarks[0]
        
        # Draw hand skeleton (connections)
        for connection in [(0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
                          (0, 5), (5, 6), (6, 7), (7, 8),   # Index
                          (0, 9), (9, 10), (10, 11), (11, 12),  # Middle
                          (0, 13), (13, 14), (14, 15), (15, 16),  # Ring
                          (0, 17), (17, 18), (18, 19), (19, 20)]:  # Pinky
            start = hand_landmarks.landmark[connection[0]]
            end = hand_landmarks.landmark[connection[1]]
            start_x, start_y = int(start.x * frame_w), int(start.y * frame_h)
            end_x, end_y = int(end.x * frame_w), int(end.y * frame_h)
            cv2.line(frame, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)
        
        # Draw hand landmarks
        for idx, landmark in enumerate(hand_landmarks.landmark):
            x = int(landmark.x * frame_w)
            y = int(landmark.y * frame_h)
            
            # Highlight fingertips
            if idx in [4, 8, 12, 16, 20]:
                cv2.circle(frame, (x, y), 8, (0, 255, 255), -1)
                cv2.circle(frame, (x, y), 10, (255, 255, 255), 2)
            else:
                cv2.circle(frame, (x, y), 4, (255, 255, 255), -1)
        
        # Get index finger tip position (for drawing)
        index_tip = hand_landmarks.landmark[8]
        index_x = int(index_tip.x * frame_w)
        index_y = int(index_tip.y * frame_h)
        
        # Detect gesture with stability
        current_gesture = air_signature.detect_gesture(hand_landmarks)
        air_signature.current_gesture = current_gesture
        
        # Handle gestures
        if current_gesture == "DRAW":
            # Drawing mode - index finger up
            air_signature.is_drawing = True
            
            # Record trajectory for authentication
            if not air_signature.trajectory_recording:
                air_signature.trajectory_recording = True
                air_signature.current_trajectory = []
            
            # Add point to trajectory
            air_signature.current_trajectory.append((index_x, index_y))
            
            # Draw on canvas with smooth lines
            if air_signature.prev_point is not None:
                cv2.line(air_signature.canvas,
                        air_signature.prev_point,
                        (index_x, index_y),
                        air_signature.drawing_color,
                        air_signature.drawing_thickness)
            
            air_signature.prev_point = (index_x, index_y)
            
            # Visual feedback - glowing cursor
            cv2.circle(frame, (index_x, index_y), 12, (0, 255, 255), -1)
            cv2.circle(frame, (index_x, index_y), 15, (255, 255, 0), 2)
        
        elif current_gesture == "SAVE":
            # Save gesture - index + middle fingers up
            air_signature.is_drawing = False
            air_signature.prev_point = None
            
            # Stop recording trajectory
            air_signature.trajectory_recording = False
            
            # Perform save action with cooldown
            if current_time - air_signature.last_save_time > air_signature.action_cooldown:
                
                # Check if in authentication mode
                if air_signature.auth_mode == "ENROLL":
                    # Process enrollment
                    result = air_signature.process_enrollment()
                    print(f"[AUTH] Enrollment result: {result}")
                    
                elif air_signature.auth_mode == "VERIFY":
                    # Process verification
                    result = air_signature.process_verification()
                    print(f"[AUTH] Verification result: {result}")
                    
                else:
                    # Normal save mode — uploads to Cloudinary
                    cloud_url = air_signature.save_signature()
                    if cloud_url == "ERROR_CLOUDINARY":
                        cv2.putText(frame, "UPLOAD FAILED!", (frame_w//2 - 130, frame_h//2),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                        cv2.putText(frame, "Check Cloudinary keys in .env", 
                                   (frame_w//2 - 180, frame_h//2 + 40),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    elif cloud_url:
                        cv2.putText(frame, "SIGNATURE SAVED!", (frame_w//2 - 150, frame_h//2),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                        cv2.putText(frame, "Uploaded to Cloudinary", 
                                   (frame_w//2 - 150, frame_h//2 + 40),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    else:
                        cv2.putText(frame, "Nothing to save!", (frame_w//2 - 120, frame_h//2),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                air_signature.last_save_time = current_time
            
            # Visual feedback for save gesture
            middle_tip = hand_landmarks.landmark[12]
            middle_x = int(middle_tip.x * frame_w)
            middle_y = int(middle_tip.y * frame_h)
            cv2.circle(frame, (index_x, index_y), 10, (255, 255, 0), -1)
            cv2.circle(frame, (middle_x, middle_y), 10, (255, 255, 0), -1)
        
        elif current_gesture == "CLEAR":
            # Clear gesture - fist closed
            air_signature.is_drawing = False
            air_signature.prev_point = None
            
            # Perform clear action with cooldown
            if current_time - air_signature.last_clear_time > air_signature.action_cooldown:
                air_signature.clear_canvas()
                cv2.putText(frame, "CANVAS CLEARED!", (frame_w//2 - 130, frame_h//2),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                air_signature.last_clear_time = current_time
            
            # Visual feedback for clear gesture
            wrist = hand_landmarks.landmark[0]
            wrist_x = int(wrist.x * frame_w)
            wrist_y = int(wrist.y * frame_h)
            cv2.circle(frame, (wrist_x, wrist_y), 20, (0, 0, 255), 3)
        
        else:
            # No recognized gesture
            air_signature.is_drawing = False
            air_signature.prev_point = None
    
    else:
        # No hand detected
        air_signature.frames_without_hand += 1
        air_signature.is_drawing = False
        air_signature.prev_point = None
        
        # Only reset gesture buffer after significant loss of tracking
        if air_signature.frames_without_hand > air_signature.max_frames_without_hand:
            air_signature.gesture_buffer = []
            air_signature.current_gesture = "NONE"
        
        # Display "no hand" message
        cv2.putText(frame, "No hand detected - Show your hand", (10, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    # Overlay canvas on frame
    if air_signature.canvas is not None:
        # Create mask of non-black pixels in canvas
        mask = cv2.cvtColor(air_signature.canvas, cv2.COLOR_BGR2GRAY)
        mask = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)[1]
        
        # Overlay canvas on frame with transparency
        frame_copy = frame.copy()
        frame_copy[mask > 0] = air_signature.canvas[mask > 0]
        frame = cv2.addWeighted(frame, 0.6, frame_copy, 0.4, 0)
    
    # Draw UI indicators
    frame = air_signature.draw_ui_indicators(frame, frame_h, frame_w, current_gesture)
    
    # Display current gesture at top
    cv2.putText(frame, f"Gesture: {current_gesture}", (10, 80),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
    
    return frame, signature_points