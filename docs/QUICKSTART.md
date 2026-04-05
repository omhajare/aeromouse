# Quick Start Guide - Signature Authentication

## Installation

### 1. Install Dependencies

```bash
cd aero-mouse
pip install -r requirements.txt
```

**New dependencies added**:
- `fastdtw==0.3.4` - Dynamic Time Warping for signature matching
- `scipy==1.11.4` - Scientific computing utilities

### 2. Verify Installation

```bash
python -c "import cv2, mediapipe, flask, fastdtw, scipy; print('✓ All dependencies installed')"
```

---

## Running the System

### Start the Backend Server

```bash
cd aero-mouse/backend
python app.py
```

You should see:
```
==================================================
AERO MOUSE - Multi-Modal Touchless HCI System
Flask Backend API Server
==================================================

Backend server starting...
Access the application at: http://localhost:5000

API Endpoints:
  ...
Authentication Endpoints:
  GET    /api/auth/users       - List enrolled users
  POST   /api/auth/enroll      - Start enrollment
  POST   /api/auth/verify      - Start verification
  ...
```

### Access Web Interface

Open browser: `http://localhost:5000`

---

## Using Authentication - 3 Simple Steps

### Step 1: Start the System

1. Open `http://localhost:5000`
2. Click **"Start System"** button
3. Allow camera access if prompted
4. System will show camera feed

### Step 2: Enroll Your Signature

#### Option A: Using API (Recommended for testing)

```bash
# Start enrollment
curl -X POST http://localhost:5000/api/auth/enroll \
     -H "Content-Type: application/json" \
     -d '{"username": "your_name"}'
```

#### Option B: Using Test Script

```bash
cd aero-mouse
python test_authentication.py
# Choose option 2: Enroll new user
```

#### In the Camera View:

1. **System shows**: "ENROLLMENT MODE: your_name"
2. **Draw your signature**:
   - Show only your **INDEX FINGER** to camera
   - Draw your signature in the air
   - Try to make it consistent and recognizable
   - Draw at least 20-30 points (signature path length)
3. **Submit**:
   - Show **TWO FINGERS** (index + middle) to submit
   - Wait for confirmation: "✓ ENROLLMENT SUCCESS"

### Step 3: Verify Your Signature

#### Start Verification:

```bash
curl -X POST http://localhost:5000/api/auth/verify \
     -H "Content-Type: application/json" \
     -d '{"username": "your_name"}'
```

#### In the Camera View:

1. **System shows**: "VERIFICATION MODE: your_name"
2. **Draw your signature** (try to match your enrolled signature)
3. **Submit** with **TWO FINGERS**
4. **Result**:
   - ✓ "AUTHENTICATION SUCCESS (XX.X%)" - Match!
   - ✗ "AUTHENTICATION FAILED" - No match

---

## Hand Gestures Reference

| Gesture | Fingers | Action |
|---------|---------|--------|
| **Draw** | Index finger only | Draw signature in air |
| **Submit/Save** | Index + Middle fingers | Submit signature for enrollment/verification |
| **Clear** | Closed fist | Clear current signature |

---

## Testing Tips

### For Best Results:

1. **Lighting**: Ensure good lighting so camera can detect hand clearly
2. **Distance**: Stay at consistent distance from camera (~50-80cm)
3. **Speed**: Draw at moderate speed (not too fast, not too slow)
4. **Consistency**: Try to reproduce your signature similarly each time
5. **Size**: Draw signature using natural hand movements

### Signature Design Tips:

- ✓ Use 3-5 distinct strokes or curves
- ✓ Include some loops or direction changes
- ✓ Make it reproducible (not too complex)
- ✗ Avoid overly simple signatures (single line)
- ✗ Avoid extremely complex signatures (hard to reproduce)

---

## Quick Verification Commands

### List all enrolled users:
```bash
curl http://localhost:5000/api/auth/users
```

### Delete a user:
```bash
curl -X DELETE http://localhost:5000/api/auth/delete/username
```

### Check authentication status:
```bash
curl http://localhost:5000/api/auth/status
```

### View current thresholds:
```bash
curl http://localhost:5000/api/auth/thresholds
```

---

## Troubleshooting

### "Signature too short" error
**Problem**: Not enough points captured  
**Solution**: Draw a longer signature (minimum 20 points)

### "Authentication failed" every time
**Problem**: Signatures too different OR thresholds too strict  
**Solutions**:
1. Try to reproduce signature more consistently
2. Increase thresholds:
   ```bash
   curl -X POST http://localhost:5000/api/auth/thresholds \
        -H "Content-Type: application/json" \
        -d '{"dtw_threshold": 200, "feature_threshold": 0.4}'
   ```
3. Re-enroll with a simpler signature

### Hand not detected
**Problem**: Poor lighting or camera issues  
**Solutions**:
- Improve room lighting
- Clean camera lens
- Ensure hand is in camera frame
- Check camera permissions

### "User already exists"
**Problem**: Username is taken  
**Solution**: Either use different username or delete existing:
```bash
curl -X DELETE http://localhost:5000/api/auth/delete/username
```

---

## What Changed in the Code?

### Files Modified:
- ✏️ `air.py` - Added authentication integration (trajectory tracking)
- ✏️ `app.py` - Added authentication API endpoints
- ✏️ `requirements.txt` - Added fastdtw and scipy

### Files Added:
- ➕ `signature_auth.py` - Complete authentication engine
- ➕ `AUTHENTICATION_DOCS.md` - Detailed documentation
- ➕ `test_authentication.py` - Testing script
- ➕ `QUICKSTART.md` - This file

### Files Unchanged:
- ✓ `mouse.py` - Virtual Mouse (untouched)
- ✓ `facial.py` - Facial Control (untouched)
- ✓ `main.py` - Main controller (untouched)
- ✓ All frontend files (untouched)

---

## Next Steps

1. **Try enrolling** yourself: `python test_authentication.py`
2. **Test verification** with your enrolled signature
3. **Read full docs**: `AUTHENTICATION_DOCS.md` for detailed information
4. **Adjust thresholds** if needed for your use case
5. **Enroll multiple users** to test multi-user support

---

## Architecture Overview

```
User draws in air
       ↓
MediaPipe detects hand
       ↓
Trajectory captured (x, y points)
       ↓
Features extracted (velocity, curvature, etc.)
       ↓
DTW distance computed
       ↓
Comparison with enrolled signature
       ↓
Accept/Reject + Confidence Score
```

---

## Important Notes

⚠️ **Original functionality preserved**:
- Virtual Mouse (Mode 1) works exactly as before
- Facial Control (Mode 2) works exactly as before
- Air Signature saving (Mode 3) still works - authentication is OPTIONAL

⚠️ **Storage location**:
- Enrolled users: `backend/signature_profiles/users.json`
- Saved signatures: `signatures/` (unchanged)

⚠️ **Security**:
- This is for educational/demo purposes
- Production use requires encryption, anti-spoofing, etc.
- See AUTHENTICATION_DOCS.md for security considerations

---

## Support

For detailed information:
- **Technical details**: See `AUTHENTICATION_DOCS.md`
- **API reference**: See Authentication Endpoints section in docs
- **Code**: `backend/signature_auth.py` (heavily commented)

---

**Version**: 1.0  
**Date**: February 3, 2026
