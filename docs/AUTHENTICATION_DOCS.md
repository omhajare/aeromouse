# Air Signature Authentication System - Documentation

## Overview

This document describes the **User Authentication System** added to the **Air Signature Module** of the AERO MOUSE project. The authentication system allows users to enroll their air signatures and subsequently verify their identity by drawing their signature in the air.

## Table of Contents

1. [Authentication Approach](#authentication-approach)
2. [Technical Implementation](#technical-implementation)
3. [File Structure](#file-structure)
4. [Feature Extraction](#feature-extraction)
5. [Enrollment Process](#enrollment-process)
6. [Verification Process](#verification-process)
7. [API Endpoints](#api-endpoints)
8. [Testing Instructions](#testing-instructions)
9. [Configuration](#configuration)
10. [Limitations and Assumptions](#limitations-and-assumptions)

---

## Authentication Approach

### Why Dynamic Time Warping (DTW)?

The authentication system uses **Dynamic Time Warping (DTW)** combined with **feature extraction** for signature verification. This approach was chosen for several key reasons:

1. **Temporal Alignment**: DTW automatically handles variations in signing speed and timing
2. **Scale Invariance**: Features are normalized to handle size differences
3. **Rotation Tolerance**: Feature extraction focuses on shape characteristics rather than absolute coordinates
4. **No Training Required**: Unlike ML models, DTW works with a single enrollment sample
5. **Real-time Performance**: Fast enough for interactive use (< 100ms verification time)
6. **Natural Variation Handling**: Accounts for human inconsistency in reproducing signatures

### Alternative Approaches Considered

- **K-Nearest Neighbors (KNN)**: Requires multiple samples per user
- **Support Vector Machines (SVM)**: Needs substantial training data
- **Neural Networks**: Overkill for single-user scenarios and requires extensive datasets
- **Template Matching**: Too sensitive to minor variations

DTW provides the best balance of accuracy, simplicity, and real-time performance for this use case.

---

## Technical Implementation

### Core Technologies

- **Python 3.8+**
- **NumPy**: Array operations and mathematical computations
- **SciPy**: Distance calculations
- **FastDTW**: Efficient Dynamic Time Warping implementation
- **OpenCV**: Video capture and visual feedback
- **MediaPipe**: Hand landmark detection
- **Flask**: REST API for web interface

### Algorithm Flow

```
1. User draws signature in air
   ↓
2. MediaPipe detects hand landmarks
   ↓
3. Index finger position tracked → trajectory points collected
   ↓
4. Feature extraction (normalization, velocity, acceleration, curvature)
   ↓
5. DTW distance computed between enrolled and test signatures
   ↓
6. Feature distance computed for statistical properties
   ↓
7. Both distances compared against thresholds
   ↓
8. Authentication decision (Accept/Reject) + confidence score
```

---

## File Structure

### New Files Added

```
aero-mouse/
├── backend/
│   ├── signature_auth.py          # NEW - Authentication engine
│   ├── air.py                      # MODIFIED - Added auth integration
│   ├── app.py                      # MODIFIED - Added auth API endpoints
│   └── signature_profiles/         # NEW - Storage directory
│       └── users.json              # NEW - Enrolled user database
├── requirements.txt                # MODIFIED - Added fastdtw, scipy
└── AUTHENTICATION_DOCS.md          # NEW - This documentation file
```

### Unchanged Files (Preserved)

- `mouse.py` - Virtual Mouse module (untouched)
- `facial.py` - Facial Control module (untouched)
- `main.py` - Main controller (untouched)
- All frontend files (untouched)

---

## Feature Extraction

### Extracted Features

The system extracts the following features from each signature:

#### 1. Trajectory Features
- **Normalized coordinates**: Translation and scale invariant (x, y) points
- **Number of points**: Total trajectory length

#### 2. Velocity Features
- **Average velocity**: Mean speed of drawing
- **Maximum velocity**: Peak drawing speed
- **Velocity standard deviation**: Speed consistency measure

#### 3. Acceleration Features
- **Average acceleration**: Mean rate of speed change
- **Maximum acceleration**: Peak acceleration value

#### 4. Curvature Features
- **Average curvature**: Mean direction change
- **Maximum curvature**: Sharpest turn angle
- **Direction change count**: Number of sharp turns (> 45°)

#### 5. Shape Features
- **Aspect ratio**: Width/height ratio
- **Signature width**: Horizontal extent (normalized)
- **Signature height**: Vertical extent (normalized)

### Feature Normalization

All features are normalized to ensure:
- **Scale invariance**: Signatures at different sizes match
- **Translation invariance**: Position on screen doesn't matter
- **Rotation tolerance**: Minor rotations are acceptable

---

## Enrollment Process

### Location in Code

**File**: `aero-mouse/backend/air.py`
**Method**: `AirSignature.start_enrollment(username)` (Line ~200)
**Processing**: `AirSignature.process_enrollment()` (Line ~240)

### Step-by-Step Enrollment

1. **Initiation**:
   ```python
   POST /api/auth/enroll
   Body: {"username": "john_doe"}
   ```

2. **Drawing Phase**:
   - System switches to Air Signature mode (mode 3)
   - User draws signature using index finger (draw gesture)
   - Trajectory points are recorded in real-time
   - Minimum 20 points required for valid signature

3. **Submission**:
   - User shows TWO FINGERS (index + middle) gesture
   - System calls `process_enrollment()`
   - Features extracted from trajectory
   - Profile saved to `signature_profiles/users.json`

4. **Confirmation**:
   - Success message displayed on screen
   - User profile created with unique user ID
   - Authentication mode automatically exits

### Enrollment API Response

```json
{
  "success": true,
  "message": "User 'john_doe' enrolled successfully!",
  "user_id": "a1b2c3d4e5f6g7h8",
  "num_points": 127
}
```

---

## Verification Process

### Location in Code

**File**: `aero-mouse/backend/air.py`
**Method**: `AirSignature.start_verification(username)` (Line ~220)
**Processing**: `AirSignature.process_verification()` (Line ~260)

### Step-by-Step Verification

1. **Initiation**:
   ```python
   POST /api/auth/verify
   Body: {"username": "john_doe"}
   ```

2. **Drawing Phase**:
   - System switches to Air Signature mode (mode 3)
   - User draws signature using index finger (draw gesture)
   - Trajectory points are recorded in real-time

3. **Submission**:
   - User shows TWO FINGERS (index + middle) gesture
   - System calls `process_verification()`
   - Features extracted from test signature
   - DTW distance computed vs enrolled signature
   - Feature distance computed for statistical properties

4. **Decision**:
   - **DTW threshold**: 150.0 (max acceptable distance)
   - **Feature threshold**: 0.30 (max 30% difference)
   - Authentication succeeds only if BOTH thresholds pass

5. **Result Display**:
   - Success/failure shown on screen with confidence score
   - Detailed metrics available via API

### Verification API Response

```json
{
  "authenticated": true,
  "confidence": 87.3,
  "message": "✓ Authentication successful! Confidence: 87.3%",
  "details": {
    "dtw_distance": 45.2,
    "dtw_threshold": 150.0,
    "dtw_match": true,
    "feature_distance": 0.15,
    "feature_threshold": 0.30,
    "feature_match": true,
    "num_points_enrolled": 127,
    "num_points_test": 119
  }
}
```

---

## API Endpoints

### Authentication Endpoints

#### 1. List Enrolled Users
```http
GET /api/auth/users
```
**Response**:
```json
{
  "status": "success",
  "users": [
    {
      "username": "john_doe",
      "enrolled_date": "2026-02-03 14:30:22",
      "user_id": "a1b2c3d4e5f6g7h8"
    }
  ],
  "count": 1
}
```

#### 2. Start Enrollment
```http
POST /api/auth/enroll
Content-Type: application/json

{
  "username": "john_doe"
}
```

#### 3. Start Verification
```http
POST /api/auth/verify
Content-Type: application/json

{
  "username": "john_doe"
}
```

#### 4. Cancel Authentication
```http
POST /api/auth/cancel
```

#### 5. Delete User
```http
DELETE /api/auth/delete/john_doe
```

#### 6. Get Authentication Status
```http
GET /api/auth/status
```

#### 7. Get Thresholds
```http
GET /api/auth/thresholds
```
**Response**:
```json
{
  "status": "success",
  "thresholds": {
    "dtw_threshold": 150.0,
    "feature_threshold": 0.30,
    "min_signature_points": 20
  }
}
```

#### 8. Update Thresholds
```http
POST /api/auth/thresholds
Content-Type: application/json

{
  "dtw_threshold": 200.0,
  "feature_threshold": 0.35
}
```

---

## Testing Instructions

### Prerequisites

1. **Install Dependencies**:
   ```bash
   cd aero-mouse
   pip install -r requirements.txt
   ```

2. **Start Backend Server**:
   ```bash
   cd aero-mouse/backend
   python app.py
   ```

3. **Access Web Interface**:
   - Open browser: `http://localhost:5000`
   - Click "Start System"

### Test Scenario 1: Enrollment

1. **API Method** (using curl or Postman):
   ```bash
   curl -X POST http://localhost:5000/api/auth/enroll \
        -H "Content-Type: application/json" \
        -d '{"username": "test_user"}'
   ```

2. **Draw Signature**:
   - Make sure you're in Air Signature mode (Mode 3)
   - Show your index finger to camera
   - Draw a signature in the air (minimum 20 points)
   - System will show "ENROLLMENT MODE" banner at top

3. **Complete Enrollment**:
   - Show TWO FINGERS (index + middle) to submit
   - Watch for confirmation message on screen
   - Verify success via API:
     ```bash
     curl http://localhost:5000/api/auth/users
     ```

### Test Scenario 2: Successful Verification

1. **Start Verification**:
   ```bash
   curl -X POST http://localhost:5000/api/auth/verify \
        -H "Content-Type: application/json" \
        -d '{"username": "test_user"}'
   ```

2. **Draw Signature**:
   - Draw your signature as similarly as possible to enrollment
   - System shows "VERIFICATION MODE" banner

3. **Submit**:
   - Show TWO FINGERS to verify
   - Expect: "✓ AUTHENTICATION SUCCESS" with confidence %

### Test Scenario 3: Failed Verification (Wrong Signature)

1. **Start Verification** for enrolled user

2. **Draw Different Signature**:
   - Intentionally draw a completely different pattern

3. **Submit**:
   - Expect: "✗ AUTHENTICATION FAILED" with reasons

### Test Scenario 4: Multiple Users

1. **Enroll Multiple Users**:
   ```bash
   curl -X POST http://localhost:5000/api/auth/enroll \
        -H "Content-Type: application/json" \
        -d '{"username": "alice"}'
   
   # Draw Alice's signature, submit
   
   curl -X POST http://localhost:5000/api/auth/enroll \
        -H "Content-Type: application/json" \
        -d '{"username": "bob"}'
   
   # Draw Bob's signature, submit
   ```

2. **Verify Each User**:
   - Verify Alice with Alice's signature → Should succeed
   - Verify Bob with Bob's signature → Should succeed
   - Verify Alice with Bob's signature → Should fail

### Test Scenario 5: Delete User

```bash
# Delete a user
curl -X DELETE http://localhost:5000/api/auth/delete/test_user

# Verify deletion
curl http://localhost:5000/api/auth/users
```

---

## Configuration

### Adjustable Thresholds

The authentication system uses two main thresholds that can be adjusted:

#### 1. DTW Threshold (default: 150.0)
- **Purpose**: Maximum acceptable trajectory distance
- **Lower value**: More strict (fewer false accepts, more false rejects)
- **Higher value**: More lenient (more false accepts, fewer false rejects)
- **Recommended range**: 100.0 - 250.0

#### 2. Feature Threshold (default: 0.30)
- **Purpose**: Maximum normalized feature distance (30%)
- **Lower value**: Stricter feature matching
- **Higher value**: More tolerant to feature variations
- **Recommended range**: 0.20 - 0.50

### Updating Thresholds

**Via API**:
```python
import requests

response = requests.post('http://localhost:5000/api/auth/thresholds', 
    json={
        'dtw_threshold': 200.0,
        'feature_threshold': 0.35
    })
```

**In Code** (`signature_auth.py`):
```python
authenticator.set_thresholds(
    dtw_threshold=200.0,
    feature_threshold=0.35
)
```

### Storage Configuration

User profiles are stored in JSON format:

**Location**: `aero-mouse/backend/signature_profiles/users.json`

**Format**:
```json
{
  "john_doe": {
    "user_id": "a1b2c3d4e5f6g7h8",
    "enrolled_date": "2026-02-03 14:30:22",
    "features": {
      "trajectory": [[x1, y1], [x2, y2], ...],
      "num_points": 127,
      "avg_velocity": 0.023,
      "max_velocity": 0.089,
      ...
    }
  }
}
```

---

## Limitations and Assumptions

### Current Limitations

1. **Single Sample Enrollment**:
   - System uses only one signature sample per user
   - More samples would improve accuracy but increase complexity

2. **2D Trajectory Only**:
   - Uses only X-Y coordinates (no Z-depth)
   - 3D tracking would require depth cameras

3. **No Pressure/Speed Modeling**:
   - Doesn't account for pen pressure (not applicable to air signatures)
   - Speed is captured but not as a primary authentication factor

4. **Lighting Dependency**:
   - Hand detection quality depends on camera lighting
   - Poor lighting affects trajectory capture quality

5. **Camera Position**:
   - User should be at consistent distance from camera
   - Extreme angles may affect detection

6. **Storage Format**:
   - Features stored as JSON (not encrypted)
   - For production, consider encryption

### Assumptions

1. **User Consistency**:
   - Users will try to reproduce their signature reasonably consistently
   - Assumes conscious effort to match enrolled signature

2. **Single User Per Session**:
   - System designed for one user at a time
   - Multiple simultaneous users not supported

3. **Honest Users**:
   - No adversarial attack modeling
   - System assumes users aren't deliberately trying to forge signatures

4. **Adequate Lighting**:
   - Assumes reasonable lighting conditions for camera

5. **Stable Camera**:
   - Assumes camera is stationary during signature capture

### Security Considerations

⚠️ **Important**: This authentication system is designed for **educational and demonstration purposes**. For production deployment:

1. **Encrypt stored profiles** using industry-standard encryption
2. **Implement anti-spoofing** measures (liveness detection)
3. **Use HTTPS** for all API communications
4. **Add rate limiting** to prevent brute-force attacks
5. **Implement session management** with proper timeouts
6. **Log authentication attempts** for security auditing
7. **Consider multi-factor authentication** for high-security applications

### Performance Characteristics

- **Enrollment time**: < 5 seconds (including drawing)
- **Verification time**: < 1 second (after drawing)
- **DTW computation**: ~50-100ms for typical signatures
- **Feature extraction**: ~10-20ms
- **Storage per user**: ~5-10 KB (JSON format)

---

## Future Enhancements

### Potential Improvements

1. **Multi-Sample Enrollment**:
   - Collect 3-5 signature samples during enrollment
   - Use average/consensus features for better accuracy

2. **Adaptive Thresholds**:
   - Machine learning to optimize thresholds per user
   - Dynamic adjustment based on verification history

3. **3D Trajectory Capture**:
   - Utilize depth cameras for Z-axis data
   - Capture hand orientation and palm facing direction

4. **Biometric Fusion**:
   - Combine signature with facial recognition
   - Multi-modal authentication for higher security

5. **Template Updating**:
   - Incrementally update enrolled template with successful verifications
   - Adapt to natural signature evolution over time

6. **Advanced Features**:
   - Pen-up/pen-down segments
   - Stroke order analysis
   - Writing pressure estimation from hand pose

---

## Troubleshooting

### Common Issues

#### Issue: "Signature too short" error
**Solution**: Draw a longer, more detailed signature (minimum 20 points)

#### Issue: Authentication always fails
**Solutions**:
- Increase thresholds via API
- Ensure consistent camera distance during enrollment and verification
- Check lighting conditions
- Re-enroll with a simpler, more reproducible signature

#### Issue: Hand not detected
**Solutions**:
- Improve lighting
- Ensure hand is clearly visible in camera frame
- Check camera permissions
- Verify MediaPipe installation

#### Issue: "User already exists" during enrollment
**Solution**: Delete existing user first: `DELETE /api/auth/delete/<username>`

---

## Contact and Support

For questions, issues, or contributions related to the authentication system:

- Review code in: `aero-mouse/backend/signature_auth.py`
- Check API logs for detailed error messages
- Refer to main project documentation for general issues

---

**Document Version**: 1.0  
**Last Updated**: February 3, 2026  
**Author**: AERO MOUSE Development Team
