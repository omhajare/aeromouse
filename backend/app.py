"""
Flask Backend API - Connects frontend UI to backend controller
Provides REST API endpoints for mode switching and signature authentication
Environment-driven configuration for production deployment
"""

import os
from dotenv import load_dotenv

# Load environment variables FIRST (before any other module imports)
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import time
import json

# Import main controller
from main import start_system, get_controller
# Import authentication system
from signature_auth import authenticator
from air import air_signature
# Import database
from db import get_connection, close_pool
# Import cloud storage
from cloud_storage import list_signatures as cloudinary_list_signatures
# Import DB initialization
from init_db import create_tables

# ===== Configuration from Environment =====
FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.environ.get('FLASK_PORT', 5000))
FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')

# ===== Flask App Setup =====
app = Flask(__name__)
CORS(app, origins=[origin.strip() for origin in CORS_ORIGINS])

# Global state
system_running = False
system_starting = False
controller = None


@app.route('/api/start', methods=['POST'])
def start_api():
    """Start the AERO MOUSE system"""
    global system_running, controller, system_starting
    
    if system_running:
        return jsonify({
            'status': 'info',
            'message': 'System is already running',
            'mode': controller.current_mode if controller else 0
        })
        
    if system_starting:
        return jsonify({
            'status': 'starting',
            'message': 'System is warming up...',
            'mode': 0
        })

    try:
        system_starting = True
        
        # Start system in background thread
        start_system()

        # Thread 2: watcher — polls until controller is fully ready (or fails)
        def _wait_for_controller():
            global system_running, system_starting, controller
            start_wait = time.time()
            # Poll until controller.running == True (camera + MediaPipe fully ready)
            while time.time() - start_wait < 30:
                c = get_controller()
                if c is not None:
                    # Camera failed to open — abort cleanly
                    if getattr(c, 'start_failed', False):
                        print("[WATCHER] Camera failed to open. Resetting to stopped.")
                        system_starting = False
                        system_running = False
                        controller = None
                        return
                    # System is fully up
                    if getattr(c, 'running', False):
                        controller = c
                        system_running = True
                        system_starting = False
                        print("[WATCHER] System is ONLINE.")
                        return
                time.sleep(0.5)
            # Timeout after 30 s — reset to stopped so UI doesn't hang
            print("[WATCHER] Timeout waiting for system to start. Resetting to stopped.")
            system_starting = False
            system_running = False
            controller = None

        threading.Thread(target=_wait_for_controller, daemon=True).start()
        
        return jsonify({
            'status': 'starting',
            'message': 'AERO MOUSE system is warming up',
            'mode': 0
        })
    except Exception as e:
        system_starting = False
        return jsonify({
            'status': 'error',
            'message': f'Failed to start system: {str(e)}'
        }), 500


