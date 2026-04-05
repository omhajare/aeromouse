"""
Cloudinary Cloud Storage Module
Handles uploading and deleting signature images to/from Cloudinary.
Falls back to local storage when offline.
"""

import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Configure Cloudinary from environment
_cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
_api_key = os.environ.get('CLOUDINARY_API_KEY')
_api_secret = os.environ.get('CLOUDINARY_API_SECRET')
_cloudinary_configured = bool(_cloud_name and _api_key and _api_secret)

if _cloudinary_configured:
    cloudinary.config(
        cloud_name=_cloud_name,
        api_key=_api_key,
        api_secret=_api_secret,
        secure=True
    )

# Cloudinary folder for all signature images
SIGNATURE_FOLDER = "aero-mouse/signatures"

# Local fallback directory (relative to backend/)
LOCAL_SAVE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'signatures')
os.makedirs(LOCAL_SAVE_DIR, exist_ok=True)


def is_cloud_available():
    """Check if Cloudinary is configured and reachable."""
    if not _cloudinary_configured:
        return False
    try:
        cloudinary.api.ping()
        return True
    except Exception:
        return False


def upload_signature(image_bytes, filename):
    """
    Upload a signature image to Cloudinary.
    Falls back to local save on failure.

    Args:
        image_bytes: PNG image as bytes
        filename: Original filename (used as public_id base)

    Returns:
        dict: {
            'url': Full Cloudinary URL or local path,
            'public_id': Cloudinary public ID (or None if local),
            'secure_url': HTTPS URL (or None if local),
            'storage': 'cloud' | 'local'
        }
        None if both cloud and local save fail
    """
    # Try Cloudinary first
    if _cloudinary_configured:
        try:
            name_without_ext = os.path.splitext(filename)[0]
            public_id = f"{SIGNATURE_FOLDER}/{name_without_ext}"

            result = cloudinary.uploader.upload(
                image_bytes,
                public_id=public_id,
                resource_type="image",
                format="png",
                overwrite=True
            )

            return {
                'url': result.get('url', ''),
                'secure_url': result.get('secure_url', ''),
                'public_id': result.get('public_id', ''),
                'width': result.get('width', 0),
                'height': result.get('height', 0),
                'storage': 'cloud'
            }

        except Exception as e:
            print(f"[Cloudinary] Upload failed (offline?): {e}")
            print("[Cloudinary] Falling back to local storage...")

    # Fallback: save locally
    try:
        local_path = os.path.join(LOCAL_SAVE_DIR, filename)
        with open(local_path, 'wb') as f:
            f.write(image_bytes)

        print(f"[Storage] Saved locally: {local_path}")
        return {
            'url': f'/data/signatures/{filename}',
            'secure_url': None,
            'public_id': None,
            'width': 0,
            'height': 0,
            'storage': 'local'
        }
    except Exception as e:
        print(f"[Storage] Local save also failed: {e}")
        return None


def delete_signature(public_id):
    """
    Delete a signature image from Cloudinary.

    Args:
        public_id: Cloudinary public ID of the image

    Returns:
        bool: True if deleted successfully
    """
    if not _cloudinary_configured or not public_id:
        return False

    try:
        result = cloudinary.uploader.destroy(public_id, resource_type="image")
        return result.get('result') == 'ok'
    except Exception as e:
        print(f"[Cloudinary] Delete failed: {e}")
        return False


def list_signatures():
    """
    List all signature images stored in Cloudinary.

    Returns:
        list: List of dicts with image info, or empty list on failure
    """
    if not _cloudinary_configured:
        return []

    try:
        result = cloudinary.api.resources(
            type="upload",
            prefix=SIGNATURE_FOLDER,
            resource_type="image",
            max_results=100
        )

        images = []
        for resource in result.get('resources', []):
            images.append({
                'public_id': resource.get('public_id', ''),
                'url': resource.get('url', ''),
                'secure_url': resource.get('secure_url', ''),
                'filename': os.path.basename(resource.get('public_id', '')),
                'created_at': resource.get('created_at', ''),
                'width': resource.get('width', 0),
                'height': resource.get('height', 0),
                'bytes': resource.get('bytes', 0)
            })

        return images

    except Exception as e:
        print(f"[Cloudinary] List failed: {e}")
        return []
