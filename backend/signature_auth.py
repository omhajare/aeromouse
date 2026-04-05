"""
Signature Authentication Module
Provides user enrollment and verification for air signatures using DTW
Features: Dynamic Time Warping, Feature Extraction, PostgreSQL Storage
"""

import numpy as np
import json
import os
from datetime import datetime
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw
import hashlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from db import get_connection


class SignatureAuthenticator:
    """
    Signature authentication system using Dynamic Time Warping (DTW)

    This class handles:
    - Feature extraction from signature trajectories
    - User enrollment (registration)
    - Signature verification (authentication)
    - PostgreSQL-backed storage of enrolled signatures
    """

    def __init__(self):
        """Initialize the authenticator with thresholds from database."""
        # Load thresholds from database (with fallback defaults)
        self.dtw_threshold = 150.0
        self.feature_threshold = 0.30
        self.min_signature_points = 20
        self._load_thresholds()

    def _load_thresholds(self):
        """Load authentication thresholds from database."""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT dtw_threshold, feature_threshold, min_signature_points FROM auth_thresholds LIMIT 1")
                    row = cur.fetchone()
                    if row:
                        self.dtw_threshold = float(row[0])
                        self.feature_threshold = float(row[1])
                        self.min_signature_points = int(row[2])
        except (ConnectionError, Exception) as e:
            print(f"[Auth] Could not load thresholds from DB, using defaults: {e}")

    def _generate_user_id(self, username):
        """Generate a unique user ID from username"""
        return hashlib.sha256(username.encode()).hexdigest()[:16]

    def extract_features(self, trajectory):
        """
        Extract comprehensive features from signature trajectory

        Args:
            trajectory: List of (x, y) coordinates representing the signature path

        Returns:
            dict: Extracted features including trajectory, velocity, acceleration, etc.
        """
        if len(trajectory) < self.min_signature_points:
            return None

        trajectory = np.array(trajectory)

        # 1. Normalize trajectory (translation and scale invariance)
        min_coords = trajectory.min(axis=0)
        max_coords = trajectory.max(axis=0)
        range_coords = max_coords - min_coords

        # Avoid division by zero
        range_coords[range_coords == 0] = 1

        normalized_trajectory = (trajectory - min_coords) / range_coords

        # 2. Calculate velocity (first derivative)
        velocity = np.diff(normalized_trajectory, axis=0)
        velocity_magnitude = np.linalg.norm(velocity, axis=1)

        # 3. Calculate acceleration (second derivative)
        acceleration = np.diff(velocity, axis=0)
        acceleration_magnitude = np.linalg.norm(acceleration, axis=1)

        # 4. Calculate curvature (change in direction)
        angles = np.arctan2(velocity[:, 1], velocity[:, 0])
        curvature = np.diff(angles)

        # Normalize angles to [-pi, pi]
        curvature = np.arctan2(np.sin(curvature), np.cos(curvature))

        # 5. Statistical features
        features = {
            # Trajectory (most important for DTW)
            'trajectory': normalized_trajectory.tolist(),
            'num_points': len(trajectory),

            # Velocity features
            'avg_velocity': float(np.mean(velocity_magnitude)),
            'max_velocity': float(np.max(velocity_magnitude)),
            'velocity_std': float(np.std(velocity_magnitude)),

            # Acceleration features
            'avg_acceleration': float(np.mean(acceleration_magnitude)),
            'max_acceleration': float(np.max(acceleration_magnitude)),

            # Curvature features
            'avg_curvature': float(np.mean(np.abs(curvature))),
            'max_curvature': float(np.max(np.abs(curvature))),

            # Shape features
            'aspect_ratio': float(range_coords[0] / range_coords[1]) if range_coords[1] > 0 else 1.0,
            'signature_width': float(range_coords[0]),
            'signature_height': float(range_coords[1]),

            # Direction changes (sharp turns)
            'num_direction_changes': int(np.sum(np.abs(curvature) > np.pi/4))
        }

        return features

    def _compute_dtw_distance(self, trajectory1, trajectory2):
        """
        Compute Dynamic Time Warping distance between two trajectories

        Args:
            trajectory1, trajectory2: Arrays of (x, y) coordinates

        Returns:
            float: DTW distance
        """
        traj1 = np.array(trajectory1)
        traj2 = np.array(trajectory2)

        # Use Fast DTW for efficiency
        distance, _ = fastdtw(traj1, traj2, dist=euclidean)

        return distance

    def _compute_feature_distance(self, features1, features2):
        """
        Compute normalized distance between feature sets

        Args:
            features1, features2: Feature dictionaries

        Returns:
            float: Normalized feature distance (0-1 scale)
        """
        # Features to compare (excluding trajectory which is handled by DTW)
        feature_keys = [
            'avg_velocity', 'max_velocity', 'velocity_std',
            'avg_acceleration', 'max_acceleration',
            'avg_curvature', 'max_curvature',
            'aspect_ratio', 'num_direction_changes'
        ]

        distances = []

        for key in feature_keys:
            if key in features1 and key in features2:
                f1 = features1[key]
                f2 = features2[key]

                # Normalize by the maximum value to get relative difference
                max_val = max(abs(f1), abs(f2), 1e-10)
                normalized_dist = abs(f1 - f2) / max_val
                distances.append(normalized_dist)

        # Average normalized distance
        return np.mean(distances) if distances else 1.0

    def enroll_user(self, username, trajectory):
        """
        Enroll a new user with their signature

        Args:
            username: Unique username for the user
            trajectory: List of (x, y) coordinates from their signature

        Returns:
            dict: Result with status, message, and user_id
        """
        # Check if username already exists in database
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                    if cur.fetchone():
                        return {
                            'success': False,
                            'message': f'User "{username}" already exists. Use a different username or delete the existing profile.',
                            'user_id': None
                        }
        except ConnectionError:
            return {
                'success': False,
                'message': 'Database is offline. Enrollment requires an internet connection.',
                'user_id': None
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Database error: {str(e)}',
                'user_id': None
            }

        # Extract features
        features = self.extract_features(trajectory)

        if features is None:
            return {
                'success': False,
                'message': f'Signature too short. Please draw at least {self.min_signature_points} points.',
                'user_id': None
            }

        # Generate user ID
        user_id = self._generate_user_id(username)

        # Store user profile in PostgreSQL
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO users (username, user_id, features, enrolled_date)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (username, user_id, json.dumps(features), datetime.now())
                    )

            return {
                'success': True,
                'message': f'User "{username}" enrolled successfully!',
                'user_id': user_id,
                'num_points': features['num_points']
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to save user profile: {str(e)}',
                'user_id': None
            }

    def verify_signature(self, username, trajectory):
        """
        Verify if a signature matches the enrolled signature for a user

        Args:
            username: Username to verify against
            trajectory: List of (x, y) coordinates from the signature attempt

        Returns:
            dict: Verification result with detailed metrics
        """
        # Get enrolled features from database
        enrolled_features = None
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT features FROM users WHERE username = %s", (username,))
                    row = cur.fetchone()
                    if row:
                        enrolled_features = row[0] if isinstance(row[0], dict) else json.loads(row[0])
        except ConnectionError:
            return {
                'authenticated': False,
                'confidence': 0.0,
                'message': 'Database is offline. Verification requires an internet connection.',
                'details': None
            }
        except Exception as e:
            return {
                'authenticated': False,
                'confidence': 0.0,
                'message': f'Database error: {str(e)}',
                'details': None
            }

        if enrolled_features is None:
            return {
                'authenticated': False,
                'confidence': 0.0,
                'message': f'User "{username}" not found. Please enroll first.',
                'details': None
            }

        # Extract features from test signature
        test_features = self.extract_features(trajectory)

        if test_features is None:
            return {
                'authenticated': False,
                'confidence': 0.0,
                'message': f'Signature too short. Please draw at least {self.min_signature_points} points.',
                'details': None
            }

        # Compute DTW distance on trajectories
        dtw_distance = self._compute_dtw_distance(
            enrolled_features['trajectory'],
            test_features['trajectory']
        )

        # Compute feature distance
        feature_distance = self._compute_feature_distance(
            enrolled_features,
            test_features
        )

        # Decision making
        dtw_match = dtw_distance <= self.dtw_threshold
        feature_match = feature_distance <= self.feature_threshold

        authenticated = dtw_match and feature_match

        # Calculate confidence score (0-100%)
        # Inverse relationship: smaller distance = higher confidence
        dtw_confidence = max(0, 100 * (1 - dtw_distance / (self.dtw_threshold * 2)))
        feature_confidence = max(0, 100 * (1 - feature_distance / (self.feature_threshold * 2)))

        # Combined confidence (weighted average: DTW is more important)
        confidence = 0.7 * dtw_confidence + 0.3 * feature_confidence

        # Detailed results
        details = {
            'dtw_distance': float(dtw_distance),
            'dtw_threshold': float(self.dtw_threshold),
            'dtw_match': dtw_match,
            'feature_distance': float(feature_distance),
            'feature_threshold': float(self.feature_threshold),
            'feature_match': feature_match,
            'num_points_enrolled': enrolled_features['num_points'],
            'num_points_test': test_features['num_points']
        }

        if authenticated:
            message = f'✓ Authentication successful! Confidence: {confidence:.1f}%'
        else:
            reasons = []
            if not dtw_match:
                reasons.append(f'trajectory mismatch (distance: {dtw_distance:.1f})')
            if not feature_match:
                reasons.append(f'feature mismatch (distance: {feature_distance:.2f})')
            message = f'✗ Authentication failed: {", ".join(reasons)}'

        return {
            'authenticated': authenticated,
            'confidence': float(confidence),
            'message': message,
            'details': details
        }

    def delete_user(self, username):
        """
        Delete an enrolled user

        Args:
            username: Username to delete

        Returns:
            dict: Result with status and message
        """
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM users WHERE username = %s RETURNING id", (username,))
                    deleted = cur.fetchone()

                    if deleted:
                        return {
                            'success': True,
                            'message': f'User "{username}" deleted successfully.'
                        }
                    else:
                        return {
                            'success': False,
                            'message': f'User "{username}" not found.'
                        }
        except ConnectionError:
            return {
                'success': False,
                'message': 'Database is offline. Cannot delete user without internet.'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to delete user: {str(e)}'
            }

    def list_users(self):
        """
        Get list of all enrolled users

        Returns:
            list: List of usernames with enrollment dates
        """
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT username, user_id, enrolled_date FROM users ORDER BY enrolled_date DESC")
                    rows = cur.fetchall()

                    return [
                        {
                            'username': row[0],
                            'user_id': row[1],
                            'enrolled_date': row[2].strftime("%Y-%m-%d %H:%M:%S") if row[2] else None
                        }
                        for row in rows
                    ]
        except ConnectionError:
            print("[Auth] Database offline — cannot list users")
            return []
        except Exception as e:
            print(f"[Auth] Failed to list users: {e}")
            return []

    def get_thresholds(self):
        """Get current authentication thresholds from database"""
        self._load_thresholds()
        return {
            'dtw_threshold': self.dtw_threshold,
            'feature_threshold': self.feature_threshold,
            'min_signature_points': self.min_signature_points
        }

    def set_thresholds(self, dtw_threshold=None, feature_threshold=None):
        """
        Update authentication thresholds in database

        Args:
            dtw_threshold: New DTW threshold (optional)
            feature_threshold: New feature threshold (optional)

        Returns:
            dict: Updated thresholds
        """
        if dtw_threshold is not None:
            self.dtw_threshold = float(dtw_threshold)
        if feature_threshold is not None:
            self.feature_threshold = float(feature_threshold)

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE auth_thresholds
                        SET dtw_threshold = %s, feature_threshold = %s, updated_at = NOW()
                        WHERE id = 1
                        """,
                        (self.dtw_threshold, self.feature_threshold)
                    )
        except ConnectionError:
            print("[Auth] Database offline — thresholds saved in-memory only")
        except Exception as e:
            print(f"[Auth] Failed to save thresholds: {e}")

        return self.get_thresholds()


# Global authenticator instance
authenticator = SignatureAuthenticator()
