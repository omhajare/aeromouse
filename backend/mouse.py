"""
Virtual Mouse Module - Hand Gesture Based Mouse Control
Features: Cursor movement, Left/Right click, Double click, Scroll, Drag & Drop
"""

import cv2
import numpy as np
import pyautogui
import math
import time

# PyAutoGUI settings
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

class VirtualMouse:
    """Hand gesture based virtual mouse controller"""
    
    def __init__(self):
        self.screen_w, self.screen_h = pyautogui.size()
        self.smoothening = 5
        self.prev_x, self.prev_y = 0, 0
        self.curr_x, self.curr_y = 0, 0
        
        # Click detection
        self.click_threshold = 30
        self.click_cooldown = 0.3
        self.last_click_time = 0
        self.last_double_click_time = 0
        self.double_click_threshold = 0.4
        
        # Drag detection
        self.is_dragging = False
        self.drag_start_time = 0
        
        # Scroll detection
        self.scroll_mode = False
        self.prev_scroll_y = 0
        
    def get_distance(self, p1, p2):
        """Calculate Euclidean distance between two points"""
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def get_angle(self, p1, p2, p3):
        """Calculate angle between three points"""
        v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
        v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])
        
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
        return np.degrees(angle)
    
    def is_finger_up(self, hand_landmarks, finger_tip_id, finger_pip_id):
        """Check if a finger is extended"""
        tip = hand_landmarks.landmark[finger_tip_id]
        pip = hand_landmarks.landmark[finger_pip_id]
        return tip.y < pip.y
    
    def is_thumb_extended(self, hand_landmarks):
        """
        Check if thumb is extended laterally (L-shape outward).
        Uses vector projection of the thumb relative to the palm width.
        This is completely invariant to hand rotation, camera mirroring, and left/right hand.
        """
        p17 = hand_landmarks.landmark[17] # pinky MCP
        p5 = hand_landmarks.landmark[5]   # index MCP
        p4 = hand_landmarks.landmark[4]   # thumb tip
        
        # Palm lateral vector (Points from pinky side to index side)
        v_palm_x = p5.x - p17.x
        v_palm_y = p5.y - p17.y
        
        # Thumb vector (Points from index MCP to thumb tip)
        v_thumb_x = p4.x - p5.x
        v_thumb_y = p4.y - p5.y
        
        # Dot product (Projects thumb direction onto the lateral palm direction)
        dot = v_palm_x * v_thumb_x + v_palm_y * v_thumb_y
        
        # Normalize by squared length of palm vector
        palm_sq_len = v_palm_x**2 + v_palm_y**2 + 1e-6
        projection_ratio = dot / palm_sq_len
        
        # If ratio > 0.5, the thumb is extending outward to the side by at least half a palm width.
        # A pinch (thumb meeting index tip) moves almost orthogonally, giving a ratio near 0.
        return projection_ratio > 0.6

    def detect_gesture(self, hand_landmarks):
        """Detect hand gesture and return gesture type"""
        # Get finger states
        index_up = self.is_finger_up(hand_landmarks, 8, 6)
        middle_up = self.is_finger_up(hand_landmarks, 12, 10)
        ring_up = self.is_finger_up(hand_landmarks, 16, 14)
        pinky_up = self.is_finger_up(hand_landmarks, 20, 18)
        thumb_extended = self.is_thumb_extended(hand_landmarks)
        
        # Gesture 2: Index + Thumb extended laterally (Left click) — checked BEFORE MOVE
        if index_up and thumb_extended and not middle_up and not ring_up and not pinky_up:
            return "LEFT_CLICK"
        
        # Gesture 1: Index finger only (Move cursor)
        elif index_up and not middle_up and not ring_up and not pinky_up:
            return "MOVE"
        
        # Gesture 4: All fingers up (Scroll mode) — before right click
        elif index_up and middle_up and ring_up and pinky_up:
            return "SCROLL"
        
        # Gesture 3: Index + Middle + Ring (Right click)
        elif index_up and middle_up and ring_up and not pinky_up:
            return "RIGHT_CLICK"
        
        # Gesture 5: Pinch (Drag)
        else:
            index_tip = hand_landmarks.landmark[8]
            thumb_tip = hand_landmarks.landmark[4]
            distance = self.get_distance(
                (index_tip.x, index_tip.y),
                (thumb_tip.x, thumb_tip.y)
            )
            if distance < 0.05:
                return "DRAG"
        
        return "NONE"
    
    def move_cursor(self, x, y, frame_w, frame_h):
        """Move cursor with smoothing"""
        # Convert frame coordinates to screen coordinates
        screen_x = np.interp(x, (100, frame_w - 100), (0, self.screen_w))
        screen_y = np.interp(y, (100, frame_h - 100), (0, self.screen_h))
        
        # Smoothing
        self.curr_x = self.prev_x + (screen_x - self.prev_x) / self.smoothening
        self.curr_y = self.prev_y + (screen_y - self.prev_y) / self.smoothening
        
        pyautogui.moveTo(self.curr_x, self.curr_y)
        
        self.prev_x, self.prev_y = self.curr_x, self.curr_y
    
    def left_click(self):
        """Perform left click with cooldown"""
        current_time = time.time()
        
        if current_time - self.last_click_time > self.click_cooldown:
            # Check for double click
            if current_time - self.last_double_click_time < self.double_click_threshold:
                pyautogui.doubleClick()
                self.last_double_click_time = 0
                return "DOUBLE_CLICK"
            else:
                pyautogui.click()
                self.last_double_click_time = current_time
            
            self.last_click_time = current_time
            return "LEFT_CLICK"
        
        return None
    
    def right_click(self):
        """Perform right click"""
        current_time = time.time()
        if current_time - self.last_click_time > self.click_cooldown:
            pyautogui.rightClick()
            self.last_click_time = current_time
            return "RIGHT_CLICK"
        return None
    
    def start_drag(self):
        """Start drag operation"""
        if not self.is_dragging:
            pyautogui.mouseDown()
            self.is_dragging = True
            self.drag_start_time = time.time()
    
    def stop_drag(self):
        """Stop drag operation"""
        if self.is_dragging:
            pyautogui.mouseUp()
            self.is_dragging = False
    
    def scroll(self, y):
        """Perform scrolling"""
        if self.prev_scroll_y != 0:
            scroll_delta = int((self.prev_scroll_y - y) * 2)
            if abs(scroll_delta) > 5:
                pyautogui.scroll(scroll_delta)
        self.prev_scroll_y = y