@app.route('/api/mode/<int:mode>', methods=['POST'])
def set_mode_api(mode):
    """Switch to a specific mode"""
    global controller, system_running
    
    if not system_running:
        return jsonify({
            'status': 'error',
            'message': 'System is not running. Please start the system first.'
        }), 400
    
    if controller is None:
        controller = get_controller()
        if controller is None:
            return jsonify({
                'status': 'error',
                'message': 'Controller not initialized'
            }), 500
    
    if mode < 0 or mode > 3:
        return jsonify({
            'status': 'error',
            'message': 'Invalid mode. Mode must be 0, 1, 2, or 3.'
        }), 400
    
    try:
        # This calls the set_mode method which internally calls switch_mode
        success = controller.set_mode(mode)
        
        if not success:
            raise Exception("Mode switch failed")
        
        mode_names = {
            0: "Standby",
            1: "Virtual Mouse",
            2: "Facial Control",
            3: "Air Signature"
        }
        
        return jsonify({
            'status': 'success',
            'message': f'Switched to {mode_names[mode]} mode',
            'mode': mode
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to switch mode: {str(e)}'
        }), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current system status"""
    global controller, system_running, system_starting
    
    if system_starting:
        return jsonify({
            'status': 'starting',
            'mode': 0,
            'running': False
        })
        
    if not system_running or controller is None:
        return jsonify({
            'status': 'stopped',
            'mode': None,
            'running': False
        })
    
    mode_names = {
        0: "Standby",
        1: "Virtual Mouse",
        2: "Facial Control",
        3: "Air Signature"
    }
    
    current_mode = controller.current_mode if hasattr(controller, 'current_mode') else 0
    
    return jsonify({
        'status': 'running',
        'mode': current_mode,
        'mode_name': mode_names.get(current_mode, "Unknown"),
        'running': controller.running if hasattr(controller, 'running') else True
    })


@app.route('/api/stop', methods=['POST'])
def stop_api():
    """Stop the system"""
    global system_running, controller
    
    if system_running and controller:
        try:
            controller.running = False
            system_running = False
            
            # Give time for cleanup
            time.sleep(1)
            
            controller = None
            
            return jsonify({
                'status': 'success',
                'message': 'System stopped successfully'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Failed to stop system: {str(e)}'
            }), 500
    else:
        return jsonify({
            'status': 'info',
            'message': 'System is not running'
        })


@app.route('/api/signatures', methods=['GET'])
def list_signatures():
    """List all saved signatures from PostgreSQL (with Cloudinary URLs)"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT s.id, s.filename, s.cloudinary_url, s.cloudinary_public_id,
                           s.point_count, s.created_at, u.username
                    FROM signatures s
                    LEFT JOIN users u ON s.user_id = u.id
                    ORDER BY s.created_at DESC
                """)
                rows = cur.fetchall()

                signatures = []
                for row in rows:
                    signatures.append({
                        'id': row[0],
                        'filename': row[1],
                        'url': row[2],
                        'public_id': row[3],
                        'point_count': row[4],
                        'created_at': row[5].isoformat() if row[5] else None,
                        'username': row[6]
                    })

        return jsonify({
            'status': 'success',
            'signatures': signatures,
            'count': len(signatures)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to list signatures: {str(e)}'
        }), 500


# ===== AUTHENTICATION API ENDPOINTS =====

@app.route('/api/auth/users', methods=['GET'])
def list_users():
    """List all enrolled users"""
    try:
        users = authenticator.list_users()
        return jsonify({
            'status': 'success',
            'users': users,
            'count': len(users)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to list users: {str(e)}'
        }), 500


@app.route('/api/auth/enroll', methods=['POST'])
def start_enrollment():
    """Start enrollment mode for a user"""
    global system_running, controller
    
    if not system_running:
        return jsonify({
            'status': 'error',
            'message': 'System is not running. Please start the system first.'
        }), 400
    
    data = request.get_json()
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({
            'status': 'error',
            'message': 'Username is required'
        }), 400
    
    try:
        # Switch to air signature mode if not already there
        if controller and controller.current_mode != 3:
            controller.set_mode(3)
            time.sleep(0.5)  # Brief pause for mode switch
        
        # Start enrollment
        air_signature.start_enrollment(username)
        
        return jsonify({
            'status': 'success',
            'message': f'Enrollment started for user: {username}',
            'username': username,
            'mode': 'enroll'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to start enrollment: {str(e)}'
        }), 500


@app.route('/api/auth/verify', methods=['POST'])
def start_verification():
    """Start verification mode for a user"""
    global system_running, controller
    
    if not system_running:
        return jsonify({
            'status': 'error',
            'message': 'System is not running. Please start the system first.'
        }), 400
    
    data = request.get_json()
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({
            'status': 'error',
            'message': 'Username is required'
        }), 400
    
    try:
        # Switch to air signature mode if not already there
        if controller and controller.current_mode != 3:
            controller.set_mode(3)
            time.sleep(0.5)  # Brief pause for mode switch
        
        # Start verification
        air_signature.start_verification(username)
        
        return jsonify({
            'status': 'success',
            'message': f'Verification started for user: {username}',
            'username': username,
            'mode': 'verify'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to start verification: {str(e)}'
        }), 500


@app.route('/api/auth/cancel', methods=['POST'])
def cancel_authentication():
    """Cancel current authentication operation"""
    try:
        air_signature.cancel_authentication()
        return jsonify({
            'status': 'success',
            'message': 'Authentication cancelled'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to cancel authentication: {str(e)}'
        }), 500


@app.route('/api/auth/delete/<username>', methods=['DELETE'])
def delete_user(username):
    """Delete an enrolled user"""
    try:
        result = authenticator.delete_user(username)
        
        if result['success']:
            return jsonify({
                'status': 'success',
                'message': result['message']
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result['message']
            }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to delete user: {str(e)}'
        }), 500


@app.route('/api/auth/status', methods=['GET'])
def get_auth_status():
    """Get current authentication status"""
    try:
        status = {
            'auth_mode': air_signature.auth_mode,
            'auth_username': air_signature.auth_username,
            'trajectory_points': len(air_signature.current_trajectory) if air_signature.current_trajectory else 0,
            'has_result': air_signature.auth_result is not None
        }
        
        # Include result if available and recent
        if air_signature.auth_result is not None:
            if time.time() - air_signature.auth_result_time < air_signature.auth_result_duration:
                status['result'] = air_signature.auth_result
        
        return jsonify({
            'status': 'success',
            'auth_status': status
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get auth status: {str(e)}'
        }), 500


@app.route('/api/auth/thresholds', methods=['GET'])
def get_thresholds():
    """Get current authentication thresholds"""
    try:
        thresholds = authenticator.get_thresholds()
        return jsonify({
            'status': 'success',
            'thresholds': thresholds
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get thresholds: {str(e)}'
        }), 500


@app.route('/api/auth/thresholds', methods=['POST'])
def update_thresholds():
    """Update authentication thresholds"""
    data = request.get_json()
    
    try:
        dtw_threshold = data.get('dtw_threshold')
        feature_threshold = data.get('feature_threshold')
        
        updated = authenticator.set_thresholds(dtw_threshold, feature_threshold)
        
        return jsonify({
            'status': 'success',
            'message': 'Thresholds updated successfully',
            'thresholds': updated
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to update thresholds: {str(e)}'
        }), 500


if __name__ == '__main__':
    # Initialize database tables on startup
    print("=" * 50)
    print("AERO MOUSE - Multi-Modal Touchless HCI System")
    print("Flask Backend API Server")
    print("=" * 50)

    print("\n[DB] Initializing database tables...")
    try:
        create_tables()
    except Exception as e:
        print(f"[DB] Warning: Could not initialize database: {e}")
        print("[DB] The app will still start, but DB features may not work.\n")

    print(f"\nBackend server starting on {FLASK_HOST}:{FLASK_PORT}")
    print(f"CORS allowed origins: {CORS_ORIGINS}")
    print(f"Debug mode: {FLASK_DEBUG}")
    print("\nAPI Endpoints:")
    print("  POST /api/start       - Start the system")
    print("  POST /api/mode/<1-3>  - Switch mode")
    print("  GET  /api/status      - Get system status")
    print("  POST /api/stop        - Stop the system")
    print("  GET  /api/signatures  - List saved signatures")
    print("\nAuthentication Endpoints:")
    print("  GET    /api/auth/users       - List enrolled users")
    print("  POST   /api/auth/enroll      - Start enrollment")
    print("  POST   /api/auth/verify      - Start verification")
    print("  POST   /api/auth/cancel      - Cancel authentication")
    print("  DELETE /api/auth/delete/<user> - Delete user")
    print("  GET    /api/auth/status      - Get auth status")
    print("  GET    /api/auth/thresholds  - Get auth thresholds")
    print("  POST   /api/auth/thresholds  - Update thresholds")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT, threaded=True)