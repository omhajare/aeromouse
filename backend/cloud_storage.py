"""
Cloudinary Cloud Storage Module
Handles uploading and deleting signature images to/from Cloudinary.
Reads credentials from environment variables.
"""

import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Configure Cloudinary from environment
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET'),
    secure=True
)

# Cloudinary folder for all signature images
SIGNATURE_FOLDER = "aero-mouse/signatures"


def upload_signature(image_bytes, filename):
    """
    Upload a signature image to Cloudinary.

    Args:
        image_bytes: PNG image as bytes
        filename: Original filename (used as public_id base)

    Returns:
        dict: {
            'url': Full Cloudinary URL,
            'public_id': Cloudinary public ID (needed for deletion),
            'secure_url': HTTPS URL
        }
        None if upload fails
    """
    try:
        # Remove file extension for public_id
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
            'height': result.get('height', 0)
        }

    except Exception as e:
        print(f"[Cloudinary] Upload failed: {e}")
        return None


def delete_signature(public_id):
    """
    Delete a signature image from Cloudinary.

    Args:
        public_id: Cloudinary public ID of the image

    Returns:
        bool: True if deleted successfully
    """
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
