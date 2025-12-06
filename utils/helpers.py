"""
utils/helpers.py

Generic helper utilities for ServeLoop.
Contains small reusable functions shared across pages and modules.
"""
import uuid
import datetime
import base64
from typing import Optional
import streamlit as st

# -----------------------------
# ID + Timestamp Helpers
# -----------------------------
def generate_id() -> str:
    """Generate a short UUID string."""
    return uuid.uuid4().hex[:12]


def current_timestamp() -> str:
    """Return current timestamp as ISO string."""
    return datetime.datetime.utcnow().isoformat()

# -----------------------------
# Streamlit Helpers
# -----------------------------
def toast(msg: str, type_: str = "info"):
    """Show quick toast-like feedback in Streamlit."""
    if type_ == "success":
        st.success(msg)
    elif type_ == "error":
        st.error(msg)
    elif type_ == "warning":
        st.warning(msg)
    else:
        st.info(msg)


# -----------------------------
# Media Helpers (fallback)
# -----------------------------
def file_to_base64(file_bytes: bytes) -> str:
    """Convert bytes to base64 string for inline fallback media display."""
    return base64.b64encode(file_bytes).decode("utf-8")


def build_data_url(file_bytes: bytes, mime: str) -> str:
    """Return a data: URL string for inline images/videos (Cloudinary fallback)."""
    b64 = file_to_base64(file_bytes)
    return f"data:{mime};base64,{b64}"


# -----------------------------
# Validation Helpers
# -----------------------------
def validate_event_fields(title: str, category: str, date: str) -> Optional[str]:
    """Validate create-event inputs. Returns error message or None."""
    if not title.strip():
        return "Title is required."
    if not category.strip():
        return "Category is required."
    if not date:
        return "Event date is required."
    return None


# -----------------------------
# Safe Int Helper
# -----------------------------
def to_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default