# Global instance
mouse_controller = VirtualMouse()


def run_virtual_mouse(frame, hand_results, frame_w, frame_h):
    """
    Main function for virtual mouse control
    Called from main.py with each frame
    """
    global mouse_controller
    
    if hand_results and hand_results.multi_hand_landmarks:
        hand_landmarks = hand_results.multi_hand_landmarks[0]
        
        # Draw hand landmarks
        for landmark in hand_landmarks.landmark:
            x = int(landmark.x * frame_w)
            y = int(landmark.y * frame_h)
            cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)
        
        # Get index finger tip position
        index_tip = hand_landmarks.landmark[8]
        index_x = int(index_tip.x * frame_w)
        index_y = int(index_tip.y * frame_h)
        
        # Detect gesture
        gesture = mouse_controller.detect_gesture(hand_landmarks)
        
        # Display gesture
        cv2.putText(frame, f"Gesture: {gesture}", (10, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        # Execute action based on gesture
        if gesture == "MOVE":
            mouse_controller.stop_drag()
            mouse_controller.move_cursor(index_x, index_y, frame_w, frame_h)
            cv2.circle(frame, (index_x, index_y), 15, (0, 255, 255), 2)
        
        elif gesture == "LEFT_CLICK":
            mouse_controller.stop_drag()
            click_result = mouse_controller.left_click()
            if click_result:
                cv2.circle(frame, (index_x, index_y), 25, (0, 0, 255), 3)
        
        elif gesture == "RIGHT_CLICK":
            mouse_controller.stop_drag()
            click_result = mouse_controller.right_click()
            if click_result:
                cv2.circle(frame, (index_x, index_y), 25, (255, 0, 0), 3)
        
        elif gesture == "DRAG":
            mouse_controller.start_drag()
            mouse_controller.move_cursor(index_x, index_y, frame_w, frame_h)
            cv2.circle(frame, (index_x, index_y), 20, (255, 0, 255), -1)
            cv2.putText(frame, "DRAGGING", (10, 110),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
        
        elif gesture == "SCROLL":
            mouse_controller.stop_drag()
            mouse_controller.scroll(index_y)
            cv2.circle(frame, (index_x, index_y), 15, (255, 255, 255), 2)
            cv2.putText(frame, "SCROLL MODE", (10, 110),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        else:
            mouse_controller.stop_drag()
    
    else:
        mouse_controller.stop_drag()
    
    # Instructions
    cv2.putText(frame, "Index: Move | Index+Thumb: L-Click | 3 fingers: R-Click",
               (10, frame_h - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(frame, "Pinch: Drag | All fingers: Scroll",
               (10, frame_h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return frame