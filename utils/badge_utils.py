"""
utils/badge_utils.py

Generate dynamic badge images for ServeLoop using Pillow.

Functions:
- badge_level(hours, events): simple rule to pick badge tier (Bronze/Silver/Gold/Platinum)
- generate_badge_image(title, subtitle, size=(400,240), bg_color="#FFFFFF", accent_color="#2B7A78"): returns PIL Image
- badge_image_bytes(img, fmt="PNG"): return PNG bytes
- badge_data_url(img): return data URL (useful for Streamlit st.image)
- save_badge(img, path): save image to disk
- generate_user_badge(user_name, hours, events, outfile=None): convenience to produce badge image/file with computed tier

This is lightweight and dependency-light (Pillow required). Works well for hackathon MVP.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
import base64
from typing import Tuple

# Attempt to load a TTF font if available; fallback to default
try:
    # Common system font paths; adjust if not available
    FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    FONT_BOLD = ImageFont.truetype(FONT_PATH, size=36)
    FONT_REGULAR = ImageFont.truetype(FONT_PATH, size=18)
except Exception:
    FONT_BOLD = ImageFont.load_default()
    FONT_REGULAR = ImageFont.load_default()


def badge_level(hours: int, events: int) -> Tuple[str, int]:
    """Decide badge tier based on hours/events.

    Returns (tier_name, tier_score)
    """
    score = hours + events * 2
    if score >= 100:
        return "Platinum", 4
    if score >= 50:
        return "Gold", 3
    if score >= 20:
        return "Silver", 2
    return "Bronze", 1


def generate_badge_image(title: str, subtitle: str, size: Tuple[int, int] = (400, 240), bg_color: str = "#FFFFFF", accent_color: str = "#2B7A78") -> Image.Image:
    """Create a badge PIL image with title and subtitle.

    Args:
        title: main text (e.g., user name)
        subtitle: secondary text (e.g., "100 hrs • 12 events • Gold")
        size: (width, height)
        bg_color: background color
        accent_color: color for ribbons / accents
    Returns:
        PIL.Image
    """
    w, h = size
    img = Image.new("RGBA", (w, h), bg_color)
    draw = ImageDraw.Draw(img)

    # soft rounded rectangle background
    radius = 18
    # draw rounded rectangle manually
    rect = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rdraw = ImageDraw.Draw(rect)
    rdraw.rounded_rectangle([(4, 4), (w-4, h-4)], radius=radius, fill=bg_color)
    img = Image.alpha_composite(img, rect)
    draw = ImageDraw.Draw(img)

    # accent bar on top
    bar_height = int(h * 0.22)
    draw.rectangle([0, 0, w, bar_height], fill=accent_color)

    # badge circle / emblem on left
    emblem_radius = int(h * 0.22)
    emblem_center = (int(w * 0.12 + emblem_radius), int(bar_height / 2 + emblem_radius / 2))
    ex = emblem_center[0] - emblem_radius
    ey = emblem_center[1] - emblem_radius
    draw.ellipse([ex, ey, ex + emblem_radius*2, ey + emblem_radius*2], fill="#FFFFFF")
    # small inner circle
    draw.ellipse([ex+6, ey+6, ex + emblem_radius*2-6, ey + emblem_radius*2-6], fill=accent_color)

    # Title text (on bar)
    t_x = emblem_center[0] + emblem_radius + 12
    t_y = int(bar_height/2 - 18)
    draw.text((t_x, t_y), title, font=FONT_BOLD, fill="#FFFFFF")

    # Subtitle and details below
    detail_x = int(w * 0.06)
    detail_y = int(bar_height + 20)
    draw.text((detail_x, detail_y), subtitle, font=FONT_REGULAR, fill="#222222")

    # ribbon / tier tag on right
    tier_box_w = int(w * 0.28)
    tier_box_h = int(h * 0.16)
    tier_x0 = w - tier_box_w - 20
    tier_y0 = int(h * 0.5 - tier_box_h/2)
    draw.rounded_rectangle([tier_x0, tier_y0, tier_x0 + tier_box_w, tier_y0 + tier_box_h], radius=12, fill=accent_color)
    # tier text placeholder (we'll fill later externally if needed)
    return img


def badge_image_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    buf = BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.read()


def badge_data_url(img: Image.Image, fmt: str = "PNG") -> str:
    b = badge_image_bytes(img, fmt=fmt)
    b64 = base64.b64encode(b).decode()
    return f"data:image/{fmt.lower()};base64,{b64}"


def save_badge(img: Image.Image, path: str, fmt: str = "PNG") -> None:
    img.save(path, format=fmt)


def generate_user_badge(user_name: str, hours: int, events: int, outfile: str = None) -> Image.Image:
    """Convenience: generate a badge image for a user and optionally save to outfile.

    Subtitle format: "{hours} hrs • {events} events • {Tier}".
    """
    tier_name, _score = badge_level(hours, events)
    subtitle = f"{hours} hrs • {events} events • {tier_name}"
    # choose accent color by tier
    accent_map = {"Bronze": "#B87333", "Silver": "#C0C0C0", "Gold": "#D4AF37", "Platinum": "#E5E4E2"}
    accent = accent_map.get(tier_name, "#2B7A78")
    img = generate_badge_image(user_name, subtitle, accent_color=accent)

    # draw tier text onto ribbon
    draw = ImageDraw.Draw(img)
    w, h = img.size
    tier_box_w = int(w * 0.28)
    tier_box_h = int(h * 0.16)
    tier_x0 = w - tier_box_w - 20
    tier_y0 = int(h * 0.5 - tier_box_h/2)
    # center text
    try:
        font_tier = ImageFont.truetype(FONT_PATH, size=20)
    except Exception:
        font_tier = ImageFont.load_default()
    text = tier_name.upper()
    tw, th = draw.textsize(text, font=font_tier)
    tx = tier_x0 + (tier_box_w - tw)/2
    ty = tier_y0 + (tier_box_h - th)/2
    draw.text((tx, ty), text, font=font_tier, fill="#111111")

    if outfile:
        save_badge(img, outfile)
    return img


# Quick self-test
if __name__ == "__main__":
    img = generate_user_badge("Alice", hours=42, events=7, outfile="alice_badge.png")
    print("Saved alice_badge.png")
