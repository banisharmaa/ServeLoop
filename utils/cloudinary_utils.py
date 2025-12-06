"""
utils/cloudinary_utils.py

Handles Cloudinary media uploads for ServeLoop.
Supports images and videos.

Functions:
- init_cloudinary(): call once at startup using env vars
- upload_image(file_bytes): returns secure URL
- upload_video(file_bytes): returns secure URL
- upload_generic(file_bytes, resource_type="auto")

Make sure your .env contains:
CLOUDINARY_CLOUD_NAME="your-cloud-name"
CLOUDINARY_API_KEY="your-api-key"
CLOUDINARY_API_SECRET="your-secret"
"""

import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
from typing import Optional


# --------------------------
# Initialization
# --------------------------
def init_cloudinary():
    """Initialize Cloudinary using env vars.
    Call this once at startup (e.g., in app.py).
    """
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        secure=True
    )


# --------------------------
# Upload Functions
# --------------------------
def upload_generic(file_bytes: bytes, resource_type: str = "auto") -> Optional[str]:
    """Upload any binary media to Cloudinary.

    Args:
        file_bytes: raw bytes of uploaded file
        resource_type: "image", "video", or "auto"

    Returns:
        secure_url (str) or None
    """
    try:
        resp = cloudinary.uploader.upload(
            file_bytes,
            resource_type=resource_type,
            folder="serveloop/uploads"
        )
        return resp.get("secure_url")
    except Exception as e:
        print("Cloudinary upload error:", e)
        return None


def upload_image(file_bytes: bytes) -> Optional[str]:
    """Uploads an image and returns secure URL."""
    return upload_generic(file_bytes, resource_type="image")


def upload_video(file_bytes: bytes) -> Optional[str]:
    """Uploads a video and returns secure URL."""
    return upload_generic(file_bytes, resource_type="video")


# Quick test
if __name__ == "__main__":
    init_cloudinary()
    print("Cloudinary initialized.")