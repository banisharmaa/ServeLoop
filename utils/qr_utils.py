"""
utils/qr_utils.py

Small utility to generate QR codes for ServeLoop events.

Functions:
- generate_qr_token(length=16): returns a URL-safe token (string)
- qr_png_bytes(token, box_size=10, border=4): returns PNG bytes for the given token
- qr_data_url(token): returns a data URL (image/png;base64,...) suitable for embedding in Streamlit st.image
- save_qr_to_path(token, path): save PNG to disk

Dependencies: qrcode, Pillow

Example usage in Streamlit:

from utils.qr_utils import generate_qr_token, qr_data_url
qr = generate_qr_token()
img_data_url = qr_data_url(qr)
st.image(img_data_url)

"""
from io import BytesIO
import base64
import secrets
import qrcode
from qrcode.constants import ERROR_CORRECT_M


def generate_qr_token(length: int = 16) -> str:
    """Generate a url-safe token for event QR codes.

    Args:
        length: number of chars in the token (approximate; uses urlsafe base64 truncation)
    Returns:
        str: token
    """
    return secrets.token_urlsafe(length)[:length]


def qr_png_bytes(token: str, box_size: int = 10, border: int = 4) -> bytes:
    """Return PNG bytes for the given token.

    Args:
        token: string to encode in the QR
        box_size: size of each box in pixels
        border: border width (boxes)
    Returns:
        bytes: PNG image bytes
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio.read()


def qr_data_url(token: str, box_size: int = 10, border: int = 4) -> str:
    """Return a data URL (base64) for embedding in HTML or Streamlit.

    Example: st.image(qr_data_url(token))
    """
    png = qr_png_bytes(token, box_size=box_size, border=border)
    b64 = base64.b64encode(png).decode()
    return f"data:image/png;base64,{b64}"


def save_qr_to_path(token: str, path: str, box_size: int = 10, border: int = 4) -> None:
    """Save QR PNG to a filesystem path.

    Args:
        token: token to encode
        path: destination file path (should end with .png)
    """
    png = qr_png_bytes(token, box_size=box_size, border=border)
    with open(path, "wb") as f:
        f.write(png)


# Quick self-test when run directly
if __name__ == "__main__":
    t = generate_qr_token()
    print("Token:", t)
    durl = qr_data_url(t)
    # save to file for manual inspection
    save_qr_to_path(t, f"qr_{t}.png")
    print("Saved qr_{}.png".format(t))
