"""
config/settings.py

Centralized configuration settings for ServeLoop.
Loads environment variables and provides app-wide constants.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# -------------------------
# Cloudinary
# -------------------------
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

# -------------------------
# Database
# -------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///serveloop.db")

# -------------------------
# AI / Automation
# -------------------------
HUGGINGFACE_SUMMARY_MODEL = os.getenv("HUGGINGFACE_SUMMARY_MODEL", "facebook/bart-large-cnn")
HUGGINGFACE_IMAGE_TAGGER = os.getenv("HUGGINGFACE_IMAGE_TAGGER", "google/vit-base-patch16-224")

# -------------------------
# Streamlit Settings
# -------------------------
STREAMLIT_SERVER_PORT = int(os.getenv("STREAMLIT_SERVER_PORT", 8501))
STREAMLIT_SERVER_ADDRESS = os.getenv("STREAMLIT_SERVER_ADDRESS", "0.0.0.0")

# -------------------------
# App Constants
# -------------------------
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "supersecretkey")